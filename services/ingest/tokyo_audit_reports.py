from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

from ingest.contracts import (
    ConnectorDefinition,
    FetchManifestRecord,
    JsonDict,
    JurisdictionProfile,
    SourceDocumentCandidate,
    SourceFamily,
)
from ingest.filesystem import FileSystemOutputWriter

AUDIT_REPORT_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "financial_aid_organization_audit_report",
        "comprehensive_external_audit_report",
        "audit_measure_status_report",
    }
)
LOCAL_FIXTURE_OPERATION = "local_fixture_read"

TOKYO_AUDIT_REPORTS_CONNECTOR = ConnectorDefinition(
    connector_id="jp_tokyo.audit_reports.v1",
    connector_version="2026-07-07",
    jurisdiction=JurisdictionProfile(
        jurisdiction_id="jp-tokyo",
        jurisdiction_level="prefecture",
        country_code="JP",
        subdivision_code="JP-13",
        municipality_code=None,
        display_name="東京都",
    ),
    source_family=SourceFamily(
        source_family="tokyo_audit_reports",
        source_system="tokyo_audit_and_inspection_office",
        display_name="東京都監査事務局 監査報告",
    ),
    start_url="https://www.kansa.metro.tokyo.lg.jp/",
    rate_limit_policy="fixture-only; live acquisition requires a manual gate",
    terms_note="official Tokyo audit and inspection office public website pages",
)


@dataclass(frozen=True, slots=True)
class FakeTokyoAuditReportsResponse:
    content: bytes
    media_type: str = "text/html; charset=utf-8"
    http_status: int = 200


@dataclass(frozen=True, slots=True)
class AuditReportIndexRecord:
    connector: ConnectorDefinition
    canonical_url: str
    discovered_at: datetime
    parent_url: str
    source_type: str
    title: str
    operations: tuple[str, ...] = (LOCAL_FIXTURE_OPERATION,)

    def __post_init__(self) -> None:
        if self.source_type not in AUDIT_REPORT_SOURCE_TYPES:
            msg = f"unsupported audit report source_type: {self.source_type}"
            raise ValueError(msg)

    def to_json_dict(self) -> JsonDict:
        return {
            **self.connector.identity_json_dict(),
            "canonical_url": self.canonical_url,
            "discovered_at": _datetime_to_json(self.discovered_at),
            "parent_url": self.parent_url,
            "source_type": self.source_type,
            "title": self.title,
            "operations": list(self.operations),
        }


@dataclass(frozen=True, slots=True)
class _AuditAnchor:
    href: str
    title: str
    source_type: str


class _AuditIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[_AuditAnchor] = []
        self._active_href: str | None = None
        self._active_source_type: str | None = None
        self._active_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a" or self._active_href is not None:
            return

        attr_map = dict(attrs)
        href = attr_map.get("href")
        source_type = attr_map.get("data-source-type")
        if href is None or source_type is None:
            return

        self._active_href = href
        self._active_source_type = source_type
        self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_href is None or self._active_source_type is None:
            return

        self.anchors.append(
            _AuditAnchor(
                href=self._active_href,
                title=_collapse_whitespace("".join(self._active_text)),
                source_type=self._active_source_type,
            )
        )
        self._active_href = None
        self._active_source_type = None
        self._active_text = []


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _canonicalize_url(href: str, parent_url: str) -> str:
    joined_url, _fragment = urldefrag(urljoin(parent_url, href.strip()))
    parsed = urlparse(joined_url)
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower()).geturl()


def _extension_from_media_type(media_type: str) -> str:
    normalized = media_type.lower()
    if "text/html" in normalized:
        return "html"
    if "application/pdf" in normalized:
        return "pdf"
    return "bin"


def build_audit_report_fixture_html(
    *,
    title: str,
    source_type: str,
    fiscal_year: str,
    audited_entity: str,
    finding_text: str,
    measure_status: str,
) -> bytes:
    if source_type not in AUDIT_REPORT_SOURCE_TYPES:
        msg = f"unsupported audit report source_type: {source_type}"
        raise ValueError(msg)

    html = f"""<!doctype html>
<html lang="ja">
  <head>
    <meta charset="utf-8">
    <title>{escape(title)}</title>
  </head>
  <body>
    <article class="audit-report">
      <h1>{escape(title)}</h1>
      <section
        class="audit-finding"
        data-finding-id="fixture-finding-1"
        data-source-type="{source_type}"
      >
        <p data-field="fiscal_year">{escape(fiscal_year)}</p>
        <p data-field="audited_entity">{escape(audited_entity)}</p>
        <p data-field="finding_text">{escape(finding_text)}</p>
        <p data-field="measure_status">{escape(measure_status)}</p>
      </section>
    </article>
  </body>
</html>
"""
    return html.encode("utf-8")


class FakeTokyoAuditReportsFetcher:
    def __init__(
        self,
        responses: Mapping[str, bytes | FakeTokyoAuditReportsResponse],
    ) -> None:
        self._responses = {
            canonical_url: self._coerce_response(response)
            for canonical_url, response in responses.items()
        }

    def fetch(self, canonical_url: str) -> FakeTokyoAuditReportsResponse:
        try:
            return self._responses[canonical_url]
        except KeyError as exc:
            msg = f"fake fetch response is not registered: {canonical_url}"
            raise KeyError(msg) from exc

    @staticmethod
    def _coerce_response(
        response: bytes | FakeTokyoAuditReportsResponse,
    ) -> FakeTokyoAuditReportsResponse:
        if isinstance(response, bytes):
            return FakeTokyoAuditReportsResponse(content=response)
        return response


class TokyoAuditReportsConnector:
    def __init__(
        self,
        *,
        definition: ConnectorDefinition = TOKYO_AUDIT_REPORTS_CONNECTOR,
    ) -> None:
        self.definition = definition

    def discover_from_html(
        self,
        html: str,
        *,
        discovered_at: datetime,
        output_writer: FileSystemOutputWriter | None = None,
        run_id: str | None = None,
        parent_url: str | None = None,
    ) -> tuple[AuditReportIndexRecord, ...]:
        if output_writer is not None and run_id is None:
            msg = "run_id is required when output_writer is provided"
            raise ValueError(msg)

        parser = _AuditIndexParser()
        parser.feed(html)

        effective_parent_url = parent_url or self.definition.start_url
        records: list[AuditReportIndexRecord] = []
        seen_urls: set[str] = set()
        for anchor in parser.anchors:
            if not anchor.href or not anchor.title:
                continue
            canonical_url = _canonicalize_url(anchor.href, effective_parent_url)
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)
            records.append(
                AuditReportIndexRecord(
                    connector=self.definition,
                    canonical_url=canonical_url,
                    discovered_at=discovered_at,
                    parent_url=effective_parent_url,
                    source_type=anchor.source_type,
                    title=anchor.title,
                )
            )

        result = tuple(records)
        if output_writer is not None and run_id is not None:
            for record in result:
                output_writer.append_jsonl(run_id=run_id, name="audit_report_index", record=record)

        return result

    def fetch_candidates(
        self,
        candidates: Iterable[AuditReportIndexRecord],
        *,
        fetcher: FakeTokyoAuditReportsFetcher,
        output_writer: FileSystemOutputWriter,
        run_id: str,
        fetched_at: datetime,
    ) -> tuple[FetchManifestRecord, ...]:
        records: list[FetchManifestRecord] = []
        for candidate in candidates:
            response = fetcher.fetch(candidate.canonical_url)
            raw_artifact = output_writer.write_raw_artifact(
                content=response.content,
                jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
                source_family=self.definition.source_family.source_family,
                fetched_at=fetched_at,
                extension=_extension_from_media_type(response.media_type),
            )
            raw_artifact_path = raw_artifact.relative_path.as_posix()
            source_document_candidate = SourceDocumentCandidate(
                canonical_url=candidate.canonical_url,
                title=candidate.title,
                source_type=candidate.source_type,
                jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
                source_family=self.definition.source_family.source_family,
                language="ja",
                retrieved_at=fetched_at,
                raw_artifact_path=raw_artifact_path,
            )
            record = FetchManifestRecord(
                connector=self.definition,
                canonical_url=candidate.canonical_url,
                fetched_at=fetched_at,
                http_status=response.http_status,
                content_hash=raw_artifact.content_hash,
                media_type=response.media_type,
                byte_size=raw_artifact.byte_size,
                raw_artifact_path=raw_artifact_path,
                source_document_candidate=source_document_candidate,
            )
            output_writer.append_jsonl(run_id=run_id, name="audit_report_fetched", record=record)
            records.append(record)

        return tuple(records)
