import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from xml.etree import ElementTree

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
class FakeEgovPublicCommentResponse:
    content: bytes
    source_url: str | None = None
    media_type: str = "application/json; charset=utf-8"
    http_status: int = 200


EGOV_PUBLIC_COMMENT_CONNECTOR = ConnectorDefinition(
    connector_id="jp.egov_public_comment.v1",
    connector_version="2026-07-08",
    jurisdiction=JurisdictionProfile(
        jurisdiction_id="jp",
        jurisdiction_level="country",
        country_code="JP",
        subdivision_code=None,
        municipality_code=None,
        display_name="日本",
    ),
    source_family=SourceFamily(
        source_family="jp_public_comment",
        source_system="egov_public_comment",
        display_name="e-Gov パブリック・コメント",
    ),
    start_url="https://public-comment.e-gov.go.jp/rss/PCM1400.xml",
    rate_limit_policy="fixture-only; live network fetch is disabled by default",
    terms_note="official e-Gov public comment feed and detail payloads",
)


class FakeEgovPublicCommentFetcher:
    def __init__(
        self,
        responses: Mapping[str, bytes | FakeEgovPublicCommentResponse],
    ) -> None:
        self._responses = {
            canonical_url: self._coerce_response(response)
            for canonical_url, response in responses.items()
        }

    def fetch(self, canonical_url: str) -> FakeEgovPublicCommentResponse:
        try:
            return self._responses[canonical_url]
        except KeyError as exc:
            msg = f"fake fetch response is not registered: {canonical_url}"
            raise KeyError(msg) from exc

    @staticmethod
    def _coerce_response(
        response: bytes | FakeEgovPublicCommentResponse,
    ) -> FakeEgovPublicCommentResponse:
        if isinstance(response, bytes):
            return FakeEgovPublicCommentResponse(content=response)
        return response


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _parse_detail_payload(raw_payload: bytes) -> dict[str, object]:
    payload = json.loads(raw_payload.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("public comment detail payload must be a JSON object")
    return payload


def _required_payload_str(payload: dict[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required in public comment detail payload")
    return value.strip()


class EgovPublicCommentConnector:
    def __init__(
        self,
        *,
        definition: ConnectorDefinition = EGOV_PUBLIC_COMMENT_CONNECTOR,
    ) -> None:
        self.definition = definition

    def discover_from_rss(
        self,
        rss_xml: str,
        *,
        discovered_at: datetime,
        output_writer: FileSystemOutputWriter | None = None,
        run_id: str | None = None,
    ) -> tuple[DiscoveryRecord, ...]:
        if output_writer is not None and run_id is None:
            msg = "run_id is required when output_writer is provided"
            raise ValueError(msg)

        root = ElementTree.fromstring(rss_xml)
        records: list[DiscoveryRecord] = []
        for item in root.findall("./channel/item"):
            title = _collapse_whitespace(item.findtext("title", default=""))
            link = _collapse_whitespace(item.findtext("link", default=""))
            if not title or not link:
                continue
            record = DiscoveryRecord(
                connector=self.definition,
                canonical_url=link,
                discovered_at=discovered_at,
                parent_url=self.definition.start_url,
                candidate_type="public_comment_case_candidate",
                title=title,
                matched_keywords=("public_comment",),
                relevance_reason="official e-Gov RSS feed item",
            )
            records.append(record)

        ordered_records = tuple(sorted(records, key=lambda record: record.canonical_url))
        if output_writer is not None and run_id is not None:
            for record in ordered_records:
                output_writer.append_jsonl(run_id=run_id, name="discovered", record=record)
        return ordered_records

    def fetch_candidates(
        self,
        candidates: Iterable[DiscoveryRecord],
        *,
        fetcher: FakeEgovPublicCommentFetcher,
        output_writer: FileSystemOutputWriter,
        run_id: str,
        fetched_at: datetime,
    ) -> tuple[FetchManifestRecord, ...]:
        records: list[FetchManifestRecord] = []
        for candidate in candidates:
            response = fetcher.fetch(candidate.canonical_url)
            fetched_source_url = response.source_url or candidate.canonical_url
            payload = _parse_detail_payload(response.content)
            raw_artifact = output_writer.write_raw_artifact(
                content=response.content,
                jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
                source_family=self.definition.source_family.source_family,
                fetched_at=fetched_at,
                extension="json",
            )
            metadata = {
                "case_id": _required_payload_str(payload, "caseId"),
                "operator_name": _required_payload_str(payload, "ministry"),
                "public_page_url": candidate.canonical_url,
                "detail_api_url": fetched_source_url,
                "comment_start_date": _required_payload_str(payload, "commentStartDate"),
                "comment_end_text": _collapse_whitespace(
                    str(payload.get("commentEndText") or payload.get("commentEndDate") or "")
                ),
                "result_url": _required_payload_str(payload, "resultUrl"),
                "result_published_date": _required_payload_str(payload, "resultPublishedDate"),
            }
            warnings: list[str] = []
            comment_end_date = payload.get("commentEndDate")
            if isinstance(comment_end_date, str) and comment_end_date.strip():
                metadata["comment_end_date"] = comment_end_date.strip()
            else:
                warnings.append("comment_end_date_is_month_precision")
            source_document_candidate = SourceDocumentCandidate(
                canonical_url=fetched_source_url,
                title=_required_payload_str(payload, "title"),
                source_type="public_comment_case",
                jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
                source_family=self.definition.source_family.source_family,
                language="ja",
                retrieved_at=fetched_at,
                raw_artifact_path=raw_artifact.relative_path.as_posix(),
                metadata=metadata,
                warnings=tuple(warnings),
            )
            record = FetchManifestRecord(
                connector=self.definition,
                canonical_url=fetched_source_url,
                fetched_at=fetched_at,
                http_status=response.http_status,
                content_hash=raw_artifact.content_hash,
                media_type=response.media_type,
                byte_size=raw_artifact.byte_size,
                raw_artifact_path=raw_artifact.relative_path.as_posix(),
                source_document_candidate=source_document_candidate,
            )
            output_writer.append_jsonl(run_id=run_id, name="fetched", record=record)
            records.append(record)
        return tuple(records)
