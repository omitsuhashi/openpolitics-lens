create table if not exists source_documents (
    source_document_id uuid primary key,
    raw_artifact_id uuid not null,
    source_system text not null,
    source_type text not null,
    canonical_url text not null,
    title text not null,
    published_at timestamptz,
    retrieved_at timestamptz not null,
    raw_artifact_path text not null,
    content_hash text not null check (content_hash ~ '^[0-9a-f]{64}$'),
    license_note text not null,
    source_reliability text not null,
    jurisdiction_id text not null,
    source_family text not null,
    language text not null,
    created_at timestamptz not null default now(),
    constraint source_documents_raw_artifact_fk
        foreign key (raw_artifact_id, raw_artifact_path, jurisdiction_id, source_family)
        references raw_artifacts (raw_artifact_id, raw_artifact_path, jurisdiction_id, source_family)
        on delete restrict,
    unique (canonical_url, source_type, content_hash)
);

create index if not exists source_documents_source_family_idx
    on source_documents (jurisdiction_id, source_family, source_type);

comment on table source_documents is
    'Normalized public source documents promoted from ingest source document candidates.';
comment on column source_documents.source_reliability is
    'Initial reliability label for official source pages.';

create table if not exists evidence_items (
    evidence_item_id uuid primary key,
    source_document_id uuid not null references source_documents (source_document_id)
        on delete restrict,
    location_type text not null check (
        location_type in ('html_selector', 'page_span', 'text_offset', 'table_cell', 'api_record')
    ),
    location_value text not null,
    source_span_start integer not null check (source_span_start >= 0),
    source_span_end integer not null check (source_span_end >= source_span_start),
    quote_text text not null,
    normalized_text text not null,
    raw_artifact_path text not null,
    extraction_method text not null,
    confidence numeric(5,4) not null check (confidence >= 0 and confidence <= 1),
    created_at timestamptz not null default now(),
    unique (
        source_document_id,
        location_type,
        location_value,
        source_span_start,
        source_span_end,
        extraction_method
    )
);

create index if not exists evidence_items_source_document_idx
    on evidence_items (source_document_id);

comment on table evidence_items is
    'Machine-extracted source spans that support directly observable claims.';
comment on column evidence_items.raw_artifact_path is
    'Back-reference to the immutable raw artifact path used for source inspection.';

create table if not exists evidence_claims (
    evidence_claim_id uuid primary key,
    evidence_item_id uuid not null references evidence_items (evidence_item_id)
        on delete restrict,
    claim_type text not null check (claim_type in ('grant_program_page_title_observed')),
    subject_ref text not null,
    predicate text not null check (predicate in ('observed_page_title')),
    object_ref text,
    object_value text not null,
    event_date date,
    amount numeric,
    currency text,
    review_state text not null default 'machine_extracted'
        check (review_state in ('machine_extracted', 'human_verified', 'rejected')),
    created_at timestamptz not null default now(),
    unique (evidence_item_id, claim_type, predicate, object_value)
);

create index if not exists evidence_claims_evidence_item_idx
    on evidence_claims (evidence_item_id);

comment on table evidence_claims is
    'Minimal claims directly observable from evidence items; initial scope is page title observation.';
