import json
from datetime import UTC, datetime
from pathlib import Path

from ingest import FileSystemOutputWriter
from ingest.tokyo_metro_grants import FakeTokyoMetroGrantsFetcher, TokyoMetroGrantsConnector

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tokyo_metro_grants_index.html"
DISCOVERED_AT = datetime(2026, 7, 5, 9, 0, tzinfo=UTC)
FETCHED_AT = datetime(2026, 7, 5, 9, 1, tzinfo=UTC)


def test_tokyo_metro_grants_discovers_deterministic_fixture_candidates(
    tmp_path: Path,
) -> None:
    connector = TokyoMetroGrantsConnector()
    writer = FileSystemOutputWriter(tmp_path)

    assert connector.definition.connector_id == "jp_tokyo.metro_grants.v1"
    assert connector.definition.jurisdiction.jurisdiction_id == "jp-tokyo"
    assert connector.definition.source_family.source_family == "tokyo_metro_grants"
    assert connector.config.allowed_hosts == (
        "www.metro.tokyo.lg.jp",
        "www.kyoiku.metro.tokyo.lg.jp",
        "www.kodomoseisaku.metro.tokyo.lg.jp",
        "www.fukushi.metro.tokyo.lg.jp",
    )
    assert connector.config.theme_keywords == (
        "教育",
        "子供",
        "子ども",
        "こども",
        "若者",
        "子育て",
        "学校",
        "保育",
    )

    records = connector.discover_from_html(
        FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
        output_writer=writer,
        run_id="run-20260705",
    )

    payloads = [record.to_json_dict() for record in records]
    assert [payload["canonical_url"] for payload in payloads] == [
        "https://www.fukushi.metro.tokyo.lg.jp/childcare/nursery-subsidy.html",
        "https://www.kodomoseisaku.metro.tokyo.lg.jp/kosodate/support.html",
        "https://www.metro.tokyo.lg.jp/education/support/private-school-subsidy.html",
    ]
    assert payloads[0]["matched_keywords"] == ["保育", "補助"]
    assert payloads[1]["matched_keywords"] == ["子育て", "補助"]
    assert payloads[2]["matched_keywords"] == ["学校", "助成"]

    for payload in payloads:
        assert payload["jurisdiction_id"] == "jp-tokyo"
        assert payload["source_family"] == "tokyo_metro_grants"
        assert payload["connector_id"] == "jp_tokyo.metro_grants.v1"
        assert payload["candidate_type"] == "grant_program_page_candidate"

    manifest_lines = (
        (tmp_path / "manifests/run-20260705/discovered.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert [json.loads(line) for line in manifest_lines] == payloads


def test_tokyo_metro_grants_fake_fetch_writes_raw_artifacts_and_fetch_manifest(
    tmp_path: Path,
) -> None:
    connector = TokyoMetroGrantsConnector()
    candidates = connector.discover_from_html(
        FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
    )
    fetcher = FakeTokyoMetroGrantsFetcher(
        {
            candidates[0].canonical_url: b"<html><body>nursery subsidy</body></html>",
            candidates[1].canonical_url: b"<html><body>child support subsidy</body></html>",
            candidates[2].canonical_url: b"<html><body>private school subsidy</body></html>",
        }
    )
    writer = FileSystemOutputWriter(tmp_path)

    records = connector.fetch_candidates(
        candidates,
        fetcher=fetcher,
        output_writer=writer,
        run_id="run-20260705",
        fetched_at=FETCHED_AT,
    )

    payloads = [record.to_json_dict() for record in records]
    assert len(payloads) == 3
    assert [payload["canonical_url"] for payload in payloads] == [
        candidate.canonical_url for candidate in candidates
    ]

    manifest_lines = (
        (tmp_path / "manifests/run-20260705/fetched.jsonl").read_text(encoding="utf-8").splitlines()
    )
    assert [json.loads(line) for line in manifest_lines] == payloads
    assert [payload["source_document_candidate"]["title"] for payload in payloads] == [
        candidate.title for candidate in candidates
    ]

    for payload, candidate in zip(payloads, candidates, strict=True):
        raw_path = tmp_path / payload["raw_artifact_path"]
        assert raw_path.read_bytes()
        assert payload["http_status"] == 200
        assert payload["media_type"] == "text/html; charset=utf-8"
        assert payload["source_document_candidate"] == {
            "canonical_url": payload["canonical_url"],
            "title": candidate.title,
            "source_type": "grant_program_page",
            "jurisdiction_id": "jp-tokyo",
            "source_family": "tokyo_metro_grants",
            "language": "ja",
            "retrieved_at": "2026-07-05T09:01:00Z",
            "raw_artifact_path": payload["raw_artifact_path"],
        }
