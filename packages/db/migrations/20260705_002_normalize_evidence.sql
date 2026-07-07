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
comment on column source_documents.raw_artifact_id is
    'Deterministic ingest raw_artifacts identifier supplied by the normalize caller.';
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
    location_metadata jsonb not null default '{}'::jsonb,
    parse_warnings text[] not null default array[]::text[] check (
        parse_warnings <@ array[
            'pdf_text_layer_missing',
            'ocr_required',
            'ocr_low_confidence',
            'table_structure_inferred',
            'merged_cell_or_header_inferred',
            'multi_page_table',
            'amount_unit_ambiguous',
            'name_or_org_ocr_ambiguous',
            'entity_resolution_required',
            'search_ui_snapshot',
            'meaning_not_interpreted',
            'source_layout_unverified'
        ]::text[]
    ),
    extraction_artifact_path text,
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
comment on column evidence_items.source_span_start is
    'Inclusive raw HTML bytes offset, or PDF / table extraction artifact text offset, for the beginning of quote_text.';
comment on column evidence_items.source_span_end is
    'Exclusive raw HTML bytes offset, or PDF / table extraction artifact text offset, for the end of quote_text.';
comment on column evidence_items.raw_artifact_path is
    'Back-reference to the immutable raw artifact path used for source inspection.';
comment on column evidence_items.location_metadata is
    'Source-family-specific locator metadata such as PDF page/bbox, table cell, or search snapshot conditions.';
comment on column evidence_items.parse_warnings is
    'Phase 0 parser warning catalog for lossy, inferred, ambiguous, or review-required extraction.';
comment on column evidence_items.extraction_artifact_path is
    'Intermediate artifact path for PDF text extraction, OCR output, or table extraction output.';

create table if not exists evidence_claims (
    evidence_claim_id uuid primary key,
    evidence_item_id uuid not null references evidence_items (evidence_item_id)
        on delete restrict,
    claim_type text not null,
    subject_ref text not null,
    predicate text not null,
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
    'Minimal claims directly observable from evidence items.';
comment on column evidence_claims.claim_type is
    'Claim type catalog is enforced by normalize service contract tests. Initial Phase 0 catalog includes grant_program_page_title_observed, subsidy_program_candidate_observed, assembly_member_name_observed, bill_decision_observed, petition_status_observed, speech_text_observed, election_result_observed, political_group_registry_observed, political_fund_report_metadata_observed, budget_document_metadata_observed, budget_table_cell_observed, procurement_search_row_observed, audit_report_finding_text_observed, and audit_measure_status_observed.';
comment on column evidence_claims.predicate is
    'Predicate catalog is enforced by normalize service contract tests and paired with claim_type in code.';
