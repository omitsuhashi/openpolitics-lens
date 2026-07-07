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

create table if not exists audit_finding_candidates (
    audit_finding_candidate_id uuid primary key,
    source_document_id uuid not null references source_documents (source_document_id)
        on delete restrict,
    claim_type text not null default 'audit_finding_candidate_observed'
        check (claim_type = 'audit_finding_candidate_observed'),
    source_type text not null check (
        source_type in (
            'financial_aid_organization_audit_report',
            'comprehensive_external_audit_report',
            'audit_measure_status_report'
        )
    ),
    fiscal_year text not null,
    audited_entity text not null,
    finding_text text not null,
    measure_status text not null,
    evidence_item_ids uuid[] not null check (cardinality(evidence_item_ids) > 0),
    field_evidence_item_ids jsonb not null,
    review_state text not null default 'machine_extracted'
        check (review_state in ('machine_extracted', 'human_verified', 'rejected')),
    created_at timestamptz not null default now()
);

create index if not exists audit_finding_candidates_source_document_idx
    on audit_finding_candidates (source_document_id);

comment on table audit_finding_candidates is
    'Official audit source findings kept separate from app-calculated review signals.';
comment on column audit_finding_candidates.claim_type is
    'Candidate claim type is audit_finding_candidate_observed and is not reused for app-calculated review signal candidates.';
comment on column audit_finding_candidates.finding_text is
    'Official finding wording copied from source evidence without app-side evaluation labels.';
comment on column audit_finding_candidates.evidence_item_ids is
    'EvidenceItem IDs for official source spans that support this candidate.';
comment on column audit_finding_candidates.field_evidence_item_ids is
    'JSON object mapping official fields such as fiscal_year, audited_entity, finding_text, and measure_status to EvidenceItem IDs.';

create table if not exists spending_review_signal_candidates (
    spending_review_signal_candidate_id uuid primary key,
    claim_type text not null default 'app_calculated_review_signal_candidate'
        check (claim_type = 'app_calculated_review_signal_candidate'),
    signal_type text not null,
    target_ref text not null,
    method_version text not null,
    supporting_evidence_item_ids uuid[] not null
        check (cardinality(supporting_evidence_item_ids) > 0),
    counter_evidence_item_ids uuid[] not null default array[]::uuid[],
    limitations text[] not null check (cardinality(limitations) > 0),
    computed_at timestamptz not null,
    review_state text not null default 'needs_human_review'
        check (review_state in ('needs_human_review', 'human_verified', 'rejected')),
    public_visibility text not null default 'internal_only'
        check (public_visibility = 'internal_only'),
    created_at timestamptz not null default now()
);

create index if not exists spending_review_signal_candidates_target_ref_idx
    on spending_review_signal_candidates (target_ref);

comment on table spending_review_signal_candidates is
    'Internal-only app-calculated spending review signal candidates; not public SpendingReviewSignal rows and not scoring output.';
comment on column spending_review_signal_candidates.claim_type is
    'Candidate claim type is app_calculated_review_signal_candidate and is not reused for official audit finding candidates.';
comment on column spending_review_signal_candidates.method_version is
    'Versioned app method used to compute this internal candidate.';
comment on column spending_review_signal_candidates.supporting_evidence_item_ids is
    'EvidenceItem IDs that support the app-calculated candidate.';
comment on column spending_review_signal_candidates.counter_evidence_item_ids is
    'EvidenceItem IDs that weaken or counter the app-calculated candidate.';
comment on column spending_review_signal_candidates.limitations is
    'Explicit limitations required before review; candidates do not assert waste, fraud, illegality, or score.';
comment on column spending_review_signal_candidates.public_visibility is
    'Guard fixed to internal_only so Phase 0 candidates do not feed public UI, score, or ranking.';
