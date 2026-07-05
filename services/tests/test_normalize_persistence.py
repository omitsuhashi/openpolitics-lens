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
    assert "content_hash" in sql
    assert "source_span_start" in sql
    assert "source_span_end" in sql
    assert "extraction_method" in sql
    assert "confidence" in sql
    assert "grant_program_page_title_observed" in sql
    assert "machine_extracted" in sql


def test_normalize_evidence_migration_excludes_later_fact_tables() -> None:
    sql = _sql()

    assert "subsidy_program" not in sql
    assert "public_money_flow" not in sql
    assert "spending_review_signal" not in sql
    assert "audit_finding" not in sql
