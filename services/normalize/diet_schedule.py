import re
from dataclasses import dataclass
from datetime import UTC, date
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from normalize.contracts import (
    EventSourceAssertion,
    EvidenceItem,
    OfficialPoliticalEventCandidate,
    SourceDocument,
)

_TITLE_PATTERN = re.compile(rb"<title\b[^>]*>(?P<title>.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
_TABLE_LABELS: dict[str, str] = {
    "meeting_date": "開会日",
    "meeting_time": "開会時刻",
    "meeting_kind": "会議",
    "session_start": "召集日",
    "session_end": "会期末日",
}
_DATE_PATTERN = re.compile(r"(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日")
_TIME_PATTERN = re.compile(r"(?P<hour>\d{1,2})時(?P<minute>\d{2})分")
_NO_EVENTS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"予定はありません"),
    re.compile(r"掲載はありません"),
)


def _table_value_pattern(label: str) -> re.Pattern[bytes]:
    return re.compile(
        rb"<th\b[^>]*>\s*"
        + re.escape(label.encode("utf-8"))
        + rb"\s*</th>\s*<td\b[^>]*>(?P<value>.*?)</td\s*>",
        re.IGNORECASE | re.DOTALL,
    )


_TABLE_VALUE_PATTERNS: dict[str, re.Pattern[bytes]] = {
    field_name: _table_value_pattern(label) for field_name, label in _TABLE_LABELS.items()
}


@dataclass(frozen=True, slots=True)
class EventNormalizeResult:
    source_document: SourceDocument
    evidence_items: tuple[EvidenceItem, ...]
    event_candidates: tuple[OfficialPoliticalEventCandidate, ...]


def _stable_uuid(*parts: object) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join(str(part) for part in parts)))


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _normalize_html_text(value: bytes) -> str:
    return _collapse_whitespace(unescape(re.sub(rb"<[^>]+>", b" ", value).decode("utf-8")))


def _extract_title(raw_html: bytes) -> str:
    match = _TITLE_PATTERN.search(raw_html)
    if match is None:
        raise ValueError("diet schedule page title is required")
    title = _normalize_html_text(match.group("title"))
    if not title:
        raise ValueError("diet schedule page title is empty")
    return title


def _extract_field(raw_html: bytes, field_name: str) -> tuple[str, int, int]:
    match = _TABLE_VALUE_PATTERNS[field_name].search(raw_html)
    if match is None:
        raise ValueError(f"diet schedule page {field_name} is required")
    start, end = match.span("value")
    value = _normalize_html_text(match.group("value"))
    if not value:
        raise ValueError(f"diet schedule page {field_name} is empty")
    return value, start, end


def _parse_meeting_date(value: str) -> date:
    match = _DATE_PATTERN.search(value)
    if match is None:
        raise ValueError("diet schedule page meeting_date must contain YYYY年M月D日")
    return date(
        int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
    )


def _parse_meeting_time(value: str) -> str:
    match = _TIME_PATTERN.search(value)
    if match is None:
        raise ValueError("diet schedule page meeting_time must contain HH時MM分")
    return f"{int(match.group('hour')):02d}:{match.group('minute')}"


def _promote_source_document(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    title: str,
) -> SourceDocument:
    candidate = record.source_document_candidate
    return SourceDocument(
        source_document_id=_stable_uuid(
            "source_document",
            raw_artifact_id,
            record.connector.source_family.source_system,
            candidate.source_type,
            candidate.canonical_url,
            record.content_hash,
        ),
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


def _build_evidence_item(
    *,
    source_document: SourceDocument,
    raw_artifact_path: str,
    quote_text: str,
    normalized_text: str,
    source_span_start: int,
    source_span_end: int,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_item_id=_stable_uuid(
            "evidence_item",
            source_document.source_document_id,
            "diet_schedule_meeting_date",
            source_span_start,
            source_span_end,
            normalized_text,
        ),
        source_document_id=source_document.source_document_id,
        location_type="html_selector",
        location_value="table:meeting_date",
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        quote_text=quote_text,
        normalized_text=normalized_text,
        raw_artifact_path=raw_artifact_path,
        extraction_method="diet_schedule_table_date",
        confidence=0.95,
    )


def _build_event_candidate(
    *,
    record: FetchManifestRecord,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    meeting_date: date,
    meeting_time: str,
    meeting_kind: str,
) -> OfficialPoliticalEventCandidate:
    chamber_name = (
        "衆議院"
        if record.connector.source_family.source_system == "house_of_representatives"
        else "参議院"
    )
    if "本会議" in meeting_kind:
        event_type = "plenary_meeting_scheduled"
    else:
        event_type = "committee_meeting_scheduled"
    title = f"{chamber_name}{meeting_kind}"
    event_candidate_id = _stable_uuid(
        "official_political_event_candidate",
        record.connector.connector_id,
        record.canonical_url,
        event_type,
        meeting_date.isoformat(),
        meeting_time,
    )
    source_assertion = EventSourceAssertion(
        event_candidate_id=event_candidate_id,
        source_document_id=source_document.source_document_id,
        evidence_item_id=evidence_item.evidence_item_id,
        asserted_field="scheduled_date",
        asserted_value=meeting_date.isoformat(),
        asserted_at=record.fetched_at.astimezone(UTC),
        source_priority=100,
        conflict_state="none",
        confidence=0.95,
        review_state="machine_extracted",
        limitations=("fixture-first diet schedule parsing",),
    )
    return OfficialPoliticalEventCandidate(
        event_candidate_id=event_candidate_id,
        event_family="Diet",
        event_type=event_type,
        jurisdiction_id=record.connector.jurisdiction.jurisdiction_id,
        jurisdiction_level=record.connector.jurisdiction.jurisdiction_level,
        source_system=record.connector.source_family.source_system,
        source_family=record.connector.source_family.source_family,
        connector_id=record.connector.connector_id,
        title=title,
        scheduled_date=meeting_date,
        scheduled_time=meeting_time,
        timezone="Asia/Tokyo",
        date_precision="date_time",
        office_or_body=title,
        event_status="scheduled",
        canonical_url=record.canonical_url,
        source_document_id=source_document.source_document_id,
        evidence_item_id=evidence_item.evidence_item_id,
        extraction_method="diet_schedule_table",
        confidence=0.95,
        review_state="machine_extracted",
        limitations=("fixture-first diet schedule parsing",),
        source_assertions=(source_assertion,),
    )


def _build_session_event_candidate(
    *,
    record: FetchManifestRecord,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
    event_type: str,
    event_date: date,
) -> OfficialPoliticalEventCandidate:
    chamber_name = (
        "衆議院"
        if record.connector.source_family.source_system == "house_of_representatives"
        else "参議院"
    )
    title_suffix = "会期開会" if event_type == "diet_session_convened" else "会期末日"
    title = f"{chamber_name}{title_suffix}"
    event_candidate_id = _stable_uuid(
        "official_political_event_candidate",
        record.connector.connector_id,
        record.canonical_url,
        event_type,
        event_date.isoformat(),
    )
    source_assertion = EventSourceAssertion(
        event_candidate_id=event_candidate_id,
        source_document_id=source_document.source_document_id,
        evidence_item_id=evidence_item.evidence_item_id,
        asserted_field="scheduled_date",
        asserted_value=event_date.isoformat(),
        asserted_at=record.fetched_at.astimezone(UTC),
        source_priority=100,
        conflict_state="none",
        confidence=0.95,
        review_state="machine_extracted",
        limitations=("fixture-first diet schedule parsing",),
    )
    return OfficialPoliticalEventCandidate(
        event_candidate_id=event_candidate_id,
        event_family="Diet",
        event_type=event_type,
        jurisdiction_id=record.connector.jurisdiction.jurisdiction_id,
        jurisdiction_level=record.connector.jurisdiction.jurisdiction_level,
        source_system=record.connector.source_family.source_system,
        source_family=record.connector.source_family.source_family,
        connector_id=record.connector.connector_id,
        title=title,
        scheduled_date=event_date,
        scheduled_time=None,
        timezone="Asia/Tokyo",
        date_precision="date",
        office_or_body=chamber_name,
        event_status="scheduled",
        canonical_url=record.canonical_url,
        source_document_id=source_document.source_document_id,
        evidence_item_id=evidence_item.evidence_item_id,
        extraction_method="diet_session_table",
        confidence=0.95,
        review_state="machine_extracted",
        limitations=("fixture-first diet schedule parsing",),
        source_assertions=(source_assertion,),
    )


def normalize_diet_schedule_page(
    record: FetchManifestRecord,
    raw_html: bytes,
    *,
    raw_artifact_id: str,
) -> EventNormalizeResult:
    decoded_html = raw_html.decode("utf-8")
    title = _extract_title(raw_html)
    source_document = _promote_source_document(record, raw_artifact_id=raw_artifact_id, title=title)
    if record.source_document_candidate.source_type == "diet_schedule_page" and any(
        pattern.search(decoded_html) for pattern in _NO_EVENTS_PATTERNS
    ):
        return EventNormalizeResult(
            source_document=source_document,
            evidence_items=(),
            event_candidates=(),
        )
    if record.source_document_candidate.source_type == "diet_session_page":
        start_text, start_span_start, start_span_end = _extract_field(raw_html, "session_start")
        end_text, end_span_start, end_span_end = _extract_field(raw_html, "session_end")
        start_item = _build_evidence_item(
            source_document=source_document,
            raw_artifact_path=record.raw_artifact_path,
            quote_text=start_text,
            normalized_text=start_text,
            source_span_start=start_span_start,
            source_span_end=start_span_end,
        )
        end_item = _build_evidence_item(
            source_document=source_document,
            raw_artifact_path=record.raw_artifact_path,
            quote_text=end_text,
            normalized_text=end_text,
            source_span_start=end_span_start,
            source_span_end=end_span_end,
        )
        return EventNormalizeResult(
            source_document=source_document,
            evidence_items=(start_item, end_item),
            event_candidates=(
                _build_session_event_candidate(
                    record=record,
                    source_document=source_document,
                    evidence_item=start_item,
                    event_type="diet_session_convened",
                    event_date=_parse_meeting_date(start_text),
                ),
                _build_session_event_candidate(
                    record=record,
                    source_document=source_document,
                    evidence_item=end_item,
                    event_type="diet_session_ends",
                    event_date=_parse_meeting_date(end_text),
                ),
            ),
        )

    meeting_date_text, span_start, span_end = _extract_field(raw_html, "meeting_date")
    meeting_time_text, _time_start, _time_end = _extract_field(raw_html, "meeting_time")
    meeting_kind, _kind_start, _kind_end = _extract_field(raw_html, "meeting_kind")
    evidence_item = _build_evidence_item(
        source_document=source_document,
        raw_artifact_path=record.raw_artifact_path,
        quote_text=meeting_date_text,
        normalized_text=meeting_date_text,
        source_span_start=span_start,
        source_span_end=span_end,
    )
    event_candidate = _build_event_candidate(
        record=record,
        source_document=source_document,
        evidence_item=evidence_item,
        meeting_date=_parse_meeting_date(meeting_date_text),
        meeting_time=_parse_meeting_time(meeting_time_text),
        meeting_kind=meeting_kind,
    )
    return EventNormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        event_candidates=(event_candidate,),
    )
