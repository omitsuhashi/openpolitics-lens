from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = REPO_ROOT / "packages/db/migrations/20260705_002_normalize_evidence.sql"


def _sql() -> str:
    return " ".join(MIGRATION_PATH.read_text(encoding="utf-8").lower().split())


def test_normalize_evidence_migration_declares_source_documents_and_evidence_tables() -> None:
    sql = _sql()

    assert "create table if not exists source_documents" in sql
    assert "create table if not exists evidence_items" in sql
    assert "create table if not exists evidence_claims" in sql
    assert "references raw_artifacts" in sql
    assert "references source_documents" in sql
    assert "references evidence_items" in sql
    assert "raw_artifact_path" in sql
    assert "raw_artifact_id uuid not null" in sql
    assert "content_hash" in sql
    assert "source_span_start" in sql
    assert "source_span_end" in sql
    assert "raw html bytes offset" in sql
    assert "pdf / table extraction artifact text offset" in sql
    assert "extraction_method" in sql
    assert "location_metadata jsonb not null default '{}'::jsonb" in sql
    assert "parse_warnings text[] not null default array[]::text[]" in sql
    assert "extraction_artifact_path text" in sql
    assert "confidence" in sql
    assert "grant_program_page_title_observed" in sql
    assert "claim type catalog is enforced by normalize service contract tests" in sql
    assert "claim_type in ('grant_program_page_title_observed')" not in sql
    assert "predicate in ('observed_page_title')" not in sql
    assert "machine_extracted" in sql


def test_normalize_evidence_migration_names_phase0_warning_catalog() -> None:
    sql = _sql()

    for warning_code in [
        "pdf_text_layer_missing",
        "ocr_low_confidence",
        "table_structure_inferred",
        "amount_unit_ambiguous",
        "search_ui_snapshot",
        "source_layout_unverified",
    ]:
        assert warning_code in sql


def test_normalize_evidence_migration_excludes_later_fact_tables() -> None:
    sql = _sql()

    assert "create table if not exists subsidy_program" not in sql
    assert "create table if not exists public_money_flow" not in sql
    assert "create table if not exists spending_review_signal" not in sql
    assert "create table if not exists audit_finding" not in sql
