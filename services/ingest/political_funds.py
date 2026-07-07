from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord, JsonDict, SourceDocumentCandidate
from ingest.phase0_sources import (
    LOCAL_FIXTURE_OPERATION,
    PHASE0_SOURCE_REGISTRY,
    FixtureMetadata,
)
from normalize.contracts import (
    EvidenceClaim,
    EvidenceItem,
    SourceDocument,
    build_observed_claim,
    can_promote_to_evidence_claim,
)

TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY = "tokyo_political_funds"
_FIXTURE_FETCHED_AT = datetime(2026, 7, 7, 0, 0, tzinfo=UTC)
_CONNECTOR = PHASE0_SOURCE_REGISTRY[TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY].connector


def _stable_uuid(*parts: object) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join(str(part) for part in parts)))


def _fixture_hash(fixture_id: str) -> str:
    return sha256(fixture_id.encode("utf-8")).hexdigest()


PHASE0_POLITICAL_FUNDS_FIXTURES: tuple[FixtureMetadata, ...] = (
    FixtureMetadata(
        fixture_id="tokyo-political-funds-report-index-2026-fixture",
        source_family=TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY,
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku/",
        fetched_at=_FIXTURE_FETCHED_AT,
        media_type="text/html; charset=utf-8",
        byte_size=4096,
        content_hash=_fixture_hash("tokyo-political-funds-report-index-2026-fixture"),
        source_type="political_fund_report_index",
        expected_evidence_item_count=2,
        operations=(LOCAL_FIXTURE_OPERATION,),
    ),
    FixtureMetadata(
        fixture_id="tokyo-political-funds-group-registry-2026-fixture",
        source_family=TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY,
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/organization/seijidantai/",
        fetched_at=_FIXTURE_FETCHED_AT,
        media_type="text/html; charset=utf-8",
        byte_size=6144,
        content_hash=_fixture_hash("tokyo-political-funds-group-registry-2026-fixture"),
        source_type="political_group_registry",
        expected_evidence_item_count=2,
        operations=(LOCAL_FIXTURE_OPERATION,),
    ),
    FixtureMetadata(
        fixture_id="tokyo-political-funds-pdf-samples-2026-fixture",
        source_family=TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY,
        canonical_url=(
            "https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku/pdf-sample-index/"
        ),
        fetched_at=_FIXTURE_FETCHED_AT,
        media_type="application/pdf",
        byte_size=32768,
        content_hash=_fixture_hash("tokyo-political-funds-pdf-samples-2026-fixture"),
        source_type="political_fund_report_pdf_sample",
        expected_evidence_item_count=6,
        operations=(LOCAL_FIXTURE_OPERATION,),
    ),
)


@dataclass(frozen=True, slots=True)
class PoliticalFundsFixtureProbe:
    raw_artifacts: tuple[FetchManifestRecord, ...]
    source_documents: tuple[SourceDocument, ...]
    evidence_items: tuple[EvidenceItem, ...]
    evidence_claims: tuple[EvidenceClaim, ...]
    non_goal_guards: JsonDict

    @property
    def source_document_candidates(self) -> tuple[SourceDocumentCandidate, ...]:
        return tuple(record.source_document_candidate for record in self.raw_artifacts)

    @property
    def evidence_item_by_id(self) -> dict[str, EvidenceItem]:
        return {item.evidence_item_id: item for item in self.evidence_items}

    @property
    def review_required_count(self) -> int:
        return sum(1 for item in self.evidence_items if item.location_metadata["review_required"])


@dataclass(frozen=True, slots=True)
class _PoliticalFundsSampleSpec:
    fixture_role: str
    source_type: str
    title: str
    canonical_url: str
    media_type: str
    evidence_text: str
    claim_type: str | None
    confidence: float
    review_required: bool
    text_layer: str
    ocr_required: bool
    parse_warnings: tuple[str, ...]
    page_number: int
    row_index: int
    column_index: int


_SAMPLE_SPECS: tuple[_PoliticalFundsSampleSpec, ...] = (
    _PoliticalFundsSampleSpec(
        fixture_role="political_group_registry",
        source_type="political_group_registry",
        title="政治団体名簿 令和8年 index fixture",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/organization/seijidantai/2026-01",
        media_type="text/html; charset=utf-8",
        evidence_text="政治団体名簿掲載: 東京政策研究会",
        claim_type="political_group_registry_observed",
        confidence=0.92,
        review_required=False,
        text_layer="html",
        ocr_required=False,
        parse_warnings=("table_structure_inferred", "entity_resolution_required"),
        page_number=1,
        row_index=1,
        column_index=2,
    ),
    _PoliticalFundsSampleSpec(
        fixture_role="political_group_registry",
        source_type="political_group_registry",
        title="政治団体名簿 令和8年 update fixture",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/organization/seijidantai/2026-02",
        media_type="text/html; charset=utf-8",
        evidence_text="政治団体名簿掲載: 都民政策フォーラム",
        claim_type="political_group_registry_observed",
        confidence=0.91,
        review_required=False,
        text_layer="html",
        ocr_required=False,
        parse_warnings=("table_structure_inferred", "entity_resolution_required"),
        page_number=1,
        row_index=2,
        column_index=2,
    ),
    _PoliticalFundsSampleSpec(
        fixture_role="political_fund_report_index",
        source_type="political_fund_report_index",
        title="政治資金収支報告書 index 令和8年 fixture",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku/2026-01",
        media_type="text/html; charset=utf-8",
        evidence_text="令和8年分 政治資金収支報告書 PDF sample A",
        claim_type="political_fund_report_metadata_observed",
        confidence=0.93,
        review_required=False,
        text_layer="html",
        ocr_required=False,
        parse_warnings=("table_structure_inferred",),
        page_number=1,
        row_index=3,
        column_index=1,
    ),
    _PoliticalFundsSampleSpec(
        fixture_role="political_fund_report_index",
        source_type="political_fund_report_index",
        title="政治資金収支報告書 index 令和8年 supplemental fixture",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku/2026-02",
        media_type="text/html; charset=utf-8",
        evidence_text="令和8年分 政治資金収支報告書 PDF sample B",
        claim_type="political_fund_report_metadata_observed",
        confidence=0.93,
        review_required=False,
        text_layer="html",
        ocr_required=False,
        parse_warnings=("table_structure_inferred",),
        page_number=1,
        row_index=4,
        column_index=1,
    ),
    *(
        _PoliticalFundsSampleSpec(
            fixture_role="political_fund_report_pdf_sample",
            source_type="political_fund_report_pdf_sample",
            title=f"政治資金収支報告書 PDF sample {sample_number}",
            canonical_url=(
                "https://www.senkyo.metro.tokyo.lg.jp/organization/"
                f"shuushihoukoku/pdf-fixture-{sample_number}.pdf"
            ),
            media_type="application/pdf",
            evidence_text=f"OCR候補 行{sample_number}: 団体名・氏名・金額の要確認セル",
            claim_type=None,
            confidence=0.62 if sample_number % 2 else 0.74,
            review_required=True,
            text_layer="missing" if sample_number % 2 else "partial",
            ocr_required=sample_number % 2 == 1,
            parse_warnings=(
                "ocr_required" if sample_number % 2 == 1 else "pdf_text_layer_missing",
                "table_structure_inferred",
                "amount_unit_ambiguous",
                "name_or_org_ocr_ambiguous",
                "entity_resolution_required",
            ),
            page_number=sample_number,
            row_index=sample_number + 1,
            column_index=3,
        )
        for sample_number in range(1, 7)
    ),
)


def _raw_artifact_path(spec: _PoliticalFundsSampleSpec, content_hash: str) -> str:
    extension = "pdf" if spec.media_type == "application/pdf" else "html"
    return f"raw/jp-tokyo/tokyo_political_funds/2026/07/{content_hash}.{extension}"


def _build_record(spec: _PoliticalFundsSampleSpec) -> FetchManifestRecord:
    content_hash = _fixture_hash(spec.canonical_url)
    raw_artifact_path = _raw_artifact_path(spec, content_hash)
    candidate = SourceDocumentCandidate(
        canonical_url=spec.canonical_url,
        title=spec.title,
        source_type=spec.source_type,
        jurisdiction_id=_CONNECTOR.jurisdiction.jurisdiction_id,
        source_family=TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY,
        language="ja",
        retrieved_at=_FIXTURE_FETCHED_AT,
        raw_artifact_path=raw_artifact_path,
    )
    return FetchManifestRecord(
        connector=_CONNECTOR,
        canonical_url=spec.canonical_url,
        fetched_at=_FIXTURE_FETCHED_AT,
        http_status=200,
        content_hash=content_hash,
        media_type=spec.media_type,
        byte_size=len(spec.evidence_text.encode("utf-8")) + 1024,
        raw_artifact_path=raw_artifact_path,
        source_document_candidate=candidate,
    )


def _build_source_document(record: FetchManifestRecord) -> SourceDocument:
    candidate = record.source_document_candidate
    raw_artifact_id = _stable_uuid("raw_artifact", record.raw_artifact_path, record.content_hash)
    source_document_id = _stable_uuid(
        "source_document",
        raw_artifact_id,
        candidate.source_type,
        candidate.canonical_url,
    )
    return SourceDocument(
        source_document_id=source_document_id,
        raw_artifact_id=raw_artifact_id,
        source_system=record.connector.source_family.source_system,
        source_type=candidate.source_type,
        canonical_url=candidate.canonical_url,
        title=candidate.title,
        published_at=None,
        retrieved_at=candidate.retrieved_at,
        raw_artifact_path=candidate.raw_artifact_path,
        content_hash=record.content_hash,
        license_note=record.connector.terms_note,
        source_reliability="official_source",
        jurisdiction_id=candidate.jurisdiction_id,
        source_family=candidate.source_family,
        language=candidate.language,
    )


def _build_evidence_item(
    spec: _PoliticalFundsSampleSpec,
    source_document: SourceDocument,
) -> EvidenceItem:
    source_span_start = spec.row_index * 100
    source_span_end = source_span_start + len(spec.evidence_text)
    extraction_artifact_path = None
    extraction_method = "html_table_fixture"
    if spec.media_type == "application/pdf":
        extraction_method = "pdf_table_probe_fixture"
        extraction_artifact_path = (
            "derived/jp-tokyo/tokyo_political_funds/2026/07/"
            f"{source_document.content_hash}-table.json"
        )

    return EvidenceItem(
        evidence_item_id=_stable_uuid(
            "political_funds_evidence_item",
            source_document.source_document_id,
            spec.fixture_role,
            spec.row_index,
            spec.evidence_text,
        ),
        source_document_id=source_document.source_document_id,
        location_type="table_cell",
        location_value=f"page[{spec.page_number}]/table[1]/row[{spec.row_index}]/cell[{spec.column_index}]",
        source_span_start=source_span_start,
        source_span_end=source_span_end,
        quote_text=spec.evidence_text,
        normalized_text=spec.evidence_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method=extraction_method,
        confidence=spec.confidence,
        location_metadata={
            "fixture_role": spec.fixture_role,
            "page_number": spec.page_number,
            "table_index": 1,
            "row_index": spec.row_index,
            "column_index": spec.column_index,
            "table_locator": {
                "page_number": spec.page_number,
                "table_index": 1,
                "row_index": spec.row_index,
                "column_index": spec.column_index,
            },
            "text_layer": spec.text_layer,
            "ocr_required": spec.ocr_required,
            "review_required": spec.review_required,
            "direct_observation": spec.claim_type is not None,
        },
        parse_warnings=spec.parse_warnings,
        extraction_artifact_path=extraction_artifact_path,
    )


def _build_claim(
    spec: _PoliticalFundsSampleSpec,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
) -> EvidenceClaim | None:
    if spec.claim_type is None or not can_promote_to_evidence_claim(evidence_item):
        return None

    return build_observed_claim(
        evidence_claim_id=_stable_uuid(
            "political_funds_evidence_claim",
            evidence_item.evidence_item_id,
            spec.claim_type,
        ),
        claim_type=spec.claim_type,
        subject_ref=source_document.source_document_id,
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=TOKYO_POLITICAL_FUNDS_SOURCE_FAMILY,
    )


def build_tokyo_political_funds_fixture_probe() -> PoliticalFundsFixtureProbe:
    records = tuple(_build_record(spec) for spec in _SAMPLE_SPECS)
    source_documents = tuple(_build_source_document(record) for record in records)
    evidence_items = tuple(
        _build_evidence_item(spec, source_document)
        for spec, source_document in zip(_SAMPLE_SPECS, source_documents, strict=True)
    )
    claims = tuple(
        claim
        for claim in (
            _build_claim(spec, source_document, evidence_item)
            for spec, source_document, evidence_item in zip(
                _SAMPLE_SPECS,
                source_documents,
                evidence_items,
                strict=True,
            )
        )
        if claim is not None
    )

    return PoliticalFundsFixtureProbe(
        raw_artifacts=records,
        source_documents=source_documents,
        evidence_items=evidence_items,
        evidence_claims=claims,
        non_goal_guards={
            "FundingContact": "not_generated",
            "PublicMoneyFlow": "not_generated",
            "SpendingReviewSignal": "not_generated",
            "policy_stance": "not_interpreted",
            "semantic_classification": "not_interpreted",
        },
    )


def can_generate_funding_contact_from_political_funds_probe(
    _probe: PoliticalFundsFixtureProbe,
) -> bool:
    return False
