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


def test_normalize_grant_program_page_promotes_candidate_and_title_evidence() -> None:
    record = _fetch_manifest_record()
    observed_title = "子育て応援助成制度｜東京都"
    raw_html = (
        "<!doctype html><html><head>"
        f"<title>{observed_title}</title>"
        "</head><body><h1>本文の制度名</h1></body></html>"
    ).encode()

    result = normalize.normalize_grant_program_page(record, raw_html)
    repeated = normalize.normalize_grant_program_page(record, raw_html)

    assert result.to_json_dict() == repeated.to_json_dict()
    json.dumps(result.to_json_dict(), ensure_ascii=False)

    assert result.source_document.to_json_dict() == {
        "source_document_id": result.source_document.source_document_id,
        "source_system": "tokyo_metropolitan_government",
        "source_type": "grant_program_page",
        "canonical_url": "https://www.metro.tokyo.lg.jp/example/grant.html",
        "title": "子育て助成制度",
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
        )
