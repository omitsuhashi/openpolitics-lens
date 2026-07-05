import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import ingest

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = REPO_ROOT / "packages/db/migrations/20260705_001_ingest_persistence.sql"


def _sql() -> str:
    return " ".join(MIGRATION_PATH.read_text(encoding="utf-8").lower().split())


def test_ingest_persistence_migration_declares_raw_artifacts_and_candidates() -> None:
    sql = _sql()

    assert "create table if not exists raw_artifacts" in sql
    assert "create table if not exists source_document_candidates" in sql
    assert "object_key" in sql
    assert "raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}" in sql
    assert "sha256" in sql
    assert "unique (object_bucket, object_key)" in sql
    assert "raw_artifacts_content_hash_idx" in sql
    assert "unique (content_hash)" not in sql
    assert "raw_artifact_id" in sql
    assert "references raw_artifacts" in sql
    assert "constraint raw_artifacts_candidate_identity_key" in sql
    assert "unique (raw_artifact_id, raw_artifact_path, jurisdiction_id, source_family)" in sql
    assert "constraint source_document_candidates_raw_artifact_fk" in sql
    assert (
        "foreign key (raw_artifact_id, raw_artifact_path, jurisdiction_id, source_family) "
        "references raw_artifacts (raw_artifact_id, raw_artifact_path, jurisdiction_id, "
        "source_family)"
    ) in sql


class FakeObjectStorageClient:
    def __init__(self) -> None:
        self.puts: list[dict[str, Any]] = []

    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None:
        self.puts.append(
            {
                "bucket": bucket,
                "key": key,
                "body": body,
                "content_type": content_type,
                "metadata": metadata,
            }
        )


def test_object_storage_writer_uses_raw_object_key_contract() -> None:
    client = FakeObjectStorageClient()
    writer = ingest.ObjectStorageOutputWriter(client=client, bucket="ingest-raw")
    content = b"<html><body>object storage</body></html>"
    digest = hashlib.sha256(content).hexdigest()

    written = writer.write_raw_artifact(
        content=content,
        jurisdiction_id="jp-tokyo",
        source_family="tokyo_metro_grants",
        fetched_at=datetime(2026, 7, 5, 9, 1),
        extension=".HTML",
        media_type="text/html; charset=utf-8",
    )

    expected_key = f"raw/jp-tokyo/tokyo_metro_grants/2026/07/{digest}.html"
    assert written.content_hash == digest
    assert written.object_key == expected_key
    assert written.raw_artifact_path == expected_key
    assert written.byte_size == len(content)
    assert client.puts == [
        {
            "bucket": "ingest-raw",
            "key": expected_key,
            "body": content,
            "content_type": "text/html; charset=utf-8",
            "metadata": {
                "content_hash": digest,
                "hash_algorithm": "sha256",
                "jurisdiction_id": "jp-tokyo",
                "source_family": "tokyo_metro_grants",
            },
        }
    ]


@pytest.mark.parametrize(
    "metadata",
    [
        {"content_hash": "b" * 64},
        {"Content_Hash": "b" * 64},
        {"CONTENT_HASH": "b" * 64},
        {"hash_algorithm": "md5"},
        {"Hash_Algorithm": "md5"},
        {"jurisdiction_id": "jp-yokohama"},
        {"JURISDICTION_ID": "jp-yokohama"},
        {"source_family": "other_family"},
        {"Source_Family": "other_family"},
    ],
)
def test_object_storage_writer_rejects_reserved_metadata_collision(
    metadata: dict[str, str],
) -> None:
    client = FakeObjectStorageClient()
    writer = ingest.ObjectStorageOutputWriter(client=client, bucket="ingest-raw")

    with pytest.raises(ValueError, match="reserved metadata"):
        writer.write_raw_artifact(
            content=b"<html></html>",
            jurisdiction_id="jp-tokyo",
            source_family="tokyo_metro_grants",
            fetched_at=datetime(2026, 7, 5, 9, 1),
            extension="html",
            media_type="text/html; charset=utf-8",
            metadata=metadata,
        )

    assert client.puts == []


def test_object_storage_writer_preserves_non_reserved_metadata() -> None:
    client = FakeObjectStorageClient()
    writer = ingest.ObjectStorageOutputWriter(client=client, bucket="ingest-raw")

    writer.write_raw_artifact(
        content=b"<html></html>",
        jurisdiction_id="jp-tokyo",
        source_family="tokyo_metro_grants",
        fetched_at=datetime(2026, 7, 5, 9, 1),
        extension="html",
        media_type="text/html; charset=utf-8",
        metadata={"source_url": "https://www.metro.tokyo.lg.jp/example.html"},
    )

    assert client.puts[0]["metadata"]["source_url"] == "https://www.metro.tokyo.lg.jp/example.html"


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


def test_fetch_manifest_record_builds_db_row_payloads() -> None:
    record = _fetch_manifest_record()

    rows = ingest.build_fetch_manifest_db_rows(record, object_bucket="ingest-raw")

    assert rows.raw_artifact == {
        "raw_artifact_id": rows.source_document_candidate["raw_artifact_id"],
        "jurisdiction_id": "jp-tokyo",
        "source_system": "tokyo_metropolitan_government",
        "source_family": "tokyo_metro_grants",
        "connector_id": "jp_tokyo.metro_grants.v1",
        "connector_version": "2026-07-05",
        "canonical_url": "https://www.metro.tokyo.lg.jp/example/grant.html",
        "fetched_at": datetime(2026, 7, 5, 9, 1, tzinfo=UTC),
        "http_status": 200,
        "content_hash": "a" * 64,
        "hash_algorithm": "sha256",
        "media_type": "text/html; charset=utf-8",
        "byte_size": 1234,
        "object_bucket": "ingest-raw",
        "object_key": record.raw_artifact_path,
        "raw_artifact_path": record.raw_artifact_path,
        "rate_limit_policy": "fixture-only; live network fetch is disabled by default",
        "terms_note": "official Tokyo Metropolitan Government public website pages",
    }
    assert rows.source_document_candidate == {
        "raw_artifact_id": rows.raw_artifact["raw_artifact_id"],
        "canonical_url": "https://www.metro.tokyo.lg.jp/example/grant.html",
        "title": "子育て助成制度",
        "source_type": "grant_program_page",
        "jurisdiction_id": "jp-tokyo",
        "source_family": "tokyo_metro_grants",
        "language": "ja",
        "retrieved_at": datetime(2026, 7, 5, 9, 1, tzinfo=UTC),
        "raw_artifact_path": record.raw_artifact_path,
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
def test_fetch_manifest_db_rows_reject_candidate_invariant_mismatches(
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
        ingest.build_fetch_manifest_db_rows(mismatched_record, object_bucket="ingest-raw")
