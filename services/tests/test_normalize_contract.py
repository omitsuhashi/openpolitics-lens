import json
from dataclasses import replace
from datetime import UTC, date, datetime

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


def _event_source_assertion(
    *,
    asserted_field: str = "scheduled_date",
    asserted_value: str = "2026-07-21",
    conflict_state: str = "none",
    evidence_item_id: str = "evidence-election-notice-1",
) -> normalize.EventSourceAssertion:
    return normalize.EventSourceAssertion(
        event_candidate_id="event-candidate-tokyo-governor-polling-day",
        source_document_id="source-document-election-notice",
        evidence_item_id=evidence_item_id,
        asserted_field=asserted_field,
        asserted_value=asserted_value,
        asserted_at=datetime(2026, 7, 7, 9, 30, tzinfo=UTC),
        source_priority=10,
        conflict_state=conflict_state,
        confidence=0.95,
        review_state="machine_extracted",
        limitations=("fixture source only",),
    )


def _official_event_candidate(
    *source_assertions: normalize.EventSourceAssertion,
) -> normalize.OfficialPoliticalEventCandidate:
    assertions = source_assertions or (_event_source_assertion(),)
    return normalize.OfficialPoliticalEventCandidate(
        event_candidate_id="event-candidate-tokyo-governor-polling-day",
        event_family="Election",
        event_type="polling_day",
        jurisdiction_id="jp-tokyo",
        jurisdiction_level="prefecture",
        source_system="tokyo_election_administration_commission",
        source_family="jp_prefecture_election_schedules",
        connector_id="jp_tokyo.election_schedule.v1",
        title="東京都知事選挙 投票日",
        scheduled_date=date(2026, 7, 21),
        scheduled_time=None,
        timezone="Asia/Tokyo",
        date_precision="date",
        office_or_body="東京都知事",
        event_status="scheduled",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/example/schedule.html",
        source_document_id="source-document-election-notice",
        evidence_item_id="evidence-election-notice-1",
        extraction_method="fixture_html_table",
        confidence=0.95,
        review_state="machine_extracted",
        limitations=("fixture source only",),
        source_assertions=assertions,
    )


def test_official_political_event_candidate_round_trips_json_contract() -> None:
    candidate = _official_event_candidate()

    candidate_json = candidate.to_json_dict()
    json.dumps(candidate_json, ensure_ascii=False)

    assert candidate_json["event_family"] == "Election"
    assert candidate_json["event_type"] == "polling_day"
    assert candidate_json["event_status"] == "scheduled"
    assert candidate_json["scheduled_date"] == "2026-07-21"
    assert candidate_json["scheduled_time"] is None
    assert candidate_json["timezone"] == "Asia/Tokyo"
    assert candidate_json["date_precision"] == "date"
    assert candidate_json["source_document_id"] == "source-document-election-notice"
    assert candidate_json["evidence_item_id"] == "evidence-election-notice-1"
    assert candidate_json["confidence"] == 0.95
    assert candidate_json["review_state"] == "machine_extracted"
    assert candidate_json["limitations"] == ["fixture source only"]
    assert candidate_json["conflict_states"] == []
    assert normalize.OfficialPoliticalEventCandidate.from_json_dict(candidate_json) == candidate


def test_event_candidate_keeps_multiple_source_assertions_and_conflicts() -> None:
    primary_assertion = _event_source_assertion()
    date_conflict = _event_source_assertion(
        asserted_value="2026-07-20",
        conflict_state="date_mismatch",
        evidence_item_id="evidence-aggregator-date-1",
    )
    title_conflict = _event_source_assertion(
        asserted_field="title",
        asserted_value="東京都知事選挙期日",
        conflict_state="title_mismatch",
        evidence_item_id="evidence-aggregator-title-1",
    )
    status_conflict = _event_source_assertion(
        asserted_field="event_status",
        asserted_value="postponed",
        conflict_state="status_mismatch",
        evidence_item_id="evidence-aggregator-status-1",
    )

    candidate = _official_event_candidate(
        primary_assertion,
        date_conflict,
        title_conflict,
        status_conflict,
    )

    candidate_json = candidate.to_json_dict()

    assert len(candidate.source_assertions) == 4
    assert candidate.conflict_states() == (
        "date_mismatch",
        "title_mismatch",
        "status_mismatch",
    )
    assert candidate_json["scheduled_date"] == "2026-07-21"
    assert [item["asserted_value"] for item in candidate_json["source_assertions"]] == [
        "2026-07-21",
        "2026-07-20",
        "東京都知事選挙期日",
        "postponed",
    ]
    assert candidate_json["conflict_states"] == [
        "date_mismatch",
        "title_mismatch",
        "status_mismatch",
    ]
    assert normalize.OfficialPoliticalEventCandidate.from_json_dict(candidate_json) == candidate


@pytest.mark.parametrize(
    ("asserted_field", "asserted_value", "expected_conflict_state"),
    [
        ("scheduled_date", "2026-07-20", "date_mismatch"),
        ("title", "東京都知事選挙期日", "title_mismatch"),
        ("event_status", "postponed", "status_mismatch"),
    ],
)
def test_event_candidate_rejects_tracked_field_mismatch_without_conflict_state(
    asserted_field: str,
    asserted_value: str,
    expected_conflict_state: str,
) -> None:
    assertion = _event_source_assertion(
        asserted_field=asserted_field,
        asserted_value=asserted_value,
        conflict_state="none",
    )

    with pytest.raises(ValueError, match=expected_conflict_state):
        _official_event_candidate(assertion)

    candidate_json = _official_event_candidate().to_json_dict()
    candidate_json["source_assertions"][0] = {
        **candidate_json["source_assertions"][0],
        "asserted_field": asserted_field,
        "asserted_value": asserted_value,
        "conflict_state": "none",
    }

    with pytest.raises(ValueError, match=expected_conflict_state):
        normalize.OfficialPoliticalEventCandidate.from_json_dict(candidate_json)


@pytest.mark.parametrize(
    ("asserted_field", "asserted_value", "wrong_conflict_state"),
    [
        ("scheduled_date", "2026-07-20", "title_mismatch"),
        ("title", "東京都知事選挙期日", "status_mismatch"),
        ("event_status", "postponed", "date_mismatch"),
        ("canonical_url", "https://www.senkyo.metro.tokyo.lg.jp/other.html", "date_mismatch"),
    ],
)
def test_event_candidate_rejects_mismatch_state_for_wrong_asserted_field(
    asserted_field: str,
    asserted_value: str,
    wrong_conflict_state: str,
) -> None:
    assertion = _event_source_assertion(
        asserted_field=asserted_field,
        asserted_value=asserted_value,
        conflict_state=wrong_conflict_state,
    )

    with pytest.raises(ValueError, match=wrong_conflict_state):
        _official_event_candidate(assertion)

    candidate_json = _official_event_candidate().to_json_dict()
    candidate_json["source_assertions"][0] = {
        **candidate_json["source_assertions"][0],
        "asserted_field": asserted_field,
        "asserted_value": asserted_value,
        "conflict_state": wrong_conflict_state,
    }

    with pytest.raises(ValueError, match=wrong_conflict_state):
        normalize.OfficialPoliticalEventCandidate.from_json_dict(candidate_json)


def test_event_candidate_allows_tracked_field_mismatch_when_marked_needs_review() -> None:
    assertion = _event_source_assertion(
        asserted_value="2026-07-20",
        conflict_state="needs_review",
    )

    candidate = _official_event_candidate(assertion)

    assert candidate.conflict_states() == ("needs_review",)


def test_event_candidates_require_evidence_backed_source_assertions() -> None:
    with pytest.raises(ValueError, match="source_assertions"):
        replace(_official_event_candidate(), source_assertions=())

    with pytest.raises(ValueError, match="evidence_item_id"):
        _official_event_candidate(
            _event_source_assertion(evidence_item_id=""),
        )

    candidate_json = _official_event_candidate().to_json_dict()
    candidate_json["evidence_item_id"] = ""
    with pytest.raises(ValueError, match="evidence_item_id"):
        normalize.OfficialPoliticalEventCandidate.from_json_dict(candidate_json)


def test_vote_event_candidate_does_not_generate_vote_positions_without_source_positions() -> None:
    candidate = replace(
        _official_event_candidate(),
        event_family="Diet",
        event_type="vote_held",
        title="本会議 採決",
        office_or_body="衆議院本会議",
    )

    candidate_json = candidate.to_json_dict()

    assert "vote_positions" not in candidate_json
    assert "VotePosition" not in json.dumps(candidate_json, ensure_ascii=False)
