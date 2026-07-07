import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import normalize
from ingest.filesystem import FileSystemOutputWriter
from ingest.persistence import build_fetch_manifest_db_rows
from ingest.phase0_sources import (
    NORMAL_TEST_FORBIDDEN_OPERATIONS,
    PHASE0_FEASIBILITY_REPORT_RELATIVE_PATH,
    PHASE0_FIXTURE_CATALOG,
    PHASE0_FIXTURE_REPORT_JSON_FILENAME,
    FixtureCoverageSample,
    build_fixture_coverage_sample,
    build_phase0_fixture_report,
    render_phase0_feasibility_markdown,
    summarize_phase0_fixture_coverage,
    validate_normal_test_fixture_metadata,
)
from ingest.storage_smoke import StorageSmokeError, run_storage_smoke
from ingest.tokyo_audit_reports import (
    FakeTokyoAuditReportsFetcher,
    TokyoAuditReportsConnector,
    build_audit_report_fixture_html,
)
from ingest.tokyo_metro_grants import FakeTokyoMetroGrantsFetcher, TokyoMetroGrantsConnector


def _parse_datetime(value: str) -> datetime:
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ingest")
    subcommands = parser.add_subparsers(dest="command", required=True)

    tokyo_grants = subcommands.add_parser(
        "tokyo-metro-grants",
        help="run Tokyo Metropolitan Government grants ingest",
    )
    tokyo_grants_subcommands = tokyo_grants.add_subparsers(
        dest="tokyo_metro_grants_command",
        required=True,
    )

    fixture = tokyo_grants_subcommands.add_parser(
        "fixture",
        help="run deterministic fixture ingest without external network",
    )
    fixture.add_argument(
        "--fixture-html",
        type=Path,
        required=True,
        help="local HTML fixture used for discovery and fake fetch content",
    )
    _add_tokyo_metro_grants_common_args(fixture)
    fixture.set_defaults(handler=_run_tokyo_metro_grants_fixture)

    run = tokyo_grants_subcommands.add_parser(
        "run",
        help="run daily live ingest once connector live fetching is implemented",
    )
    _add_tokyo_metro_grants_common_args(run)
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="future live-run rehearsal mode; no durable write beyond planned temp output",
    )
    run.set_defaults(handler=_run_tokyo_metro_grants_run)

    storage_smoke = subcommands.add_parser(
        "storage-smoke",
        help="put one RawArtifact to local MinIO and verify metadata plus DB payload",
    )
    storage_smoke.add_argument(
        "--bucket",
        default=_env_default("S3_BUCKET", default="openpolitics-raw"),
        help="S3-compatible bucket name; defaults to S3_BUCKET or openpolitics-raw",
    )
    storage_smoke.add_argument(
        "--endpoint",
        default=_env_default("S3_ENDPOINT", default="http://localhost:9000"),
        help=(
            "local MinIO endpoint; defaults to S3_ENDPOINT or http://localhost:9000. "
            "External endpoints are rejected before PUT."
        ),
    )
    storage_smoke.add_argument(
        "--access-key",
        default=_env_default("MINIO_ROOT_USER", default="openpolitics"),
        help="S3 access key; defaults to local development credentials",
    )
    storage_smoke.add_argument(
        "--secret-key",
        default=_env_default(
            "MINIO_ROOT_PASSWORD",
            default="openpolitics_minio_dev_password",
        ),
        help="S3 secret key; defaults to local development credentials",
    )
    storage_smoke.add_argument(
        "--region",
        default=_env_default("S3_REGION", default="ap-northeast-1"),
        help="S3 signing region; defaults to S3_REGION or ap-northeast-1",
    )
    storage_smoke.add_argument(
        "--timeout-seconds",
        type=float,
        default=2.0,
        help="HTTP timeout for local MinIO requests",
    )
    storage_smoke.add_argument(
        "--require-available",
        action="store_true",
        help="return non-zero when MinIO is not reachable instead of reporting skipped",
    )
    storage_smoke.set_defaults(handler=_run_storage_smoke)

    phase0 = subcommands.add_parser(
        "phase0",
        help="run Phase 0 fixture-only reporting commands",
    )
    phase0_subcommands = phase0.add_subparsers(dest="phase0_command", required=True)
    fixture_report = phase0_subcommands.add_parser(
        "fixture-report",
        help="build Phase 0 source-family coverage from local fixtures",
    )
    fixture_report.add_argument(
        "--fixtures",
        type=Path,
        required=True,
        help="local fixture directory; no network, browser automation, PDF download, or OCR",
    )
    fixture_report.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory where phase0-fixture-report.json and temporary fixture outputs are written",
    )
    fixture_report.add_argument(
        "--knowledge-report",
        type=Path,
        default=None,
        help=(
            "markdown report path; defaults to "
            f"{PHASE0_FEASIBILITY_REPORT_RELATIVE_PATH} from the repository root"
        ),
    )
    fixture_report.set_defaults(handler=_run_phase0_fixture_report)
    return parser


def _env_default(*names: str, default: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def _add_tokyo_metro_grants_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory where manifests/ and raw/ output are written",
    )
    parser.add_argument("--run-id", required=True, help="manifest run id path component")
    parser.add_argument(
        "--discovered-at",
        default=None,
        help="ISO-8601 timestamp for discovery records; defaults to current UTC time",
    )
    parser.add_argument(
        "--fetched-at",
        default=None,
        help="ISO-8601 timestamp for fetch records; defaults to discovered-at",
    )
    parser.add_argument(
        "--parent-url",
        default=None,
        help="parent URL used to resolve relative links; defaults to connector start URL",
    )


def _run_tokyo_metro_grants_fixture(args: argparse.Namespace) -> int:
    try:
        fixture_bytes = args.fixture_html.read_bytes()
        fixture_html = fixture_bytes.decode("utf-8")
    except OSError as exc:
        print(f"failed to read fixture HTML: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"fixture HTML must be UTF-8: {exc}", file=sys.stderr)
        return 2

    now = datetime.now(tz=UTC)
    discovered_at = _parse_datetime(args.discovered_at) if args.discovered_at else now
    fetched_at = _parse_datetime(args.fetched_at) if args.fetched_at else discovered_at

    connector = TokyoMetroGrantsConnector()
    writer = FileSystemOutputWriter(args.output_dir)
    discovered = connector.discover_from_html(
        fixture_html,
        discovered_at=discovered_at,
        output_writer=writer,
        run_id=args.run_id,
        parent_url=args.parent_url,
    )
    fetcher = FakeTokyoMetroGrantsFetcher(
        {record.canonical_url: fixture_bytes for record in discovered}
    )
    fetched = connector.fetch_candidates(
        discovered,
        fetcher=fetcher,
        output_writer=writer,
        run_id=args.run_id,
        fetched_at=fetched_at,
    )

    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "output_dir": str(args.output_dir),
                "discovered_count": len(discovered),
                "fetched_count": len(fetched),
            },
            ensure_ascii=False,
        )
    )
    return 0


def _run_tokyo_metro_grants_run(args: argparse.Namespace) -> int:
    print(
        "tokyo-metro-grants live ingest is not implemented yet; no network request was made. "
        "Use `tokyo-metro-grants fixture` for deterministic local verification.",
        file=sys.stderr,
    )
    return 2


def _run_storage_smoke(args: argparse.Namespace) -> int:
    try:
        result = run_storage_smoke(
            bucket=args.bucket,
            endpoint=args.endpoint,
            access_key=args.access_key,
            secret_key=args.secret_key,
            region=args.region,
            timeout_seconds=args.timeout_seconds,
            skip_if_unavailable=not args.require_available,
        )
    except StorageSmokeError as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "bucket": args.bucket,
                    "endpoint": args.endpoint,
                    "reason": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True))
    return 0


def _run_phase0_fixture_report(args: argparse.Namespace) -> int:
    try:
        validate_normal_test_fixture_metadata(PHASE0_FIXTURE_CATALOG.values())
        samples = _build_phase0_fixture_samples(
            fixtures_dir=args.fixtures,
            output_dir=args.output_dir,
        )
        report = build_phase0_fixture_report(summarize_phase0_fixture_coverage(samples))

        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_report_path = args.output_dir / PHASE0_FIXTURE_REPORT_JSON_FILENAME
        json_report_path.write_text(
            json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        markdown_report_path = args.knowledge_report or _default_phase0_knowledge_report_path()
        markdown_report_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_report_path.write_text(
            render_phase0_feasibility_markdown(report),
            encoding="utf-8",
        )
    except (OSError, UnicodeDecodeError, ValueError, KeyError) as exc:
        print(f"failed to build Phase 0 fixture report: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "phase0_status": report.phase0_status,
                "json_report_path": str(json_report_path),
                "markdown_report_path": str(markdown_report_path),
                "forbidden_operations_not_used": sorted(NORMAL_TEST_FORBIDDEN_OPERATIONS),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _build_phase0_fixture_samples(
    *,
    fixtures_dir: Path,
    output_dir: Path,
) -> tuple[FixtureCoverageSample, ...]:
    artifact_root = output_dir / "phase0-fixture-artifacts"
    return (
        _build_tokyo_metro_grants_fixture_sample(
            fixtures_dir=fixtures_dir,
            artifact_root=artifact_root / "tokyo_metro_grants",
        ),
        _build_tokyo_audit_reports_fixture_sample(
            fixtures_dir=fixtures_dir,
            artifact_root=artifact_root / "tokyo_audit_reports",
        ),
    )


def _build_tokyo_metro_grants_fixture_sample(
    *,
    fixtures_dir: Path,
    artifact_root: Path,
) -> FixtureCoverageSample:
    fixture_path = fixtures_dir / "tokyo_metro_grants_index.html"
    fixture_bytes = fixture_path.read_bytes()
    fixture_html = fixture_bytes.decode("utf-8")
    connector = TokyoMetroGrantsConnector()
    writer = FileSystemOutputWriter(artifact_root)
    run_id = "phase0-tokyo-metro-grants"
    discovered_at = datetime(2026, 7, 7, 0, 0, tzinfo=UTC)
    fetched_at = datetime(2026, 7, 7, 0, 1, tzinfo=UTC)

    discovered = connector.discover_from_html(
        fixture_html,
        discovered_at=discovered_at,
        output_writer=writer,
        run_id=run_id,
    )
    fetched = connector.fetch_candidates(
        discovered,
        fetcher=FakeTokyoMetroGrantsFetcher(
            {record.canonical_url: fixture_bytes for record in discovered}
        ),
        output_writer=writer,
        run_id=run_id,
        fetched_at=fetched_at,
    )
    return build_fixture_coverage_sample(
        source_family="tokyo_metro_grants",
        raw_artifacts=fetched,
        source_document_candidates=[record.source_document_candidate for record in fetched],
    )


def _build_tokyo_audit_reports_fixture_sample(
    *,
    fixtures_dir: Path,
    artifact_root: Path,
) -> FixtureCoverageSample:
    index_path = fixtures_dir / "tokyo_audit_reports_index.html"
    pages_path = fixtures_dir / "tokyo_audit_reports_pages.json"
    report_payloads = json.loads(pages_path.read_text(encoding="utf-8"))
    connector = TokyoAuditReportsConnector()
    writer = FileSystemOutputWriter(artifact_root)
    run_id = "phase0-tokyo-audit-reports"
    discovered_at = datetime(2026, 7, 7, 0, 0, tzinfo=UTC)
    fetched_at = datetime(2026, 7, 7, 0, 1, tzinfo=UTC)

    discovered = connector.discover_from_html(
        index_path.read_text(encoding="utf-8"),
        discovered_at=discovered_at,
        output_writer=writer,
        run_id=run_id,
    )
    response_map = _build_tokyo_audit_response_map(
        connector=connector,
        report_payloads=report_payloads,
    )
    fetched = connector.fetch_candidates(
        discovered,
        fetcher=FakeTokyoAuditReportsFetcher(response_map),
        output_writer=writer,
        run_id=run_id,
        fetched_at=fetched_at,
    )

    evidence_items = []
    review_required_count = 0
    for record in fetched:
        raw_artifact_id = str(
            build_fetch_manifest_db_rows(
                record,
                object_bucket="fixture-report",
            ).raw_artifact["raw_artifact_id"]
        )
        result = normalize.normalize_audit_report_fixture(
            record,
            (artifact_root / record.raw_artifact_path).read_bytes(),
            raw_artifact_id=raw_artifact_id,
        )
        evidence_items.extend(result.evidence_items)
        review_required_count += _review_required_count(result)

    sample = build_fixture_coverage_sample(
        source_family="tokyo_audit_reports",
        raw_artifacts=fetched,
        source_document_candidates=[record.source_document_candidate for record in fetched],
        evidence_items=evidence_items,
    )
    return FixtureCoverageSample(
        source_family=sample.source_family,
        raw_artifact_count=sample.raw_artifact_count,
        source_document_candidate_count=sample.source_document_candidate_count,
        evidence_item_count=sample.evidence_item_count,
        warning_count=sample.warning_count,
        review_required_count=review_required_count,
    )


def _build_tokyo_audit_response_map(
    *,
    connector: TokyoAuditReportsConnector,
    report_payloads: object,
) -> dict[str, bytes]:
    if not isinstance(report_payloads, list):
        msg = "tokyo_audit_reports_pages.json must contain a list"
        raise ValueError(msg)

    base_url = connector.definition.start_url.rstrip("/")
    response_map: dict[str, bytes] = {}
    for payload in report_payloads:
        if not isinstance(payload, dict):
            msg = "tokyo_audit_reports_pages.json entries must be objects"
            raise ValueError(msg)
        response_map[base_url + str(payload["path"])] = build_audit_report_fixture_html(
            title=str(payload["title"]),
            source_type=str(payload["source_type"]),
            fiscal_year=str(payload["fiscal_year"]),
            audited_entity=str(payload["audited_entity"]),
            finding_text=str(payload["finding_text"]),
            measure_status=str(payload["measure_status"]),
        )
    return response_map


def _review_required_count(result: normalize.NormalizeResult) -> int:
    review_required = 0
    review_objects = (
        *result.evidence_claims,
        *result.audit_finding_candidates,
        *result.spending_review_signal_candidates,
    )
    for review_object in review_objects:
        if getattr(review_object, "review_state", None) == "needs_human_review":
            review_required += 1
    return review_required


def _default_phase0_knowledge_report_path() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        knowledge_root = candidate / "knowledge" / "wiki" / "syntheses"
        if knowledge_root.is_dir():
            return candidate / PHASE0_FEASIBILITY_REPORT_RELATIVE_PATH

    return cwd / PHASE0_FEASIBILITY_REPORT_RELATIVE_PATH


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
