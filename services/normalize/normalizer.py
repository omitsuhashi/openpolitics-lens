import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from normalize.contracts import (
    ElectionCandidateObservation,
    EvidenceClaim,
    EvidenceItem,
    NormalizeResult,
    SourceDocument,
    build_observed_claim,
    validate_tokyo_election_claims_do_not_merge_entities,
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


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


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


def _validate_tokyo_election_observation_input(
    record: FetchManifestRecord,
    observation: ElectionCandidateObservation,
) -> None:
    candidate = record.source_document_candidate
    allowed_source_types = {
        "election_result_html",
        "election_result_pdf",
        "public_bulletin_metadata",
    }
    if candidate.source_family != "tokyo_elections":
        msg = f"unsupported source_family for election normalization: {candidate.source_family}"
        raise ValueError(msg)
    if candidate.source_type not in allowed_source_types:
        msg = f"unsupported source_type for election normalization: {candidate.source_type}"
        raise ValueError(msg)
    if observation.source_url != record.canonical_url:
        msg = "observation source_url must match canonical_url"
        raise ValueError(msg)
    if observation.retrieved_at != record.fetched_at:
        msg = "observation retrieved_at must match fetched_at"
        raise ValueError(msg)
    if observation.entity_ref is not None:
        msg = "tokyo election observations must not carry entity merge refs"
        raise ValueError(msg)
    if candidate.source_type == "public_bulletin_metadata" and observation.votes is not None:
        msg = "public bulletin metadata must not carry votes"
        raise ValueError(msg)
    if candidate.source_type != "public_bulletin_metadata" and observation.votes is None:
        msg = "election result observations must carry votes"
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

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="grant_program_page_title_observed",
        subject_ref=source_document.source_document_id,
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
    )


def _election_observation_payload(observation: ElectionCandidateObservation) -> str:
    return json.dumps(
        {
            "election_name": observation.election_name,
            "district": observation.district,
            "candidate_name": observation.candidate_name,
            "votes": observation.votes,
            "source_url": observation.source_url,
            "retrieved_at": _datetime_to_json(observation.retrieved_at),
        },
        ensure_ascii=False,
        sort_keys=False,
    )


def _build_election_candidate_evidence_item(
    *,
    source_document: SourceDocument,
    observation: ElectionCandidateObservation,
) -> EvidenceItem:
    payload = _election_observation_payload(observation)
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "election_candidate",
        observation.source_locator,
        payload,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="api_record",
        location_value=observation.source_locator,
        source_span_start=0,
        source_span_end=len(payload.encode("utf-8")),
        quote_text=payload,
        normalized_text=payload,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="fixture_structured_election_record",
        confidence=1.0,
        location_metadata={
            "source_type": source_document.source_type,
            "source_url": observation.source_url,
            "retrieved_at": _datetime_to_json(observation.retrieved_at),
            "election_name": observation.election_name,
            "district": observation.district,
            "candidate_name": observation.candidate_name,
            "votes": observation.votes,
        },
    )


def _build_election_candidate_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "election_candidate_observed",
        evidence_item.normalized_text,
    )

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="election_candidate_observed",
        subject_ref=f"{source_document.source_document_id}#candidate:{evidence_item.location_value}",
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
    )


def _build_election_result_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    observation: ElectionCandidateObservation,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "election_result_observed",
        evidence_item.normalized_text,
    )

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="election_result_observed",
        subject_ref=f"{source_document.source_document_id}#result:{evidence_item.location_value}",
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
        amount=None if observation.votes is None else str(observation.votes),
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


def normalize_tokyo_election_candidate_observation(
    record: FetchManifestRecord,
    observation: ElectionCandidateObservation,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    _validate_tokyo_election_observation_input(record, observation)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=record.source_document_candidate.title,
    )
    evidence_item = _build_election_candidate_evidence_item(
        source_document=source_document,
        observation=observation,
    )
    evidence_claims = [
        _build_election_candidate_claim(
            source_document=source_document,
            evidence_item=evidence_item,
        )
    ]
    if observation.votes is not None:
        evidence_claims.append(
            _build_election_result_claim(
                source_document=source_document,
                evidence_item=evidence_item,
                observation=observation,
            )
        )
    validate_tokyo_election_claims_do_not_merge_entities(evidence_claims)

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=tuple(evidence_claims),
    )
