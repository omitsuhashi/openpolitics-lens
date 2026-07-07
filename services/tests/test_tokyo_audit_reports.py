import json
from datetime import UTC, datetime
from pathlib import Path

import ingest
import normalize
from ingest import FileSystemOutputWriter
from ingest.tokyo_audit_reports import (
    AUDIT_REPORT_SOURCE_TYPES,
    FakeTokyoAuditReportsFetcher,
    TokyoAuditReportsConnector,
    build_audit_report_fixture_html,
)

INDEX_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tokyo_audit_reports_index.html"
REPORT_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "tokyo_audit_reports_pages.json"
DISCOVERED_AT = datetime(2026, 7, 7, 9, 0, tzinfo=UTC)
FETCHED_AT = datetime(2026, 7, 7, 9, 1, tzinfo=UTC)


def _report_fixture_payloads() -> list[dict[str, str]]:
    return json.loads(REPORT_FIXTURE_PATH.read_text(encoding="utf-8"))


def _fixture_response_map(connector: TokyoAuditReportsConnector) -> dict[str, bytes]:
    base_url = connector.definition.start_url
    return {
        base_url.rstrip("/") + payload["path"]: build_audit_report_fixture_html(
            title=payload["title"],
            source_type=payload["source_type"],
            fiscal_year=payload["fiscal_year"],
            audited_entity=payload["audited_entity"],
            finding_text=payload["finding_text"],
            measure_status=payload["measure_status"],
        )
        for payload in _report_fixture_payloads()
    }


def test_tokyo_audit_reports_discovers_source_types_and_fetches_fixture_artifacts(
    tmp_path: Path,
) -> None:
    connector = TokyoAuditReportsConnector()
    writer = FileSystemOutputWriter(tmp_path)

    records = connector.discover_from_html(
        INDEX_FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
        output_writer=writer,
        run_id="audit-run-20260707",
    )

    assert len(records) == 10
    assert {record.source_type for record in records} == AUDIT_REPORT_SOURCE_TYPES
    assert [record.source_type for record in records].count(
        "financial_aid_organization_audit_report"
    ) == 4
    assert [record.source_type for record in records].count(
        "comprehensive_external_audit_report"
    ) == 3
    assert [record.source_type for record in records].count("audit_measure_status_report") == 3
    assert all(record.operations == ("local_fixture_read",) for record in records)

    fetched_records = connector.fetch_candidates(
        records,
        fetcher=FakeTokyoAuditReportsFetcher(_fixture_response_map(connector)),
        output_writer=writer,
        run_id="audit-run-20260707",
        fetched_at=FETCHED_AT,
    )

    assert len(fetched_records) == 10
    assert [record.source_document_candidate.source_type for record in fetched_records] == [
        record.source_type for record in records
    ]
    assert {
        record.source_document_candidate.source_type for record in fetched_records
    } == AUDIT_REPORT_SOURCE_TYPES

    coverage_sample = ingest.build_fixture_coverage_sample(
        source_family="tokyo_audit_reports",
        raw_artifacts=[
            tmp_path / record.raw_artifact_path
            for record in fetched_records
            if (tmp_path / record.raw_artifact_path).exists()
        ],
        source_document_candidates=[record.source_document_candidate for record in fetched_records],
    )
    assert coverage_sample.raw_artifact_count == 10
    assert coverage_sample.source_document_candidate_count == 10
    assert coverage_sample.evidence_item_count == 0


def test_normalize_audit_report_fixture_preserves_official_wording_and_trace(
    tmp_path: Path,
) -> None:
    connector = TokyoAuditReportsConnector()
    writer = FileSystemOutputWriter(tmp_path)
    discovered_records = connector.discover_from_html(
        INDEX_FIXTURE_PATH.read_text(encoding="utf-8"),
        discovered_at=DISCOVERED_AT,
    )
    fetched_records = connector.fetch_candidates(
        discovered_records,
        fetcher=FakeTokyoAuditReportsFetcher(_fixture_response_map(connector)),
        output_writer=writer,
        run_id="audit-run-20260707",
        fetched_at=FETCHED_AT,
    )

    results = [
        normalize.normalize_audit_report_fixture(
            record,
            (tmp_path / record.raw_artifact_path).read_bytes(),
            raw_artifact_id=str(
                ingest.build_fetch_manifest_db_rows(
                    record,
                    object_bucket="ingest-raw",
                ).raw_artifact["raw_artifact_id"]
            ),
        )
        for record in fetched_records
    ]
    evidence_items = [item for result in results for item in result.evidence_items]
    audit_candidates = [
        candidate for result in results for candidate in result.audit_finding_candidates
    ]

    assert len(evidence_items) >= 10
    assert len(audit_candidates) >= 5
    assert all(candidate.source_type in AUDIT_REPORT_SOURCE_TYPES for candidate in audit_candidates)
    assert all(candidate.evidence_item_ids for candidate in audit_candidates)
    assert all(
        candidate.claim_type == normalize.AUDIT_FINDING_CANDIDATE_CLAIM_TYPE
        for candidate in audit_candidates
    )
    assert all(
        {
            "fiscal_year",
            "audited_entity",
            "finding_text",
            "measure_status",
        }.issubset(candidate.field_evidence_item_ids)
        for candidate in audit_candidates
    )

    first_payload = _report_fixture_payloads()[0]
    first_candidate = audit_candidates[0]
    assert first_candidate.fiscal_year == first_payload["fiscal_year"]
    assert first_candidate.audited_entity == first_payload["audited_entity"]
    assert first_candidate.finding_text == first_payload["finding_text"]
    assert first_candidate.measure_status == first_payload["measure_status"]

    first_finding_evidence_id = first_candidate.field_evidence_item_ids["finding_text"]
    first_finding_evidence = next(
        item for item in evidence_items if item.evidence_item_id == first_finding_evidence_id
    )
    assert first_finding_evidence.quote_text == first_payload["finding_text"]
    assert first_finding_evidence.normalized_text == first_payload["finding_text"]
    assert first_finding_evidence.location_metadata["field_name"] == "finding_text"
    assert first_finding_evidence.location_metadata["source_type"] == first_payload["source_type"]
    assert first_finding_evidence.location_metadata["fiscal_year"] == first_payload["fiscal_year"]
    assert (
        first_finding_evidence.location_metadata["audited_entity"]
        == first_payload["audited_entity"]
    )
    assert all(result.spending_review_signal_candidates == () for result in results)


def test_audit_finding_candidate_guard_rejects_app_classification_labels() -> None:
    for label in ["無駄遣い", "不正", "違法"]:
        try:
            normalize.validate_audit_finding_no_app_classification([label])
        except ValueError as exc:
            assert "audit finding classification is out of scope" in str(exc)
        else:
            raise AssertionError(f"expected guard to reject {label}")
