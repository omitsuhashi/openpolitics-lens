from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord, JsonDict


@dataclass(frozen=True, slots=True)
class FetchManifestDbRows:
    raw_artifact: JsonDict
    source_document_candidate: JsonDict


def build_fetch_manifest_db_rows(
    record: FetchManifestRecord,
    *,
    object_bucket: str,
) -> FetchManifestDbRows:
    raw_artifact_id = str(
        uuid5(
            NAMESPACE_URL,
            f"raw_artifact:{object_bucket}:{record.raw_artifact_path}:{record.content_hash}",
        )
    )
    candidate = record.source_document_candidate

    raw_artifact = {
        "raw_artifact_id": raw_artifact_id,
        "jurisdiction_id": record.connector.jurisdiction.jurisdiction_id,
        "source_system": record.connector.source_family.source_system,
        "source_family": record.connector.source_family.source_family,
        "connector_id": record.connector.connector_id,
        "connector_version": record.connector.connector_version,
        "canonical_url": record.canonical_url,
        "fetched_at": record.fetched_at,
        "http_status": record.http_status,
        "content_hash": record.content_hash,
        "hash_algorithm": "sha256",
        "media_type": record.media_type,
        "byte_size": record.byte_size,
        "object_bucket": object_bucket,
        "object_key": record.raw_artifact_path,
        "raw_artifact_path": record.raw_artifact_path,
        "rate_limit_policy": record.connector.rate_limit_policy,
        "terms_note": record.connector.terms_note,
    }
    source_document_candidate = {
        "raw_artifact_id": raw_artifact_id,
        "canonical_url": candidate.canonical_url,
        "title": candidate.title,
        "source_type": candidate.source_type,
        "jurisdiction_id": candidate.jurisdiction_id,
        "source_family": candidate.source_family,
        "language": candidate.language,
        "retrieved_at": candidate.retrieved_at,
        "raw_artifact_path": candidate.raw_artifact_path,
    }

    return FetchManifestDbRows(
        raw_artifact=raw_artifact,
        source_document_candidate=source_document_candidate,
    )
