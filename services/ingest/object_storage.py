from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Protocol

from ingest.filesystem import _normalize_extension, _validate_path_component, content_sha256


class ObjectStorageClient(Protocol):
    def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class ObjectStorageWrite:
    content_hash: str
    object_key: str
    raw_artifact_path: str
    byte_size: int


class ObjectStorageOutputWriter:
    def __init__(self, *, client: ObjectStorageClient, bucket: str) -> None:
        _validate_path_component(bucket, "bucket")
        self.client = client
        self.bucket = bucket

    def raw_artifact_object_key(
        self,
        *,
        content: bytes,
        jurisdiction_id: str,
        source_family: str,
        fetched_at: datetime,
        extension: str,
    ) -> str:
        _validate_path_component(jurisdiction_id, "jurisdiction_id")
        _validate_path_component(source_family, "source_family")
        normalized_extension = _normalize_extension(extension)
        digest = content_sha256(content)

        return (
            PurePosixPath("raw")
            / jurisdiction_id
            / source_family
            / f"{fetched_at:%Y}"
            / f"{fetched_at:%m}"
            / f"{digest}.{normalized_extension}"
        ).as_posix()

    def write_raw_artifact(
        self,
        *,
        content: bytes,
        jurisdiction_id: str,
        source_family: str,
        fetched_at: datetime,
        extension: str,
        media_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectStorageWrite:
        digest = content_sha256(content)
        object_key = self.raw_artifact_object_key(
            content=content,
            jurisdiction_id=jurisdiction_id,
            source_family=source_family,
            fetched_at=fetched_at,
            extension=extension,
        )
        object_metadata = {
            "content_hash": digest,
            "hash_algorithm": "sha256",
            "jurisdiction_id": jurisdiction_id,
            "source_family": source_family,
        }
        if metadata is not None:
            object_metadata.update(metadata)

        self.client.put_object(
            bucket=self.bucket,
            key=object_key,
            body=content,
            content_type=media_type,
            metadata=object_metadata,
        )

        return ObjectStorageWrite(
            content_hash=digest,
            object_key=object_key,
            raw_artifact_path=object_key,
            byte_size=len(content),
        )
