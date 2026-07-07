import re
from dataclasses import dataclass
from html import unescape
from uuid import NAMESPACE_URL, uuid5

from ingest.contracts import FetchManifestRecord
from normalize.contracts import (
    EvidenceClaim,
    EvidenceItem,
    JsonDict,
    NormalizeResult,
    SourceDocument,
    build_observed_claim,
)


@dataclass(frozen=True, slots=True)
class _ExtractedTitle:
    quote_text: str
    normalized_text: str
    source_span_start: int
    source_span_end: int


_TITLE_PATTERN = re.compile(rb"<title\b[^>]*>(?P<title>.*?)</title\s*>", re.IGNORECASE | re.DOTALL)


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _stable_uuid(*parts: object) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join(str(part) for part in parts)))


def _validate_candidate_invariants(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    expected_values = {
        "canonical_url": record.canonical_url,
        "raw_artifact_path": record.raw_artifact_path,
        "jurisdiction_id": record.connector.jurisdiction.jurisdiction_id,
        "source_family": record.connector.source_family.source_family,
    }
    actual_values = {
        "canonical_url": candidate.canonical_url,
        "raw_artifact_path": candidate.raw_artifact_path,
        "jurisdiction_id": candidate.jurisdiction_id,
        "source_family": candidate.source_family,
    }

    mismatches = [
        field_name
        for field_name, expected_value in expected_values.items()
        if actual_values[field_name] != expected_value
    ]
    if mismatches:
        fields = ", ".join(mismatches)
        msg = f"source_document_candidate invariant mismatch: {fields}"
        raise ValueError(msg)


def _validate_grant_program_page_input(record: FetchManifestRecord) -> None:
    candidate = record.source_document_candidate
    if candidate.source_type != "grant_program_page":
        msg = f"unsupported source_type for grant page normalization: {candidate.source_type}"
        raise ValueError(msg)

    if "text/html" not in record.media_type.lower():
        msg = f"unsupported media_type for grant page normalization: {record.media_type}"
        raise ValueError(msg)


def _extract_title(raw_html: bytes) -> _ExtractedTitle:
    match = _TITLE_PATTERN.search(raw_html)
    if match is None:
        msg = "grant program page title is required"
        raise ValueError(msg)

    title_start, title_end = match.span("title")
    title_bytes = raw_html[title_start:title_end]
    stripped_title_bytes = title_bytes.strip()
    leading_whitespace = len(title_bytes) - len(title_bytes.lstrip())
    source_span_start = title_start + leading_whitespace
    source_span_end = source_span_start + len(stripped_title_bytes)
    quote_text = stripped_title_bytes.decode("utf-8")
    normalized_text = _collapse_whitespace(unescape(quote_text))
    if not normalized_text:
        msg = "grant program page title is empty"
        raise ValueError(msg)

    return _ExtractedTitle(
        quote_text=quote_text,
        normalized_text=normalized_text,
        source_span_start=source_span_start,
        source_span_end=source_span_end,
    )


def _promote_source_document(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    title: str,
) -> SourceDocument:
    candidate = record.source_document_candidate
    source_document_id = _stable_uuid(
        "source_document",
        raw_artifact_id,
        record.connector.source_family.source_system,
        candidate.source_type,
        candidate.canonical_url,
        record.content_hash,
    )

    return SourceDocument(
        source_document_id=source_document_id,
        raw_artifact_id=raw_artifact_id,
        source_system=record.connector.source_family.source_system,
        source_type=candidate.source_type,
        canonical_url=candidate.canonical_url,
        title=title,
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


def _build_title_evidence_item(
    *,
    source_document: SourceDocument,
    extracted_title: _ExtractedTitle,
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        "html_title",
        extracted_title.source_span_start,
        extracted_title.source_span_end,
        extracted_title.quote_text,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type="html_selector",
        location_value="title",
        source_span_start=extracted_title.source_span_start,
        source_span_end=extracted_title.source_span_end,
        quote_text=extracted_title.quote_text,
        normalized_text=extracted_title.normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method="html_title",
        confidence=1.0,
    )


def _build_title_claim(
    *,
    source_document: SourceDocument,
    evidence_item: EvidenceItem,
) -> EvidenceClaim:
    evidence_claim_id = _stable_uuid(
        "evidence_claim",
        evidence_item.evidence_item_id,
        "grant_program_page_title_observed",
        evidence_item.normalized_text,
    )

    return build_observed_claim(
        evidence_claim_id=evidence_claim_id,
        claim_type="grant_program_page_title_observed",
        subject_ref=source_document.source_document_id,
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
    )


def _build_probe_evidence_item(
    *,
    source_document: SourceDocument,
    location_type: str,
    location_value: str,
    quote_text: str,
    normalized_text: str,
    extraction_method: str,
    confidence: float,
    location_metadata: JsonDict,
    parse_warnings: tuple[str, ...],
) -> EvidenceItem:
    evidence_item_id = _stable_uuid(
        "evidence_item",
        source_document.source_document_id,
        location_type,
        location_value,
        normalized_text,
    )

    return EvidenceItem(
        evidence_item_id=evidence_item_id,
        source_document_id=source_document.source_document_id,
        location_type=location_type,
        location_value=location_value,
        source_span_start=0,
        source_span_end=len(quote_text.encode("utf-8")),
        quote_text=quote_text,
        normalized_text=normalized_text,
        raw_artifact_path=source_document.raw_artifact_path,
        extraction_method=extraction_method,
        confidence=confidence,
        location_metadata=location_metadata,
        parse_warnings=parse_warnings,
    )


def _normalize_budget_settlement_record(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    sample_index: int,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=record.source_document_candidate.title,
    )
    if sample_index % 2:
        claim_type = "budget_document_metadata_observed"
        quote_text = f"予算・決算資料 metadata fixture {sample_index:02d}"
        evidence_item = _build_probe_evidence_item(
            source_document=source_document,
            location_type="page_span",
            location_value=f"p.{sample_index}",
            quote_text=quote_text,
            normalized_text=quote_text,
            extraction_method="fixture_budget_index",
            confidence=0.93,
            location_metadata={
                "page_number": sample_index,
                "document_kind": "budget_or_settlement_index",
            },
            parse_warnings=("meaning_not_interpreted",),
        )
    else:
        claim_type = "budget_table_cell_observed"
        quote_text = f"歳出 事業費 {sample_index * 100:,} 千円"
        evidence_item = _build_probe_evidence_item(
            source_document=source_document,
            location_type="table_cell",
            location_value=f"table[1]/row[{sample_index}]/cell[4]",
            quote_text=quote_text,
            normalized_text=quote_text,
            extraction_method="fixture_table_cell",
            confidence=0.86,
            location_metadata={
                "page_number": sample_index,
                "table_index": 1,
                "row_index": sample_index,
                "column_index": 4,
                "unit_note": "fixture states 金額単位 but not normalized",
                "tax_note": "税込・税抜は資料セルから確定しない",
            },
            parse_warnings=(
                "table_structure_inferred",
                "amount_unit_ambiguous",
                "meaning_not_interpreted",
            ),
        )

    evidence_claim = build_observed_claim(
        evidence_claim_id=_stable_uuid(
            "evidence_claim",
            evidence_item.evidence_item_id,
            claim_type,
        ),
        claim_type=claim_type,
        subject_ref=source_document.source_document_id,
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=(evidence_claim,),
    )


def _normalize_procurement_record(
    record: FetchManifestRecord,
    *,
    raw_artifact_id: str,
    sample_index: int,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=record.source_document_candidate.title,
    )
    quote_text = f"委託案件 fixture {sample_index:02d} 株式会社サンプル {sample_index}"
    evidence_item = _build_probe_evidence_item(
        source_document=source_document,
        location_type="api_record",
        location_value=f"result-row-{sample_index}",
        quote_text=quote_text,
        normalized_text=quote_text,
        extraction_method="search_ui_snapshot",
        confidence=0.9,
        location_metadata={
            "search_form_url": "https://www.e-procurement.metro.tokyo.lg.jp/index.jsp",
            "query_parameters": {
                "keyword": "委託",
                "status": "結果公表",
            },
            "page_number": 1,
            "sort_order": "published_at_desc",
            "snapshot_timestamp": "2026-07-07T00:00:00Z",
            "result_row_locator": f"tr[data-fixture-row='{sample_index}']",
            "tax_note": "税込・税抜は検索結果 snapshot から確定しない",
            "vendor_resolution_note": "vendor 名寄せは行わない",
            "contract_match_note": "契約案との突合は行わない",
        },
        parse_warnings=(
            "search_ui_snapshot",
            "amount_unit_ambiguous",
            "entity_resolution_required",
        ),
    )
    evidence_claim = build_observed_claim(
        evidence_claim_id=_stable_uuid(
            "evidence_claim",
            evidence_item.evidence_item_id,
            "procurement_search_row_observed",
        ),
        claim_type="procurement_search_row_observed",
        subject_ref=source_document.source_document_id,
        object_value=evidence_item.normalized_text,
        evidence_item=evidence_item,
        source_family=source_document.source_family,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=(evidence_claim,),
    )


def normalize_p0r008_procurement_budget_fixture(
    records: tuple[FetchManifestRecord, ...],
) -> tuple[NormalizeResult, ...]:
    results: list[NormalizeResult] = []
    source_family_counts: dict[str, int] = {}
    for record in records:
        source_family = record.connector.source_family.source_family
        source_family_counts[source_family] = source_family_counts.get(source_family, 0) + 1
        sample_index = source_family_counts[source_family]
        raw_artifact_id = _stable_uuid(
            "raw_artifact",
            record.raw_artifact_path,
            record.content_hash,
        )

        if source_family == "tokyo_budget_settlement":
            results.append(
                _normalize_budget_settlement_record(
                    record,
                    raw_artifact_id=raw_artifact_id,
                    sample_index=sample_index,
                )
            )
        elif source_family == "tokyo_procurement":
            results.append(
                _normalize_procurement_record(
                    record,
                    raw_artifact_id=raw_artifact_id,
                    sample_index=sample_index,
                )
            )
        else:
            msg = f"unsupported P0R-008 source_family: {source_family}"
            raise ValueError(msg)

    return tuple(results)


def p0r008_procurement_budget_non_goal_guard() -> JsonDict:
    return {
        "blocked_entity_types": [
            "BudgetLine",
            "ContractAward",
            "PublicMoneyFlow",
            "SpendingReviewSignal",
        ],
        "blocked_confirmations": [
            "amount_normalization_confirmation",
            "tax_included_or_excluded_confirmation",
            "vendor_entity_resolution",
            "contract_proposal_match_confirmation",
        ],
    }


def normalize_grant_program_page(
    record: FetchManifestRecord,
    raw_html: bytes,
    *,
    raw_artifact_id: str,
) -> NormalizeResult:
    _validate_candidate_invariants(record)
    _validate_grant_program_page_input(record)
    extracted_title = _extract_title(raw_html)
    source_document = _promote_source_document(
        record,
        raw_artifact_id=raw_artifact_id,
        title=extracted_title.normalized_text,
    )
    evidence_item = _build_title_evidence_item(
        source_document=source_document,
        extracted_title=extracted_title,
    )
    evidence_claim = _build_title_claim(
        source_document=source_document,
        evidence_item=evidence_item,
    )

    return NormalizeResult(
        source_document=source_document,
        evidence_items=(evidence_item,),
        evidence_claims=(evidence_claim,),
    )
