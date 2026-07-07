import json

import ingest
import normalize


def test_p0r008_fixture_probe_builds_budget_and_procurement_raw_artifacts() -> None:
    fixture = ingest.build_p0r008_procurement_budget_fixture()

    assert len(fixture.budget_records) == 10
    assert len(fixture.procurement_records) == 10
    assert len(fixture.records) == 20

    for record in fixture.budget_records:
        assert record.connector.connector_id == "jp_tokyo.budget_settlement.v1"
        assert record.connector.source_family.source_family == "tokyo_budget_settlement"
        assert record.source_document_candidate.source_type == "budget_or_settlement_document"
        assert record.raw_artifact_path.startswith("raw/jp-tokyo/tokyo_budget_settlement/")
        assert record.raw_artifact_path.endswith(".html")
        assert record.raw_artifact_path == record.source_document_candidate.raw_artifact_path
        assert record.canonical_url == record.source_document_candidate.canonical_url
        assert record.content_hash

    for record in fixture.procurement_records:
        assert record.connector.connector_id == "jp_tokyo.procurement.v1"
        assert record.connector.source_family.source_family == "tokyo_procurement"
        assert record.source_document_candidate.source_type == (
            "procurement_search_result_or_bid_result"
        )
        assert record.raw_artifact_path.startswith("raw/jp-tokyo/tokyo_procurement/")
        assert record.raw_artifact_path.endswith(".html")
        assert record.raw_artifact_path == record.source_document_candidate.raw_artifact_path
        assert record.canonical_url == record.source_document_candidate.canonical_url
        assert record.content_hash

    ingest.validate_normal_test_fixture_metadata(fixture.fixture_metadata)


def test_p0r008_fixture_probe_normalizes_observed_claims_with_warnings() -> None:
    fixture = ingest.build_p0r008_procurement_budget_fixture()

    results = normalize.normalize_p0r008_procurement_budget_fixture(fixture.records)

    budget_results = [
        result
        for result in results
        if result.source_document.source_family == "tokyo_budget_settlement"
    ]
    procurement_results = [
        result for result in results if result.source_document.source_family == "tokyo_procurement"
    ]
    assert len(budget_results) == 10
    assert len(procurement_results) == 10

    evidence_items = [item for result in results for item in result.evidence_items]
    evidence_claims = [claim for result in results for claim in result.evidence_claims]
    assert len(evidence_items) == 20
    assert len(evidence_claims) == 20
    assert {claim.claim_type for claim in evidence_claims if "budget" in claim.claim_type} == {
        "budget_document_metadata_observed",
        "budget_table_cell_observed",
    }
    assert {claim.claim_type for claim in evidence_claims if "procurement" in claim.claim_type} == {
        "procurement_search_row_observed"
    }

    budget_table_items = [item for item in evidence_items if item.location_type == "table_cell"]
    assert budget_table_items
    for item in budget_table_items:
        assert "amount_unit_ambiguous" in item.parse_warnings
        assert "table_structure_inferred" in item.parse_warnings
        assert item.location_metadata["unit_note"] == "fixture states 金額単位 but not normalized"

    procurement_items = [
        item for item in evidence_items if item.extraction_method == "search_ui_snapshot"
    ]
    assert len(procurement_items) == 10
    for item in procurement_items:
        assert item.parse_warnings == (
            "search_ui_snapshot",
            "amount_unit_ambiguous",
            "entity_resolution_required",
        )
        assert item.location_metadata["search_form_url"].startswith(
            "https://www.e-procurement.metro.tokyo.lg.jp/"
        )
        assert item.location_metadata["query_parameters"] == {
            "keyword": "委託",
            "status": "結果公表",
        }
        assert normalize.can_promote_to_evidence_claim(item)

    json.dumps([result.to_json_dict() for result in results], ensure_ascii=False)


def test_p0r008_probe_summarizes_fixture_coverage_without_external_operations() -> None:
    fixture = ingest.build_p0r008_procurement_budget_fixture()
    results = normalize.normalize_p0r008_procurement_budget_fixture(fixture.records)

    budget_summary = ingest.build_fixture_coverage_sample(
        source_family="tokyo_budget_settlement",
        raw_artifacts=fixture.budget_records,
        source_document_candidates=[
            record.source_document_candidate for record in fixture.budget_records
        ],
        evidence_items=[
            item
            for result in results
            if result.source_document.source_family == "tokyo_budget_settlement"
            for item in result.evidence_items
        ],
    )
    procurement_summary = ingest.build_fixture_coverage_sample(
        source_family="tokyo_procurement",
        raw_artifacts=fixture.procurement_records,
        source_document_candidates=[
            record.source_document_candidate for record in fixture.procurement_records
        ],
        evidence_items=[
            item
            for result in results
            if result.source_document.source_family == "tokyo_procurement"
            for item in result.evidence_items
        ],
    )

    summaries = ingest.summarize_phase0_fixture_coverage([budget_summary, procurement_summary])

    assert summaries["tokyo_budget_settlement"].meets_target
    assert summaries["tokyo_budget_settlement"].raw_artifact_count == 10
    assert summaries["tokyo_budget_settlement"].source_document_candidate_count == 10
    assert summaries["tokyo_budget_settlement"].evidence_item_count == 10
    assert summaries["tokyo_budget_settlement"].warning_count >= 10
    assert summaries["tokyo_procurement"].meets_target
    assert summaries["tokyo_procurement"].raw_artifact_count == 10
    assert summaries["tokyo_procurement"].source_document_candidate_count == 10
    assert summaries["tokyo_procurement"].evidence_item_count == 10
    assert summaries["tokyo_procurement"].warning_count == 30


def test_p0r008_probe_keeps_budget_line_contract_award_and_money_flow_as_non_goals() -> None:
    guard = normalize.p0r008_procurement_budget_non_goal_guard()

    assert guard["blocked_entity_types"] == [
        "BudgetLine",
        "ContractAward",
        "PublicMoneyFlow",
        "SpendingReviewSignal",
    ]
    assert guard["blocked_confirmations"] == [
        "amount_normalization_confirmation",
        "tax_included_or_excluded_confirmation",
        "vendor_entity_resolution",
        "contract_proposal_match_confirmation",
    ]

    fixture = ingest.build_p0r008_procurement_budget_fixture()
    results = normalize.normalize_p0r008_procurement_budget_fixture(fixture.records)
    payload = json.dumps([result.to_json_dict() for result in results], ensure_ascii=False)

    assert "BudgetLine" not in payload
    assert "ContractAward" not in payload
    assert "PublicMoneyFlow" not in payload
    assert "SpendingReviewSignal" not in payload
    assert all(claim.object_ref is None for result in results for claim in result.evidence_claims)
    assert all(claim.amount is None for result in results for claim in result.evidence_claims)
    assert all(claim.currency is None for result in results for claim in result.evidence_claims)
