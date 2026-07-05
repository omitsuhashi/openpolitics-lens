import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from ingest import (
    ConnectorDefinition,
    DiscoveryRecord,
    FetchManifestRecord,
    FileSystemOutputWriter,
    JurisdictionProfile,
    SourceDocumentCandidate,
    SourceFamily,
)


def test_contract_records_serialize_with_connector_identity() -> None:
    profile = JurisdictionProfile(
        jurisdiction_id="jp-tokyo",
        jurisdiction_level="prefecture",
        country_code="JP",
        subdivision_code="JP-13",
        municipality_code=None,
        display_name="東京都",
    )
    source_family = SourceFamily(
        source_family="tokyo_metro_grants",
        source_system="tokyo_metropolitan_government",
        display_name="東京都助成・補助金",
    )
    connector = ConnectorDefinition(
        connector_id="jp_tokyo.metro_grants.v1",
        connector_version="2026-07-05",
        jurisdiction=profile,
        source_family=source_family,
        start_url="https://www.metro.tokyo.lg.jp/purpose/grant",
        rate_limit_policy="manual fixture only",
        terms_note="official website public pages",
    )

    discovered = DiscoveryRecord(
        connector=connector,
        canonical_url="https://www.metro.tokyo.lg.jp/example",
        discovered_at=datetime(2026, 7, 5, 9, 0, tzinfo=UTC),
        parent_url=connector.start_url,
        candidate_type="grant_program_page_candidate",
        title="子育て助成制度",
        matched_keywords=("子育て", "助成"),
        relevance_reason="教育・子育て keyword に一致",
    )
    candidate = SourceDocumentCandidate(
        canonical_url=discovered.canonical_url,
        title=discovered.title,
        source_type="grant_program_page",
        jurisdiction_id=profile.jurisdiction_id,
        source_family=source_family.source_family,
        language="ja",
        retrieved_at=datetime(2026, 7, 5, 9, 1, tzinfo=UTC),
        raw_artifact_path="raw/jp-tokyo/tokyo_metro_grants/2026/07/example.html",
    )
    fetched = FetchManifestRecord(
        connector=connector,
        canonical_url=candidate.canonical_url,
        fetched_at=candidate.retrieved_at,
        http_status=200,
        content_hash="a" * 64,
        media_type="text/html; charset=utf-8",
        byte_size=123,
        raw_artifact_path=candidate.raw_artifact_path,
        source_document_candidate=candidate,
    )

    discovery_record = discovered.to_json_dict()
    fetch_record = fetched.to_json_dict()

    json.dumps(discovery_record, ensure_ascii=False)
    json.dumps(fetch_record, ensure_ascii=False)

    for record in (discovery_record, fetch_record):
        assert record["jurisdiction_id"] == "jp-tokyo"
        assert record["source_system"] == "tokyo_metropolitan_government"
        assert record["source_family"] == "tokyo_metro_grants"
        assert record["connector_id"] == "jp_tokyo.metro_grants.v1"

    assert fetch_record["source_document_candidate"]["jurisdiction_id"] == "jp-tokyo"
    assert fetch_record["source_document_candidate"]["source_family"] == "tokyo_metro_grants"


def test_filesystem_writer_uses_stable_content_hash_and_partitioned_raw_path(
    tmp_path: Path,
) -> None:
    fetched_at = datetime(2026, 7, 5, 9, 1, tzinfo=UTC)
    content = b"<html><body>tokyo grants</body></html>"
    expected_hash = hashlib.sha256(content).hexdigest()
    writer = FileSystemOutputWriter(tmp_path)

    first = writer.write_raw_artifact(
        content=content,
        jurisdiction_id="jp-tokyo",
        source_family="tokyo_metro_grants",
        fetched_at=fetched_at,
        extension="html",
    )
    second = writer.write_raw_artifact(
        content=content,
        jurisdiction_id="jp-tokyo",
        source_family="tokyo_metro_grants",
        fetched_at=fetched_at,
        extension="html",
    )
    other_scope = writer.write_raw_artifact(
        content=content,
        jurisdiction_id="jp-yokohama",
        source_family="yokohama_city_council_minutes",
        fetched_at=fetched_at,
        extension="html",
    )

    expected_path = Path("raw/jp-tokyo/tokyo_metro_grants/2026/07") / f"{expected_hash}.html"
    assert first.content_hash == expected_hash
    assert first.relative_path == expected_path
    assert second.content_hash == expected_hash
    assert second.relative_path == expected_path
    assert first.absolute_path.read_bytes() == content
    assert other_scope.relative_path != expected_path
    assert other_scope.relative_path.parts[:3] == (
        "raw",
        "jp-yokohama",
        "yokohama_city_council_minutes",
    )


def test_generated_ingest_output_is_gitignored() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    gitignore = repo_root / ".gitignore"

    assert "services/ingest/out/" in gitignore.read_text()
