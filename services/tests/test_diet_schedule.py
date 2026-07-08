import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import ingest
import normalize

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FETCHED_AT = datetime(2026, 7, 8, 9, 0, tzinfo=UTC)


def _house_plenary_fetch_record() -> ingest.FetchManifestRecord:
    candidate = ingest.SourceDocumentCandidate(
        canonical_url="https://www.shugiin.go.jp/internet/itdb_honkaigi.nsf/html/honkaigi/20260721.htm",
        title="衆議院本会議開会情報",
        source_type="diet_schedule_page",
        jurisdiction_id="jp",
        source_family="jp_diet_schedule",
        language="ja",
        retrieved_at=FETCHED_AT,
        raw_artifact_path="raw/jp/jp_diet_schedule/2026/07/house-plenary.html",
    )
    return ingest.FetchManifestRecord(
        connector=ingest.HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR,
        canonical_url=candidate.canonical_url,
        fetched_at=FETCHED_AT,
        http_status=200,
        content_hash="a" * 64,
        media_type="text/html; charset=utf-8",
        byte_size=1234,
        raw_artifact_path=candidate.raw_artifact_path,
        source_document_candidate=candidate,
    )


def _house_session_fetch_record() -> ingest.FetchManifestRecord:
    candidate = ingest.SourceDocumentCandidate(
        canonical_url="https://www.shugiin.go.jp/internet/itdb_kaiki.nsf/html/kaiji/217.htm",
        title="第217回国会 会期情報",
        source_type="diet_session_page",
        jurisdiction_id="jp",
        source_family="jp_diet_schedule",
        language="ja",
        retrieved_at=FETCHED_AT,
        raw_artifact_path="raw/jp/jp_diet_schedule/2026/07/house-session.html",
    )
    return ingest.FetchManifestRecord(
        connector=ingest.HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR,
        canonical_url=candidate.canonical_url,
        fetched_at=FETCHED_AT,
        http_status=200,
        content_hash="b" * 64,
        media_type="text/html; charset=utf-8",
        byte_size=1234,
        raw_artifact_path=candidate.raw_artifact_path,
        source_document_candidate=candidate,
    )


def _councillors_committee_fetch_record() -> ingest.FetchManifestRecord:
    candidate = ingest.SourceDocumentCandidate(
        canonical_url="https://www.sangiin.go.jp/japanese/joho1/kousei/kaigi/217/committee20260722.html",
        title="参議院 財政金融委員会 開会情報",
        source_type="diet_schedule_page",
        jurisdiction_id="jp",
        source_family="jp_diet_schedule",
        language="ja",
        retrieved_at=FETCHED_AT,
        raw_artifact_path="raw/jp/jp_diet_schedule/2026/07/councillors-committee.html",
    )
    return ingest.FetchManifestRecord(
        connector=ingest.HOUSE_OF_COUNCILLORS_DIET_SCHEDULE_CONNECTOR,
        canonical_url=candidate.canonical_url,
        fetched_at=FETCHED_AT,
        http_status=200,
        content_hash="c" * 64,
        media_type="text/html; charset=utf-8",
        byte_size=1234,
        raw_artifact_path=candidate.raw_artifact_path,
        source_document_candidate=candidate,
    )


def _house_empty_schedule_fetch_record() -> ingest.FetchManifestRecord:
    candidate = ingest.SourceDocumentCandidate(
        canonical_url="https://www.shugiin.go.jp/internet/itdb_iinkai.nsf/html/iinkai/noevents.htm",
        title="衆議院委員会予定",
        source_type="diet_schedule_page",
        jurisdiction_id="jp",
        source_family="jp_diet_schedule",
        language="ja",
        retrieved_at=FETCHED_AT,
        raw_artifact_path="raw/jp/jp_diet_schedule/2026/07/house-empty-schedule.html",
    )
    return ingest.FetchManifestRecord(
        connector=ingest.HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR,
        canonical_url=candidate.canonical_url,
        fetched_at=FETCHED_AT,
        http_status=200,
        content_hash="d" * 64,
        media_type="text/html; charset=utf-8",
        byte_size=1234,
        raw_artifact_path=candidate.raw_artifact_path,
        source_document_candidate=candidate,
    )


def test_normalize_house_plenary_schedule_page_emits_diet_event_candidate() -> None:
    record = _house_plenary_fetch_record()
    raw_html = (FIXTURES_DIR / "diet_schedule_house_plenary.html").read_bytes()

    result = normalize.normalize_diet_schedule_page(
        record,
        raw_html,
        raw_artifact_id="raw-artifact-house-plenary-1",
    )

    assert result.source_document.source_family == "jp_diet_schedule"
    assert len(result.event_candidates) == 1
    event_candidate = result.event_candidates[0]
    assert event_candidate.event_family == "Diet"
    assert event_candidate.event_type == "plenary_meeting_scheduled"
    assert event_candidate.scheduled_date == date(2026, 7, 21)
    assert event_candidate.source_system == "house_of_representatives"
    assert event_candidate.source_family == "jp_diet_schedule"
    assert event_candidate.connector_id == "jp.diet_schedule.house_of_representatives.v1"
    assert event_candidate.office_or_body == "衆議院本会議"
    assert event_candidate.canonical_url == record.canonical_url
    assert event_candidate.evidence_item_id == result.evidence_items[0].evidence_item_id
    assert result.evidence_items[0].quote_text == "2026年7月21日"
    expected_date_bytes = "2026年7月21日".encode()
    assert result.evidence_items[0].source_span_start == raw_html.index(expected_date_bytes)
    assert result.evidence_items[0].source_span_end == result.evidence_items[
        0
    ].source_span_start + len(expected_date_bytes)


def test_normalize_house_session_page_emits_convened_and_end_candidates() -> None:
    record = _house_session_fetch_record()
    raw_html = (FIXTURES_DIR / "diet_schedule_house_session.html").read_bytes()

    result = normalize.normalize_diet_schedule_page(
        record,
        raw_html,
        raw_artifact_id="raw-artifact-house-session-1",
    )

    assert [candidate.event_type for candidate in result.event_candidates] == [
        "diet_session_convened",
        "diet_session_ends",
    ]
    assert [candidate.scheduled_date for candidate in result.event_candidates] == [
        date(2026, 1, 24),
        date(2026, 6, 22),
    ]


def test_normalize_councillors_committee_page_emits_committee_candidate() -> None:
    record = _councillors_committee_fetch_record()
    raw_html = (FIXTURES_DIR / "diet_schedule_councillors_committee.html").read_bytes()

    result = normalize.normalize_diet_schedule_page(
        record,
        raw_html,
        raw_artifact_id="raw-artifact-councillors-committee-1",
    )

    assert len(result.event_candidates) == 1
    event_candidate = result.event_candidates[0]
    assert event_candidate.event_type == "committee_meeting_scheduled"
    assert event_candidate.scheduled_date == date(2026, 7, 22)
    assert event_candidate.source_system == "house_of_councillors"
    assert event_candidate.connector_id == "jp.diet_schedule.house_of_councillors.v1"
    assert event_candidate.office_or_body == "参議院財政金融委員会"


def test_empty_schedule_page_returns_no_events_and_supported_coverage_record() -> None:
    record = _house_empty_schedule_fetch_record()
    raw_html = (FIXTURES_DIR / "diet_schedule_house_empty.html").read_bytes()

    result = normalize.normalize_diet_schedule_page(
        record,
        raw_html,
        raw_artifact_id="raw-artifact-house-empty-1",
    )

    connector = ingest.DietScheduleConnector(
        definition=ingest.HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR
    )
    coverage = connector.coverage_record_for_observed_page(
        checked_at=FETCHED_AT,
        observed_event_count=len(result.event_candidates),
    )

    assert result.event_candidates == ()
    assert coverage.coverage_status == "supported"
    assert coverage.last_error is None
    assert "予定掲載なし" in coverage.manual_notes


def test_diet_schedule_connector_fetches_fixture_pages_into_manifest_and_raw(
    tmp_path: Path,
) -> None:
    connector = ingest.DietScheduleConnector(
        definition=ingest.HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR
    )
    pages = (
        ingest.DietScheduleFixturePage(
            canonical_url="https://www.shugiin.go.jp/internet/itdb_honkaigi.nsf/html/honkaigi/20260721.htm",
            title="衆議院本会議開会情報",
            source_type="diet_schedule_page",
            content=(FIXTURES_DIR / "diet_schedule_house_plenary.html").read_bytes(),
        ),
        ingest.DietScheduleFixturePage(
            canonical_url="https://www.shugiin.go.jp/internet/itdb_kaiki.nsf/html/kaiji/217.htm",
            title="第217回国会 会期情報",
            source_type="diet_session_page",
            content=(FIXTURES_DIR / "diet_schedule_house_session.html").read_bytes(),
        ),
    )
    writer = ingest.FileSystemOutputWriter(tmp_path)

    records = connector.fetch_fixture_pages(
        pages,
        output_writer=writer,
        run_id="diet-fixture-run",
        fetched_at=FETCHED_AT,
    )

    assert len(records) == 2
    fetched_path = tmp_path / "manifests" / "diet-fixture-run" / "fetched.jsonl"
    payloads = [json.loads(line) for line in fetched_path.read_text(encoding="utf-8").splitlines()]
    assert [payload["canonical_url"] for payload in payloads] == [
        page.canonical_url for page in pages
    ]
    assert [payload["source_document_candidate"]["source_type"] for payload in payloads] == [
        "diet_schedule_page",
        "diet_session_page",
    ]
    assert all((tmp_path / payload["raw_artifact_path"]).exists() for payload in payloads)


def test_unstable_schedule_page_is_escalated_to_manual_review_coverage() -> None:
    record = _house_plenary_fetch_record()
    raw_html = (FIXTURES_DIR / "diet_schedule_house_unstable.html").read_bytes()
    connector = ingest.DietScheduleConnector(
        definition=ingest.HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR
    )

    with pytest.raises(ValueError, match="meeting_date"):
        normalize.normalize_diet_schedule_page(
            record,
            raw_html,
            raw_artifact_id="raw-artifact-house-unstable-1",
        )

    coverage = connector.coverage_record_for_parse_failure(
        checked_at=FETCHED_AT,
        error="diet schedule page meeting_date is required",
    )

    assert coverage.coverage_status == "manual_review_required"
    assert coverage.last_error == "parser_failure: diet schedule page meeting_date is required"
