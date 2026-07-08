import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from ingest.filesystem import FileSystemOutputWriter
from ingest.ndl_diet_minutes import FakeNdlDietMinutesFetcher, NdlDietMinutesConnector
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

    ndl_minutes = subcommands.add_parser(
        "ndl-diet-minutes",
        help="run National Diet Library Diet minutes ingest",
    )
    ndl_minutes_subcommands = ndl_minutes.add_subparsers(
        dest="ndl_diet_minutes_command",
        required=True,
    )

    ndl_fixture = ndl_minutes_subcommands.add_parser(
        "fixture",
        help="run deterministic fixture ingest for Diet minutes JSON/XML fixtures",
    )
    ndl_fixture.add_argument(
        "--search-json",
        type=Path,
        required=True,
        help="search response JSON fixture used for discovery",
    )
    ndl_fixture.add_argument(
        "--meeting-json",
        type=Path,
        required=True,
        help="meeting record JSON fixture fetched for meeting candidates",
    )
    ndl_fixture.add_argument(
        "--speech-xml",
        type=Path,
        required=True,
        help="speech record XML fixture fetched for speech candidates",
    )
    _add_ndl_diet_minutes_common_args(ndl_fixture)
    ndl_fixture.set_defaults(handler=_run_ndl_diet_minutes_fixture)

    ndl_run = ndl_minutes_subcommands.add_parser(
        "run",
        help="run daily live ingest once Diet minutes live fetching is implemented",
    )
    _add_ndl_diet_minutes_common_args(ndl_run)
    ndl_run.add_argument(
        "--dry-run",
        action="store_true",
        help="future live-run rehearsal mode; no durable write beyond planned temp output",
    )
    ndl_run.set_defaults(handler=_run_ndl_diet_minutes_run)
    return parser


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


def _add_ndl_diet_minutes_common_args(parser: argparse.ArgumentParser) -> None:
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


def _run_ndl_diet_minutes_fixture(args: argparse.Namespace) -> int:
    try:
        search_json = args.search_json.read_text(encoding="utf-8")
        meeting_json = args.meeting_json.read_bytes()
        speech_xml = args.speech_xml.read_bytes()
    except OSError as exc:
        print(f"failed to read Diet minutes fixture: {exc}", file=sys.stderr)
        return 2

    now = datetime.now(tz=UTC)
    discovered_at = _parse_datetime(args.discovered_at) if args.discovered_at else now
    fetched_at = _parse_datetime(args.fetched_at) if args.fetched_at else discovered_at

    connector = NdlDietMinutesConnector()
    writer = FileSystemOutputWriter(args.output_dir)
    discovered = connector.discover_from_search_json(
        search_json,
        discovered_at=discovered_at,
        output_writer=writer,
        run_id=args.run_id,
    )
    fetcher = FakeNdlDietMinutesFetcher(
        {
            "https://kokkai.ndl.go.jp/api/meeting/100105254X00120240415_001": (
                meeting_json,
                "application/json; charset=utf-8",
            ),
            "https://kokkai.ndl.go.jp/api/speech/0001.xml": (
                speech_xml,
                "application/xml; charset=utf-8",
            ),
        }
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


def _run_ndl_diet_minutes_run(args: argparse.Namespace) -> int:
    print(
        "ndl-diet-minutes live ingest is not implemented yet; no network request was made. "
        "Use `ndl-diet-minutes fixture` for deterministic local verification.",
        file=sys.stderr,
    )
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
