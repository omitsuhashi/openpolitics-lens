import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

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
class FakeNdlDietMinutesResponse:
    content: bytes
    media_type: str
    http_status: int = 200


NDL_DIET_MINUTES_CONNECTOR = ConnectorDefinition(
    connector_id="jp.ndl_diet_minutes.v1",
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
        source_family="jp_ndl_diet_minutes",
        source_system="national_diet_library",
        display_name="国立国会図書館 国会会議録検索システム",
    ),
    start_url="https://kokkai.ndl.go.jp/api/meeting",
    rate_limit_policy=(
        "fixture-only; preserve API pagination, request parameters, and rate limit metadata"
    ),
    terms_note="official National Diet Library Diet minutes API fixture content",
)


class FakeNdlDietMinutesFetcher:
    def __init__(
        self,
        responses: Mapping[str, tuple[bytes, str] | FakeNdlDietMinutesResponse],
    ) -> None:
        self._responses = {
            canonical_url: self._coerce_response(response)
            for canonical_url, response in responses.items()
        }

    def fetch(self, canonical_url: str) -> FakeNdlDietMinutesResponse:
        try:
            return self._responses[canonical_url]
        except KeyError as exc:
            raise KeyError(f"fake fetch response is not registered: {canonical_url}") from exc

    @staticmethod
    def _coerce_response(
        response: tuple[bytes, str] | FakeNdlDietMinutesResponse,
    ) -> FakeNdlDietMinutesResponse:
        if isinstance(response, FakeNdlDietMinutesResponse):
            return response
        content, media_type = response
        return FakeNdlDietMinutesResponse(content=content, media_type=media_type)


def _required_str(data: dict[str, object], field_name: str) -> str:
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _required_dict(data: dict[str, object], field_name: str) -> dict[str, object]:
    value = data.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_list(data: dict[str, object], field_name: str) -> list[object]:
    value = data.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _extension_from_media_type(media_type: str) -> str:
    normalized = media_type.lower()
    if "json" in normalized:
        return "json"
    if "xml" in normalized:
        return "xml"
    return "bin"


def _metadata_from_search_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "pagination": {
            "next_record_position": payload.get("nextRecordPosition"),
            "number_of_records": payload.get("numberOfRecords"),
            "number_of_return": payload.get("numberOfReturn"),
            "maximum_records": payload.get("maximumRecords"),
        },
        "request_params": _required_dict(payload, "request"),
        "rate_limit": _required_str(payload, "rateLimit"),
    }


class NdlDietMinutesConnector:
    def __init__(
        self,
        *,
        definition: ConnectorDefinition = NDL_DIET_MINUTES_CONNECTOR,
    ) -> None:
        self.definition = definition

    def discover_from_search_json(
        self,
        payload: str,
        *,
        discovered_at: datetime,
        output_writer: FileSystemOutputWriter | None = None,
        run_id: str | None = None,
    ) -> tuple[DiscoveryRecord, ...]:
        if output_writer is not None and run_id is None:
            raise ValueError("run_id is required when output_writer is provided")

        search_payload = json.loads(payload)
        if not isinstance(search_payload, dict):
            raise ValueError("search payload must be an object")

        search_metadata = _metadata_from_search_payload(search_payload)
        discovered: list[DiscoveryRecord] = []
        for item in _required_list(search_payload, "records"):
            if not isinstance(item, dict):
                raise ValueError("records must contain objects")
            record_id = _required_str(item, "recordId")
            house_name = _required_str(item, "nameOfHouse")
            meeting_name = _required_str(item, "nameOfMeeting")
            issue = _required_str(item, "issue")
            meeting_date = _required_str(item, "meetingDate")
            meeting_api_url = _required_str(item, "meetingApiUrl")
            if urlparse(meeting_api_url).scheme not in {"http", "https"}:
                raise ValueError("meetingApiUrl must be http(s)")

            common_metadata = {"record_id": record_id, **search_metadata}
            discovered.append(
                DiscoveryRecord(
                    connector=self.definition,
                    canonical_url=meeting_api_url,
                    discovered_at=discovered_at,
                    parent_url=self.definition.start_url,
                    candidate_type="meeting_record_candidate",
                    title=f"{house_name} {meeting_name} {issue}会議録",
                    matched_keywords=(house_name, meeting_name, "会議録"),
                    relevance_reason=(
                        "official API meeting record listed in fixture search response"
                    ),
                    metadata=common_metadata,
                )
            )

            speech_records = _required_list(item, "speechRecord")
            for speech_item in speech_records:
                if not isinstance(speech_item, dict):
                    raise ValueError("speechRecord must contain objects")
                speech_id = _required_str(speech_item, "speechId")
                speaker = _required_str(speech_item, "speaker")
                speech_api_url = _required_str(speech_item, "speechApiUrl")
                discovered.append(
                    DiscoveryRecord(
                        connector=self.definition,
                        canonical_url=speech_api_url,
                        discovered_at=discovered_at,
                        parent_url=meeting_api_url,
                        candidate_type="speech_record_candidate",
                        title=f"{speaker} 発言記録",
                        matched_keywords=(meeting_name, speaker, "発言"),
                        relevance_reason=(
                            "official API speech record listed in fixture search response"
                        ),
                        metadata={
                            **common_metadata,
                            "speech_id": speech_id,
                            "speaker": speaker,
                            "meeting_date": meeting_date,
                        },
                    )
                )

        records = tuple(discovered)
        if output_writer is not None and run_id is not None:
            for record in records:
                output_writer.append_jsonl(run_id=run_id, name="discovered", record=record)
        return records

    def fetch_candidates(
        self,
        candidates: Iterable[DiscoveryRecord],
        *,
        fetcher: FakeNdlDietMinutesFetcher,
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
            candidate_metadata = self._build_candidate_metadata(candidate, response.content)
            canonical_url = candidate_metadata.get("canonical_url", candidate.canonical_url)
            if not isinstance(canonical_url, str) or not canonical_url.strip():
                raise ValueError("canonical_url must be a non-empty string")
            source_document_candidate = SourceDocumentCandidate(
                canonical_url=canonical_url,
                title=candidate.title,
                source_type=(
                    "meeting_record"
                    if candidate.candidate_type == "meeting_record_candidate"
                    else "speech_record"
                ),
                jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
                source_family=self.definition.source_family.source_family,
                language="ja",
                retrieved_at=fetched_at,
                raw_artifact_path=raw_artifact.relative_path.as_posix(),
                metadata=candidate_metadata,
            )
            record = FetchManifestRecord(
                connector=self.definition,
                canonical_url=canonical_url,
                request_url=candidate.canonical_url,
                fetched_at=fetched_at,
                http_status=response.http_status,
                content_hash=raw_artifact.content_hash,
                media_type=response.media_type,
                byte_size=len(response.content),
                raw_artifact_path=raw_artifact.relative_path.as_posix(),
                source_document_candidate=source_document_candidate,
                metadata={**(candidate.metadata or {}), "http_status": response.http_status},
            )
            output_writer.append_jsonl(run_id=run_id, name="fetched", record=record)
            records.append(record)
        return tuple(records)

    def _build_candidate_metadata(
        self,
        candidate: DiscoveryRecord,
        raw_content: bytes,
    ) -> dict[str, object]:
        metadata = dict(candidate.metadata or {})
        if candidate.candidate_type == "meeting_record_candidate":
            payload = json.loads(raw_content.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("meeting record payload must be an object")
            metadata.update(
                {
                    "canonical_url": _required_str(payload, "meetingRecordUrl"),
                    "meeting_record_url": _required_str(payload, "meetingRecordUrl"),
                    "record_id": _required_str(payload, "recordId"),
                    "meeting_date": _required_str(payload, "meetingDate"),
                    "publication_date": _required_str(payload, "issueDate"),
                    "name_of_house": _required_str(payload, "nameOfHouse"),
                    "name_of_meeting": _required_str(payload, "nameOfMeeting"),
                    "issue": _required_str(payload, "issue"),
                    "speech_count": payload.get("speechCount"),
                    "search_api_url": _required_str(payload, "searchApiUrl"),
                    "meeting_api_url": _required_str(payload, "meetingApiUrl"),
                }
            )
        return metadata
