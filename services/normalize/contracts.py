from dataclasses import dataclass, field
from datetime import UTC, date, datetime

JsonDict = dict[str, object]

WARNING_CATALOG: frozenset[str] = frozenset(
    {
        "pdf_text_layer_missing",
        "ocr_required",
        "ocr_low_confidence",
        "table_structure_inferred",
        "merged_cell_or_header_inferred",
        "multi_page_table",
        "amount_unit_ambiguous",
        "name_or_org_ocr_ambiguous",
        "entity_resolution_required",
        "search_ui_snapshot",
        "meaning_not_interpreted",
        "source_layout_unverified",
    }
)

CLAIM_PROMOTION_MIN_CONFIDENCE = 0.8
CLAIM_BLOCKING_WARNING_CODES: frozenset[str] = frozenset(
    {
        "ocr_low_confidence",
        "source_layout_unverified",
    }
)

_REQUIRED_LOCATOR_METADATA_KEYS: dict[str, tuple[str, ...]] = {
    "html_selector": (),
    "page_span": ("page_number",),
    "text_offset": (),
    "table_cell": ("page_number", "table_index", "row_index", "column_index"),
    "api_record": (),
}
_SEARCH_SNAPSHOT_LOCATOR_METADATA_KEYS: tuple[str, ...] = (
    "search_form_url",
    "query_parameters",
    "page_number",
    "sort_order",
    "snapshot_timestamp",
    "result_row_locator",
)


@dataclass(frozen=True, slots=True)
class ClaimCatalogEntry:
    claim_type: str
    predicate: str
    source_families: tuple[str, ...]


_CLAIM_CATALOG_ENTRIES: tuple[ClaimCatalogEntry, ...] = (
    ClaimCatalogEntry(
        claim_type="grant_program_page_title_observed",
        predicate="observed_page_title",
        source_families=("tokyo_metro_grants",),
    ),
    ClaimCatalogEntry(
        claim_type="subsidy_program_candidate_observed",
        predicate="observed_subsidy_program_candidate",
        source_families=("tokyo_metro_grants",),
    ),
    ClaimCatalogEntry(
        claim_type="assembly_member_name_observed",
        predicate="observed_assembly_member_name",
        source_families=("tokyo_assembly_records_bills",),
    ),
    ClaimCatalogEntry(
        claim_type="bill_decision_observed",
        predicate="observed_bill_decision",
        source_families=("tokyo_assembly_records_bills",),
    ),
    ClaimCatalogEntry(
        claim_type="petition_status_observed",
        predicate="observed_petition_status",
        source_families=("tokyo_assembly_records_bills",),
    ),
    ClaimCatalogEntry(
        claim_type="speech_text_observed",
        predicate="observed_speech_text",
        source_families=("tokyo_assembly_records_bills",),
    ),
    ClaimCatalogEntry(
        claim_type="election_candidate_observed",
        predicate="observed_election_candidate",
        source_families=("tokyo_elections",),
    ),
    ClaimCatalogEntry(
        claim_type="election_result_observed",
        predicate="observed_election_result",
        source_families=("tokyo_elections",),
    ),
    ClaimCatalogEntry(
        claim_type="political_group_registry_observed",
        predicate="observed_political_group_registry",
        source_families=("tokyo_political_funds",),
    ),
    ClaimCatalogEntry(
        claim_type="political_fund_report_metadata_observed",
        predicate="observed_political_fund_report_metadata",
        source_families=("tokyo_political_funds",),
    ),
    ClaimCatalogEntry(
        claim_type="budget_document_metadata_observed",
        predicate="observed_budget_document_metadata",
        source_families=("tokyo_budget_settlement",),
    ),
    ClaimCatalogEntry(
        claim_type="budget_table_cell_observed",
        predicate="observed_budget_table_cell",
        source_families=("tokyo_budget_settlement",),
    ),
    ClaimCatalogEntry(
        claim_type="procurement_search_row_observed",
        predicate="observed_procurement_search_row",
        source_families=("tokyo_procurement",),
    ),
    ClaimCatalogEntry(
        claim_type="audit_report_finding_text_observed",
        predicate="observed_audit_finding_text",
        source_families=("tokyo_audit_reports",),
    ),
    ClaimCatalogEntry(
        claim_type="audit_measure_status_observed",
        predicate="observed_audit_measure_status",
        source_families=("tokyo_audit_reports",),
    ),
)

CLAIM_TYPE_CATALOG: dict[str, ClaimCatalogEntry] = {
    entry.claim_type: entry for entry in _CLAIM_CATALOG_ENTRIES
}
PREDICATE_CATALOG: frozenset[str] = frozenset(entry.predicate for entry in _CLAIM_CATALOG_ENTRIES)
ELECTION_ENTITY_MERGE_REF_PREFIXES: tuple[str, ...] = (
    "person:",
    "political_group:",
    "party_branch:",
    "support_group:",
)


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _date_to_json(value: date) -> str:
    return value.isoformat()


def claim_catalog_entry(
    claim_type: str,
    *,
    source_family: str | None = None,
    predicate: str | None = None,
) -> ClaimCatalogEntry:
    entry = CLAIM_TYPE_CATALOG.get(claim_type)
    if entry is None:
        msg = f"unknown claim_type: {claim_type}"
        raise ValueError(msg)

    if predicate is not None and predicate != entry.predicate:
        msg = f"predicate does not match claim_type catalog: {claim_type}"
        raise ValueError(msg)

    if source_family is not None and source_family not in entry.source_families:
        msg = f"source_family is not allowed for claim_type {claim_type}: {source_family}"
        raise ValueError(msg)

    return entry


@dataclass(frozen=True, slots=True)
class ElectionCandidateObservation:
    election_name: str
    district: str
    candidate_name: str
    votes: int | None
    source_url: str
    retrieved_at: datetime
    source_locator: str
    entity_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.election_name.strip():
            msg = "election_name is required"
            raise ValueError(msg)
        if not self.district.strip():
            msg = "district is required"
            raise ValueError(msg)
        if not self.candidate_name.strip():
            msg = "candidate_name is required"
            raise ValueError(msg)
        if self.votes is not None and self.votes < 0:
            msg = "votes must be non-negative"
            raise ValueError(msg)
        if not self.source_url.startswith("https://"):
            msg = "source_url must be an https URL"
            raise ValueError(msg)
        if not self.source_locator.strip():
            msg = "source_locator is required"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class SourceDocument:
    source_document_id: str
    raw_artifact_id: str
    source_system: str
    source_type: str
    canonical_url: str
    title: str
    published_at: datetime | None
    retrieved_at: datetime
    raw_artifact_path: str
    content_hash: str
    license_note: str
    source_reliability: str
    jurisdiction_id: str
    source_family: str
    language: str

    def to_json_dict(self) -> JsonDict:
        return {
            "source_document_id": self.source_document_id,
            "raw_artifact_id": self.raw_artifact_id,
            "source_system": self.source_system,
            "source_type": self.source_type,
            "canonical_url": self.canonical_url,
            "title": self.title,
            "published_at": (
                None if self.published_at is None else _datetime_to_json(self.published_at)
            ),
            "retrieved_at": _datetime_to_json(self.retrieved_at),
            "raw_artifact_path": self.raw_artifact_path,
            "content_hash": self.content_hash,
            "license_note": self.license_note,
            "source_reliability": self.source_reliability,
            "jurisdiction_id": self.jurisdiction_id,
            "source_family": self.source_family,
            "language": self.language,
        }


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """Evidence span within the raw artifact.

    source_span_start and source_span_end are raw HTML byte offsets for HTML
    sources, or text offsets in an extraction artifact for PDF/table sources.
    quote_text is the decoded source span text; normalized_text is cleaned for
    claims.
    """

    evidence_item_id: str
    source_document_id: str
    location_type: str
    location_value: str
    source_span_start: int
    source_span_end: int
    quote_text: str
    normalized_text: str
    raw_artifact_path: str
    extraction_method: str
    confidence: float
    location_metadata: JsonDict = field(default_factory=dict)
    parse_warnings: tuple[str, ...] = ()
    extraction_artifact_path: str | None = None

    def __post_init__(self) -> None:
        if self.source_span_start < 0:
            msg = "source_span_start must be non-negative"
            raise ValueError(msg)
        if self.source_span_end < self.source_span_start:
            msg = "source_span_end must be greater than or equal to source_span_start"
            raise ValueError(msg)
        if self.location_type not in _REQUIRED_LOCATOR_METADATA_KEYS:
            msg = f"unsupported location_type: {self.location_type}"
            raise ValueError(msg)
        if self.confidence < 0 or self.confidence > 1:
            msg = "confidence must be between 0 and 1"
            raise ValueError(msg)

        object.__setattr__(self, "location_metadata", dict(self.location_metadata))
        object.__setattr__(self, "parse_warnings", tuple(self.parse_warnings))

        unknown_warning_codes = sorted(set(self.parse_warnings) - WARNING_CATALOG)
        if unknown_warning_codes:
            msg = "unknown parse_warnings: " + ", ".join(unknown_warning_codes)
            raise ValueError(msg)

    def to_json_dict(self) -> JsonDict:
        return {
            "evidence_item_id": self.evidence_item_id,
            "source_document_id": self.source_document_id,
            "location_type": self.location_type,
            "location_value": self.location_value,
            "source_span_start": self.source_span_start,
            "source_span_end": self.source_span_end,
            "quote_text": self.quote_text,
            "normalized_text": self.normalized_text,
            "raw_artifact_path": self.raw_artifact_path,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "location_metadata": self.location_metadata,
            "parse_warnings": list(self.parse_warnings),
            "extraction_artifact_path": self.extraction_artifact_path,
        }


def can_promote_to_evidence_claim(evidence_item: EvidenceItem) -> bool:
    if evidence_item.confidence < CLAIM_PROMOTION_MIN_CONFIDENCE:
        return False
    if set(evidence_item.parse_warnings) & CLAIM_BLOCKING_WARNING_CODES:
        return False
    if not evidence_item.location_value.strip():
        return False
    if evidence_item.source_span_end <= evidence_item.source_span_start:
        return False
    if not evidence_item.normalized_text.strip():
        return False

    required_keys = _REQUIRED_LOCATOR_METADATA_KEYS[evidence_item.location_type]
    if (
        evidence_item.extraction_method == "search_ui_snapshot"
        or "search_ui_snapshot" in evidence_item.parse_warnings
    ):
        required_keys = (*required_keys, *_SEARCH_SNAPSHOT_LOCATOR_METADATA_KEYS)

    return all(key in evidence_item.location_metadata for key in required_keys)


@dataclass(frozen=True, slots=True)
class EvidenceClaim:
    evidence_claim_id: str
    claim_type: str
    subject_ref: str
    predicate: str
    object_ref: str | None
    object_value: str
    event_date: date | None
    amount: str | None
    currency: str | None
    evidence_item_id: str
    review_state: str

    def __post_init__(self) -> None:
        claim_catalog_entry(self.claim_type, predicate=self.predicate)

    def to_json_dict(self) -> JsonDict:
        return {
            "evidence_claim_id": self.evidence_claim_id,
            "claim_type": self.claim_type,
            "subject_ref": self.subject_ref,
            "predicate": self.predicate,
            "object_ref": self.object_ref,
            "object_value": self.object_value,
            "event_date": None if self.event_date is None else _date_to_json(self.event_date),
            "amount": self.amount,
            "currency": self.currency,
            "evidence_item_id": self.evidence_item_id,
            "review_state": self.review_state,
        }


def build_observed_claim(
    *,
    evidence_claim_id: str,
    claim_type: str,
    subject_ref: str,
    object_value: str,
    evidence_item: EvidenceItem,
    source_family: str,
    object_ref: str | None = None,
    event_date: date | None = None,
    amount: str | None = None,
    currency: str | None = None,
    review_state: str = "machine_extracted",
) -> EvidenceClaim:
    entry = claim_catalog_entry(claim_type, source_family=source_family)
    if not can_promote_to_evidence_claim(evidence_item):
        msg = f"evidence_item is not eligible for EvidenceClaim: {evidence_item.evidence_item_id}"
        raise ValueError(msg)

    return EvidenceClaim(
        evidence_claim_id=evidence_claim_id,
        claim_type=entry.claim_type,
        subject_ref=subject_ref,
        predicate=entry.predicate,
        object_ref=object_ref,
        object_value=object_value,
        event_date=event_date,
        amount=amount,
        currency=currency,
        evidence_item_id=evidence_item.evidence_item_id,
        review_state=review_state,
    )


def validate_tokyo_election_claims_do_not_merge_entities(
    evidence_claims: tuple[EvidenceClaim, ...] | list[EvidenceClaim],
) -> None:
    for claim in evidence_claims:
        refs = (claim.subject_ref, claim.object_ref or "")
        if any(ref.startswith(ELECTION_ENTITY_MERGE_REF_PREFIXES) for ref in refs):
            msg = "tokyo election claims must not carry entity merge refs"
            raise ValueError(msg)
        if claim.object_ref is not None:
            msg = "tokyo election claims must not carry entity merge refs"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class NormalizeResult:
    source_document: SourceDocument
    evidence_items: tuple[EvidenceItem, ...]
    evidence_claims: tuple[EvidenceClaim, ...]

    def to_json_dict(self) -> JsonDict:
        return {
            "source_document": self.source_document.to_json_dict(),
            "evidence_items": [item.to_json_dict() for item in self.evidence_items],
            "evidence_claims": [claim.to_json_dict() for claim in self.evidence_claims],
        }
