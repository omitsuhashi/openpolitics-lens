import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ingest import (
    ConnectorDefinition,
    DiscoveryRecord,
    FetchManifestRecord,
    FileSystemOutputWriter,
    JurisdictionProfile,
    MissingSourceCoverageError,
    SourceCoverageRecord,
    SourceDocumentCandidate,
    SourceFamily,
    SourceRegistryRecord,
    connector_execution_targets,
    validate_required_coverage_records,
)


def _diet_schedule_registry_record() -> SourceRegistryRecord:
    return SourceRegistryRecord(
        jurisdiction_id="jp",
        jurisdiction_level="country",
        country_code="JP",
        subdivision_code=None,
        municipality_code=None,
        source_system="house_of_representatives",
        source_family="jp_diet_schedule",
        connector_id="jp.diet_schedule.v1",
        officiality_level="official_primary",
        operator_name="衆議院",
        entrypoint_url="https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/",
        retrieval_method="static_html_index",
        coverage_scope="diet_meeting_schedule",
        coverage_status="source_identified",
        rate_limit_policy="fixture only until live acquisition gate approval",
        terms_note="official website public pages",
        last_verified_at=datetime(2026, 7, 7, 9, 0, tzinfo=UTC),
        connector_status="planned",
    )


def _coverage_record_for(registry: SourceRegistryRecord) -> SourceCoverageRecord:
    return SourceCoverageRecord(
        jurisdiction_id=registry.jurisdiction_id,
        jurisdiction_level=registry.jurisdiction_level,
        source_system=registry.source_system,
        source_family=registry.source_family,
        connector_id=registry.connector_id,
        retrieval_method=registry.retrieval_method,
        coverage_scope=registry.coverage_scope,
        coverage_status=registry.coverage_status,
        entrypoint_url=registry.entrypoint_url,
        last_checked_at=datetime(2026, 7, 7, 9, 5, tzinfo=UTC),
        last_successful_fetch_at=None,
        last_verified_at=registry.last_verified_at,
        last_error=None,
        terms_note=registry.terms_note,
        manual_notes="公式入口は特定済み。fixture connector は後続 issue。",
        next_action="G2PR-012 で fixture connector を追加する",
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


def test_source_registry_and_coverage_records_round_trip_json_contract() -> None:
    registry = _diet_schedule_registry_record()
    coverage = _coverage_record_for(registry)

    registry_json = registry.to_json_dict()
    coverage_json = coverage.to_json_dict()

    registry_jsonl_line = json.dumps(registry_json, ensure_ascii=False)
    coverage_jsonl_line = json.dumps(coverage_json, ensure_ascii=False)

    assert registry_json["officiality_level"] == "official_primary"
    assert registry_json["coverage_status"] == "source_identified"
    assert registry_json["last_verified_at"] == "2026-07-07T09:00:00Z"
    assert coverage_json["source_system"] == "house_of_representatives"
    assert coverage_json["connector_id"] == "jp.diet_schedule.v1"
    assert coverage_json["coverage_status"] == "source_identified"
    assert coverage_json["last_verified_at"] == "2026-07-07T09:00:00Z"
    assert coverage_json["last_successful_fetch_at"] is None
    assert SourceRegistryRecord.from_json_dict(registry_json) == registry
    assert SourceCoverageRecord.from_json_dict(coverage_json) == coverage
    assert SourceRegistryRecord.from_json_dict(json.loads(registry_jsonl_line)) == registry
    assert SourceCoverageRecord.from_json_dict(json.loads(coverage_jsonl_line)) == coverage


def test_source_registry_and_coverage_records_reject_unknown_contract_values() -> None:
    registry_json = _diet_schedule_registry_record().to_json_dict()
    coverage_json = _coverage_record_for(_diet_schedule_registry_record()).to_json_dict()

    with pytest.raises(ValueError, match="officiality_level"):
        SourceRegistryRecord.from_json_dict(
            {**registry_json, "officiality_level": "non_official_primary"}
        )

    with pytest.raises(ValueError, match="coverage_status"):
        SourceCoverageRecord.from_json_dict({**coverage_json, "coverage_status": "complete"})


def test_source_registry_and_coverage_records_require_contract_fields() -> None:
    registry_json = _diet_schedule_registry_record().to_json_dict()
    coverage_json = _coverage_record_for(_diet_schedule_registry_record()).to_json_dict()
    del registry_json["connector_id"]
    del coverage_json["last_checked_at"]

    with pytest.raises(ValueError, match="connector_id"):
        SourceRegistryRecord.from_json_dict(registry_json)

    with pytest.raises(ValueError, match="last_checked_at"):
        SourceCoverageRecord.from_json_dict(coverage_json)


def test_election_and_meeting_source_families_require_coverage_records() -> None:
    registry = _diet_schedule_registry_record()

    with pytest.raises(MissingSourceCoverageError, match="jp.diet_schedule.v1"):
        validate_required_coverage_records((registry,), ())

    validate_required_coverage_records((registry,), (_coverage_record_for(registry),))


def test_coverage_records_do_not_satisfy_different_source_system_or_connector() -> None:
    house_registry = _diet_schedule_registry_record()
    council_registry = replace(
        house_registry,
        source_system="house_of_councillors",
        connector_id="jp.diet_schedule.councillors.v1",
        operator_name="参議院",
    )
    house_coverage = SourceCoverageRecord(
        jurisdiction_id=house_registry.jurisdiction_id,
        jurisdiction_level=house_registry.jurisdiction_level,
        source_system=house_registry.source_system,
        source_family=house_registry.source_family,
        connector_id=house_registry.connector_id,
        retrieval_method=house_registry.retrieval_method,
        coverage_scope=house_registry.coverage_scope,
        coverage_status=house_registry.coverage_status,
        entrypoint_url=house_registry.entrypoint_url,
        last_checked_at=datetime(2026, 7, 7, 9, 5, tzinfo=UTC),
        last_successful_fetch_at=None,
        last_verified_at=house_registry.last_verified_at,
        last_error=None,
        terms_note=house_registry.terms_note,
        manual_notes="衆議院側の入口だけを確認済み",
        next_action="参議院側の coverage record は別途必要",
    )

    validate_required_coverage_records((house_registry,), (house_coverage,))
    with pytest.raises(MissingSourceCoverageError, match="jp.diet_schedule.councillors.v1"):
        validate_required_coverage_records((house_registry, council_registry), (house_coverage,))


def test_non_official_reference_cannot_be_supported_connector_source() -> None:
    with pytest.raises(ValueError, match="non_official_reference"):
        replace(
            _diet_schedule_registry_record(),
            officiality_level="non_official_reference",
            coverage_status="supported",
        )


def test_blocked_by_terms_sources_are_not_connector_execution_targets() -> None:
    supported = replace(
        _diet_schedule_registry_record(),
        coverage_status="supported",
        connector_status="fixture_ready",
    )
    blocked = replace(
        _diet_schedule_registry_record(),
        connector_id="jp.diet_schedule.blocked.v1",
        coverage_status="blocked_by_terms",
        connector_status="blocked",
        terms_note="利用条件上、自動取得対象から外す",
    )

    assert connector_execution_targets((supported, blocked)) == (supported,)


def test_coverage_blocked_by_terms_sources_are_not_connector_execution_targets() -> None:
    registry = replace(
        _diet_schedule_registry_record(),
        coverage_status="supported",
        connector_status="fixture_ready",
    )
    coverage = replace(_coverage_record_for(registry), coverage_status="blocked_by_terms")

    assert connector_execution_targets((registry,), (coverage,)) == ()


def test_source_registry_and_coverage_records_reject_naive_datetimes() -> None:
    registry = _diet_schedule_registry_record()

    with pytest.raises(ValueError, match="last_verified_at"):
        replace(registry, last_verified_at=datetime(2026, 7, 7, 9, 0))

    with pytest.raises(ValueError, match="last_checked_at"):
        replace(_coverage_record_for(registry), last_checked_at=datetime(2026, 7, 7, 9, 5))

    with pytest.raises(ValueError, match="last_successful_fetch_at"):
        replace(
            _coverage_record_for(registry),
            coverage_status="supported",
            last_successful_fetch_at=datetime(2026, 7, 7, 9, 10),
        )


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


def test_filesystem_writer_builds_manifest_jsonl_paths(tmp_path: Path) -> None:
    writer = FileSystemOutputWriter(tmp_path)

    assert writer.manifest_relative_path(run_id="run-20260705", name="discovered") == Path(
        "manifests/run-20260705/discovered.jsonl"
    )
    assert writer.manifest_relative_path(run_id="run-20260705", name="fetched.jsonl") == Path(
        "manifests/run-20260705/fetched.jsonl"
    )


def test_filesystem_writer_appends_manifest_records_as_utf8_json_lines(
    tmp_path: Path,
) -> None:
    writer = FileSystemOutputWriter(tmp_path)
    profile = JurisdictionProfile(
        jurisdiction_id="jp-tokyo",
        jurisdiction_level="prefecture",
        country_code="JP",
        subdivision_code="JP-13",
        municipality_code=None,
        display_name="東京都",
    )
    discovered_record = {"canonical_url": "https://example.test/grants", "title": "東京都助成"}

    relative_path = writer.append_jsonl(
        run_id="run-20260705",
        name="discovered",
        record=discovered_record,
    )
    writer.append_jsonl(
        run_id="run-20260705",
        name="discovered",
        record=profile,
    )

    manifest_path = tmp_path / "manifests/run-20260705/discovered.jsonl"
    manifest_bytes = manifest_path.read_bytes()
    manifest_text = manifest_bytes.decode("utf-8")
    lines = manifest_text.splitlines()

    assert relative_path == Path("manifests/run-20260705/discovered.jsonl")
    assert manifest_bytes.endswith(b"\n")
    assert "東京都" in manifest_text
    assert "\\u6771" not in manifest_text
    assert len(lines) == 2
    assert json.loads(lines[0]) == discovered_record
    assert json.loads(lines[1]) == profile.to_json_dict()


def test_generated_ingest_output_is_gitignored() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    gitignore = repo_root / ".gitignore"

    assert "services/ingest/out/" in gitignore.read_text()
