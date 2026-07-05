create extension if not exists pgcrypto;

create table if not exists raw_artifacts (
    raw_artifact_id uuid primary key default gen_random_uuid(),
    jurisdiction_id text not null,
    source_system text not null,
    source_family text not null,
    connector_id text not null,
    connector_version text not null,
    canonical_url text not null,
    fetched_at timestamptz not null,
    http_status integer not null check (http_status between 100 and 599),
    content_hash text not null check (content_hash ~ '^[0-9a-f]{64}$'),
    hash_algorithm text not null default 'sha256' check (hash_algorithm = 'sha256'),
    media_type text not null,
    byte_size bigint not null check (byte_size >= 0),
    object_bucket text not null,
    object_key text not null,
    raw_artifact_path text not null,
    rate_limit_policy text not null,
    terms_note text not null,
    created_at timestamptz not null default now(),
    unique (object_bucket, object_key),
    check (object_key = raw_artifact_path),
    check (object_key ~ '^raw/[^/]+/[^/]+/[0-9]{4}/[0-9]{2}/[0-9a-f]{64}\.[^/]+$')
);

create index if not exists raw_artifacts_content_hash_idx
    on raw_artifacts (content_hash);

comment on table raw_artifacts is
    'Immutable ingest raw artifacts stored in object storage.';
comment on column raw_artifacts.object_key is
    'Object key contract: raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}';
comment on column raw_artifacts.raw_artifact_path is
    'Manifest-compatible raw artifact path; equal to object_key for object storage-backed ingest.';

create table if not exists source_document_candidates (
    source_document_candidate_id uuid primary key default gen_random_uuid(),
    raw_artifact_id uuid not null references raw_artifacts (raw_artifact_id) on delete restrict,
    canonical_url text not null,
    title text not null,
    source_type text not null,
    jurisdiction_id text not null,
    source_family text not null,
    language text not null,
    retrieved_at timestamptz not null,
    raw_artifact_path text not null,
    created_at timestamptz not null default now(),
    unique (raw_artifact_id, canonical_url, source_type)
);

comment on table source_document_candidates is
    'Ingest-produced candidates for later SourceDocument normalization.';
