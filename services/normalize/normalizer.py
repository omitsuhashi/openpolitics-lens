import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from normalize.contracts import (
    EventSourceAssertion,
    EvidenceClaim,
    EvidenceItem,
    NormalizeResult,
    OfficialPoliticalEventCandidate,
    SourceDocument,
)


@dataclass(frozen=True, slots=True)
class _ExtractedTitle:
    quote_text: str
    normalized_text: str
    source_span_start: int
    source_span_end: int


_TITLE_PATTERN = re.compile(rb"<title\b[^>]*>(?P<title>.*?)</title\s*>", re.IGNORECASE | re.DOTALL)


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _stable_uuid(*parts: object) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join(str(part) for part in parts)))


def _validate_candidate_invariants(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    expected_values = {
        "canonical_url": record.canonical_url,
        "raw_artifact_path": record.raw_artifact_path,
        "jurisdiction_id": record.connector.jurisdiction.jurisdiction_id,
        "source_family": record.connector.source_family.source_family,
    }
    actual_values = {
        "canonical_url": candidate.canonical_url,
        "raw_artifact_path": candidate.raw_artifact_path,
        "jurisdiction_id": candidate.jurisdiction_id,
        "source_family": candidate.source_family,
    }

    mismatches = [
        field_name
        for field_name, expected_value in expected_values.items()
        if actual_values[field_name] != expected_value
    ]
    if mismatches:
        fields = ", ".join(mismatches)
        msg = f"source_document_candidate invariant mismatch: {fields}"
        raise ValueError(msg)


def _validate_grant_program_page_input(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    if candidate.source_type != "grant_program_page":
        msg = f"unsupported source_type for grant page normalization: {candidate.source_type}"
        raise ValueError(msg)

    if "text/html" not in record.media_type.lower():
        msg = f"unsupported media_type for grant page normalization: {record.media_type}"
        raise ValueError(msg)


def _extract_title(raw_html: bytes) -> _ExtractedTitle:
    match = _TITLE_PATTERN.search(raw_html)
    if match is None:
        msg = "grant program page title is required"
        raise ValueError(msg)

    title_start, title_end = match.span("title")
    title_bytes = raw_html[title_start:title_end]
    stripped_title_bytes = title_bytes.strip()
    leading_whitespace = len(title_bytes) - len(title_bytes.lstrip())
    source_span_start = title_start + leading_whitespace
    source_span_end = source_span_start + len(stripped_title_bytes)
    quote_text = stripped_title_bytes.decode("utf-8")
    normalized_text = _collapse_whitespace(unescape(quote_text))
    if not normalized_text:
        msg = "grant program page title is empty"
        raise ValueError(msg)

    return _ExtractedTitle(
        quote_text=quote_text,
        normalized_text=normalized_text,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
    )


def _promote_source_document(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    title: str,
) -> SourceDocument:
    candidate = record.source_document_candidate
    source_document_id = _stable_uuid(
        "source_document",
        raw_artifact_id,
        record.connector.source_family.source_system,
        candidate.source_type,
        candidate.canonical_url,
        record.content_hash,
    )

    return SourceDocument(
        source_document_id=source_document_id,
        raw_artifact_id=raw_artifact_id,
        source_system=record.connector.source_family.source_system,
        source_type=candidate.source_type,
        canonical_url=candidate.canonical_url,
        title=title,
        published_at=None,
        retrieved_at=candidate.retrieved_at,
        raw_artifact_path=candidate.raw_artifact_path,
        content_hash=record.content_hash,
        license_note=record.connector.terms_note,
        source_reliability="official_source",
        jurisdiction_id=candidate.jurisdiction_id,
        source_family=candidate.source_family,
        language=candidate.language,
    )


def _build_title_evidence_item(
    *,
    source_document: SourceDocument,
    extracted_title: _ExtractedTitle,
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "html_title",
        extracted_title.source_span_start,
        extracted_title.source_span_end,
        extracted_title.quote_text,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="html_selector",
        location_value="title",
        source_span_start=extracted_title.source_span_start,
        source_span_end=extracted_title.source_span_end,
        quote_text=extracted_title.quote_text,
        normalized_text=extracted_title.normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="html_title",
        confidence=1.0,
    )


def _build_title_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "grant_program_page_title_observed",
        evidence_item.normalized_text,
    )

    return EvidenceClaim(
        evidence_claim_id=evidence_claim_id,
        claim_type="grant_program_page_title_observed",
        subject_ref=source_document.source_document_id,
        predicate="observed_page_title",
        object_ref=None,
        object_value=evidence_item.normalized_text,
        event_date=None,
        amount=None,
        currency=None,
        evidence_item_id=evidence_item.evidence_item_id,
        review_state="machine_extracted",
    )


def normalize_grant_program_page(
    record: FetchManifestRecord,
    raw_html: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    _validate_grant_program_page_input(record)
    extracted_title = _extract_title(raw_html)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=extracted_title.normalized_text,
    )
    evidence_item = _build_title_evidence_item(
        source_document=source_document,
        extracted_title=extracted_title,
    )
    evidence_claim = _build_title_claim(
        source_document=source_document,
        evidence_item=evidence_item,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=(evidence_claim,),
    )


def _required_metadata_str(metadata: dict[str, object], field_name: str) -> str:
    value = metadata.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be present in source document metadata")
    return value


def _date_to_utc_midnight(value: date) -> datetime:
    return datetime(value.year, value.month, value.day, tzinfo=UTC)


def _json_pointer_evidence_item(
    *,
    source_document: SourceDocument,
    location_value: str,
    quote_text: str,
    normalized_text: str,
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        location_value,
        quote_text,
    )
    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="api_json_pointer",
        location_value=location_value,
        source_span_start=0,
        source_span_end=0,
        quote_text=quote_text,
        normalized_text=normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="ndl_api_json_pointer",
        confidence=0.99,
    )


def _xml_path_evidence_item(
    *,
    source_document: SourceDocument,
    location_value: str,
    quote_text: str,
    normalized_text: str,
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        location_value,
        quote_text,
    )
    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="api_xml_path",
        location_value=location_value,
        source_span_start=0,
        source_span_end=0,
        quote_text=quote_text,
        normalized_text=normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="ndl_api_xml_path",
        confidence=0.99,
    )


def _claim(
    *,
    source_document_id: str,
    evidence_item: EvidenceItem,
    claim_type: str,
    predicate: str,
    object_value: str,
    event_date: date | None = None,
) -> EvidenceClaim:
    return EvidenceClaim(
        evidence_claim_id=_stable_uuid(
            "evidence_claim",
            evidence_item.evidence_item_id,
            claim_type,
        ),
        claim_type=claim_type,
        subject_ref=source_document_id,
        predicate=predicate,
        object_ref=None,
        object_value=object_value,
        event_date=event_date,
        amount=None,
        currency=None,
        evidence_item_id=evidence_item.evidence_item_id,
        review_state="machine_extracted",
    )


def _meeting_record_source_document(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    metadata: dict[str, object],
) -> SourceDocument:
    canonical_url = _required_metadata_str(metadata, "meeting_record_url")
    issue = _required_metadata_str(metadata, "issue")
    meeting_name = _required_metadata_str(metadata, "name_of_meeting")
    house_name = _required_metadata_str(metadata, "name_of_house")
    publication_date = date.fromisoformat(_required_metadata_str(metadata, "publication_date"))
    source_document_id = _stable_uuid(
        "source_document",
        raw_artifact_id,
        canonical_url,
        record.content_hash,
    )
    return SourceDocument(
        source_document_id=source_document_id,
        raw_artifact_id=raw_artifact_id,
        source_system=record.connector.source_family.source_system,
        source_type="meeting_record",
        canonical_url=canonical_url,
        title=f"{house_name} {meeting_name} {issue}会議録",
        published_at=_date_to_utc_midnight(publication_date),
        retrieved_at=record.fetched_at,
        raw_artifact_path=record.raw_artifact_path,
        content_hash=record.content_hash,
        license_note=record.connector.terms_note,
        source_reliability="official_source",
        jurisdiction_id=record.connector.jurisdiction.jurisdiction_id,
        source_family=record.connector.source_family.source_family,
        language="ja",
    )


def _speech_record_source_document(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    speaker: str,
) -> SourceDocument:
    source_document_id = _stable_uuid(
        "source_document",
        raw_artifact_id,
        record.canonical_url,
        record.content_hash,
    )
    return SourceDocument(
        source_document_id=source_document_id,
        raw_artifact_id=raw_artifact_id,
        source_system=record.connector.source_family.source_system,
        source_type="speech_record",
        canonical_url=record.canonical_url,
        title=f"{speaker} 発言記録",
        published_at=None,
        retrieved_at=record.fetched_at,
        raw_artifact_path=record.raw_artifact_path,
        content_hash=record.content_hash,
        license_note=record.connector.terms_note,
        source_reliability="official_source",
        jurisdiction_id=record.connector.jurisdiction.jurisdiction_id,
        source_family=record.connector.source_family.source_family,
        language="ja",
    )


def _meeting_record_event_candidate(
    *,
    record: FetchManifestRecord,
    source_document: SourceDocument,
    publication_evidence: EvidenceItem,
    metadata: dict[str, object],
) -> OfficialPoliticalEventCandidate:
    publication_date = date.fromisoformat(_required_metadata_str(metadata, "publication_date"))
    house_name = _required_metadata_str(metadata, "name_of_house")
    meeting_name = _required_metadata_str(metadata, "name_of_meeting")
    issue = _required_metadata_str(metadata, "issue")
    event_candidate_id = _stable_uuid(
        "official_event",
        record.connector.connector_id,
        _required_metadata_str(metadata, "record_id"),
        publication_date.isoformat(),
    )
    assertion = EventSourceAssertion(
        event_candidate_id=event_candidate_id,
        source_document_id=source_document.source_document_id,
        evidence_item_id=publication_evidence.evidence_item_id,
        asserted_field="scheduled_date",
        asserted_value=publication_date.isoformat(),
        asserted_at=record.fetched_at,
        source_priority=10,
        conflict_state="none",
        confidence=0.99,
        review_state="machine_extracted",
        limitations=("meeting_date preserved separately from record publication date",),
    )
    return OfficialPoliticalEventCandidate(
        event_candidate_id=event_candidate_id,
        event_family="Diet",
        event_type="meeting_record_published",
        jurisdiction_id=record.connector.jurisdiction.jurisdiction_id,
        jurisdiction_level=record.connector.jurisdiction.jurisdiction_level,
        source_system=record.connector.source_family.source_system,
        source_family=record.connector.source_family.source_family,
        connector_id=record.connector.connector_id,
        title=f"{house_name} {meeting_name} {issue}会議録",
        scheduled_date=publication_date,
        scheduled_time=None,
        timezone="Asia/Tokyo",
        date_precision="date",
        office_or_body=f"{house_name} {meeting_name}",
        event_status="published",
        canonical_url=source_document.canonical_url,
        source_document_id=source_document.source_document_id,
        evidence_item_id=publication_evidence.evidence_item_id,
        extraction_method="ndl_meeting_record_json",
        confidence=0.99,
        review_state="machine_extracted",
        limitations=("meeting_date preserved separately from record publication date",),
        source_assertions=(assertion,),
    )


def _normalize_ndl_meeting_record(
    record: FetchManifestRecord,
    raw_payload: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    payload = json.loads(raw_payload.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("meeting record payload must be an object")
    metadata = dict(record.source_document_candidate.metadata or {})
    metadata.setdefault("publication_date", payload.get("issueDate"))
    metadata.setdefault("meeting_date", payload.get("meetingDate"))
    source_document = _meeting_record_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        metadata=metadata,
    )
    publication_date = _required_metadata_str(metadata, "publication_date")
    meeting_date = _required_metadata_str(metadata, "meeting_date")
    publication_evidence = _json_pointer_evidence_item(
        source_document=source_document,
        location_value="/issueDate",
        quote_text=publication_date,
        normalized_text=publication_date,
    )
    meeting_evidence = _json_pointer_evidence_item(
        source_document=source_document,
        location_value="/meetingDate",
        quote_text=meeting_date,
        normalized_text=meeting_date,
    )
    publication_claim = _claim(
        source_document_id=source_document.source_document_id,
        evidence_item=publication_evidence,
        claim_type="meeting_record_publication_date_observed",
        predicate="record_publication_date",
        object_value=publication_date,
        event_date=date.fromisoformat(publication_date),
    )
    meeting_claim = _claim(
        source_document_id=source_document.source_document_id,
        evidence_item=meeting_evidence,
        claim_type="meeting_date_observed",
        predicate="meeting_date",
        object_value=meeting_date,
        event_date=date.fromisoformat(meeting_date),
    )
    event_candidate = _meeting_record_event_candidate(
        record=record,
        source_document=source_document,
        publication_evidence=publication_evidence,
        metadata=metadata,
    )
    return NormalizeResult(
        source_document=source_document,
        evidence_items=(publication_evidence, meeting_evidence),
        evidence_claims=(publication_claim, meeting_claim),
        event_candidates=(event_candidate,),
    )


def _normalize_ndl_speech_record(
    record: FetchManifestRecord,
    raw_payload: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    root = ET.fromstring(raw_payload.decode("utf-8"))
    speaker = root.findtext("speaker")
    if speaker is None or not speaker.strip():
        raise ValueError("speech speaker is required")
    source_document = _speech_record_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        speaker=speaker.strip(),
    )
    speaker_evidence = _xml_path_evidence_item(
        source_document=source_document,
        location_value="/speechRecord/speaker",
        quote_text=speaker.strip(),
        normalized_text=speaker.strip(),
    )
    speaker_claim = _claim(
        source_document_id=source_document.source_document_id,
        evidence_item=speaker_evidence,
        claim_type="speech_speaker_observed",
        predicate="speaker_name",
        object_value=speaker.strip(),
    )
    return NormalizeResult(
        source_document=source_document,
        evidence_items=(speaker_evidence,),
        evidence_claims=(speaker_claim,),
    )


def normalize_ndl_diet_minutes_record(
    record: FetchManifestRecord,
    raw_payload: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    if record.source_document_candidate.source_type == "meeting_record":
        return _normalize_ndl_meeting_record(
            record,
            raw_payload,
            raw_artifact_id=raw_artifact_id,
        )
    if record.source_document_candidate.source_type == "speech_record":
        return _normalize_ndl_speech_record(
            record,
            raw_payload,
            raw_artifact_id=raw_artifact_id,
        )
    raise ValueError(
        f"unsupported ndl diet minutes source_type: {record.source_document_candidate.source_type}"
    )
