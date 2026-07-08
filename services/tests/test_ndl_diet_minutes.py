import json
from datetime import UTC, datetime
from pathlib import Path

import ingest
import normalize
from ingest import FileSystemOutputWriter
from ingest.ndl_diet_minutes import FakeNdlDietMinutesFetcher, NdlDietMinutesConnector

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SEARCH_FIXTURE_PATH = FIXTURE_DIR / "ndl_diet_minutes_search.json"
MEETING_FIXTURE_PATH = FIXTURE_DIR / "ndl_diet_minutes_meeting.json"
SPEECH_FIXTURE_PATH = FIXTURE_DIR / "ndl_diet_minutes_speech.xml"
DISCOVERED_AT = datetime(2026, 7, 8, 1, 0, tzinfo=UTC)
FETCHED_AT = datetime(2026, 7, 8, 1, 1, tzinfo=UTC)


def _fixture_fetcher() -> FakeNdlDietMinutesFetcher:
    return FakeNdlDietMinutesFetcher(
        {
            "https://kokkai.ndl.go.jp/api/meeting/100105254X00120240415_001": (
                MEETING_FIXTURE_PATH.read_bytes(),
                "application/json; charset=utf-8",
            ),
            "https://kokkai.ndl.go.jp/api/speech/0001.xml": (
                SPEECH_FIXTURE_PATH.read_bytes(),
                "application/xml; charset=utf-8",
            ),
        }
    )


def test_ndl_diet_minutes_fixture_connector_discovers_fetches_and_normalizes(
    tmp_path: Path,
) -> None:
    connector = NdlDietMinutesConnector()
    writer = FileSystemOutputWriter(tmp_path)

    discovered = connector.discover_from_search_json(
        SEARCH_FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
        output_writer=writer,
        run_id="run-20260708",
    )

    assert [record.candidate_type for record in discovered] == [
        "meeting_record_candidate",
        "speech_record_candidate",
    ]
    assert [record.canonical_url for record in discovered] == [
        "https://kokkai.ndl.go.jp/api/meeting/100105254X00120240415_001",
        "https://kokkai.ndl.go.jp/api/speech/0001.xml",
    ]
    assert discovered[0].metadata == {
        "record_id": "100105254X00120240415_001",
        "pagination": {
            "next_record_position": 2,
            "number_of_records": 1,
            "number_of_return": 1,
            "maximum_records": 10,
        },
        "request_params": {
            "sessionFrom": 217,
            "sessionTo": 217,
            "nameOfMeeting": "総務委員会",
        },
        "rate_limit": "1 request per second",
    }

    fetched = connector.fetch_candidates(
        discovered,
        fetcher=_fixture_fetcher(),
        output_writer=writer,
        run_id="run-20260708",
        fetched_at=FETCHED_AT,
    )

    assert [record.media_type for record in fetched] == [
        "application/json; charset=utf-8",
        "application/xml; charset=utf-8",
    ]
    assert fetched[0].source_document_candidate.metadata["record_id"] == "100105254X00120240415_001"
    assert fetched[0].source_document_candidate.metadata["meeting_date"] == "2024-04-15"
    assert fetched[0].source_document_candidate.metadata["publication_date"] == "2024-04-20"
    assert fetched[1].source_document_candidate.metadata["speech_id"] == "0001"

    meeting_rows = ingest.build_fetch_manifest_db_rows(fetched[0], object_bucket="ingest-raw")
    meeting_result = normalize.normalize_ndl_diet_minutes_record(
        fetched[0],
        MEETING_FIXTURE_PATH.read_bytes(),
        raw_artifact_id=str(meeting_rows.raw_artifact["raw_artifact_id"]),
    )
    speech_rows = ingest.build_fetch_manifest_db_rows(fetched[1], object_bucket="ingest-raw")
    speech_result = normalize.normalize_ndl_diet_minutes_record(
        fetched[1],
        SPEECH_FIXTURE_PATH.read_bytes(),
        raw_artifact_id=str(speech_rows.raw_artifact["raw_artifact_id"]),
    )

    assert meeting_result.source_document.source_type == "meeting_record"
    assert (
        meeting_result.source_document.canonical_url
        == "https://kokkai.ndl.go.jp/txt/100105254X00120240415/1"
    )
    assert [item.location_value for item in meeting_result.evidence_items] == [
        "/issueDate",
        "/meetingDate",
    ]
    assert [claim.claim_type for claim in meeting_result.evidence_claims] == [
        "meeting_record_publication_date_observed",
        "meeting_date_observed",
    ]
    assert len(meeting_result.event_candidates) == 1
    event_candidate = meeting_result.event_candidates[0]
    assert event_candidate.event_family == "Diet"
    assert event_candidate.event_type == "meeting_record_published"
    assert event_candidate.scheduled_date.isoformat() == "2024-04-20"
    assert event_candidate.event_status == "published"
    assert event_candidate.office_or_body == "衆議院 総務委員会"
    assert event_candidate.source_assertions[0].asserted_value == "2024-04-20"
    assert "meeting_date preserved separately" in event_candidate.limitations[0]

    assert speech_result.source_document.source_type == "speech_record"
    assert [item.location_value for item in speech_result.evidence_items] == [
        "/speechRecord/speaker"
    ]
    assert [claim.claim_type for claim in speech_result.evidence_claims] == [
        "speech_speaker_observed"
    ]
    assert speech_result.event_candidates == ()

    discovered_manifest = (tmp_path / "manifests" / "run-20260708" / "discovered.jsonl").read_text(
        encoding="utf-8"
    )
    fetched_manifest = (tmp_path / "manifests" / "run-20260708" / "fetched.jsonl").read_text(
        encoding="utf-8"
    )
    assert len(discovered_manifest.splitlines()) == 2
    assert len(fetched_manifest.splitlines()) == 2
    json.loads(discovered_manifest.splitlines()[0])
    json.loads(fetched_manifest.splitlines()[0])
