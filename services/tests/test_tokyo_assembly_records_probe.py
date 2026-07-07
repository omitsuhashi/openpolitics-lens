import json
from dataclasses import replace

import pytest

import ingest
import normalize


def test_assembly_records_probe_builds_ten_fixture_only_raw_artifacts_and_candidates() -> None:
    probe = ingest.build_tokyo_assembly_records_fixture_probe()

    assert len(probe.raw_artifacts) == 10
    assert len(probe.fetch_manifests) == 10
    assert len(probe.source_document_candidates) == 10
    assert len({artifact.raw_artifact_path for artifact in probe.raw_artifacts}) == 10
    assert len({record.canonical_url for record in probe.fetch_manifests}) == 10
    assert len({record.content_hash for record in probe.fetch_manifests}) == 10

    ingest.validate_normal_test_fixture_metadata([probe.fixture_metadata])
    assert probe.fixture_metadata.operations == ("local_fixture_read",)
    assert probe.fixture_metadata.source_family == "tokyo_assembly_records_bills"
    assert probe.fixture_metadata.expected_evidence_item_count == 10

    for record in probe.fetch_manifests:
        rows = ingest.build_fetch_manifest_db_rows(record, object_bucket="openpolitics-raw")
        assert rows.raw_artifact["source_family"] == "tokyo_assembly_records_bills"
        assert rows.raw_artifact["object_key"] == record.raw_artifact_path
        assert rows.raw_artifact["raw_artifact_path"] == record.raw_artifact_path
        assert rows.source_document_candidate["source_type"] == (
            "assembly_meeting_record_search_snapshot"
        )
        assert rows.source_document_candidate["raw_artifact_path"] == record.raw_artifact_path
        assert record.source_document_candidate.source_family == "tokyo_assembly_records_bills"


def test_assembly_records_normalizer_generates_ten_speech_items_and_direct_claims() -> None:
    probe = ingest.build_tokyo_assembly_records_fixture_probe()
    results = []

    for artifact, record in zip(probe.raw_artifacts, probe.fetch_manifests, strict=True):
        rows = ingest.build_fetch_manifest_db_rows(record, object_bucket="openpolitics-raw")
        results.append(
            normalize.normalize_assembly_records_search_snapshot(
                record,
                artifact.content,
                raw_artifact_id=str(rows.raw_artifact["raw_artifact_id"]),
            )
        )

    evidence_items = tuple(item for result in results for item in result.evidence_items)
    claims = tuple(claim for result in results for claim in result.evidence_claims)
    assert len(evidence_items) == 10
    assert len(claims) == 10

    coverage = ingest.summarize_phase0_fixture_coverage(
        [
            ingest.build_fixture_coverage_sample(
                source_family="tokyo_assembly_records_bills",
                raw_artifacts=probe.raw_artifacts,
                source_document_candidates=probe.source_document_candidates,
                evidence_items=evidence_items,
            )
        ]
    )["tokyo_assembly_records_bills"]
    assert coverage.raw_artifact_count == 10
    assert coverage.source_document_candidate_count == 10
    assert coverage.evidence_item_count == 10
    assert coverage.meets_target

    for result, artifact, record in zip(
        results,
        probe.raw_artifacts,
        probe.fetch_manifests,
        strict=True,
    ):
        assert result.source_document.raw_artifact_path == record.raw_artifact_path
        assert result.source_document.raw_artifact_path == artifact.raw_artifact_path
        assert result.source_document.source_family == "tokyo_assembly_records_bills"

        item = result.evidence_items[0]
        metadata = item.location_metadata
        assert item.raw_artifact_path == artifact.raw_artifact_path
        assert item.location_type == "api_record"
        assert item.extraction_method == "search_ui_snapshot"
        assert set(item.parse_warnings) == {"search_ui_snapshot", "meaning_not_interpreted"}
        assert metadata["search_form_url"] == probe.search_snapshot.search_form_url
        assert metadata["query_parameters"] == probe.search_snapshot.query_parameters
        assert metadata["target_period"] == probe.search_snapshot.target_period
        assert metadata["page_number"] == probe.search_snapshot.page_number
        assert metadata["sort_order"] == probe.search_snapshot.sort_order
        assert metadata["snapshot_timestamp"] == probe.search_snapshot.snapshot_timestamp_json
        assert metadata["result_row_locator"]
        assert metadata["meeting_id"]
        assert metadata["meeting_name"]
        assert metadata["meeting_date"]
        assert metadata["speaker_name"]
        assert metadata["speaker_role"]
        assert metadata["speech_block_id"]
        assert metadata["speech_block_locator"]

        claim = result.evidence_claims[0]
        assert claim.claim_type == "speech_text_observed"
        assert claim.predicate == "observed_speech_text"
        assert claim.object_value == item.normalized_text
        assert claim.object_ref is None
        assert claim.event_date is None
        assert claim.amount is None
        assert claim.currency is None

    assert {claim.claim_type for claim in claims} == {"speech_text_observed"}


def test_assembly_records_normalizer_does_not_generate_policy_stance_or_meaning_claims() -> None:
    probe = ingest.build_tokyo_assembly_records_fixture_probe()
    artifact = probe.raw_artifacts[0]
    record = probe.fetch_manifests[0]
    rows = ingest.build_fetch_manifest_db_rows(record, object_bucket="openpolitics-raw")
    raw_html_with_semantic_hint = artifact.content.replace(
        b"</body>",
        b'<aside data-policy-stance="support" data-meaning-classification="childcare">'
        b"fixture-only semantic hint that must be ignored"
        b"</aside></body>",
    )

    result = normalize.normalize_assembly_records_search_snapshot(
        record,
        raw_html_with_semantic_hint,
        raw_artifact_id=str(rows.raw_artifact["raw_artifact_id"]),
    )

    assert len(result.evidence_claims) == 1
    assert result.evidence_claims[0].claim_type == "speech_text_observed"
    serialized = json.dumps(result.to_json_dict(), ensure_ascii=False)
    assert "policy_stance" not in serialized
    assert "meaning_classification" not in serialized

    with pytest.raises(ValueError, match="unknown claim_type"):
        normalize.claim_catalog_entry(
            "assembly_policy_stance_observed",
            source_family="tokyo_assembly_records_bills",
        )


def test_assembly_records_probe_rejects_live_browser_ops_in_normal_tests() -> None:
    probe = ingest.build_tokyo_assembly_records_fixture_probe()
    assert "browser_automation" in ingest.NORMAL_TEST_FORBIDDEN_OPERATIONS
    assert "external_network" in ingest.NORMAL_TEST_FORBIDDEN_OPERATIONS
    assert "live_search" in ingest.NORMAL_TEST_FORBIDDEN_OPERATIONS

    unsafe_fixture = replace(
        probe.fixture_metadata,
        operations=(
            "local_fixture_read",
            "browser_automation",
            "external_network",
            "live_search",
        ),
    )

    with pytest.raises(ValueError, match="normal tests must not perform"):
        ingest.validate_normal_test_fixture_metadata([unsafe_fixture])
