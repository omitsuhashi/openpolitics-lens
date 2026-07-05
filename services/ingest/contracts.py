from dataclasses import dataclass
from datetime import UTC, datetime

JsonDict = dict[str, object]


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


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
