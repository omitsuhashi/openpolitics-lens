import json
import re
from dataclasses import dataclass
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from normalize.contracts import (
    EvidenceClaim,
    EvidenceItem,
    JsonDict,
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


@dataclass(frozen=True, slots=True)
class _ExtractedAssemblySpeech:
    quote_text: str
    normalized_text: str
    source_span_start: int
    source_span_end: int
    location_metadata: JsonDict


_TITLE_PATTERN = re.compile(
    rb"<title\b[^>]*>(?P<title>.*?)</title\s*>",
    re.IGNORECASE | re.DOTALL,
)
_ASSEMBLY_METADATA_PATTERN = re.compile(
    rb"<script\b(?=[^>]*\bid=[\"']assembly-speech-metadata[\"'])[^>]*>"
    rb"(?P<metadata>.*?)"
    rb"</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_ASSEMBLY_SPEECH_PATTERN = re.compile(
    rb"<p\b(?=[^>]*\bclass=[\"']speech-text[\"'])[^>]*>"
    rb"(?P<speech>.*?)"
    rb"</p\s*>",
    re.IGNORECASE | re.DOTALL,
)
_ASSEMBLY_REQUIRED_LOCATION_METADATA_KEYS: tuple[str, ...] = (
    "search_form_url",
    "query_parameters",
    "target_period",
    "page_number",
    "sort_order",
    "snapshot_timestamp",
    "result_row_locator",
    "meeting_id",
    "meeting_name",
    "meeting_date",
    "speaker_name",
    "speaker_role",
    "speech_block_id",
    "speech_block_locator",
)


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


def _validate_assembly_records_input(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    if candidate.source_type != "assembly_meeting_record_search_snapshot":
        msg = f"unsupported source_type for assembly records normalization: {candidate.source_type}"
        raise ValueError(msg)

    if candidate.source_family != "tokyo_assembly_records_bills":
        msg = (
            "unsupported source_family for assembly records normalization: "
            f"{candidate.source_family}"
        )
        raise ValueError(msg)

    if "text/html" not in record.media_type.lower():
        msg = f"unsupported media_type for assembly records normalization: {record.media_type}"
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


def _extract_assembly_location_metadata(raw_html: bytes) -> JsonDict:
    match = _ASSEMBLY_METADATA_PATTERN.search(raw_html)
    if match is None:
        msg = "assembly speech metadata script is required"
        raise ValueError(msg)

    try:
        metadata = json.loads(unescape(match.group("metadata").decode("utf-8")).strip())
    except json.JSONDecodeError as exc:
        msg = "assembly speech metadata script must contain JSON"
        raise ValueError(msg) from exc

    if not isinstance(metadata, dict):
        msg = "assembly speech metadata must be a JSON object"
        raise ValueError(msg)

    missing_keys = [key for key in _ASSEMBLY_REQUIRED_LOCATION_METADATA_KEYS if key not in metadata]
    if missing_keys:
        msg = "assembly speech metadata missing keys: " + ", ".join(missing_keys)
        raise ValueError(msg)

    if not isinstance(metadata["query_parameters"], dict):
        msg = "assembly speech query_parameters must be a JSON object"
        raise ValueError(msg)
    if not isinstance(metadata["target_period"], dict):
        msg = "assembly speech target_period must be a JSON object"
        raise ValueError(msg)

    return dict(metadata)


def _extract_assembly_speech(raw_html: bytes) -> _ExtractedAssemblySpeech:
    match = _ASSEMBLY_SPEECH_PATTERN.search(raw_html)
    if match is None:
        msg = "assembly speech text block is required"
        raise ValueError(msg)

    speech_start, _speech_end = match.span("speech")
    speech_bytes = match.group("speech")
    stripped_speech_bytes = speech_bytes.strip()
    leading_whitespace = len(speech_bytes) - len(speech_bytes.lstrip())
    source_span_start = speech_start + leading_whitespace
    source_span_end = source_span_start + len(stripped_speech_bytes)
    quote_text = stripped_speech_bytes.decode("utf-8")
    normalized_text = _collapse_whitespace(unescape(quote_text))
    if not normalized_text:
        msg = "assembly speech text is empty"
        raise ValueError(msg)

    return _ExtractedAssemblySpeech(
        quote_text=quote_text,
        normalized_text=normalized_text,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        location_metadata=_extract_assembly_location_metadata(raw_html),
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


def _build_assembly_speech_evidence_item(
    *,
    source_document: SourceDocument,
    extracted_speech: _ExtractedAssemblySpeech,
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "assembly_speech_text",
        extracted_speech.source_span_start,
        extracted_speech.source_span_end,
        extracted_speech.quote_text,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="api_record",
        location_value=str(extracted_speech.location_metadata["speech_block_locator"]),
        source_span_start=extracted_speech.source_span_start,
        source_span_end=extracted_speech.source_span_end,
        quote_text=extracted_speech.quote_text,
        normalized_text=extracted_speech.normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="search_ui_snapshot",
        confidence=1.0,
        location_metadata=extracted_speech.location_metadata,
        parse_warnings=("search_ui_snapshot", "meaning_not_interpreted"),
    )


def _build_assembly_speech_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "speech_text_observed",
        evidence_item.normalized_text,
    )

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="speech_text_observed",
        subject_ref=source_document.source_document_id,
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


def normalize_assembly_records_search_snapshot(
    record: FetchManifestRecord,
    raw_html: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    _validate_assembly_records_input(record)
    extracted_speech = _extract_assembly_speech(raw_html)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=record.source_document_candidate.title,
    )
    evidence_item = _build_assembly_speech_evidence_item(
        source_document=source_document,
        extracted_speech=extracted_speech,
    )
    evidence_claim = _build_assembly_speech_claim(
        source_document=source_document,
        evidence_item=evidence_item,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=(evidence_claim,),
    )
