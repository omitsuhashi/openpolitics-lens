import json
from datetime import UTC, datetime
from pathlib import Path

import ingest
import normalize
from ingest.egov_public_comment import EgovPublicCommentConnector, FakeEgovPublicCommentFetcher

RSS_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "egov_public_comment_feed.xml"
CASE_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "egov_public_comment_case_495000123.json"
DISCOVERED_AT = datetime(2026, 7, 8, 10, 0, tzinfo=UTC)
FETCHED_AT = datetime(2026, 7, 8, 10, 5, tzinfo=UTC)
DETAIL_API_URL = (
    "https://public-comment.e-gov.go.jp/api/servlet/Public"
    "?CLASSNAME=PCM1040&id=495000123&detail_format=json"
)


def test_egov_public_comment_discovers_fixture_candidates_from_rss(tmp_path: Path) -> None:
    connector = EgovPublicCommentConnector()
    writer = ingest.FileSystemOutputWriter(tmp_path)

    records = connector.discover_from_rss(
        RSS_FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
        output_writer=writer,
        run_id="run-20260708",
    )

    payloads = [record.to_json_dict() for record in records]
    assert [payload["canonical_url"] for payload in payloads] == [
        "https://public-comment.e-gov.go.jp/servlet/Public?CLASSNAME=PCM1040&id=495000123",
        "https://public-comment.e-gov.go.jp/servlet/Public?CLASSNAME=PCM1040&id=495000124",
    ]
    assert payloads[0]["title"] == "行政手続デジタル化に関する意見募集"
    assert payloads[0]["candidate_type"] == "public_comment_case_candidate"
    assert payloads[0]["source_family"] == "jp_public_comment"
    assert payloads[0]["connector_id"] == "jp.egov_public_comment.v1"

    manifest_lines = (
        (tmp_path / "manifests/run-20260708/discovered.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert [json.loads(line) for line in manifest_lines] == payloads


def test_egov_public_comment_fetch_uses_json_detail_and_keeps_case_metadata(tmp_path: Path) -> None:
    connector = EgovPublicCommentConnector()
    discovery_records = connector.discover_from_rss(
        RSS_FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
    )
    fetcher = FakeEgovPublicCommentFetcher(
        {
            discovery_records[0].canonical_url: ingest.FakeEgovPublicCommentResponse(
                content=CASE_FIXTURE_PATH.read_bytes(),
                source_url=DETAIL_API_URL,
            ),
        }
    )
    writer = ingest.FileSystemOutputWriter(tmp_path)

    records = connector.fetch_candidates(
        (discovery_records[0],),
        fetcher=fetcher,
        output_writer=writer,
        run_id="run-20260708",
        fetched_at=FETCHED_AT,
    )

    payload = records[0].to_json_dict()
    assert payload["media_type"] == "application/json; charset=utf-8"
    assert payload["canonical_url"] == DETAIL_API_URL
    assert payload["source_document_candidate"] == {
        "canonical_url": DETAIL_API_URL,
        "title": "行政手続デジタル化に関する意見募集",
        "source_type": "public_comment_case",
        "jurisdiction_id": "jp",
        "source_family": "jp_public_comment",
        "language": "ja",
        "retrieved_at": "2026-07-08T10:05:00Z",
        "raw_artifact_path": payload["raw_artifact_path"],
        "metadata": {
            "case_id": "495000123",
            "operator_name": "デジタル庁",
            "public_page_url": discovery_records[0].canonical_url,
            "detail_api_url": DETAIL_API_URL,
            "comment_start_date": "2026-07-01",
            "comment_end_text": "2026年8月",
            "result_url": "https://public-comment.e-gov.go.jp/servlet/Public?CLASSNAME=PCM1040&id=495000123&Mode=1",
            "result_published_date": "2026-09-15",
        },
        "warnings": ["comment_end_date_is_month_precision"],
    }


def test_normalize_public_comment_case_emits_open_close_and_result_events(
    tmp_path: Path,
) -> None:
    connector = EgovPublicCommentConnector()
    discovery_record = connector.discover_from_rss(
        RSS_FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
    )[0]
    record = connector.fetch_candidates(
        (discovery_record,),
        fetcher=FakeEgovPublicCommentFetcher(
            {
                discovery_record.canonical_url: ingest.FakeEgovPublicCommentResponse(
                    content=CASE_FIXTURE_PATH.read_bytes(),
                    source_url=DETAIL_API_URL,
                )
            }
        ),
        output_writer=ingest.FileSystemOutputWriter(tmp_path),
        run_id="run-20260708-normalize",
        fetched_at=FETCHED_AT,
    )[0]
    raw_artifact_id = str(
        ingest.build_fetch_manifest_db_rows(record, object_bucket="ingest-raw").raw_artifact[
            "raw_artifact_id"
        ]
    )

    result = normalize.normalize_public_comment_case(
        record,
        CASE_FIXTURE_PATH.read_bytes(),
        raw_artifact_id=raw_artifact_id,
    )

    assert result.source_document.source_type == "public_comment_case"
    assert result.source_document.canonical_url == DETAIL_API_URL
    assert len(result.official_event_candidates) == 3
    assert [candidate.event_type for candidate in result.official_event_candidates] == [
        "public_comment_opened",
        "public_comment_closed",
        "public_comment_result_published",
    ]

    opened, closed, result_published = result.official_event_candidates
    assert opened.scheduled_date.isoformat() == "2026-07-01"
    assert opened.date_precision == "date"
    assert opened.office_or_body == "デジタル庁"
    assert opened.canonical_url == DETAIL_API_URL
    assert closed.scheduled_date.isoformat() == "2026-08-01"
    assert closed.date_precision == "month"
    assert "comment_end_date_is_month_precision" in closed.limitations
    assert closed.canonical_url == DETAIL_API_URL
    assert result_published.scheduled_date.isoformat() == "2026-09-15"
    assert result_published.event_status == "published"
    assert result_published.canonical_url == DETAIL_API_URL
