from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path


def content_sha256(content: bytes) -> str:
    return sha256(content).hexdigest()


def _validate_path_component(value: str, field_name: str) -> None:
    if not value:
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
    if value in {".", ".."} or "/" in value or "\\" in value:
        msg = f"{field_name} must be a single path component"
        raise ValueError(msg)


def _normalize_extension(extension: str) -> str:
    normalized = extension.removeprefix(".").lower()
    _validate_path_component(normalized, "extension")
    return normalized


@dataclass(frozen=True, slots=True)
class RawArtifactWrite:
    content_hash: str
    relative_path: Path
    absolute_path: Path
    byte_size: int


class FileSystemOutputWriter:
    def __init__(self, output_root: str | Path) -> None:
        self.output_root = Path(output_root)

    def raw_artifact_relative_path(
        self,
        *,
        content: bytes,
        jurisdiction_id: str,
        source_family: str,
        fetched_at: datetime,
        extension: str,
    ) -> Path:
        _validate_path_component(jurisdiction_id, "jurisdiction_id")
        _validate_path_component(source_family, "source_family")
        normalized_extension = _normalize_extension(extension)
        digest = content_sha256(content)

        return (
            Path("raw")
            / jurisdiction_id
            / source_family
            / f"{fetched_at:%Y}"
            / f"{fetched_at:%m}"
            / f"{digest}.{normalized_extension}"
        )

    def write_raw_artifact(
        self,
        *,
        content: bytes,
        jurisdiction_id: str,
        source_family: str,
        fetched_at: datetime,
        extension: str,
    ) -> RawArtifactWrite:
        relative_path = self.raw_artifact_relative_path(
            content=content,
            jurisdiction_id=jurisdiction_id,
            source_family=source_family,
            fetched_at=fetched_at,
            extension=extension,
        )
        absolute_path = self.output_root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        return RawArtifactWrite(
            content_hash=content_sha256(content),
            relative_path=relative_path,
            absolute_path=absolute_path,
            byte_size=len(content),
        )
