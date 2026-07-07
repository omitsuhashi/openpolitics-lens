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


def test_ingest_help_lists_storage_smoke_command() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "--help",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0
    assert "storage-smoke" in result.stdout


def test_ingest_help_lists_phase0_fixture_report_command() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "--help",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0
    assert "phase0" in result.stdout


def test_phase0_fixture_report_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    knowledge_report = tmp_path / "phase0-source-probe-feasibility-report.md"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ingest",
            "phase0",
            "fixture-report",
            "--fixtures",
            "tests/fixtures",
            "--output-dir",
            str(tmp_path),
            "--knowledge-report",
            str(knowledge_report),
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 0, result.stderr

    stdout_payload = json.loads(result.stdout)
    report_path = tmp_path / "phase0-fixture-report.json"
    assert stdout_payload["phase0_status"] == "incomplete"
    assert stdout_payload["json_report_path"] == str(report_path)
    assert stdout_payload["markdown_report_path"] == str(knowledge_report)
    assert stdout_payload["forbidden_operations_not_used"] == [
        "browser_automation",
        "external_network",
        "ocr_execution",
        "pdf_download",
    ]

    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    rows_by_family = {row["source_family"]: row for row in report_payload["source_families"]}
    assert len(rows_by_family) == 7
    assert rows_by_family["tokyo_audit_reports"]["status"] == "complete"
    assert rows_by_family["tokyo_audit_reports"]["raw_artifact_count"] == 10
    assert rows_by_family["tokyo_audit_reports"]["evidence_item_count"] >= 10
    assert rows_by_family["tokyo_metro_grants"]["status"] == "blocked"
    assert rows_by_family["tokyo_metro_grants"]["raw_artifact_count"] == 3
    assert report_payload["phase0_status"] == "incomplete"

    markdown = knowledge_report.read_text(encoding="utf-8")
    assert "Phase 0 判定: `incomplete`" in markdown
    assert "東京都監査事務局 財政援助団体等監査・包括外部監査" in markdown
    assert "都庁総合ホームページ 助成・補助金" in markdown


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
