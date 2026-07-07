import hmac
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from ipaddress import ip_address
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from ingest.contracts import FetchManifestRecord, JsonDict, SourceDocumentCandidate
from ingest.object_storage import ObjectStorageOutputWriter
from ingest.persistence import build_fetch_manifest_db_rows
from ingest.tokyo_metro_grants import TOKYO_METRO_GRANTS_CONNECTOR

SMOKE_CANONICAL_URL = "https://example.test/openpolitics/storage-smoke"
SMOKE_CONTENT = b"<!doctype html><title>OpenPolitics Lens storage smoke</title>\n"
SMOKE_MEDIA_TYPE = "text/html; charset=utf-8"


class StorageSmokeError(RuntimeError):
    pass


class StorageUnavailable(StorageSmokeError):
    pass


@dataclass(frozen=True, slots=True)
class StorageSmokeResult:
    status: str
    bucket: str
    endpoint: str
    object_key: str | None
    raw_artifact_path: str | None
    content_hash: str | None
    byte_size: int | None
    raw_artifact: JsonDict
    source_document_candidate: JsonDict
    reason: str | None = None

    def to_json_dict(self) -> JsonDict:
        payload: JsonDict = {
            "status": self.status,
            "bucket": self.bucket,
            "endpoint": self.endpoint,
            "object_key": self.object_key,
            "raw_artifact_path": self.raw_artifact_path,
            "content_hash": self.content_hash,
            "byte_size": self.byte_size,
            "raw_artifact": _json_ready(self.raw_artifact),
            "source_document_candidate": _json_ready(self.source_document_candidate),
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


class S3CompatibleObjectStorageClient:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region: str,
        timeout_seconds: float = 2.0,
    ) -> None:
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            msg = "endpoint must be an absolute http(s) URL"
            raise ValueError(msg)
        if not access_key:
            msg = "access_key must not be empty"
            raise ValueError(msg)
        if not secret_key:
            msg = "secret_key must not be empty"
            raise ValueError(msg)
        if not region:
            msg = "region must not be empty"
            raise ValueError(msg)

        self.endpoint = endpoint.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.timeout_seconds = timeout_seconds

    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None:
        self._request(
            method="PUT",
            bucket=bucket,
            key=key,
            body=body,
            content_type=content_type,
            metadata=metadata,
        )

    def head_object(self, *, bucket: str, key: str) -> dict[str, str]:
        headers = self._request(method="HEAD", bucket=bucket, key=key)
        metadata: dict[str, str] = {}
        for header_name, header_value in headers.items():
            normalized_name = header_name.lower()
            if normalized_name.startswith("x-amz-meta-"):
                metadata[normalized_name.removeprefix("x-amz-meta-")] = header_value
        return metadata

    def _request(
        self,
        *,
        method: str,
        bucket: str,
        key: str,
        body: bytes = b"",
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> Mapping[str, str]:
        parsed_endpoint = urlsplit(self.endpoint)
        canonical_uri = _canonical_object_uri(parsed_endpoint.path, bucket, key)
        url = urlunsplit(
            (
                parsed_endpoint.scheme,
                parsed_endpoint.netloc,
                canonical_uri,
                "",
                "",
            )
        )
        request_time = datetime.now(tz=UTC)
        payload_hash = sha256(body).hexdigest()
        headers = {
            "host": parsed_endpoint.netloc,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": request_time.strftime("%Y%m%dT%H%M%SZ"),
        }
        if content_type is not None:
            headers["content-type"] = content_type
        if metadata is not None:
            for key_name, value in metadata.items():
                headers[f"x-amz-meta-{key_name}"] = value
        headers["authorization"] = self._authorization_header(
            method=method,
            canonical_uri=canonical_uri,
            headers=headers,
            payload_hash=payload_hash,
            request_time=request_time,
        )

        request = Request(
            url,
            data=body if method != "HEAD" else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return dict(response.headers.items())
        except HTTPError as exc:
            if exc.code in {502, 503, 504}:
                raise StorageUnavailable(f"MinIO endpoint is not ready: HTTP {exc.code}") from exc
            error_body = exc.read(512).decode("utf-8", errors="replace")
            msg = f"S3 {method} failed with HTTP {exc.code}: {error_body}"
            raise StorageSmokeError(msg) from exc
        except URLError as exc:
            msg = f"MinIO endpoint is not reachable: {exc.reason}"
            raise StorageUnavailable(msg) from exc
        except TimeoutError as exc:
            raise StorageUnavailable("MinIO endpoint timed out") from exc

    def _authorization_header(
        self,
        *,
        method: str,
        canonical_uri: str,
        headers: Mapping[str, str],
        payload_hash: str,
        request_time: datetime,
    ) -> str:
        date_scope = request_time.strftime("%Y%m%d")
        credential_scope = f"{date_scope}/{self.region}/s3/aws4_request"
        canonical_headers, signed_headers = _canonical_headers(headers)
        canonical_request = "\n".join(
            [
                method,
                canonical_uri,
                "",
                canonical_headers,
                "",
                signed_headers,
                payload_hash,
            ]
        )
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                request_time.strftime("%Y%m%dT%H%M%SZ"),
                credential_scope,
                sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signing_key = _signing_key(self.secret_key, date_scope, self.region)
        signature = hmac.new(
            signing_key,
            string_to_sign.encode("utf-8"),
            sha256,
        ).hexdigest()
        return (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )


def run_storage_smoke(
    *,
    bucket: str,
    endpoint: str,
    access_key: str = "openpolitics",
    secret_key: str = "openpolitics_minio_dev_password",
    region: str = "ap-northeast-1",
    timeout_seconds: float = 2.0,
    client: object | None = None,
    fetched_at: datetime | None = None,
    skip_if_unavailable: bool = True,
) -> StorageSmokeResult:
    _validate_local_minio_endpoint(endpoint)
    storage_client = client or S3CompatibleObjectStorageClient(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        timeout_seconds=timeout_seconds,
    )
    fetched_timestamp = fetched_at or datetime.now(tz=UTC)
    connector = TOKYO_METRO_GRANTS_CONNECTOR
    writer = ObjectStorageOutputWriter(client=storage_client, bucket=bucket)

    try:
        written = writer.write_raw_artifact(
            content=SMOKE_CONTENT,
            jurisdiction_id=connector.jurisdiction.jurisdiction_id,
            source_family=connector.source_family.source_family,
            fetched_at=fetched_timestamp,
            extension="html",
            media_type=SMOKE_MEDIA_TYPE,
            metadata={"canonical_url": SMOKE_CANONICAL_URL},
        )
    except StorageUnavailable as exc:
        if not skip_if_unavailable:
            raise
        return StorageSmokeResult(
            status="skipped",
            bucket=bucket,
            endpoint=endpoint,
            object_key=None,
            raw_artifact_path=None,
            content_hash=None,
            byte_size=None,
            raw_artifact={},
            source_document_candidate={},
            reason=str(exc),
        )
    try:
        metadata = storage_client.head_object(bucket=bucket, key=written.object_key)
    except StorageUnavailable as exc:
        msg = f"metadata verification failed after PUT: {exc}"
        raise StorageSmokeError(msg) from exc

    _validate_smoke_metadata(
        metadata,
        {
            "content_hash": written.content_hash,
            "hash_algorithm": "sha256",
            "jurisdiction_id": connector.jurisdiction.jurisdiction_id,
            "source_family": connector.source_family.source_family,
            "canonical_url": SMOKE_CANONICAL_URL,
        },
    )
    candidate = SourceDocumentCandidate(
        canonical_url=SMOKE_CANONICAL_URL,
        title="OpenPolitics Lens storage smoke",
        source_type="storage_smoke",
        jurisdiction_id=connector.jurisdiction.jurisdiction_id,
        source_family=connector.source_family.source_family,
        language="en",
        retrieved_at=fetched_timestamp,
        raw_artifact_path=written.raw_artifact_path,
    )
    record = FetchManifestRecord(
        connector=connector,
        canonical_url=SMOKE_CANONICAL_URL,
        fetched_at=fetched_timestamp,
        http_status=200,
        content_hash=written.content_hash,
        media_type=SMOKE_MEDIA_TYPE,
        byte_size=written.byte_size,
        raw_artifact_path=written.raw_artifact_path,
        source_document_candidate=candidate,
    )
    rows = build_fetch_manifest_db_rows(record, object_bucket=bucket)
    _validate_payload_matches_object_storage(
        rows.raw_artifact,
        bucket=bucket,
        object_key=written.object_key,
    )

    return StorageSmokeResult(
        status="ok",
        bucket=bucket,
        endpoint=endpoint,
        object_key=written.object_key,
        raw_artifact_path=written.raw_artifact_path,
        content_hash=written.content_hash,
        byte_size=written.byte_size,
        raw_artifact=rows.raw_artifact,
        source_document_candidate=rows.source_document_candidate,
    )


def _validate_local_minio_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or hostname is None:
        msg = "storage-smoke endpoint must be an absolute local MinIO endpoint"
        raise StorageSmokeError(msg)

    normalized_hostname = hostname.lower()
    if normalized_hostname in {"localhost", "minio"}:
        return

    try:
        parsed_ip = ip_address(normalized_hostname)
    except ValueError as exc:
        msg = (
            "storage-smoke endpoint must target a local MinIO endpoint "
            "(localhost, loopback IP, or minio)"
        )
        raise StorageSmokeError(msg) from exc
    if parsed_ip.is_loopback:
        return

    msg = (
        "storage-smoke endpoint must target a local MinIO endpoint "
        "(localhost, loopback IP, or minio)"
    )
    raise StorageSmokeError(msg)


def _canonical_object_uri(endpoint_path: str, bucket: str, key: str) -> str:
    path_prefix = endpoint_path.rstrip("/")
    raw_path = f"{path_prefix}/{bucket}/{key}" if path_prefix else f"/{bucket}/{key}"
    return quote(raw_path, safe="/-_.~")


def _canonical_headers(headers: Mapping[str, str]) -> tuple[str, str]:
    normalized = {name.lower(): " ".join(value.strip().split()) for name, value in headers.items()}
    signed_header_names = sorted(normalized)
    canonical_headers = "".join(
        f"{header_name}:{normalized[header_name]}\n" for header_name in signed_header_names
    )
    return canonical_headers, ";".join(signed_header_names)


def _signing_key(secret_key: str, date_scope: str, region: str) -> bytes:
    date_key = hmac.new(f"AWS4{secret_key}".encode(), date_scope.encode("utf-8"), sha256)
    region_key = hmac.new(date_key.digest(), region.encode("utf-8"), sha256)
    service_key = hmac.new(region_key.digest(), b"s3", sha256)
    return hmac.new(service_key.digest(), b"aws4_request", sha256).digest()


def _validate_smoke_metadata(actual: Mapping[str, str], expected: Mapping[str, str]) -> None:
    mismatches = [
        key for key, expected_value in expected.items() if actual.get(key) != expected_value
    ]
    if mismatches:
        fields = ", ".join(mismatches)
        msg = f"storage smoke metadata mismatch: {fields}"
        raise StorageSmokeError(msg)


def _validate_payload_matches_object_storage(
    raw_artifact: Mapping[str, object],
    *,
    bucket: str,
    object_key: str,
) -> None:
    expected = {
        "object_bucket": bucket,
        "object_key": object_key,
        "raw_artifact_path": object_key,
    }
    mismatches = [
        key for key, expected_value in expected.items() if raw_artifact.get(key) != expected_value
    ]
    if mismatches:
        fields = ", ".join(mismatches)
        msg = f"storage smoke DB payload mismatch: {fields}"
        raise StorageSmokeError(msg)


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    return value
