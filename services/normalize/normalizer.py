import re
from dataclasses import dataclass
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from normalize.contracts import (
    AUDIT_REPORT_SOURCE_TYPES,
    AuditFindingCandidate,
    EvidenceClaim,
    EvidenceItem,
    NormalizeResult,
    SourceDocument,
    build_audit_finding_candidate,
    build_observed_claim,
)


@dataclass(frozen=True, slots=True)
class _ExtractedTitle:
    quote_text: str
    normalized_text: str
    source_span_start: int
    source_span_end: int


@dataclass(frozen=True, slots=True)
class _ExtractedAuditField:
    field_name: str
    quote_text: str
    normalized_text: str
    source_span_start: int
    source_span_end: int


@dataclass(frozen=True, slots=True)
class _ExtractedAuditFinding:
    source_type: str
    fields: dict[str, _ExtractedAuditField]


_TITLE_PATTERN = re.compile(rb"<title\b[^>]*>(?P<title>.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
_AUDIT_FINDING_SECTION_PATTERN = re.compile(
    rb'<section\b[^>]*class="audit-finding"[^>]*data-source-type="(?P<source_type>[^"]+)"'
    rb"[^>]*>(?P<body>.*?)</section\s*>",
    re.IGNORECASE | re.DOTALL,
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


def _decode_official_field_text(field_bytes: bytes) -> str:
    return unescape(field_bytes.strip().decode("utf-8"))


def _extract_audit_field(
    *,
    section_start: int,
    section_body: bytes,
    field_name: str,
) -> _ExtractedAuditField:
    pattern = re.compile(
        rb'<(?P<tag>[a-z0-9]+)\b[^>]*data-field="'
        + re.escape(field_name.encode("utf-8"))
        + rb'"[^>]*>(?P<text>.*?)</(?P=tag)\s*>',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(section_body)
    if match is None:
        msg = f"audit report fixture field is required: {field_name}"
        raise ValueError(msg)

    text_start, _text_end = match.span("text")
    field_bytes = match.group("text")
    stripped_field_bytes = field_bytes.strip()
    leading_whitespace = len(field_bytes) - len(field_bytes.lstrip())
    source_span_start = section_start + text_start + leading_whitespace
    source_span_end = source_span_start + len(stripped_field_bytes)
    quote_text = _decode_official_field_text(stripped_field_bytes)
    if not quote_text:
        msg = f"audit report fixture field is empty: {field_name}"
        raise ValueError(msg)

    return _ExtractedAuditField(
        field_name=field_name,
        quote_text=quote_text,
        normalized_text=quote_text,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
    )


def _extract_audit_findings(raw_html: bytes) -> tuple[_ExtractedAuditFinding, ...]:
    findings: list[_ExtractedAuditFinding] = []
    for match in _AUDIT_FINDING_SECTION_PATTERN.finditer(raw_html):
        source_type = match.group("source_type").decode("utf-8")
        if source_type not in AUDIT_REPORT_SOURCE_TYPES:
            msg = f"unsupported audit report fixture source_type: {source_type}"
            raise ValueError(msg)

        body_start = match.start("body")
        body = match.group("body")
        fields = {
            field_name: _extract_audit_field(
                section_start=body_start,
                section_body=body,
                field_name=field_name,
            )
            for field_name in (
                "fiscal_year",
                "audited_entity",
                "finding_text",
                "measure_status",
            )
        }
        findings.append(_ExtractedAuditFinding(source_type=source_type, fields=fields))

    if not findings:
        msg = "audit report fixture finding section is required"
        raise ValueError(msg)

    return tuple(findings)


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


def _validate_audit_report_fixture_input(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    if candidate.source_type not in AUDIT_REPORT_SOURCE_TYPES:
        msg = f"unsupported source_type for audit report normalization: {candidate.source_type}"
        raise ValueError(msg)

    if "text/html" not in record.media_type.lower():
        msg = f"unsupported media_type for audit report normalization: {record.media_type}"
        raise ValueError(msg)


def _build_audit_field_evidence_item(
    *,
    source_document: SourceDocument,
    source_type: str,
    fields: dict[str, _ExtractedAuditField],
    field_name: str,
) -> EvidenceItem:
    extracted_field = fields[field_name]
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "audit_report_fixture",
        field_name,
        extracted_field.source_span_start,
        extracted_field.source_span_end,
        extracted_field.quote_text,
    )
    fiscal_year = fields["fiscal_year"].normalized_text
    audited_entity = fields["audited_entity"].normalized_text

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="html_selector",
        location_value=f'[data-field="{field_name}"]',
        source_span_start=extracted_field.source_span_start,
        source_span_end=extracted_field.source_span_end,
        quote_text=extracted_field.quote_text,
        normalized_text=extracted_field.normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="audit_report_fixture_html",
        confidence=1.0,
        location_metadata={
            "field_name": field_name,
            "source_type": source_type,
            "fiscal_year": fiscal_year,
            "audited_entity": audited_entity,
        },
        parse_warnings=("meaning_not_interpreted",),
    )


def _build_audit_finding_candidate(
    *,
    source_document: SourceDocument,
    source_type: str,
    fields: dict[str, _ExtractedAuditField],
    field_evidence_item_ids: dict[str, str],
) -> AuditFindingCandidate:
    fiscal_year = fields["fiscal_year"].normalized_text
    audited_entity = fields["audited_entity"].normalized_text
    finding_text = fields["finding_text"].normalized_text
    measure_status = fields["measure_status"].normalized_text
    candidate_id = _stable_uuid(
        "audit_finding_candidate",
        source_document.source_document_id,
        source_type,
        fiscal_year,
        audited_entity,
        finding_text,
        measure_status,
    )

    return build_audit_finding_candidate(
        audit_finding_candidate_id=candidate_id,
        source_document_id=source_document.source_document_id,
        source_type=source_type,
        fiscal_year=fiscal_year,
        audited_entity=audited_entity,
        finding_text=finding_text,
        measure_status=measure_status,
        field_evidence_item_ids=field_evidence_item_ids,
    )


def _build_audit_claims(
    *,
    candidate: AuditFindingCandidate,
    field_evidence_items: dict[str, EvidenceItem],
    source_family: str,
) -> tuple[EvidenceClaim, ...]:
    finding_evidence = field_evidence_items["finding_text"]
    measure_evidence = field_evidence_items["measure_status"]
    finding_claim_id = _stable_uuid(
        "evidence_claim",
        candidate.audit_finding_candidate_id,
        "audit_report_finding_text_observed",
        candidate.finding_text,
    )
    measure_claim_id = _stable_uuid(
        "evidence_claim",
        candidate.audit_finding_candidate_id,
        "audit_measure_status_observed",
        candidate.measure_status,
    )

    return (
        build_observed_claim(
            evidence_claim_id=finding_claim_id,
            claim_type="audit_report_finding_text_observed",
            subject_ref=candidate.audit_finding_candidate_id,
            object_value=candidate.finding_text,
            evidence_item=finding_evidence,
            source_family=source_family,
        ),
        build_observed_claim(
            evidence_claim_id=measure_claim_id,
            claim_type="audit_measure_status_observed",
            subject_ref=candidate.audit_finding_candidate_id,
            object_value=candidate.measure_status,
            evidence_item=measure_evidence,
            source_family=source_family,
        ),
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


def normalize_audit_report_fixture(
    record: FetchManifestRecord,
    raw_html: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    _validate_audit_report_fixture_input(record)
    extracted_title = _extract_title(raw_html)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=extracted_title.normalized_text,
    )
    extracted_findings = _extract_audit_findings(raw_html)

    evidence_items: list[EvidenceItem] = []
    evidence_claims: list[EvidenceClaim] = []
    audit_finding_candidates: list[AuditFindingCandidate] = []
    for extracted_finding in extracted_findings:
        if extracted_finding.source_type != record.source_document_candidate.source_type:
            msg = (
                "audit report fixture source_type does not match source_document_candidate: "
                f"{extracted_finding.source_type}"
            )
            raise ValueError(msg)

        field_evidence_items = {
            field_name: _build_audit_field_evidence_item(
                source_document=source_document,
                source_type=extracted_finding.source_type,
                fields=extracted_finding.fields,
                field_name=field_name,
            )
            for field_name in (
                "fiscal_year",
                "audited_entity",
                "finding_text",
                "measure_status",
            )
        }
        field_evidence_item_ids = {
            field_name: evidence_item.evidence_item_id
            for field_name, evidence_item in field_evidence_items.items()
        }
        candidate = _build_audit_finding_candidate(
            source_document=source_document,
            source_type=extracted_finding.source_type,
            fields=extracted_finding.fields,
            field_evidence_item_ids=field_evidence_item_ids,
        )
        audit_finding_candidates.append(candidate)
        evidence_items.extend(field_evidence_items.values())
        evidence_claims.extend(
            _build_audit_claims(
                candidate=candidate,
                field_evidence_items=field_evidence_items,
                source_family=source_document.source_family,
            )
        )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=tuple(evidence_items),
        evidence_claims=tuple(evidence_claims),
        audit_finding_candidates=tuple(audit_finding_candidates),
    )
