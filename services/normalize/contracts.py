from dataclasses import dataclass
from datetime import UTC, date, datetime

JsonDict = dict[str, object]


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _date_to_json(value: date) -> str:
    return value.isoformat()


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
