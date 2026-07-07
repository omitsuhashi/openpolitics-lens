import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from ingest.tokyo_assembly_bills import TokyoAssemblyBillDecisionFixture
from normalize.contracts import (
    AUDIT_REPORT_SOURCE_TYPES,
    AuditFindingCandidate,
    ElectionCandidateObservation,
    EvidenceClaim,
    EvidenceItem,
    JsonDict,
    NormalizeResult,
    SourceDocument,
    build_audit_finding_candidate,
    build_observed_claim,
    validate_tokyo_election_claims_do_not_merge_entities,
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
_AUDIT_FINDING_SECTION_PATTERN = re.compile(
    rb'<section\b[^>]*class="audit-finding"[^>]*data-source-type="(?P<source_type>[^"]+)"'
    rb"[^>]*>(?P<body>.*?)</section\s*>",
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


def _validate_audit_report_fixture_input(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    if candidate.source_type not in AUDIT_REPORT_SOURCE_TYPES:
        msg = f"unsupported source_type for audit report normalization: {candidate.source_type}"
        raise ValueError(msg)

    if "text/html" not in record.media_type.lower():
        msg = f"unsupported media_type for audit report normalization: {record.media_type}"
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


def build_vote_positions_from_bill_decision_fixture(
    fixture: TokyoAssemblyBillDecisionFixture,
) -> tuple[object, ...]:
    if not fixture.has_individual_vote_positions:
        return ()

    msg = "VotePosition generation is outside the Phase 0 bill decision fixture scope"
    raise ValueError(msg)


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
