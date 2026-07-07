import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from ingest.filesystem import FileSystemOutputWriter
from ingest.storage_smoke import StorageSmokeError, run_storage_smoke
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
