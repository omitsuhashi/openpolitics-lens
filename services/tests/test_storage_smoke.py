from datetime import UTC, datetime
from typing import Any

import pytest

import ingest
from ingest.storage_smoke import StorageSmokeError, StorageUnavailable


class FakeReadableObjectStorageClient:
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

    def head_object(self, *, bucket: str, key: str) -> dict[str, str]:
        assert self.puts
        latest = self.puts[-1]
        assert latest["bucket"] == bucket
        assert latest["key"] == key
        return latest["metadata"]


class UnavailableObjectStorageClient:
    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None:
        raise StorageUnavailable("MinIO endpoint is not reachable")

    def head_object(self, *, bucket: str, key: str) -> dict[str, str]:
        raise AssertionError("head_object should not be called when put_object is unavailable")


class HeadUnavailableAfterPutClient(FakeReadableObjectStorageClient):
    def head_object(self, *, bucket: str, key: str) -> dict[str, str]:
        assert self.puts
        raise StorageUnavailable("MinIO endpoint disappeared after PUT")


def test_storage_smoke_puts_one_artifact_and_verifies_metadata_and_db_payload() -> None:
    client = FakeReadableObjectStorageClient()
    fetched_at = datetime(2026, 7, 5, 9, 1, tzinfo=UTC)

    result = ingest.run_storage_smoke(
        bucket="openpolitics-raw",
        endpoint="http://localhost:9000",
        client=client,
        fetched_at=fetched_at,
    )

    assert result.status == "ok"
    assert result.object_key is not None
    assert result.object_key.startswith("raw/jp-tokyo/tokyo_metro_grants/2026/07/")
    assert result.object_key.endswith(".html")
    assert result.raw_artifact["object_bucket"] == "openpolitics-raw"
    assert result.raw_artifact["object_key"] == result.object_key
    assert result.raw_artifact["raw_artifact_path"] == result.object_key
    assert result.raw_artifact["canonical_url"] == "https://example.test/openpolitics/storage-smoke"
    assert result.raw_artifact["fetched_at"] == fetched_at
    assert result.raw_artifact["content_hash"] == result.content_hash
    assert result.raw_artifact["media_type"] == "text/html; charset=utf-8"
    assert result.raw_artifact["byte_size"] == result.byte_size
    assert result.raw_artifact["connector_version"] == "2026-07-05"
    assert result.raw_artifact["terms_note"] == (
        "official Tokyo Metropolitan Government public website pages"
    )

    metadata = client.puts[0]["metadata"]
    assert metadata == {
        "content_hash": result.content_hash,
        "hash_algorithm": "sha256",
        "jurisdiction_id": "jp-tokyo",
        "source_family": "tokyo_metro_grants",
        "canonical_url": "https://example.test/openpolitics/storage-smoke",
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost:9000",
        "http://127.0.0.1:9000",
        "http://127.42.0.1:9000",
        "http://[::1]:9000",
        "http://minio:9000",
    ],
)
def test_storage_smoke_allows_local_minio_endpoints(endpoint: str) -> None:
    result = ingest.run_storage_smoke(
        bucket="openpolitics-raw",
        endpoint=endpoint,
        client=FakeReadableObjectStorageClient(),
    )

    assert result.status == "ok"
    assert result.endpoint == endpoint


def test_storage_smoke_rejects_external_endpoint_before_put() -> None:
    client = FakeReadableObjectStorageClient()

    with pytest.raises(StorageSmokeError, match="local MinIO endpoint"):
        ingest.run_storage_smoke(
            bucket="openpolitics-raw",
            endpoint="https://s3.ap-northeast-1.amazonaws.com",
            client=client,
        )

    assert client.puts == []


def test_storage_smoke_skips_when_minio_is_unavailable() -> None:
    result = ingest.run_storage_smoke(
        bucket="openpolitics-raw",
        endpoint="http://localhost:9000",
        client=UnavailableObjectStorageClient(),
    )

    assert result.status == "skipped"
    assert result.reason == "MinIO endpoint is not reachable"
    assert result.object_key is None
    assert result.raw_artifact == {}


def test_storage_smoke_fails_when_head_is_unavailable_after_put() -> None:
    client = HeadUnavailableAfterPutClient()

    with pytest.raises(StorageSmokeError, match="metadata verification failed after PUT"):
        ingest.run_storage_smoke(
            bucket="openpolitics-raw",
            endpoint="http://localhost:9000",
            client=client,
        )

    assert len(client.puts) == 1


def test_storage_smoke_can_require_available_minio() -> None:
    with pytest.raises(StorageUnavailable, match="MinIO endpoint is not reachable"):
        ingest.run_storage_smoke(
            bucket="openpolitics-raw",
            endpoint="http://localhost:9000",
            client=UnavailableObjectStorageClient(),
            skip_if_unavailable=False,
        )
