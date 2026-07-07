from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal, Self

JsonDict = dict[str, object]
EventFamily = Literal[
    "Election",
    "Diet",
    "LocalAssembly",
    "PublicConsultation",
    "AdministrativeDeliberation",
]
EventStatus = Literal[
    "scheduled",
    "announced",
    "opened",
    "closed",
    "published",
    "completed",
    "cancelled",
    "postponed",
    "unknown",
]
DatePrecision = Literal["date", "date_time", "month", "year", "unknown"]
ReviewState = Literal["machine_extracted", "needs_review", "human_verified", "rejected"]
ConflictState = Literal[
    "none",
    "duplicate",
    "date_mismatch",
    "title_mismatch",
    "status_mismatch",
    "needs_review",
]
EVENT_FAMILIES: tuple[str, ...] = (
    "Election",
    "Diet",
    "LocalAssembly",
    "PublicConsultation",
    "AdministrativeDeliberation",
)
EVENT_STATUSES: tuple[str, ...] = (
    "scheduled",
    "announced",
    "opened",
    "closed",
    "published",
    "completed",
    "cancelled",
    "postponed",
    "unknown",
)
DATE_PRECISIONS: tuple[str, ...] = ("date", "date_time", "month", "year", "unknown")
REVIEW_STATES: tuple[str, ...] = (
    "machine_extracted",
    "needs_review",
    "human_verified",
    "rejected",
)
CONFLICT_STATES: tuple[str, ...] = (
    "none",
    "duplicate",
    "date_mismatch",
    "title_mismatch",
    "status_mismatch",
    "needs_review",
)


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _date_to_json(value: date) -> str:
    return value.isoformat()


def _datetime_from_json(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 string")
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    _validate_timezone_aware_datetime(parsed, field_name)
    return parsed.astimezone(UTC)


def _date_from_json(value: object, field_name: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 date string")
    parsed = date.fromisoformat(value)
    return parsed


def _required_str(data: JsonDict, field_name: str) -> str:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    value = data[field_name]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _required_nullable_str(data: JsonDict, field_name: str) -> str | None:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    value = data[field_name]
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be null or a non-empty string")
    return value


def _required_date(data: JsonDict, field_name: str) -> date:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    return _date_from_json(data[field_name], field_name)


def _required_datetime(data: JsonDict, field_name: str) -> datetime:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    return _datetime_from_json(data[field_name], field_name)


def _required_float(data: JsonDict, field_name: str) -> float:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    value = data[field_name]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a number")
    return float(value)


def _required_int(data: JsonDict, field_name: str) -> int:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    value = data[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _required_str_tuple(data: JsonDict, field_name: str) -> tuple[str, ...]:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    value = data[field_name]
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings")
    values = tuple(value)
    _validate_str_tuple(values, field_name)
    return values


def _validate_non_empty_fields(record: object, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        value = getattr(record, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")


def _validate_nullable_text(value: str | None, field_name: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"{field_name} must be null or a non-empty string")


def _validate_choice(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        allowed = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _validate_timezone_aware_datetime(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _validate_date(value: date, field_name: str) -> None:
    if type(value) is not date:
        raise ValueError(f"{field_name} must be a date")


def _validate_confidence(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be a number")
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _validate_source_priority(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")


def _validate_str_tuple(values: tuple[str, ...], field_name: str) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple of strings")
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must contain only non-empty strings")


def _validate_assertions(
    event_candidate_id: str,
    source_assertions: tuple["EventSourceAssertion", ...],
) -> None:
    if not source_assertions:
        raise ValueError("source_assertions must contain at least one evidence-backed assertion")
    for assertion in source_assertions:
        if not isinstance(assertion, EventSourceAssertion):
            raise ValueError("source_assertions must contain EventSourceAssertion records")
        if assertion.event_candidate_id != event_candidate_id:
            raise ValueError("source_assertions event_candidate_id must match event_candidate_id")


def _source_assertions_from_json(data: JsonDict) -> tuple["EventSourceAssertion", ...]:
    if "source_assertions" not in data:
        raise ValueError("source_assertions is required")
    value = data["source_assertions"]
    if not isinstance(value, list):
        raise ValueError("source_assertions must be a list")
    assertions: list[EventSourceAssertion] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("source_assertions must contain objects")
        assertions.append(EventSourceAssertion.from_json_dict(item))
    return tuple(assertions)


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

    source_span_start and source_span_end are byte offsets in the raw HTML bytes.
    quote_text is the decoded raw span text; normalized_text is cleaned for claims.
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
        }


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


@dataclass(frozen=True, slots=True)
class EventSourceAssertion:
    """Source-specific assertion for an official political event candidate."""

    event_candidate_id: str
    source_document_id: str
    evidence_item_id: str
    asserted_field: str
    asserted_value: str
    asserted_at: datetime
    source_priority: int
    conflict_state: ConflictState
    confidence: float
    review_state: ReviewState
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_non_empty_fields(
            self,
            (
                "event_candidate_id",
                "source_document_id",
                "evidence_item_id",
                "asserted_field",
                "asserted_value",
                "conflict_state",
                "review_state",
            ),
        )
        _validate_timezone_aware_datetime(self.asserted_at, "asserted_at")
        _validate_source_priority(self.source_priority, "source_priority")
        _validate_choice("conflict_state", self.conflict_state, CONFLICT_STATES)
        _validate_confidence(self.confidence, "confidence")
        _validate_choice("review_state", self.review_state, REVIEW_STATES)
        _validate_str_tuple(self.limitations, "limitations")

    @classmethod
    def from_json_dict(cls, data: JsonDict) -> Self:
        return cls(
            event_candidate_id=_required_str(data, "event_candidate_id"),
            source_document_id=_required_str(data, "source_document_id"),
            evidence_item_id=_required_str(data, "evidence_item_id"),
            asserted_field=_required_str(data, "asserted_field"),
            asserted_value=_required_str(data, "asserted_value"),
            asserted_at=_required_datetime(data, "asserted_at"),
            source_priority=_required_int(data, "source_priority"),
            conflict_state=_required_str(data, "conflict_state"),
            confidence=_required_float(data, "confidence"),
            review_state=_required_str(data, "review_state"),
            limitations=_required_str_tuple(data, "limitations"),
        )

    def to_json_dict(self) -> JsonDict:
        return {
            "event_candidate_id": self.event_candidate_id,
            "source_document_id": self.source_document_id,
            "evidence_item_id": self.evidence_item_id,
            "asserted_field": self.asserted_field,
            "asserted_value": self.asserted_value,
            "asserted_at": _datetime_to_json(self.asserted_at),
            "source_priority": self.source_priority,
            "conflict_state": self.conflict_state,
            "confidence": self.confidence,
            "review_state": self.review_state,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class OfficialPoliticalEventCandidate:
    event_candidate_id: str
    event_family: EventFamily
    event_type: str
    jurisdiction_id: str
    jurisdiction_level: str
    source_system: str
    source_family: str
    connector_id: str
    title: str
    scheduled_date: date
    scheduled_time: str | None
    timezone: str
    date_precision: DatePrecision
    office_or_body: str
    event_status: EventStatus
    canonical_url: str
    source_document_id: str
    evidence_item_id: str
    extraction_method: str
    confidence: float
    review_state: ReviewState
    limitations: tuple[str, ...]
    source_assertions: tuple[EventSourceAssertion, ...]

    def __post_init__(self) -> None:
        _validate_non_empty_fields(
            self,
            (
                "event_candidate_id",
                "event_family",
                "event_type",
                "jurisdiction_id",
                "jurisdiction_level",
                "source_system",
                "source_family",
                "connector_id",
                "title",
                "timezone",
                "date_precision",
                "office_or_body",
                "event_status",
                "canonical_url",
                "source_document_id",
                "evidence_item_id",
                "extraction_method",
                "review_state",
            ),
        )
        _validate_date(self.scheduled_date, "scheduled_date")
        _validate_nullable_text(self.scheduled_time, "scheduled_time")
        _validate_choice("event_family", self.event_family, EVENT_FAMILIES)
        _validate_choice("event_status", self.event_status, EVENT_STATUSES)
        _validate_choice("date_precision", self.date_precision, DATE_PRECISIONS)
        _validate_confidence(self.confidence, "confidence")
        _validate_choice("review_state", self.review_state, REVIEW_STATES)
        _validate_str_tuple(self.limitations, "limitations")
        _validate_assertions(self.event_candidate_id, self.source_assertions)
        if not any(
            assertion.source_document_id == self.source_document_id
            and assertion.evidence_item_id == self.evidence_item_id
            for assertion in self.source_assertions
        ):
            raise ValueError(
                "source_assertions must include candidate source_document_id/evidence_item_id"
            )

    @classmethod
    def from_json_dict(cls, data: JsonDict) -> Self:
        return cls(
            event_candidate_id=_required_str(data, "event_candidate_id"),
            event_family=_required_str(data, "event_family"),
            event_type=_required_str(data, "event_type"),
            jurisdiction_id=_required_str(data, "jurisdiction_id"),
            jurisdiction_level=_required_str(data, "jurisdiction_level"),
            source_system=_required_str(data, "source_system"),
            source_family=_required_str(data, "source_family"),
            connector_id=_required_str(data, "connector_id"),
            title=_required_str(data, "title"),
            scheduled_date=_required_date(data, "scheduled_date"),
            scheduled_time=_required_nullable_str(data, "scheduled_time"),
            timezone=_required_str(data, "timezone"),
            date_precision=_required_str(data, "date_precision"),
            office_or_body=_required_str(data, "office_or_body"),
            event_status=_required_str(data, "event_status"),
            canonical_url=_required_str(data, "canonical_url"),
            source_document_id=_required_str(data, "source_document_id"),
            evidence_item_id=_required_str(data, "evidence_item_id"),
            extraction_method=_required_str(data, "extraction_method"),
            confidence=_required_float(data, "confidence"),
            review_state=_required_str(data, "review_state"),
            limitations=_required_str_tuple(data, "limitations"),
            source_assertions=_source_assertions_from_json(data),
        )

    def conflict_states(self) -> tuple[ConflictState, ...]:
        conflict_states: list[ConflictState] = []
        for assertion in self.source_assertions:
            if assertion.conflict_state == "none" or assertion.conflict_state in conflict_states:
                continue
            conflict_states.append(assertion.conflict_state)
        return tuple(conflict_states)

    def to_json_dict(self) -> JsonDict:
        return {
            "event_candidate_id": self.event_candidate_id,
            "event_family": self.event_family,
            "event_type": self.event_type,
            "jurisdiction_id": self.jurisdiction_id,
            "jurisdiction_level": self.jurisdiction_level,
            "source_system": self.source_system,
            "source_family": self.source_family,
            "connector_id": self.connector_id,
            "title": self.title,
            "scheduled_date": _date_to_json(self.scheduled_date),
            "scheduled_time": self.scheduled_time,
            "timezone": self.timezone,
            "date_precision": self.date_precision,
            "office_or_body": self.office_or_body,
            "event_status": self.event_status,
            "canonical_url": self.canonical_url,
            "source_document_id": self.source_document_id,
            "evidence_item_id": self.evidence_item_id,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "review_state": self.review_state,
            "limitations": list(self.limitations),
            "source_assertions": [assertion.to_json_dict() for assertion in self.source_assertions],
            "conflict_states": list(self.conflict_states()),
        }


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
