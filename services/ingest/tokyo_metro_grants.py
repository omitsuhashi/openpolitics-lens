from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

from ingest.contracts import (
    ConnectorDefinition,
    DiscoveryRecord,
    FetchManifestRecord,
    JurisdictionProfile,
    SourceDocumentCandidate,
    SourceFamily,
)
from ingest.filesystem import FileSystemOutputWriter


@dataclass(frozen=True, slots=True)
class TokyoMetroGrantsConfig:
    allowed_hosts: tuple[str, ...]
    theme_keywords: tuple[str, ...]
    grant_keywords: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FakeTokyoMetroGrantsResponse:
    content: bytes
    media_type: str = "text/html; charset=utf-8"
    http_status: int = 200


@dataclass(frozen=True, slots=True)
class _Anchor:
    href: str
    title: str


TOKYO_METRO_GRANTS_CONFIG = TokyoMetroGrantsConfig(
    allowed_hosts=(
        "www.metro.tokyo.lg.jp",
        "www.kyoiku.metro.tokyo.lg.jp",
        "www.kodomoseisaku.metro.tokyo.lg.jp",
        "www.fukushi.metro.tokyo.lg.jp",
    ),
    theme_keywords=(
        "教育",
        "子供",
        "子ども",
        "こども",
        "若者",
        "子育て",
        "学校",
        "保育",
    ),
    grant_keywords=("助成", "補助"),
)

TOKYO_METRO_GRANTS_CONNECTOR = ConnectorDefinition(
    connector_id="jp_tokyo.metro_grants.v1",
    connector_version="2026-07-05",
    jurisdiction=JurisdictionProfile(
        jurisdiction_id="jp-tokyo",
        jurisdiction_level="prefecture",
        country_code="JP",
        subdivision_code="JP-13",
        municipality_code=None,
        display_name="東京都",
    ),
    source_family=SourceFamily(
        source_family="tokyo_metro_grants",
        source_system="tokyo_metropolitan_government",
        display_name="東京都助成・補助金",
    ),
    start_url="https://www.metro.tokyo.lg.jp/purpose/grant",
    rate_limit_policy="fixture-only; live network fetch is disabled by default",
    terms_note="official Tokyo Metropolitan Government public website pages",
)


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[_Anchor] = []
        self._active_href: str | None = None
        self._active_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a" or self._active_href is not None:
            return

        href = dict(attrs).get("href")
        if href is None:
            return

        self._active_href = href
        self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_href is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_href is None:
            return

        self.anchors.append(
            _Anchor(
                href=self._active_href,
                title=_collapse_whitespace("".join(self._active_text)),
            )
        )
        self._active_href = None
        self._active_text = []


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _canonicalize_url(href: str, parent_url: str) -> str:
    joined_url, _fragment = urldefrag(urljoin(parent_url, href.strip()))
    parsed = urlparse(joined_url)
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower()).geturl()


def _host_is_allowed(canonical_url: str, config: TokyoMetroGrantsConfig) -> bool:
    hostname = urlparse(canonical_url).hostname
    return hostname in config.allowed_hosts


def _matched_keywords(
    title: str, canonical_url: str, config: TokyoMetroGrantsConfig
) -> tuple[str, ...]:
    haystack = f"{title} {canonical_url}"
    theme_matches = tuple(keyword for keyword in config.theme_keywords if keyword in haystack)
    grant_matches = tuple(keyword for keyword in config.grant_keywords if keyword in haystack)

    if not theme_matches or not grant_matches:
        return ()

    return (*theme_matches, *grant_matches)


def _extension_from_media_type(media_type: str) -> str:
    normalized = media_type.lower()
    if "text/html" in normalized:
        return "html"
    if "application/pdf" in normalized:
        return "pdf"
    return "bin"


class FakeTokyoMetroGrantsFetcher:
    def __init__(
        self,
        responses: Mapping[str, bytes | FakeTokyoMetroGrantsResponse],
    ) -> None:
        self._responses = {
            canonical_url: self._coerce_response(response)
            for canonical_url, response in responses.items()
        }

    def fetch(self, canonical_url: str) -> FakeTokyoMetroGrantsResponse:
        try:
            return self._responses[canonical_url]
        except KeyError as exc:
            msg = f"fake fetch response is not registered: {canonical_url}"
            raise KeyError(msg) from exc

    @staticmethod
    def _coerce_response(
        response: bytes | FakeTokyoMetroGrantsResponse,
    ) -> FakeTokyoMetroGrantsResponse:
        if isinstance(response, bytes):
            return FakeTokyoMetroGrantsResponse(content=response)
        return response


class TokyoMetroGrantsConnector:
    def __init__(
        self,
        *,
        definition: ConnectorDefinition = TOKYO_METRO_GRANTS_CONNECTOR,
        config: TokyoMetroGrantsConfig = TOKYO_METRO_GRANTS_CONFIG,
    ) -> None:
        self.definition = definition
        self.config = config

    def discover_from_html(
        self,
        html: str,
        *,
        discovered_at: datetime,
        output_writer: FileSystemOutputWriter | None = None,
        run_id: str | None = None,
        parent_url: str | None = None,
    ) -> tuple[DiscoveryRecord, ...]:
        if output_writer is not None and run_id is None:
            msg = "run_id is required when output_writer is provided"
            raise ValueError(msg)

        parser = _AnchorParser()
        parser.feed(html)

        effective_parent_url = parent_url or self.definition.start_url
        records_by_url: dict[str, DiscoveryRecord] = {}
        for anchor in parser.anchors:
            if not anchor.href or not anchor.title:
                continue

            canonical_url = _canonicalize_url(anchor.href, effective_parent_url)
            if not _host_is_allowed(canonical_url, self.config):
                continue

            matched_keywords = _matched_keywords(anchor.title, canonical_url, self.config)
            if not matched_keywords or canonical_url in records_by_url:
                continue

            records_by_url[canonical_url] = DiscoveryRecord(
                connector=self.definition,
                canonical_url=canonical_url,
                discovered_at=discovered_at,
                parent_url=effective_parent_url,
                candidate_type="grant_program_page_candidate",
                title=anchor.title,
                matched_keywords=matched_keywords,
                relevance_reason=(
                    "allowlist host かつ教育・子育て関連 keyword に一致: "
                    + ", ".join(matched_keywords)
                ),
            )

        records = tuple(records_by_url[canonical_url] for canonical_url in sorted(records_by_url))

        if output_writer is not None and run_id is not None:
            for record in records:
                output_writer.append_jsonl(run_id=run_id, name="discovered", record=record)

        return records

    def fetch_candidates(
        self,
        candidates: Iterable[DiscoveryRecord],
        *,
        fetcher: FakeTokyoMetroGrantsFetcher,
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
                source_type="grant_program_page",
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
            output_writer.append_jsonl(run_id=run_id, name="fetched", record=record)
            records.append(record)

        return tuple(records)
