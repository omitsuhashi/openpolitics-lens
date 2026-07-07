import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
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


@dataclass(frozen=True, slots=True)
class _ExtractedSubsidyProgramCandidate:
    quote_text: str
    normalized_text: str
    source_span_start: int
    source_span_end: int
    fields: dict[str, str]


_TITLE_PATTERN = re.compile(rb"<title\b[^>]*>(?P<title>.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
_H1_PATTERN = re.compile(rb"<h1\b[^>]*>(?P<h1>.*?)</h1\s*>", re.IGNORECASE | re.DOTALL)
_STABLE_SUBSIDY_PROGRAM_LABELS = ("所管局", "対象者", "申請期間")


class _GrantDetailFieldParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_text: str = ""
        self.label_values: dict[str, str] = {}
        self._active_tag: str | None = None
        self._active_text: list[str] = []
        self._pending_dt: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        normalized_tag = tag.lower()
        if normalized_tag in {"h1", "dt", "dd"}:
            self._active_tag = normalized_tag
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_tag is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag != self._active_tag:
            return

        text = _collapse_whitespace(unescape("".join(self._active_text)))
        if normalized_tag == "h1" and text and not self.h1_text:
            self.h1_text = text
        elif normalized_tag == "dt":
            self._pending_dt = text
        elif normalized_tag == "dd" and self._pending_dt in _STABLE_SUBSIDY_PROGRAM_LABELS:
            self.label_values.setdefault(self._pending_dt, text)
            self._pending_dt = None

        self._active_tag = None
        self._active_text = []


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


def _extract_subsidy_program_candidate(
    raw_html: bytes,
    *,
    title: str,
) -> _ExtractedSubsidyProgramCandidate:
    h1_match = _H1_PATTERN.search(raw_html)
    if h1_match is None:
        msg = "grant program page h1 is required for subsidy program candidate"
        raise ValueError(msg)

    h1_start, h1_end = h1_match.span("h1")
    h1_bytes = raw_html[h1_start:h1_end]
    stripped_h1_bytes = h1_bytes.strip()
    leading_whitespace = len(h1_bytes) - len(h1_bytes.lstrip())
    source_span_start = h1_start + leading_whitespace
    source_span_end = source_span_start + len(stripped_h1_bytes)
    quote_text = stripped_h1_bytes.decode("utf-8")
    normalized_h1 = _collapse_whitespace(unescape(quote_text))
    if not normalized_h1:
        msg = "grant program page h1 is empty"
        raise ValueError(msg)

    parser = _GrantDetailFieldParser()
    parser.feed(raw_html.decode("utf-8"))
    fields = {
        "title": title,
        "h1": normalized_h1,
    }
    for label in _STABLE_SUBSIDY_PROGRAM_LABELS:
        value = parser.label_values.get(label, "")
        if not value:
            msg = f"stable subsidy program field is required: {label}"
            raise ValueError(msg)
        fields[label] = value

    return _ExtractedSubsidyProgramCandidate(
        quote_text=quote_text,
        normalized_text=normalized_h1,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        fields=fields,
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


def _build_subsidy_program_candidate_evidence_item(
    *,
    source_document: SourceDocument,
    extracted_candidate: _ExtractedSubsidyProgramCandidate,
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "subsidy_program_candidate",
        extracted_candidate.source_span_start,
        extracted_candidate.source_span_end,
        extracted_candidate.quote_text,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="html_selector",
        location_value="h1",
        source_span_start=extracted_candidate.source_span_start,
        source_span_end=extracted_candidate.source_span_end,
        quote_text=extracted_candidate.quote_text,
        normalized_text=extracted_candidate.normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="html_stable_subsidy_program_fields",
        confidence=1.0,
        location_metadata={
            "fields": ["title", "h1", *_STABLE_SUBSIDY_PROGRAM_LABELS],
            "selectors": {
                "h1": "h1",
                "所管局": "dt/dd label pair",
                "対象者": "dt/dd label pair",
                "申請期間": "dt/dd label pair",
            },
        },
    )


def _build_subsidy_program_candidate_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    extracted_candidate: _ExtractedSubsidyProgramCandidate,
) -> EvidenceClaim:
    candidate_id = _stable_uuid(
        "subsidy_program_candidate",
        source_document.canonical_url,
        extracted_candidate.fields["h1"],
        extracted_candidate.fields["所管局"],
        extracted_candidate.fields["対象者"],
        extracted_candidate.fields["申請期間"],
    )
    payload = {
        "candidate_id": candidate_id,
        "canonical_url": source_document.canonical_url,
        "title": extracted_candidate.fields["title"],
        "h1": extracted_candidate.fields["h1"],
        "bureau": extracted_candidate.fields["所管局"],
        "eligible": extracted_candidate.fields["対象者"],
        "application_period": extracted_candidate.fields["申請期間"],
        "source_document_id": source_document.source_document_id,
        "evidence_item_id": evidence_item.evidence_item_id,
        "review_state": "candidate",
    }
    object_value = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "subsidy_program_candidate_observed",
        object_value,
    )

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="subsidy_program_candidate_observed",
        subject_ref=f"SubsidyProgramCandidate:{candidate_id}",
        object_value=object_value,
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
    extracted_candidate = _extract_subsidy_program_candidate(
        raw_html,
        title=extracted_title.normalized_text,
    )
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
    candidate_evidence_item = _build_subsidy_program_candidate_evidence_item(
        source_document=source_document,
        extracted_candidate=extracted_candidate,
    )
    candidate_claim = _build_subsidy_program_candidate_claim(
        source_document=source_document,
        evidence_item=candidate_evidence_item,
        extracted_candidate=extracted_candidate,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item, candidate_evidence_item),
        evidence_claims=(evidence_claim, candidate_claim),
    )
