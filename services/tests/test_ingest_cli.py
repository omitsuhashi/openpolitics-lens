import json
import subprocess
import sys
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tokyo_metro_grants_index.html"
NDL_SEARCH_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ndl_diet_minutes_search.json"
NDL_MEETING_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ndl_diet_minutes_meeting.json"
NDL_SPEECH_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ndl_diet_minutes_speech.xml"


def test_tokyo_metro_grants_fixture_cli_writes_manifests_and_raw_artifact(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "tokyo-metro-grants",
            "fixture",
            "--fixture-html",
            str(FIXTURE_PATH),
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "cli-fixture-run",
            "--discovered-at",
            "2026-07-05T09:00:00Z",
            "--fetched-at",
            "2026-07-05T09:01:00Z",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0, result.stderr

    discovered_path = tmp_path / "manifests" / "cli-fixture-run" / "discovered.jsonl"
    fetched_path = tmp_path / "manifests" / "cli-fixture-run" / "fetched.jsonl"
    discovered = [json.loads(line) for line in discovered_path.read_text().splitlines()]
    fetched = [json.loads(line) for line in fetched_path.read_text().splitlines()]

    assert [record["canonical_url"] for record in discovered] == [
        "https://www.fukushi.metro.tokyo.lg.jp/childcare/nursery-subsidy.html",
        "https://www.kodomoseisaku.metro.tokyo.lg.jp/kosodate/support.html",
        "https://www.metro.tokyo.lg.jp/education/support/private-school-subsidy.html",
    ]
    assert [record["canonical_url"] for record in fetched] == [
        record["canonical_url"] for record in discovered
    ]

    raw_paths = {record["raw_artifact_path"] for record in fetched}
    assert len(raw_paths) == 1
    raw_path = tmp_path / raw_paths.pop()
    assert raw_path.read_bytes() == FIXTURE_PATH.read_bytes()
    assert raw_path.parts[-6:-3] == ("raw", "jp-tokyo", "tokyo_metro_grants")
    assert all(record["source_document_candidate"] for record in fetched)


def test_tokyo_metro_grants_cli_rejects_removed_live_flag(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "tokyo-metro-grants",
            "--live",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "removed-live-run",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 2
    assert "--live" not in result.stdout


def test_tokyo_metro_grants_help_lists_fixture_and_run_without_live_flag() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "tokyo-metro-grants",
            "--help",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0
    assert "fixture" in result.stdout
    assert "run" in result.stdout
    assert "--live" not in result.stdout


def test_tokyo_metro_grants_run_is_reserved_for_future_live_ingest(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "tokyo-metro-grants",
            "run",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "daily-run",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 2
    assert "live ingest is not implemented yet" in result.stderr


def test_ndl_diet_minutes_fixture_cli_writes_json_and_xml_manifests(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "ndl-diet-minutes",
            "fixture",
            "--search-json",
            str(NDL_SEARCH_FIXTURE_PATH),
            "--meeting-json",
            str(NDL_MEETING_FIXTURE_PATH),
            "--speech-xml",
            str(NDL_SPEECH_FIXTURE_PATH),
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "ndl-cli-fixture-run",
            "--discovered-at",
            "2026-07-08T01:00:00Z",
            "--fetched-at",
            "2026-07-08T01:01:00Z",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0, result.stderr

    discovered_path = tmp_path / "manifests" / "ndl-cli-fixture-run" / "discovered.jsonl"
    fetched_path = tmp_path / "manifests" / "ndl-cli-fixture-run" / "fetched.jsonl"
    discovered = [json.loads(line) for line in discovered_path.read_text().splitlines()]
    fetched = [json.loads(line) for line in fetched_path.read_text().splitlines()]

    assert [record["candidate_type"] for record in discovered] == [
        "meeting_record_candidate",
        "speech_record_candidate",
    ]
    assert [record["source_document_candidate"]["source_type"] for record in fetched] == [
        "meeting_record",
        "speech_record",
    ]
    assert fetched[0]["source_document_candidate"]["metadata"]["publication_date"] == "2024-04-20"
    assert fetched[1]["source_document_candidate"]["metadata"]["speech_id"] == "0001"


def test_ndl_diet_minutes_run_is_reserved_for_future_live_ingest(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "ndl-diet-minutes",
            "run",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "ndl-daily-run",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 2
    assert "live ingest is not implemented yet" in result.stderr
