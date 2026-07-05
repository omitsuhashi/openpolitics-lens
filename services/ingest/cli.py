import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from ingest.filesystem import FileSystemOutputWriter
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
    tokyo_grants.add_argument(
        "--fixture-html",
        type=Path,
        help="local HTML fixture used for discovery and fake fetch content",
    )
    tokyo_grants.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory where manifests/ and raw/ output are written",
    )
    tokyo_grants.add_argument("--run-id", required=True, help="manifest run id path component")
    tokyo_grants.add_argument(
        "--discovered-at",
        default=None,
        help="ISO-8601 timestamp for discovery records; defaults to current UTC time",
    )
    tokyo_grants.add_argument(
        "--fetched-at",
        default=None,
        help="ISO-8601 timestamp for fetch records; defaults to discovered-at",
    )
    tokyo_grants.add_argument(
        "--parent-url",
        default=None,
        help="parent URL used to resolve relative links; defaults to connector start URL",
    )
    tokyo_grants.add_argument(
        "--live",
        action="store_true",
        help="explicit opt-in for future live fetch flow; fixture mode is the default",
    )
    tokyo_grants.set_defaults(handler=_run_tokyo_metro_grants)
    return parser


def _run_tokyo_metro_grants(args: argparse.Namespace) -> int:
    if args.live:
        print(
            "--live is an explicit opt-in for manual live fetch; this CLI run made no network "
            "request. Use fixture mode for reproducible ingest.",
            file=sys.stderr,
        )
        return 2

    if args.fixture_html is None:
        print("--fixture-html is required for fixture mode", file=sys.stderr)
        return 2

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


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
