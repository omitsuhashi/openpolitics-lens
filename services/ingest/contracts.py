from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Self

JsonDict = dict[str, object]
OfficialityLevel = Literal[
    "official_primary",
    "official_notice",
    "official_aggregator",
    "official_archive",
    "non_official_reference",
]
CoverageStatus = Literal[
    "supported",
    "source_identified",
    "manual_review_required",
    "source_missing",
    "blocked_by_terms",
    "retired",
]
CoverageFailureKind = Literal["fetch_failure", "parser_failure"]
CoverageKey = tuple[str, str, str, str, str]

OFFICIALITY_LEVELS: tuple[str, ...] = (
    "official_primary",
    "official_notice",
    "official_aggregator",
    "official_archive",
    "non_official_reference",
)
COVERAGE_STATUSES: tuple[str, ...] = (
    "supported",
    "source_identified",
    "manual_review_required",
    "source_missing",
    "blocked_by_terms",
    "retired",
)
COVERAGE_FAILURE_KINDS: tuple[str, ...] = ("fetch_failure", "parser_failure")
COVERAGE_SUMMARY_STATUSES: tuple[str, ...] = (
    "supported",
    "source_identified",
    "manual_review_required",
    "source_missing",
    "blocked_by_terms",
    "retired",
)
OFFICIAL_SOURCE_LEVELS: tuple[str, ...] = (
    "official_primary",
    "official_notice",
    "official_aggregator",
    "official_archive",
)
REQUIRED_COVERAGE_SOURCE_FAMILIES: tuple[str, ...] = (
    "jp_national_election_notices",
    "jp_diet_schedule",
    "jp_ndl_diet_minutes",
    "jp_prefecture_election_schedules",
    "jp_municipality_election_schedules",
    "jp_local_assembly_schedule",
)


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _datetime_from_json(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 string")
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    _validate_timezone_aware_datetime(parsed, field_name)
    return parsed.astimezone(UTC)


def _optional_datetime_to_json(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_to_json(value)


def _optional_datetime_from_json(data: JsonDict, field_name: str) -> datetime | None:
    if field_name not in data:
        raise ValueError(f"{field_name} is required")
    value = data[field_name]
    if value is None:
        return None
    return _datetime_from_json(value, field_name)


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


def _validate_non_empty_fields(record: object, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        value = getattr(record, field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")


def _validate_nullable_text(value: str | None, field_name: str) -> None:
    if value is not None and not value.strip():
        raise ValueError(f"{field_name} must be null or a non-empty string")


def _validate_choice(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        allowed = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _validate_timezone_aware_datetime(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _validate_optional_timezone_aware_datetime(
    value: datetime | None,
    field_name: str,
) -> None:
    if value is not None:
        _validate_timezone_aware_datetime(value, field_name)


@dataclass(frozen=True, slots=True)
class JurisdictionProfile:
    jurisdiction_id: str
    jurisdiction_level: str
    country_code: str
    subdivision_code: str | None
    municipality_code: str | None
    display_name: str

    def to_json_dict(self) -> JsonDict:
        return {
            "jurisdiction_id": self.jurisdiction_id,
            "jurisdiction_level": self.jurisdiction_level,
            "country_code": self.country_code,
            "subdivision_code": self.subdivision_code,
            "municipality_code": self.municipality_code,
            "display_name": self.display_name,
        }


@dataclass(frozen=True, slots=True)
class SourceFamily:
    source_family: str
    source_system: str
    display_name: str

    def to_json_dict(self) -> JsonDict:
        return {
            "source_family": self.source_family,
            "source_system": self.source_system,
            "display_name": self.display_name,
        }


@dataclass(frozen=True, slots=True)
class SourceRegistryRecord:
    jurisdiction_id: str
    jurisdiction_level: str
    country_code: str
    subdivision_code: str | None
    municipality_code: str | None
    source_system: str
    source_family: str
    connector_id: str
    officiality_level: OfficialityLevel
    operator_name: str
    entrypoint_url: str
    retrieval_method: str
    coverage_scope: str
    coverage_status: CoverageStatus
    rate_limit_policy: str
    terms_note: str
    last_verified_at: datetime
    connector_status: str

    def __post_init__(self) -> None:
        _validate_non_empty_fields(
            self,
            (
                "jurisdiction_id",
                "jurisdiction_level",
                "country_code",
                "source_system",
                "source_family",
                "connector_id",
                "officiality_level",
                "operator_name",
                "entrypoint_url",
                "retrieval_method",
                "coverage_scope",
                "coverage_status",
                "rate_limit_policy",
                "terms_note",
                "connector_status",
            ),
        )
        _validate_nullable_text(self.subdivision_code, "subdivision_code")
        _validate_nullable_text(self.municipality_code, "municipality_code")
        _validate_choice("officiality_level", self.officiality_level, OFFICIALITY_LEVELS)
        _validate_choice("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        _validate_timezone_aware_datetime(self.last_verified_at, "last_verified_at")
        if (
            self.officiality_level == "non_official_reference"
            and self.coverage_status == "supported"
        ):
            raise ValueError("non_official_reference cannot be marked supported")

    @classmethod
    def from_json_dict(cls, data: JsonDict) -> Self:
        return cls(
            jurisdiction_id=_required_str(data, "jurisdiction_id"),
            jurisdiction_level=_required_str(data, "jurisdiction_level"),
            country_code=_required_str(data, "country_code"),
            subdivision_code=_required_nullable_str(data, "subdivision_code"),
            municipality_code=_required_nullable_str(data, "municipality_code"),
            source_system=_required_str(data, "source_system"),
            source_family=_required_str(data, "source_family"),
            connector_id=_required_str(data, "connector_id"),
            officiality_level=_required_str(data, "officiality_level"),
            operator_name=_required_str(data, "operator_name"),
            entrypoint_url=_required_str(data, "entrypoint_url"),
            retrieval_method=_required_str(data, "retrieval_method"),
            coverage_scope=_required_str(data, "coverage_scope"),
            coverage_status=_required_str(data, "coverage_status"),
            rate_limit_policy=_required_str(data, "rate_limit_policy"),
            terms_note=_required_str(data, "terms_note"),
            last_verified_at=_datetime_from_json(data.get("last_verified_at"), "last_verified_at"),
            connector_status=_required_str(data, "connector_status"),
        )

    def coverage_key(self) -> CoverageKey:
        return (
            self.jurisdiction_id,
            self.source_system,
            self.source_family,
            self.connector_id,
            self.coverage_scope,
        )

    def is_connector_execution_target(self) -> bool:
        return (
            self.coverage_status == "supported" and self.officiality_level in OFFICIAL_SOURCE_LEVELS
        )

    def to_json_dict(self) -> JsonDict:
        return {
            "jurisdiction_id": self.jurisdiction_id,
            "jurisdiction_level": self.jurisdiction_level,
            "country_code": self.country_code,
            "subdivision_code": self.subdivision_code,
            "municipality_code": self.municipality_code,
            "source_system": self.source_system,
            "source_family": self.source_family,
            "connector_id": self.connector_id,
            "officiality_level": self.officiality_level,
            "operator_name": self.operator_name,
            "entrypoint_url": self.entrypoint_url,
            "retrieval_method": self.retrieval_method,
            "coverage_scope": self.coverage_scope,
            "coverage_status": self.coverage_status,
            "rate_limit_policy": self.rate_limit_policy,
            "terms_note": self.terms_note,
            "last_verified_at": _datetime_to_json(self.last_verified_at),
            "connector_status": self.connector_status,
        }


@dataclass(frozen=True, slots=True)
class SourceCoverageRecord:
    jurisdiction_id: str
    jurisdiction_level: str
    source_system: str
    source_family: str
    connector_id: str
    retrieval_method: str
    coverage_scope: str
    coverage_status: CoverageStatus
    entrypoint_url: str
    last_checked_at: datetime
    last_successful_fetch_at: datetime | None
    last_verified_at: datetime
    last_error: str | None
    terms_note: str
    manual_notes: str
    next_action: str

    def __post_init__(self) -> None:
        _validate_non_empty_fields(
            self,
            (
                "jurisdiction_id",
                "jurisdiction_level",
                "source_system",
                "source_family",
                "connector_id",
                "retrieval_method",
                "coverage_scope",
                "coverage_status",
                "entrypoint_url",
                "terms_note",
                "manual_notes",
                "next_action",
            ),
        )
        _validate_choice("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        _validate_timezone_aware_datetime(self.last_checked_at, "last_checked_at")
        _validate_optional_timezone_aware_datetime(
            self.last_successful_fetch_at,
            "last_successful_fetch_at",
        )
        _validate_timezone_aware_datetime(self.last_verified_at, "last_verified_at")
        _validate_nullable_text(self.last_error, "last_error")

    @classmethod
    def from_json_dict(cls, data: JsonDict) -> Self:
        return cls(
            jurisdiction_id=_required_str(data, "jurisdiction_id"),
            jurisdiction_level=_required_str(data, "jurisdiction_level"),
            source_system=_required_str(data, "source_system"),
            source_family=_required_str(data, "source_family"),
            connector_id=_required_str(data, "connector_id"),
            retrieval_method=_required_str(data, "retrieval_method"),
            coverage_scope=_required_str(data, "coverage_scope"),
            coverage_status=_required_str(data, "coverage_status"),
            entrypoint_url=_required_str(data, "entrypoint_url"),
            last_checked_at=_datetime_from_json(data.get("last_checked_at"), "last_checked_at"),
            last_successful_fetch_at=_optional_datetime_from_json(
                data,
                "last_successful_fetch_at",
            ),
            last_verified_at=_datetime_from_json(
                data.get("last_verified_at"),
                "last_verified_at",
            ),
            last_error=_required_nullable_str(data, "last_error"),
            terms_note=_required_str(data, "terms_note"),
            manual_notes=_required_str(data, "manual_notes"),
            next_action=_required_str(data, "next_action"),
        )

    def coverage_key(self) -> CoverageKey:
        return (
            self.jurisdiction_id,
            self.source_system,
            self.source_family,
            self.connector_id,
            self.coverage_scope,
        )

    def to_json_dict(self) -> JsonDict:
        return {
            "jurisdiction_id": self.jurisdiction_id,
            "jurisdiction_level": self.jurisdiction_level,
            "source_system": self.source_system,
            "source_family": self.source_family,
            "connector_id": self.connector_id,
            "retrieval_method": self.retrieval_method,
            "coverage_scope": self.coverage_scope,
            "coverage_status": self.coverage_status,
            "entrypoint_url": self.entrypoint_url,
            "last_checked_at": _datetime_to_json(self.last_checked_at),
            "last_successful_fetch_at": _optional_datetime_to_json(self.last_successful_fetch_at),
            "last_verified_at": _datetime_to_json(self.last_verified_at),
            "last_error": self.last_error,
            "terms_note": self.terms_note,
            "manual_notes": self.manual_notes,
            "next_action": self.next_action,
        }


@dataclass(frozen=True, slots=True)
class CoverageStatusCount:
    coverage_status: CoverageStatus
    count: int

    def __post_init__(self) -> None:
        _validate_choice("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 0:
            raise ValueError("count must be a non-negative integer")

    def to_json_dict(self) -> JsonDict:
        return {"coverage_status": self.coverage_status, "count": self.count}


@dataclass(frozen=True, slots=True)
class RequiredCoverageSummary:
    required_source_count: int
    coverage_record_count: int
    status_counts: tuple[CoverageStatusCount, ...]
    missing_coverage_keys: tuple[CoverageKey, ...]
    coverage_gap_keys: tuple[CoverageKey, ...]
    observed_event_count: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("required_source_count", "coverage_record_count"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.observed_event_count is not None and (
            isinstance(self.observed_event_count, bool)
            or not isinstance(self.observed_event_count, int)
            or self.observed_event_count < 0
        ):
            raise ValueError("observed_event_count must be null or a non-negative integer")

    @property
    def has_all_required_coverage_records(self) -> bool:
        return not self.missing_coverage_keys

    @property
    def is_complete(self) -> bool:
        return self.has_all_required_coverage_records and not self.coverage_gap_keys

    @property
    def no_events_claimed(self) -> bool:
        return False

    def status_count(self, coverage_status: CoverageStatus) -> int:
        _validate_choice("coverage_status", coverage_status, COVERAGE_STATUSES)
        for item in self.status_counts:
            if item.coverage_status == coverage_status:
                return item.count
        return 0

    def to_json_dict(self) -> JsonDict:
        return {
            "required_source_count": self.required_source_count,
            "coverage_record_count": self.coverage_record_count,
            "status_counts": {item.coverage_status: item.count for item in self.status_counts},
            "missing_coverage_keys": [list(key) for key in self.missing_coverage_keys],
            "coverage_gap_keys": [list(key) for key in self.coverage_gap_keys],
            "has_all_required_coverage_records": self.has_all_required_coverage_records,
            "is_complete": self.is_complete,
            "observed_event_count": self.observed_event_count,
            "event_absence_claim": "not_asserted",
            "no_events_claimed": self.no_events_claimed,
        }


class MissingSourceCoverageError(ValueError):
    pass


class DuplicateSourceCoverageError(ValueError):
    pass


def _coverage_records_by_key(
    coverage_records: tuple[SourceCoverageRecord, ...],
) -> dict[CoverageKey, SourceCoverageRecord]:
    coverage_by_key: dict[CoverageKey, SourceCoverageRecord] = {}
    duplicate_keys: list[CoverageKey] = []
    for record in coverage_records:
        key = record.coverage_key()
        if key in coverage_by_key:
            duplicate_keys.append(key)
            continue
        coverage_by_key[key] = record
    if duplicate_keys:
        duplicate_text = ", ".join("/".join(key) for key in duplicate_keys)
        raise DuplicateSourceCoverageError(f"duplicate source coverage records: {duplicate_text}")
    return coverage_by_key


def summarize_required_coverage(
    registry_records: tuple[SourceRegistryRecord, ...],
    coverage_records: tuple[SourceCoverageRecord, ...],
    *,
    observed_event_count: int | None = None,
) -> RequiredCoverageSummary:
    coverage_by_key = _coverage_records_by_key(coverage_records)
    required_records = tuple(
        record
        for record in registry_records
        if record.source_family in REQUIRED_COVERAGE_SOURCE_FAMILIES
    )
    missing_coverage_keys = tuple(
        record.coverage_key()
        for record in required_records
        if record.coverage_key() not in coverage_by_key
    )
    present_coverage_records = tuple(
        coverage_by_key[record.coverage_key()]
        for record in required_records
        if record.coverage_key() in coverage_by_key
    )
    counts = {status: 0 for status in COVERAGE_SUMMARY_STATUSES}
    for record in present_coverage_records:
        counts[record.coverage_status] += 1
    coverage_gap_keys = tuple(
        record.coverage_key()
        for record in present_coverage_records
        if record.coverage_status != "supported"
    )
    return RequiredCoverageSummary(
        required_source_count=len(required_records),
        coverage_record_count=len(present_coverage_records),
        status_counts=tuple(
            CoverageStatusCount(coverage_status=status, count=count)
            for status, count in counts.items()
        ),
        missing_coverage_keys=missing_coverage_keys,
        coverage_gap_keys=coverage_gap_keys,
        observed_event_count=observed_event_count,
    )


def source_coverage_failure_record(
    registry_record: SourceRegistryRecord,
    *,
    failure_kind: CoverageFailureKind,
    checked_at: datetime,
    error: str,
    next_action: str,
    manual_notes: str | None = None,
) -> SourceCoverageRecord:
    _validate_choice("failure_kind", failure_kind, COVERAGE_FAILURE_KINDS)
    if not isinstance(error, str) or not error.strip():
        raise ValueError("error must be a non-empty string")
    return SourceCoverageRecord(
        jurisdiction_id=registry_record.jurisdiction_id,
        jurisdiction_level=registry_record.jurisdiction_level,
        source_system=registry_record.source_system,
        source_family=registry_record.source_family,
        connector_id=registry_record.connector_id,
        retrieval_method=registry_record.retrieval_method,
        coverage_scope=registry_record.coverage_scope,
        coverage_status="manual_review_required",
        entrypoint_url=registry_record.entrypoint_url,
        last_checked_at=checked_at,
        last_successful_fetch_at=None,
        last_verified_at=checked_at,
        last_error=f"{failure_kind}: {error.strip()}",
        terms_note=registry_record.terms_note,
        manual_notes=(
            manual_notes
            if manual_notes is not None
            else f"{failure_kind} recorded as a coverage gap; this is not a silent drop."
        ),
        next_action=next_action,
    )


def validate_required_coverage_records(
    registry_records: tuple[SourceRegistryRecord, ...],
    coverage_records: tuple[SourceCoverageRecord, ...],
) -> None:
    coverage_keys = set(_coverage_records_by_key(coverage_records))
    missing = [
        record.coverage_key()
        for record in registry_records
        if record.source_family in REQUIRED_COVERAGE_SOURCE_FAMILIES
        and record.coverage_key() not in coverage_keys
    ]
    if missing:
        missing_text = ", ".join("/".join(key) for key in missing)
        raise MissingSourceCoverageError(f"missing source coverage records: {missing_text}")


def connector_execution_targets(
    registry_records: tuple[SourceRegistryRecord, ...],
    coverage_records: tuple[SourceCoverageRecord, ...] = (),
) -> tuple[SourceRegistryRecord, ...]:
    coverage_by_key = _coverage_records_by_key(coverage_records)
    return tuple(
        record
        for record in registry_records
        if record.is_connector_execution_target()
        and coverage_by_key.get(record.coverage_key(), record).coverage_status != "blocked_by_terms"
    )


@dataclass(frozen=True, slots=True)
class ConnectorDefinition:
    connector_id: str
    connector_version: str
    jurisdiction: JurisdictionProfile
    source_family: SourceFamily
    start_url: str
    rate_limit_policy: str
    terms_note: str

    def identity_json_dict(self) -> JsonDict:
        return {
            "jurisdiction_id": self.jurisdiction.jurisdiction_id,
            "jurisdiction_level": self.jurisdiction.jurisdiction_level,
            "source_system": self.source_family.source_system,
            "source_family": self.source_family.source_family,
            "connector_id": self.connector_id,
            "connector_version": self.connector_version,
        }

    def to_json_dict(self) -> JsonDict:
        return {
            **self.identity_json_dict(),
            "jurisdiction": self.jurisdiction.to_json_dict(),
            "source_family_definition": self.source_family.to_json_dict(),
            "start_url": self.start_url,
            "rate_limit_policy": self.rate_limit_policy,
            "terms_note": self.terms_note,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryRecord:
    connector: ConnectorDefinition
    canonical_url: str
    discovered_at: datetime
    parent_url: str
    candidate_type: str
    title: str
    matched_keywords: tuple[str, ...]
    relevance_reason: str

    def to_json_dict(self) -> JsonDict:
        return {
            **self.connector.identity_json_dict(),
            "canonical_url": self.canonical_url,
            "discovered_at": _datetime_to_json(self.discovered_at),
            "parent_url": self.parent_url,
            "candidate_type": self.candidate_type,
            "title": self.title,
            "matched_keywords": list(self.matched_keywords),
            "relevance_reason": self.relevance_reason,
        }


@dataclass(frozen=True, slots=True)
class SourceDocumentCandidate:
    canonical_url: str
    title: str
    source_type: str
    jurisdiction_id: str
    source_family: str
    language: str
    retrieved_at: datetime
    raw_artifact_path: str

    def to_json_dict(self) -> JsonDict:
        return {
            "canonical_url": self.canonical_url,
            "title": self.title,
            "source_type": self.source_type,
            "jurisdiction_id": self.jurisdiction_id,
            "source_family": self.source_family,
            "language": self.language,
            "retrieved_at": _datetime_to_json(self.retrieved_at),
            "raw_artifact_path": self.raw_artifact_path,
        }


@dataclass(frozen=True, slots=True)
class FetchManifestRecord:
    connector: ConnectorDefinition
    canonical_url: str
    fetched_at: datetime
    http_status: int
    content_hash: str
    media_type: str
    byte_size: int
    raw_artifact_path: str
    source_document_candidate: SourceDocumentCandidate

    def to_json_dict(self) -> JsonDict:
        return {
            **self.connector.identity_json_dict(),
            "canonical_url": self.canonical_url,
            "fetched_at": _datetime_to_json(self.fetched_at),
            "http_status": self.http_status,
            "content_hash": self.content_hash,
            "media_type": self.media_type,
            "byte_size": self.byte_size,
            "raw_artifact_path": self.raw_artifact_path,
            "rate_limit_policy": self.connector.rate_limit_policy,
            "terms_note": self.connector.terms_note,
            "source_document_candidate": self.source_document_candidate.to_json_dict(),
        }
