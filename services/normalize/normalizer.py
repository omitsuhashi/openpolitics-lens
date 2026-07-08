import json
import re
from dataclasses import dataclass
from datetime import date
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


def _build_json_evidence_item(
    *,
    source_document: SourceDocument,
    raw_payload: bytes,
    location_value: str,
    normalized_text: str,
) -> EvidenceItem:
    encoded_value = normalized_text.encode("utf-8")
    source_span_start = raw_payload.index(encoded_value)
    source_span_end = source_span_start + len(encoded_value)
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        location_value,
        source_span_start,
        source_span_end,
        normalized_text,
    )
    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="json_path",
        location_value=location_value,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        quote_text=normalized_text,
        normalized_text=normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="json_field",
        confidence=1.0,
    )


def _build_json_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    claim_type: str,
    predicate: str,
    event_date: date | None = None,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        claim_type,
        evidence_item.normalized_text,
    )
    return EvidenceClaim(
        evidence_claim_id=evidence_claim_id,
        claim_type=claim_type,
        subject_ref=source_document.source_document_id,
        predicate=predicate,
        object_ref=None,
        object_value=evidence_item.normalized_text,
        event_date=event_date,
        amount=None,
        currency=None,
        evidence_item_id=evidence_item.evidence_item_id,
        review_state="machine_extracted",
    )


def _parse_public_comment_month(value: str) -> date:
    match = re.fullmatch(r"(?P<year>\d{4})年(?P<month>\d{1,2})月", value.strip())
    if match is None:
        raise ValueError(f"unsupported public comment month value: {value}")
    return date(int(match.group("year")), int(match.group("month")), 1)


def _build_event_candidate(
    *,
    record: FetchManifestRecord,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    event_type: str,
    scheduled_date: date,
    date_precision: str,
    event_status: str,
    title: str,
    office_or_body: str,
    limitations: tuple[str, ...] = (),
) -> OfficialPoliticalEventCandidate:
    event_candidate_id = _stable_uuid(
        "official_political_event",
        record.canonical_url,
        event_type,
        scheduled_date.isoformat(),
    )
    assertion = EventSourceAssertion(
        event_candidate_id=event_candidate_id,
        source_document_id=source_document.source_document_id,
        evidence_item_id=evidence_item.evidence_item_id,
        asserted_field="scheduled_date",
        asserted_value=scheduled_date.isoformat(),
        asserted_at=record.fetched_at,
        source_priority=10,
        conflict_state="none",
        confidence=1.0,
        review_state="machine_extracted",
        limitations=limitations,
    )
    return OfficialPoliticalEventCandidate(
        event_candidate_id=event_candidate_id,
        event_family="PublicConsultation",
        event_type=event_type,
        jurisdiction_id=record.connector.jurisdiction.jurisdiction_id,
        jurisdiction_level=record.connector.jurisdiction.jurisdiction_level,
        source_system=record.connector.source_family.source_system,
        source_family=record.connector.source_family.source_family,
        connector_id=record.connector.connector_id,
        title=title,
        scheduled_date=scheduled_date,
        scheduled_time=None,
        timezone="Asia/Tokyo",
        date_precision=date_precision,
        office_or_body=office_or_body,
        event_status=event_status,
        canonical_url=record.canonical_url,
        source_document_id=source_document.source_document_id,
        evidence_item_id=evidence_item.evidence_item_id,
        extraction_method="egov_public_comment_case_json",
        confidence=1.0,
        review_state="machine_extracted",
        limitations=limitations,
        source_assertions=(assertion,),
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


def normalize_public_comment_case(
    record: FetchManifestRecord,
    raw_payload: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    candidate = record.source_document_candidate
    if candidate.source_type != "public_comment_case":
        raise ValueError(
            f"unsupported source_type for public comment normalization: {candidate.source_type}"
        )
    if "application/json" not in record.media_type.lower():
        raise ValueError(
            f"unsupported media_type for public comment normalization: {record.media_type}"
        )

    metadata = candidate.metadata
    if not isinstance(metadata, dict):
        raise ValueError("public comment metadata must be a JSON object")
    json.loads(raw_payload.decode("utf-8"))

    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=candidate.title,
    )

    operator_name = str(metadata["operator_name"])
    opened_at = date.fromisoformat(str(metadata["comment_start_date"]))
    opened_item = _build_json_evidence_item(
        source_document=source_document,
        raw_payload=raw_payload,
        location_value="$.commentStartDate",
        normalized_text=opened_at.isoformat(),
    )
    opened_claim = _build_json_claim(
        source_document=source_document,
        evidence_item=opened_item,
        claim_type="public_comment_opened_at_observed",
        predicate="public_comment_opened_at",
        event_date=opened_at,
    )

    evidence_items = [opened_item]
    evidence_claims = [opened_claim]
    event_candidates = [
        _build_event_candidate(
            record=record,
            source_document=source_document,
            evidence_item=opened_item,
            event_type="public_comment_opened",
            scheduled_date=opened_at,
            date_precision="date",
            event_status="opened",
            title=candidate.title,
            office_or_body=operator_name,
        )
    ]

    if "comment_end_date" in metadata:
        closed_at = date.fromisoformat(str(metadata["comment_end_date"]))
        close_precision = "date"
        close_limitations: tuple[str, ...] = candidate.warnings
        close_text = closed_at.isoformat()
    else:
        close_text = str(metadata["comment_end_text"])
        closed_at = _parse_public_comment_month(close_text)
        close_precision = "month"
        close_limitations = candidate.warnings
    closed_item = _build_json_evidence_item(
        source_document=source_document,
        raw_payload=raw_payload,
        location_value="$.commentEndText"
        if "comment_end_date" not in metadata
        else "$.commentEndDate",
        normalized_text=close_text,
    )
    evidence_items.append(closed_item)
    evidence_claims.append(
        _build_json_claim(
            source_document=source_document,
            evidence_item=closed_item,
            claim_type="public_comment_closed_at_observed",
            predicate="public_comment_closed_at",
            event_date=closed_at,
        )
    )
    event_candidates.append(
        _build_event_candidate(
            record=record,
            source_document=source_document,
            evidence_item=closed_item,
            event_type="public_comment_closed",
            scheduled_date=closed_at,
            date_precision=close_precision,
            event_status="closed",
            title=candidate.title,
            office_or_body=operator_name,
            limitations=close_limitations,
        )
    )

    result_published_at = date.fromisoformat(str(metadata["result_published_date"]))
    result_item = _build_json_evidence_item(
        source_document=source_document,
        raw_payload=raw_payload,
        location_value="$.resultPublishedDate",
        normalized_text=result_published_at.isoformat(),
    )
    evidence_items.append(result_item)
    evidence_claims.append(
        _build_json_claim(
            source_document=source_document,
            evidence_item=result_item,
            claim_type="public_comment_result_published_at_observed",
            predicate="public_comment_result_published_at",
            event_date=result_published_at,
        )
    )
    event_candidates.append(
        _build_event_candidate(
            record=record,
            source_document=source_document,
            evidence_item=result_item,
            event_type="public_comment_result_published",
            scheduled_date=result_published_at,
            date_precision="date",
            event_status="published",
            title=candidate.title,
            office_or_body=operator_name,
        )
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=tuple(evidence_items),
        evidence_claims=tuple(evidence_claims),
        official_event_candidates=tuple(event_candidates),
    )
