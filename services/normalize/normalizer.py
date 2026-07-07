import re
from dataclasses import dataclass
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from ingest.tokyo_assembly_bills import TokyoAssemblyBillDecisionFixture
from normalize.contracts import (
    EvidenceClaim,
    EvidenceItem,
    NormalizeResult,
    SourceDocument,
    build_observed_claim,
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


def _validate_assembly_bill_decision_input(
    record: FetchManifestRecord,
    fixture: TokyoAssemblyBillDecisionFixture,
) -> None:
    candidate = record.source_document_candidate
    if candidate.source_type != "assembly_bill_decision":
        msg = f"unsupported source_type for bill decision normalization: {candidate.source_type}"
        raise ValueError(msg)

    if candidate.canonical_url != fixture.source_url:
        msg = "bill decision fixture source_url does not match candidate canonical_url"
        raise ValueError(msg)

    if candidate.title != fixture.title:
        msg = "bill decision fixture title does not match candidate title"
        raise ValueError(msg)

    if "text/html" not in record.media_type.lower():
        msg = f"unsupported media_type for bill decision normalization: {record.media_type}"
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


def _build_bill_decision_evidence_item(
    *,
    source_document: SourceDocument,
    raw_html: bytes,
    fixture: TokyoAssemblyBillDecisionFixture,
) -> EvidenceItem:
    quote_bytes = fixture.evidence_quote_text.encode("utf-8")
    source_span_start = raw_html.find(quote_bytes)
    if source_span_start < 0:
        msg = f"bill decision evidence quote not found in raw artifact: {fixture.fixture_id}"
        raise ValueError(msg)
    source_span_end = source_span_start + len(quote_bytes)
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "html_bill_decision",
        fixture.fixture_id,
        source_span_start,
        source_span_end,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="html_selector",
        location_value=fixture.row_locator,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        quote_text=fixture.evidence_quote_text,
        normalized_text=fixture.evidence_quote_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="html_bill_decision_fixture",
        confidence=1.0,
        location_metadata={
            "fiscal_year": fixture.fiscal_year,
            "regular_session": fixture.regular_session,
            "session_period": fixture.session_period,
            "bill_number": fixture.bill_number,
            "subject": fixture.subject,
            "decision_result": fixture.decision_result,
            "source_url": fixture.source_url,
            "row_locator": fixture.row_locator,
            "has_individual_vote_positions": fixture.has_individual_vote_positions,
        },
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


def _build_bill_decision_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    fixture: TokyoAssemblyBillDecisionFixture,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "bill_decision_observed",
        fixture.fixture_id,
    )

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="bill_decision_observed",
        subject_ref=f"{source_document.source_document_id}#{fixture.fixture_id}",
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
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


def normalize_assembly_bill_decision(
    record: FetchManifestRecord,
    raw_html: bytes,
    fixture: TokyoAssemblyBillDecisionFixture,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    _validate_assembly_bill_decision_input(record, fixture)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=fixture.title,
    )
    evidence_item = _build_bill_decision_evidence_item(
        source_document=source_document,
        raw_html=raw_html,
        fixture=fixture,
    )
    evidence_claim = _build_bill_decision_claim(
        source_document=source_document,
        evidence_item=evidence_item,
        fixture=fixture,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=(evidence_claim,),
    )


def build_vote_positions_from_bill_decision_fixture(
    fixture: TokyoAssemblyBillDecisionFixture,
) -> tuple[object, ...]:
    if not fixture.has_individual_vote_positions:
        return ()

    msg = "VotePosition generation is outside the Phase 0 bill decision fixture scope"
    raise ValueError(msg)
