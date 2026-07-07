from datetime import UTC, datetime

import pytest

import ingest
import normalize
from ingest.phase0_sources import (
    NORMAL_TEST_FORBIDDEN_OPERATIONS,
    PHASE0_COVERAGE_TARGETS,
    PHASE0_FIXTURE_CATALOG,
    PHASE0_ROADMAP_SOURCE_LABELS,
    PHASE0_SOURCE_REGISTRY,
    REQUIRED_PHASE0_COMPLETION_SOURCE_FAMILIES,
    TOKYO_ELECTION_BULLETIN_METADATA_FIXTURES,
    TOKYO_ELECTION_RESULT_FIXTURES,
    FixtureCoverageSample,
    FixtureMetadata,
    build_fixture_coverage_sample,
    build_phase0_fixture_report,
    build_tokyo_election_fixture_manifest_records,
    render_phase0_feasibility_markdown,
    summarize_phase0_fixture_coverage,
    validate_normal_test_fixture_metadata,
)

EXPECTED_SOURCE_FAMILIES = {
    "tokyo_assembly_records_bills",
    "tokyo_elections",
    "tokyo_political_funds",
    "tokyo_budget_settlement",
    "tokyo_procurement",
    "tokyo_metro_grants",
    "tokyo_audit_reports",
}
EXPECTED_ROADMAP_SOURCE_LABELS = {
    "東京都議会 会議録・速記録",
    "東京都議会 提出議案と議決結果",
    "東京都選挙管理委員会 選挙公報・選挙結果",
    "東京都選挙管理委員会 政治資金収支報告書",
    "東京都財務局・電子調達 契約/予算",
    "都庁総合ホームページ 助成・補助金",
    "東京都監査事務局 財政援助団体等監査・包括外部監査",
}


def test_phase0_source_registry_lists_all_roadmap_source_families() -> None:
    assert set(PHASE0_SOURCE_REGISTRY) == EXPECTED_SOURCE_FAMILIES
    assert ingest.PHASE0_SOURCE_REGISTRY is PHASE0_SOURCE_REGISTRY
    assert set(PHASE0_ROADMAP_SOURCE_LABELS) == EXPECTED_ROADMAP_SOURCE_LABELS
    assert len(PHASE0_ROADMAP_SOURCE_LABELS) == 7

    assembly = PHASE0_SOURCE_REGISTRY["tokyo_assembly_records_bills"]
    assert assembly.connector.connector_id == "jp_tokyo.assembly_records_bills.v1"
    assert assembly.source_type == "meeting_record_or_bill_decision"
    assert assembly.retrieval_method == "static_html_index + html_detail + search_ui_snapshot"
    assert assembly.evidence_granularity == "meeting_speech_or_bill_decision"
    assert assembly.roadmap_source_labels == (
        "東京都議会 会議録・速記録",
        "東京都議会 提出議案と議決結果",
    )

    for source_family, entry in PHASE0_SOURCE_REGISTRY.items():
        payload = entry.to_json_dict()
        assert payload["jurisdiction_id"] == "jp-tokyo"
        assert payload["source_family"] == source_family
        assert payload["connector_id"].startswith("jp_tokyo.")
        assert payload["source_system"]
        assert payload["source_type"]
        assert payload["retrieval_method"]
        assert payload["terms_note"]
        assert payload["evidence_granularity"]
        assert payload["roadmap_source_labels"]


def test_phase0_fixture_catalog_declares_required_metadata_and_targets() -> None:
    assert set(PHASE0_FIXTURE_CATALOG) == EXPECTED_SOURCE_FAMILIES
    assert set(PHASE0_COVERAGE_TARGETS) == EXPECTED_SOURCE_FAMILIES

    for source_family, fixture in PHASE0_FIXTURE_CATALOG.items():
        payload = fixture.to_json_dict()
        assert payload["source_family"] == source_family
        assert payload["canonical_url"].startswith("https://")
        assert payload["fetched_at"].endswith("Z")
        assert payload["media_type"]
        assert payload["byte_size"] > 0
        assert len(payload["content_hash"]) == 64
        assert payload["expected_evidence_item_count"] >= 1
        assert payload["operations"] == ["local_fixture_read"]

        target = PHASE0_COVERAGE_TARGETS[source_family]
        assert target.raw_artifact_count == 10
        assert target.source_document_candidate_count == 10
        assert target.evidence_item_count == 10

    validate_normal_test_fixture_metadata(PHASE0_FIXTURE_CATALOG.values())


def test_fixture_harness_summarizes_counts_by_source_family() -> None:
    summaries = summarize_phase0_fixture_coverage(
        [
            FixtureCoverageSample(
                source_family="tokyo_metro_grants",
                raw_artifact_count=4,
                source_document_candidate_count=4,
                evidence_item_count=3,
            ),
            FixtureCoverageSample(
                source_family="tokyo_metro_grants",
                raw_artifact_count=6,
                source_document_candidate_count=6,
                evidence_item_count=7,
                warning_count=2,
            ),
            FixtureCoverageSample(
                source_family="tokyo_audit_reports",
                raw_artifact_count=10,
                source_document_candidate_count=10,
                evidence_item_count=12,
                review_required_count=5,
            ),
        ]
    )

    grants = summaries["tokyo_metro_grants"]
    assert grants.raw_artifact_count == 10
    assert grants.source_document_candidate_count == 10
    assert grants.evidence_item_count == 10
    assert grants.warning_count == 2
    assert grants.meets_target

    audit = summaries["tokyo_audit_reports"]
    assert audit.evidence_item_count == 12
    assert audit.review_required_count == 5
    assert audit.meets_target

    elections = summaries["tokyo_elections"]
    assert elections.raw_artifact_count == 0
    assert not elections.meets_target


def test_fixture_harness_builds_samples_from_generated_records() -> None:
    evidence_item = normalize.EvidenceItem(
        evidence_item_id="search-item",
        source_document_id="source-doc",
        location_type="api_record",
        location_value="row-1",
        source_span_start=0,
        source_span_end=10,
        quote_text="検索結果行",
        normalized_text="検索結果行",
        raw_artifact_path="raw/jp-tokyo/tokyo_procurement/2026/07/search.html",
        extraction_method="search_ui_snapshot",
        confidence=0.9,
        location_metadata={
            "search_form_url": "https://www.e-procurement.metro.tokyo.lg.jp/index.jsp",
            "query_parameters": {"keyword": "委託"},
            "page_number": 1,
            "sort_order": "published_at_desc",
            "snapshot_timestamp": "2026-07-07T00:00:00Z",
            "result_row_locator": "tr:nth-child(1)",
        },
        parse_warnings=("search_ui_snapshot",),
    )

    sample = build_fixture_coverage_sample(
        source_family="tokyo_procurement",
        raw_artifacts=[object(), object()],
        source_document_candidates=[object()],
        evidence_items=[evidence_item],
    )

    assert sample == FixtureCoverageSample(
        source_family="tokyo_procurement",
        raw_artifact_count=2,
        source_document_candidate_count=1,
        evidence_item_count=1,
        warning_count=1,
        review_required_count=0,
    )


def test_tokyo_election_fixtures_separate_results_and_bulletin_metadata() -> None:
    assert len(TOKYO_ELECTION_RESULT_FIXTURES) == 6
    assert len(TOKYO_ELECTION_BULLETIN_METADATA_FIXTURES) == 4
    assert {fixture.source_type for fixture in TOKYO_ELECTION_RESULT_FIXTURES} == {
        "election_result_html",
        "election_result_pdf",
    }
    assert {fixture.source_type for fixture in TOKYO_ELECTION_BULLETIN_METADATA_FIXTURES} == {
        "public_bulletin_metadata"
    }

    fixture_records = build_tokyo_election_fixture_manifest_records()
    assert len(fixture_records) == 10
    assert len({record.raw_artifact_path for record in fixture_records}) == 10
    candidate_paths = {
        record.source_document_candidate.raw_artifact_path for record in fixture_records
    }
    assert len(candidate_paths) == 10

    validate_normal_test_fixture_metadata(
        [
            *TOKYO_ELECTION_RESULT_FIXTURES,
            *TOKYO_ELECTION_BULLETIN_METADATA_FIXTURES,
        ]
    )

    sample = build_fixture_coverage_sample(
        source_family="tokyo_elections",
        raw_artifacts=fixture_records,
        source_document_candidates=[record.source_document_candidate for record in fixture_records],
        evidence_items=[object() for _record in fixture_records],
    )
    summaries = summarize_phase0_fixture_coverage([sample])
    assert summaries["tokyo_elections"].meets_target

    for record in fixture_records:
        assert record.connector is PHASE0_SOURCE_REGISTRY["tokyo_elections"].connector
        assert record.source_document_candidate.source_family == "tokyo_elections"
        assert record.source_document_candidate.retrieved_at == record.fetched_at
        assert record.canonical_url.startswith("https://www.senkyo.metro.tokyo.lg.jp/")
        assert record.raw_artifact_path.startswith("raw/jp-tokyo/tokyo_elections/2026/07/")


def test_fixture_harness_rejects_normal_test_operations_that_touch_external_systems() -> None:
    assert NORMAL_TEST_FORBIDDEN_OPERATIONS == frozenset(
        {
            "external_network",
            "browser_automation",
            "live_search",
            "pdf_download",
            "ocr_execution",
        }
    )
    unsafe_fixture = FixtureMetadata(
        fixture_id="unsafe-live-download",
        source_family="tokyo_political_funds",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/unsafe.pdf",
        fetched_at=datetime(2026, 7, 7, 0, 0, tzinfo=UTC),
        media_type="application/pdf",
        byte_size=123,
        content_hash="a" * 64,
        source_type="political_fund_report",
        expected_evidence_item_count=1,
        operations=("local_fixture_read", "pdf_download"),
    )

    with pytest.raises(ValueError, match="normal tests must not perform"):
        validate_normal_test_fixture_metadata([unsafe_fixture])


def test_phase0_fixture_report_explains_incomplete_coverage() -> None:
    summaries = summarize_phase0_fixture_coverage(
        [
            FixtureCoverageSample(
                source_family="tokyo_audit_reports",
                raw_artifact_count=10,
                source_document_candidate_count=10,
                evidence_item_count=12,
                warning_count=4,
                review_required_count=1,
            ),
            FixtureCoverageSample(
                source_family="tokyo_metro_grants",
                raw_artifact_count=3,
                source_document_candidate_count=3,
                evidence_item_count=3,
            ),
        ]
    )

    report = build_phase0_fixture_report(summaries)
    payload = report.to_json_dict()
    rows_by_family = {row["source_family"]: row for row in payload["source_families"]}

    assert REQUIRED_PHASE0_COMPLETION_SOURCE_FAMILIES == frozenset(
        {"tokyo_metro_grants", "tokyo_audit_reports"}
    )
    assert payload["phase0_status"] == "incomplete"
    assert payload["achieved_source_family_count"] == 1
    assert payload["achieved_source_families"] == ["tokyo_audit_reports"]
    assert payload["coverage_source_family_goal_met"] is False
    assert payload["required_source_families_goal_met"] is False
    assert payload["missing_required_source_families"] == ["tokyo_metro_grants"]
    assert set(rows_by_family) == EXPECTED_SOURCE_FAMILIES

    audit = rows_by_family["tokyo_audit_reports"]
    assert audit["status"] == "complete"
    assert audit["raw_artifact_count"] == 10
    assert audit["source_document_candidate_count"] == 10
    assert audit["evidence_item_count"] == 12
    assert audit["warning_count"] == 4
    assert audit["review_required_count"] == 1
    assert audit["blocked_reason"] is None
    assert audit["non_goal_guard"]

    grants = rows_by_family["tokyo_metro_grants"]
    assert grants["status"] == "blocked"
    assert grants["raw_artifact_count"] == 3
    assert grants["evidence_item_count"] == 3
    assert "target not met" in grants["blocked_reason"]
    assert "RawArtifact 3/10" in grants["blocked_reason"]
    assert "PublicMoneyFlow" in " ".join(grants["non_goal_guard"])

    assembly = rows_by_family["tokyo_assembly_records_bills"]
    assert assembly["roadmap_source_labels"] == [
        "東京都議会 会議録・速記録",
        "東京都議会 提出議案と議決結果",
    ]
    assert "fixture probe not implemented" in assembly["blocked_reason"]


def test_phase0_feasibility_markdown_lists_all_roadmap_sources_and_guards() -> None:
    report = build_phase0_fixture_report(
        summarize_phase0_fixture_coverage(
            [
                FixtureCoverageSample(
                    source_family="tokyo_audit_reports",
                    raw_artifact_count=10,
                    source_document_candidate_count=10,
                    evidence_item_count=10,
                    warning_count=10,
                )
            ]
        )
    )

    markdown = render_phase0_feasibility_markdown(report)

    assert "Phase 0 判定: `incomplete`" in markdown
    assert (
        "通常検証では external network / browser automation / PDF download / OCR を実行しない"
        in markdown
    )
    for label in EXPECTED_ROADMAP_SOURCE_LABELS:
        assert label in markdown
    assert "| tokyo_audit_reports | complete | 10 | 10 | 10 | 10 | 0 |" in markdown
    assert "| tokyo_metro_grants | blocked | 0 | 0 | 0 | 0 | 0 |" in markdown
    assert "AuditFindingCandidate" in markdown
    assert "SpendingReviewSignal" in markdown
