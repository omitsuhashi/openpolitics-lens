import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest

import ingest
import normalize


def _fetch_manifest_record() -> ingest.FetchManifestRecord:
    fetched_at = datetime(2026, 7, 5, 9, 1, tzinfo=UTC)
    raw_artifact_path = "raw/jp-tokyo/tokyo_metro_grants/2026/07/" + ("a" * 64) + ".html"
    candidate = ingest.SourceDocumentCandidate(
        canonical_url="https://www.metro.tokyo.lg.jp/example/grant.html",
        title="子育て助成制度",
        source_type="grant_program_page",
        jurisdiction_id="jp-tokyo",
        source_family="tokyo_metro_grants",
        language="ja",
        retrieved_at=fetched_at,
        raw_artifact_path=raw_artifact_path,
    )

    return ingest.FetchManifestRecord(
        connector=ingest.TOKYO_METRO_GRANTS_CONNECTOR,
        canonical_url=candidate.canonical_url,
        fetched_at=fetched_at,
        http_status=200,
        content_hash="a" * 64,
        media_type="text/html; charset=utf-8",
        byte_size=1234,
        raw_artifact_path=raw_artifact_path,
        source_document_candidate=candidate,
    )


def _raw_artifact_id(record: ingest.FetchManifestRecord) -> str:
    rows = ingest.build_fetch_manifest_db_rows(record, object_bucket="ingest-raw")
    return str(rows.raw_artifact["raw_artifact_id"])


def test_normalize_grant_program_page_promotes_candidate_and_title_evidence() -> None:
    record = _fetch_manifest_record()
    raw_artifact_id = _raw_artifact_id(record)
    observed_title = "子育て応援助成制度｜東京都"
    raw_html = (
        "<!doctype html><html><head>"
        f"<title>{observed_title}</title>"
        "</head><body><h1>本文の制度名</h1></body></html>"
    ).encode()

    result = normalize.normalize_grant_program_page(
        record,
        raw_html,
        raw_artifact_id=raw_artifact_id,
    )
    repeated = normalize.normalize_grant_program_page(
        record,
        raw_html,
        raw_artifact_id=raw_artifact_id,
    )

    assert result.to_json_dict() == repeated.to_json_dict()
    json.dumps(result.to_json_dict(), ensure_ascii=False)

    assert result.source_document.to_json_dict() == {
        "source_document_id": result.source_document.source_document_id,
        "raw_artifact_id": raw_artifact_id,
        "source_system": "tokyo_metropolitan_government",
        "source_type": "grant_program_page",
        "canonical_url": "https://www.metro.tokyo.lg.jp/example/grant.html",
        "title": observed_title,
        "published_at": None,
        "retrieved_at": "2026-07-05T09:01:00Z",
        "raw_artifact_path": record.raw_artifact_path,
        "content_hash": "a" * 64,
        "license_note": "official Tokyo Metropolitan Government public website pages",
        "source_reliability": "official_source",
        "jurisdiction_id": "jp-tokyo",
        "source_family": "tokyo_metro_grants",
        "language": "ja",
    }

    assert len(result.evidence_items) == 1
    evidence_item = result.evidence_items[0]
    title_start = raw_html.index(observed_title.encode())
    title_end = title_start + len(observed_title.encode())
    assert evidence_item.to_json_dict() == {
        "evidence_item_id": evidence_item.evidence_item_id,
        "source_document_id": result.source_document.source_document_id,
        "location_type": "html_selector",
        "location_value": "title",
        "source_span_start": title_start,
        "source_span_end": title_end,
        "quote_text": observed_title,
        "normalized_text": observed_title,
        "raw_artifact_path": record.raw_artifact_path,
        "extraction_method": "html_title",
        "confidence": 1.0,
        "location_metadata": {},
        "parse_warnings": [],
        "extraction_artifact_path": None,
    }

    assert len(result.evidence_claims) == 1
    evidence_claim = result.evidence_claims[0]
    assert evidence_claim.to_json_dict() == {
        "evidence_claim_id": evidence_claim.evidence_claim_id,
        "claim_type": "grant_program_page_title_observed",
        "subject_ref": result.source_document.source_document_id,
        "predicate": "observed_page_title",
        "object_ref": None,
        "object_value": observed_title,
        "event_date": None,
        "amount": None,
        "currency": None,
        "evidence_item_id": evidence_item.evidence_item_id,
        "review_state": "machine_extracted",
    }


def test_normalize_keeps_quote_text_as_decoded_source_span_and_normalizes_title() -> None:
    record = _fetch_manifest_record()
    raw_title = "子育て&nbsp;\n応援助成制度"
    normalized_title = "子育て 応援助成制度"
    raw_html = f"<html><head><title>{raw_title}</title></head></html>".encode()

    result = normalize.normalize_grant_program_page(
        record,
        raw_html,
        raw_artifact_id=_raw_artifact_id(record),
    )

    evidence_item = result.evidence_items[0]
    assert result.source_document.title == normalized_title
    assert evidence_item.quote_text == raw_title
    assert evidence_item.normalized_text == normalized_title
    assert evidence_item.source_span_start == raw_html.index(raw_title.encode())
    assert evidence_item.source_span_end == evidence_item.source_span_start + len(
        raw_title.encode()
    )
    assert result.evidence_claims[0].object_value == normalized_title


def test_evidence_item_serializes_locator_warnings_and_extraction_artifact_path() -> None:
    pdf_item = normalize.EvidenceItem(
        evidence_item_id="pdf-item",
        source_document_id="source-doc",
        location_type="page_span",
        location_value="p.4",
        source_span_start=120,
        source_span_end=180,
        quote_text="監査指摘本文",
        normalized_text="監査指摘本文",
        raw_artifact_path="raw/jp-tokyo/tokyo_audit_reports/2026/07/report.pdf",
        extraction_method="pdf_text_layer",
        confidence=0.92,
        location_metadata={"page_number": 4, "bbox": [12.5, 20.0, 300.0, 84.0]},
        parse_warnings=("pdf_text_layer_missing",),
        extraction_artifact_path="derived/jp-tokyo/tokyo_audit_reports/report.txt",
    )
    table_item = normalize.EvidenceItem(
        evidence_item_id="table-item",
        source_document_id="source-doc",
        location_type="table_cell",
        location_value="table[2]/row[5]/cell[3]",
        source_span_start=48,
        source_span_end=56,
        quote_text="1,200",
        normalized_text="1200",
        raw_artifact_path="raw/jp-tokyo/tokyo_budget_settlement/2026/07/budget.pdf",
        extraction_method="table_extraction",
        confidence=0.86,
        location_metadata={
            "page_number": 12,
            "table_index": 2,
            "row_index": 5,
            "column_index": 3,
        },
        parse_warnings=("table_structure_inferred", "amount_unit_ambiguous"),
        extraction_artifact_path="derived/jp-tokyo/tokyo_budget_settlement/table-2.json",
    )
    search_snapshot_item = normalize.EvidenceItem(
        evidence_item_id="search-item",
        source_document_id="source-doc",
        location_type="api_record",
        location_value="result-row-7",
        source_span_start=0,
        source_span_end=42,
        quote_text="検索結果行",
        normalized_text="検索結果行",
        raw_artifact_path="raw/jp-tokyo/tokyo_procurement/2026/07/search.html",
        extraction_method="search_ui_snapshot",
        confidence=0.9,
        location_metadata={
            "search_form_url": "https://example.metro.tokyo.lg.jp/search",
            "query_parameters": {"keyword": "委託"},
            "page_number": 1,
            "sort_order": "published_at_desc",
            "snapshot_timestamp": "2026-07-07T00:00:00Z",
            "result_row_locator": "tr[data-row='7']",
        },
        parse_warnings=("search_ui_snapshot",),
    )

    assert pdf_item.to_json_dict()["location_metadata"] == {
        "page_number": 4,
        "bbox": [12.5, 20.0, 300.0, 84.0],
    }
    assert table_item.to_json_dict()["parse_warnings"] == [
        "table_structure_inferred",
        "amount_unit_ambiguous",
    ]
    assert search_snapshot_item.to_json_dict()["extraction_artifact_path"] is None
    assert normalize.can_promote_to_evidence_claim(search_snapshot_item)
    json.dumps(
        {
            "pdf": pdf_item.to_json_dict(),
            "table": table_item.to_json_dict(),
            "search": search_snapshot_item.to_json_dict(),
        },
        ensure_ascii=False,
    )


def test_warning_and_claim_catalogs_are_source_family_wide() -> None:
    assert {
        "pdf_text_layer_missing",
        "ocr_low_confidence",
        "table_structure_inferred",
        "search_ui_snapshot",
    }.issubset(normalize.WARNING_CATALOG)

    assert (
        normalize.claim_catalog_entry(
            "grant_program_page_title_observed",
            source_family="tokyo_metro_grants",
        ).predicate
        == "observed_page_title"
    )
    assert (
        normalize.claim_catalog_entry(
            "audit_report_finding_text_observed",
            source_family="tokyo_audit_reports",
        ).predicate
        == "observed_audit_finding_text"
    )
    assert (
        normalize.claim_catalog_entry(
            "procurement_search_row_observed",
            source_family="tokyo_procurement",
        ).predicate
        == "observed_procurement_search_row"
    )

    with pytest.raises(ValueError, match="unknown claim_type"):
        normalize.claim_catalog_entry("unknown_claim", source_family="tokyo_metro_grants")


def test_audit_finding_and_spending_review_signal_candidates_use_separate_storage_claims() -> None:
    audit_entry = normalize.candidate_claim_catalog_entry(
        normalize.AUDIT_FINDING_CANDIDATE_CLAIM_TYPE,
    )
    signal_entry = normalize.candidate_claim_catalog_entry(
        normalize.SPENDING_REVIEW_SIGNAL_CANDIDATE_CLAIM_TYPE,
    )

    assert audit_entry.storage_table == "audit_finding_candidates"
    assert signal_entry.storage_table == "spending_review_signal_candidates"
    assert audit_entry.claim_type != signal_entry.claim_type
    assert audit_entry.origin == "official_audit_source"
    assert signal_entry.origin == "app_calculated"


def test_spending_review_signal_candidate_serializes_internal_review_contract_only() -> None:
    computed_at = datetime(2026, 7, 7, 10, 30, tzinfo=UTC)

    candidate = normalize.SpendingReviewSignalCandidate(
        spending_review_signal_candidate_id="signal-candidate-1",
        signal_type="audit_finding_linked",
        target_ref="audit_finding_candidate:audit-1",
        method_version="phase0.audit-signal-separation.v1",
        supporting_evidence_item_ids=("evidence-support-1",),
        counter_evidence_item_ids=("evidence-counter-1",),
        limitations=("監査指摘との関連候補であり、違法性や無駄遣いを判定しない",),
        computed_at=computed_at,
        review_state="needs_human_review",
    )

    payload = candidate.to_json_dict()

    assert payload == {
        "contract_type": "SpendingReviewSignalCandidate",
        "spending_review_signal_candidate_id": "signal-candidate-1",
        "claim_type": "app_calculated_review_signal_candidate",
        "signal_type": "audit_finding_linked",
        "target_ref": "audit_finding_candidate:audit-1",
        "method_version": "phase0.audit-signal-separation.v1",
        "supporting_evidence_item_ids": ["evidence-support-1"],
        "counter_evidence_item_ids": ["evidence-counter-1"],
        "limitations": ["監査指摘との関連候補であり、違法性や無駄遣いを判定しない"],
        "computed_at": "2026-07-07T10:30:00Z",
        "review_state": "needs_human_review",
        "public_visibility": "internal_only",
    }
    assert payload["contract_type"] != "SpendingReviewSignal"
    assert "score" not in payload
    assert "severity_band" not in payload
    assert not hasattr(candidate, "score")
    json.dumps(payload, ensure_ascii=False)


def test_spending_review_signal_candidate_rejects_public_or_untraced_state() -> None:
    kwargs = {
        "spending_review_signal_candidate_id": "signal-candidate-1",
        "signal_type": "audit_finding_linked",
        "target_ref": "audit_finding_candidate:audit-1",
        "method_version": "phase0.audit-signal-separation.v1",
        "supporting_evidence_item_ids": ("evidence-support-1",),
        "counter_evidence_item_ids": (),
        "limitations": ("反証 evidence は未接続",),
        "computed_at": datetime(2026, 7, 7, 10, 30, tzinfo=UTC),
        "review_state": "needs_human_review",
    }

    with pytest.raises(ValueError, match="internal_only"):
        normalize.SpendingReviewSignalCandidate(**kwargs, public_visibility="public")

    with pytest.raises(ValueError, match="supporting_evidence_item_ids"):
        normalize.SpendingReviewSignalCandidate(
            **{**kwargs, "supporting_evidence_item_ids": ()},
        )

    with pytest.raises(ValueError, match="limitations"):
        normalize.SpendingReviewSignalCandidate(**{**kwargs, "limitations": ()})


@pytest.mark.parametrize(
    "case",
    [
        "missing_locator",
        "low_confidence",
        "search_snapshot_missing_metadata",
    ],
)
def test_low_confidence_or_missing_locator_evidence_does_not_promote_to_claim(
    case: str,
) -> None:
    if case == "missing_locator":
        evidence_item = normalize.EvidenceItem(
            evidence_item_id="missing-locator",
            source_document_id="source-doc",
            location_type="page_span",
            location_value="",
            source_span_start=10,
            source_span_end=20,
            quote_text="監査指摘本文",
            normalized_text="監査指摘本文",
            raw_artifact_path="raw/jp-tokyo/tokyo_audit_reports/2026/07/report.pdf",
            extraction_method="pdf_text_layer",
            confidence=0.92,
            location_metadata={},
        )
    elif case == "low_confidence":
        evidence_item = normalize.EvidenceItem(
            evidence_item_id="low-confidence",
            source_document_id="source-doc",
            location_type="page_span",
            location_value="p.2",
            source_span_start=10,
            source_span_end=20,
            quote_text="OCR本文",
            normalized_text="OCR本文",
            raw_artifact_path="raw/jp-tokyo/tokyo_audit_reports/2026/07/report.pdf",
            extraction_method="ocr",
            confidence=0.61,
            location_metadata={"page_number": 2},
            parse_warnings=("ocr_low_confidence",),
        )
    else:
        evidence_item = normalize.EvidenceItem(
            evidence_item_id="search-snapshot-missing-metadata",
            source_document_id="source-doc",
            location_type="api_record",
            location_value="result-row-7",
            source_span_start=0,
            source_span_end=42,
            quote_text="検索結果行",
            normalized_text="検索結果行",
            raw_artifact_path="raw/jp-tokyo/tokyo_procurement/2026/07/search.html",
            extraction_method="search_ui_snapshot",
            confidence=0.9,
            location_metadata={"page_number": 1},
            parse_warnings=("search_ui_snapshot",),
        )

    assert not normalize.can_promote_to_evidence_claim(evidence_item)

    with pytest.raises(ValueError, match="not eligible for EvidenceClaim"):
        normalize.build_observed_claim(
            evidence_claim_id="claim-id",
            claim_type="audit_report_finding_text_observed",
            subject_ref="source-doc",
            object_value=evidence_item.normalized_text,
            evidence_item=evidence_item,
            source_family="tokyo_audit_reports",
        )


def test_normalize_does_not_infer_non_goal_claims_from_body_text() -> None:
    record = _fetch_manifest_record()
    observed_title = "子育て応援助成制度｜東京都"
    raw_html = (
        "<html><head>"
        f"<title>{observed_title}</title>"
        "</head><body>"
        "<p>交付先: 株式会社サンプル</p>"
        "<p>100万円を助成します。</p>"
        "<p>監査指摘: 支出確認が必要です。</p>"
        "</body></html>"
    ).encode()

    result = normalize.normalize_grant_program_page(
        record,
        raw_html,
        raw_artifact_id=_raw_artifact_id(record),
    )

    assert len(result.evidence_items) == 1
    assert len(result.evidence_claims) == 1
    claim = result.evidence_claims[0]
    assert claim.claim_type == "grant_program_page_title_observed"
    assert claim.object_value == observed_title
    assert claim.amount is None
    assert claim.currency is None
    assert claim.event_date is None
    assert claim.object_ref is None


@pytest.mark.parametrize(
    ("field_name", "replacement_value"),
    [
        ("canonical_url", "https://www.metro.tokyo.lg.jp/other.html"),
        ("raw_artifact_path", "raw/jp-tokyo/tokyo_metro_grants/2026/07/" + ("b" * 64) + ".html"),
        ("jurisdiction_id", "jp-yokohama"),
        ("source_family", "other_family"),
    ],
)
def test_normalize_rejects_candidate_invariant_mismatches(
    field_name: str,
    replacement_value: str,
) -> None:
    record = _fetch_manifest_record()
    mismatched_candidate = replace(
        record.source_document_candidate,
        **{field_name: replacement_value},
    )
    mismatched_record = replace(record, source_document_candidate=mismatched_candidate)

    with pytest.raises(ValueError, match=field_name):
        normalize.normalize_grant_program_page(
            mismatched_record,
            "<html><head><title>子育て応援助成制度</title></head></html>".encode(),
            raw_artifact_id=_raw_artifact_id(record),
        )


def test_normalize_rejects_non_grant_program_source_type() -> None:
    record = _fetch_manifest_record()
    mismatched_record = replace(
        record,
        source_document_candidate=replace(
            record.source_document_candidate,
            source_type="spending_review_page",
        ),
    )

    with pytest.raises(ValueError, match="source_type"):
        normalize.normalize_grant_program_page(
            mismatched_record,
            "<html><head><title>子育て応援助成制度</title></head></html>".encode(),
            raw_artifact_id=_raw_artifact_id(record),
        )


@pytest.mark.parametrize("media_type", ["application/pdf", "text/plain", "application/json"])
def test_normalize_rejects_non_html_media_type(media_type: str) -> None:
    record = replace(_fetch_manifest_record(), media_type=media_type)

    with pytest.raises(ValueError, match="media_type"):
        normalize.normalize_grant_program_page(
            record,
            "<html><head><title>子育て応援助成制度</title></head></html>".encode(),
            raw_artifact_id=_raw_artifact_id(record),
        )
