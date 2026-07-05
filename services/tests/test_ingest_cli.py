import json
import subprocess
import sys
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tokyo_metro_grants_index.html"


def test_tokyo_metro_grants_fixture_cli_writes_manifests_and_raw_artifact(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "tokyo-metro-grants",
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
