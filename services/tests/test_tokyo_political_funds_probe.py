import ingest
import normalize


def test_political_funds_probe_builds_ten_fixture_only_records_and_evidence() -> None:
    probe = ingest.build_tokyo_political_funds_fixture_probe()

    assert len(probe.raw_artifacts) == 10
    assert len(probe.source_document_candidates) == 10
    assert len(probe.evidence_items) == 10
    assert {fixture.source_type for fixture in ingest.PHASE0_POLITICAL_FUNDS_FIXTURES} == {
        "political_fund_report_index",
        "political_group_registry",
        "political_fund_report_pdf_sample",
    }
    ingest.validate_normal_test_fixture_metadata(ingest.PHASE0_POLITICAL_FUNDS_FIXTURES)

    coverage = ingest.build_fixture_coverage_sample(
        source_family="tokyo_political_funds",
        raw_artifacts=probe.raw_artifacts,
        source_document_candidates=probe.source_document_candidates,
        evidence_items=probe.evidence_items,
    )
    summary = ingest.summarize_phase0_fixture_coverage([coverage])["tokyo_political_funds"]

    assert summary.meets_target
    assert summary.warning_count >= 10
    assert coverage.review_required_count == probe.review_required_count
    assert summary.review_required_count == probe.review_required_count
    assert probe.review_required_count >= 6
    assert all(
        record.connector.connector_id == "jp_tokyo.political_funds.v1"
        for record in probe.raw_artifacts
    )
    assert all(
        record.source_document_candidate.source_family == "tokyo_political_funds"
        for record in probe.raw_artifacts
    )


def test_political_funds_probe_preserves_pdf_ocr_and_table_locator_risk() -> None:
    probe = ingest.build_tokyo_political_funds_fixture_probe()

    pdf_items = [
        item
        for item in probe.evidence_items
        if item.location_metadata["fixture_role"] == "political_fund_report_pdf_sample"
    ]
    assert pdf_items
    assert any(item.location_metadata["text_layer"] == "missing" for item in pdf_items)
    assert any(item.location_metadata["ocr_required"] is True for item in pdf_items)
    assert all("table_locator" in item.location_metadata for item in pdf_items)
    assert any("ocr_required" in item.parse_warnings for item in pdf_items)
    assert any("table_structure_inferred" in item.parse_warnings for item in pdf_items)

    review_items = [
        item for item in probe.evidence_items if item.location_metadata["review_required"]
    ]
    assert review_items
    assert all(item.confidence < 0.8 for item in review_items)
    assert all(
        {
            "amount_unit_ambiguous",
            "name_or_org_ocr_ambiguous",
            "entity_resolution_required",
        }
        & set(item.parse_warnings)
        for item in review_items
    )


def test_political_funds_probe_promotes_only_direct_observation_claims() -> None:
    probe = ingest.build_tokyo_political_funds_fixture_probe()

    claim_types = {claim.claim_type for claim in probe.evidence_claims}
    assert claim_types == {
        "political_group_registry_observed",
        "political_fund_report_metadata_observed",
    }
    assert all(claim.amount is None for claim in probe.evidence_claims)
    assert all(claim.currency is None for claim in probe.evidence_claims)
    assert all(claim.object_ref is None for claim in probe.evidence_claims)
    assert all(claim.review_state == "machine_extracted" for claim in probe.evidence_claims)

    for claim in probe.evidence_claims:
        item = probe.evidence_item_by_id[claim.evidence_item_id]
        assert normalize.can_promote_to_evidence_claim(item)
        assert item.location_metadata["direct_observation"] is True

    assert not any(
        claim.claim_type
        in {
            "funding_contact_observed",
            "public_money_flow_observed",
            "spending_review_signal_observed",
        }
        for claim in probe.evidence_claims
    )


def test_political_funds_probe_guards_funding_contact_generation() -> None:
    probe = ingest.build_tokyo_political_funds_fixture_probe()

    assert ingest.can_generate_funding_contact_from_political_funds_probe(probe) is False
    assert probe.non_goal_guards["FundingContact"] == "not_generated"
    assert probe.non_goal_guards["PublicMoneyFlow"] == "not_generated"
    assert probe.non_goal_guards["SpendingReviewSignal"] == "not_generated"
