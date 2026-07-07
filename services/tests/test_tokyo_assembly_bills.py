import json
from datetime import UTC, datetime
from pathlib import Path

import ingest
import normalize
from ingest.tokyo_assembly_bills import (
    TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES,
    build_tokyo_assembly_bill_decision_fixture_records,
)

FETCHED_AT = datetime(2026, 7, 7, 9, 0, tzinfo=UTC)


def _raw_artifact_id(record: ingest.FetchManifestRecord) -> str:
    rows = ingest.build_fetch_manifest_db_rows(record, object_bucket="ingest-raw")
    return str(rows.raw_artifact["raw_artifact_id"])


def test_tokyo_assembly_bill_decision_fixtures_write_10_raw_artifacts(
    tmp_path: Path,
) -> None:
    writer = ingest.FileSystemOutputWriter(tmp_path)

    records = build_tokyo_assembly_bill_decision_fixture_records(
        output_writer=writer,
        run_id="run-20260707-p0r-005",
        fetched_at=FETCHED_AT,
    )

    assert len(TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES) == 10
    assert len(records) == 10
    assert len({record.canonical_url for record in records}) == 10
    assert {
        (fixture.fiscal_year, fixture.regular_session)
        for fixture in TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES
    } == {
        (2024, "令和6年第1回定例会"),
        (2024, "令和6年第2回定例会"),
    }

    manifest_lines = (
        (tmp_path / "manifests/run-20260707-p0r-005/fetched.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert [json.loads(line) for line in manifest_lines] == [
        record.to_json_dict() for record in records
    ]

    for record, fixture in zip(
        records,
        TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES,
        strict=True,
    ):
        assert (tmp_path / record.raw_artifact_path).read_bytes()
        assert record.connector.connector_id == "jp_tokyo.assembly_records_bills.v1"
        assert record.source_document_candidate.to_json_dict() == {
            "canonical_url": fixture.source_url,
            "title": fixture.title,
            "source_type": "assembly_bill_decision",
            "jurisdiction_id": "jp-tokyo",
            "source_family": "tokyo_assembly_records_bills",
            "language": "ja",
            "retrieved_at": "2026-07-07T09:00:00Z",
            "raw_artifact_path": record.raw_artifact_path,
        }


def test_tokyo_assembly_bill_decisions_normalize_to_10_evidence_items(
    tmp_path: Path,
) -> None:
    writer = ingest.FileSystemOutputWriter(tmp_path)
    records = build_tokyo_assembly_bill_decision_fixture_records(
        output_writer=writer,
        run_id="run-20260707-p0r-005",
        fetched_at=FETCHED_AT,
    )

    results = tuple(
        normalize.normalize_assembly_bill_decision(
            record,
            (tmp_path / record.raw_artifact_path).read_bytes(),
            fixture,
            raw_artifact_id=_raw_artifact_id(record),
        )
        for record, fixture in zip(
            records,
            TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES,
            strict=True,
        )
    )

    evidence_items = tuple(item for result in results for item in result.evidence_items)
    evidence_claims = tuple(claim for result in results for claim in result.evidence_claims)

    assert len(evidence_items) == 10
    assert len(evidence_claims) == 10
    assert {claim.claim_type for claim in evidence_claims} == {"bill_decision_observed"}
    assert (
        normalize.claim_catalog_entry(
            "bill_decision_observed",
            source_family="tokyo_assembly_records_bills",
        ).predicate
        == "observed_bill_decision"
    )

    first_fixture = TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES[0]
    first_item = evidence_items[0]
    assert first_item.location_type == "html_selector"
    assert first_item.location_value == first_fixture.row_locator
    assert first_item.location_metadata == {
        "fiscal_year": 2024,
        "regular_session": "令和6年第1回定例会",
        "session_period": "2024-02-20/2024-03-28",
        "bill_number": "第1号議案",
        "subject": "東京都一般会計予算",
        "decision_result": "原案可決",
        "source_url": first_fixture.source_url,
        "row_locator": first_fixture.row_locator,
        "has_individual_vote_positions": False,
    }
    assert first_item.quote_text == first_fixture.evidence_quote_text
    assert first_item.normalized_text == first_fixture.evidence_quote_text
    assert first_item.source_span_end > first_item.source_span_start

    coverage_sample = ingest.build_fixture_coverage_sample(
        source_family="tokyo_assembly_records_bills",
        raw_artifacts=records,
        source_document_candidates=[record.source_document_candidate for record in records],
        evidence_items=evidence_items,
    )
    summary = ingest.summarize_phase0_fixture_coverage([coverage_sample])[
        "tokyo_assembly_records_bills"
    ]
    assert summary.meets_target
    json.dumps([result.to_json_dict() for result in results], ensure_ascii=False)


def test_bill_decision_fixtures_without_personal_votes_do_not_create_vote_positions() -> None:
    assert all(
        not fixture.has_individual_vote_positions
        for fixture in TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES
    )

    for fixture in TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES:
        assert normalize.build_vote_positions_from_bill_decision_fixture(fixture) == ()
