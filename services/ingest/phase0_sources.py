from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from ingest.contracts import (
    ConnectorDefinition,
    FetchManifestRecord,
    JsonDict,
    JurisdictionProfile,
    SourceDocumentCandidate,
    SourceFamily,
)
from ingest.tokyo_audit_reports import TOKYO_AUDIT_REPORTS_CONNECTOR
from ingest.tokyo_metro_grants import TOKYO_METRO_GRANTS_CONNECTOR

NORMAL_TEST_FORBIDDEN_OPERATIONS: frozenset[str] = frozenset(
    {
        "external_network",
        "browser_automation",
        "live_search",
        "pdf_download",
        "ocr_execution",
    }
)
LOCAL_FIXTURE_OPERATION = "local_fixture_read"

_TOKYO_JURISDICTION = JurisdictionProfile(
    jurisdiction_id="jp-tokyo",
    jurisdiction_level="prefecture",
    country_code="JP",
    subdivision_code="JP-13",
    municipality_code=None,
    display_name="東京都",
)
_FIXTURE_FETCHED_AT = datetime(2026, 7, 7, 0, 0, tzinfo=UTC)


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _fixture_hash(fixture_id: str) -> str:
    return sha256(fixture_id.encode("utf-8")).hexdigest()


def _connector(
    *,
    connector_id: str,
    source_family: str,
    source_system: str,
    display_name: str,
    start_url: str,
    terms_note: str,
    connector_version: str = "2026-07-07",
) -> ConnectorDefinition:
    return ConnectorDefinition(
        connector_id=connector_id,
        connector_version=connector_version,
        jurisdiction=_TOKYO_JURISDICTION,
        source_family=SourceFamily(
            source_family=source_family,
            source_system=source_system,
            display_name=display_name,
        ),
        start_url=start_url,
        rate_limit_policy="fixture-only; live acquisition requires a manual gate",
        terms_note=terms_note,
    )


@dataclass(frozen=True, slots=True)
class Phase0SourceRegistryEntry:
    connector: ConnectorDefinition
    source_type: str
    retrieval_method: str
    evidence_granularity: str
    roadmap_source_labels: tuple[str, ...]

    @property
    def source_family(self) -> str:
        return self.connector.source_family.source_family

    def to_json_dict(self) -> JsonDict:
        return {
            **self.connector.identity_json_dict(),
            "start_url": self.connector.start_url,
            "source_type": self.source_type,
            "retrieval_method": self.retrieval_method,
            "terms_note": self.connector.terms_note,
            "evidence_granularity": self.evidence_granularity,
            "roadmap_source_labels": list(self.roadmap_source_labels),
        }


@dataclass(frozen=True, slots=True)
class FixtureMetadata:
    fixture_id: str
    source_family: str
    canonical_url: str
    fetched_at: datetime
    media_type: str
    byte_size: int
    content_hash: str
    source_type: str
    expected_evidence_item_count: int
    operations: tuple[str, ...] = (LOCAL_FIXTURE_OPERATION,)

    def to_json_dict(self) -> JsonDict:
        return {
            "fixture_id": self.fixture_id,
            "source_family": self.source_family,
            "canonical_url": self.canonical_url,
            "fetched_at": _datetime_to_json(self.fetched_at),
            "media_type": self.media_type,
            "byte_size": self.byte_size,
            "content_hash": self.content_hash,
            "source_type": self.source_type,
            "expected_evidence_item_count": self.expected_evidence_item_count,
            "operations": list(self.operations),
        }


@dataclass(frozen=True, slots=True)
class FixtureCoverageTarget:
    source_family: str
    raw_artifact_count: int
    source_document_candidate_count: int
    evidence_item_count: int

    def to_json_dict(self) -> JsonDict:
        return {
            "source_family": self.source_family,
            "raw_artifact_count": self.raw_artifact_count,
            "source_document_candidate_count": self.source_document_candidate_count,
            "evidence_item_count": self.evidence_item_count,
        }


@dataclass(frozen=True, slots=True)
class FixtureCoverageSample:
    source_family: str
    raw_artifact_count: int = 0
    source_document_candidate_count: int = 0
    evidence_item_count: int = 0
    warning_count: int = 0
    review_required_count: int = 0


@dataclass(frozen=True, slots=True)
class FixtureCoverageSummary:
    source_family: str
    raw_artifact_count: int
    source_document_candidate_count: int
    evidence_item_count: int
    warning_count: int
    review_required_count: int
    target: FixtureCoverageTarget

    @property
    def meets_target(self) -> bool:
        return (
            self.raw_artifact_count >= self.target.raw_artifact_count
            and self.source_document_candidate_count >= self.target.source_document_candidate_count
            and self.evidence_item_count >= self.target.evidence_item_count
        )

    def to_json_dict(self) -> JsonDict:
        return {
            "source_family": self.source_family,
            "raw_artifact_count": self.raw_artifact_count,
            "source_document_candidate_count": self.source_document_candidate_count,
            "evidence_item_count": self.evidence_item_count,
            "warning_count": self.warning_count,
            "review_required_count": self.review_required_count,
            "target": self.target.to_json_dict(),
            "meets_target": self.meets_target,
        }


MINIMUM_PHASE0_COMPLETION_SOURCE_FAMILY_COUNT = 5
REQUIRED_PHASE0_COMPLETION_SOURCE_FAMILIES: frozenset[str] = frozenset(
    {
        "tokyo_metro_grants",
        "tokyo_audit_reports",
    }
)
PHASE0_FIXTURE_REPORT_JSON_FILENAME = "phase0-fixture-report.json"
PHASE0_FEASIBILITY_REPORT_RELATIVE_PATH = (
    "knowledge/wiki/syntheses/phase0-source-probe-feasibility-report.md"
)


_SOURCE_NON_GOAL_GUARDS: dict[str, tuple[str, ...]] = {
    "tokyo_assembly_records_bills": (
        "VotePosition は source にない限り生成しない",
        "発言の政策 stance や意味分類は行わない",
    ),
    "tokyo_elections": (
        "人物、政治団体、政党支部、後援会を自動 merge しない",
        "source から直接観測できない Candidate / ElectionResult は確定しない",
    ),
    "tokyo_political_funds": (
        "FundingContact は生成しない",
        "PDF download と OCR 実行は通常検証で行わない",
    ),
    "tokyo_budget_settlement": (
        "BudgetLine は確定 entity として生成しない",
        "PublicMoneyFlow と SpendingReviewSignal は生成しない",
    ),
    "tokyo_procurement": (
        "ContractAward は確定 entity として生成しない",
        "vendor 名寄せと契約案との突合は行わない",
    ),
    "tokyo_metro_grants": (
        "PublicMoneyFlow は生成しない",
        "個別交付先、金額、成果は生成しない",
    ),
    "tokyo_audit_reports": (
        "AuditFindingCandidate は公式文言を保持し、アプリ側評価語を混ぜない",
        "public SpendingReviewSignal、score、ranking は生成しない",
    ),
}


_SOURCE_FAMILY_BLOCKED_REASONS: dict[str, str] = {
    "tokyo_assembly_records_bills": (
        "fixture probe not implemented for assembly records and bill decisions"
    ),
    "tokyo_elections": "fixture probe not implemented for election result and bulletin sources",
    "tokyo_political_funds": "fixture probe not implemented for political funds reports",
    "tokyo_budget_settlement": "fixture probe not implemented for budget and settlement sources",
    "tokyo_procurement": "fixture probe not implemented for procurement search snapshots",
    "tokyo_metro_grants": "SubsidyProgramCandidate 10 sample baseline is not yet present",
    "tokyo_audit_reports": "audit report fixture target is not yet satisfied",
}


@dataclass(frozen=True, slots=True)
class Phase0FixtureReportRow:
    source_family: str
    roadmap_source_labels: tuple[str, ...]
    status: str
    raw_artifact_count: int
    source_document_candidate_count: int
    evidence_item_count: int
    warning_count: int
    review_required_count: int
    target: FixtureCoverageTarget
    non_goal_guard: tuple[str, ...]
    blocked_reason: str | None

    @property
    def meets_target(self) -> bool:
        return self.status == "complete"

    def to_json_dict(self) -> JsonDict:
        return {
            "source_family": self.source_family,
            "roadmap_source_labels": list(self.roadmap_source_labels),
            "status": self.status,
            "raw_artifact_count": self.raw_artifact_count,
            "source_document_candidate_count": self.source_document_candidate_count,
            "evidence_item_count": self.evidence_item_count,
            "warning_count": self.warning_count,
            "review_required_count": self.review_required_count,
            "target": self.target.to_json_dict(),
            "meets_target": self.meets_target,
            "non_goal_guard": list(self.non_goal_guard),
            "blocked_reason": self.blocked_reason,
        }


@dataclass(frozen=True, slots=True)
class Phase0FixtureReport:
    source_families: tuple[Phase0FixtureReportRow, ...]
    minimum_required_source_family_count: int = MINIMUM_PHASE0_COMPLETION_SOURCE_FAMILY_COUNT
    required_source_families: frozenset[str] = REQUIRED_PHASE0_COMPLETION_SOURCE_FAMILIES

    @property
    def achieved_source_families(self) -> tuple[str, ...]:
        return tuple(row.source_family for row in self.source_families if row.meets_target)

    @property
    def achieved_source_family_count(self) -> int:
        return len(self.achieved_source_families)

    @property
    def missing_required_source_families(self) -> tuple[str, ...]:
        achieved = set(self.achieved_source_families)
        return tuple(
            source_family
            for source_family in PHASE0_SOURCE_REGISTRY
            if source_family in self.required_source_families and source_family not in achieved
        )

    @property
    def coverage_source_family_goal_met(self) -> bool:
        return self.achieved_source_family_count >= self.minimum_required_source_family_count

    @property
    def required_source_families_goal_met(self) -> bool:
        return not self.missing_required_source_families

    @property
    def phase0_status(self) -> str:
        if self.coverage_source_family_goal_met and self.required_source_families_goal_met:
            return "complete"
        return "incomplete"

    def to_json_dict(self) -> JsonDict:
        return {
            "phase0_status": self.phase0_status,
            "minimum_required_source_family_count": self.minimum_required_source_family_count,
            "roadmap_source_labels": list(PHASE0_ROADMAP_SOURCE_LABELS),
            "roadmap_source_label_count": len(PHASE0_ROADMAP_SOURCE_LABELS),
            "source_family_count": len(self.source_families),
            "achieved_source_family_count": self.achieved_source_family_count,
            "achieved_source_families": list(self.achieved_source_families),
            "coverage_source_family_goal_met": self.coverage_source_family_goal_met,
            "required_source_families": list(
                source_family
                for source_family in PHASE0_SOURCE_REGISTRY
                if source_family in self.required_source_families
            ),
            "required_source_families_goal_met": self.required_source_families_goal_met,
            "missing_required_source_families": list(self.missing_required_source_families),
            "forbidden_operations_not_used": sorted(NORMAL_TEST_FORBIDDEN_OPERATIONS),
            "source_families": [row.to_json_dict() for row in self.source_families],
        }


PHASE0_SOURCE_REGISTRY: dict[str, Phase0SourceRegistryEntry] = {
    "tokyo_assembly_records_bills": Phase0SourceRegistryEntry(
        connector=_connector(
            connector_id="jp_tokyo.assembly_records_bills.v1",
            source_family="tokyo_assembly_records_bills",
            source_system="tokyo_metropolitan_assembly",
            display_name="東京都議会 会議録・提出議案",
            start_url="https://www.gikai.metro.tokyo.lg.jp/record/",
            terms_note="official Tokyo Metropolitan Assembly public website pages",
        ),
        source_type="meeting_record_or_bill_decision",
        retrieval_method="static_html_index + html_detail + search_ui_snapshot",
        evidence_granularity="meeting_speech_or_bill_decision",
        roadmap_source_labels=(
            "東京都議会 会議録・速記録",
            "東京都議会 提出議案と議決結果",
        ),
    ),
    "tokyo_elections": Phase0SourceRegistryEntry(
        connector=_connector(
            connector_id="jp_tokyo.elections.v1",
            source_family="tokyo_elections",
            source_system="tokyo_metropolitan_election_administration_commission",
            display_name="東京都選挙管理委員会 選挙公報・選挙結果",
            start_url="https://www.senkyo.metro.tokyo.lg.jp/election/togikai-all",
            terms_note="official Tokyo election administration public website pages",
        ),
        source_type="election_result_or_bulletin",
        retrieval_method="static_html_index + html_detail + pdf_metadata",
        evidence_granularity="candidate_or_result_row",
        roadmap_source_labels=("東京都選挙管理委員会 選挙公報・選挙結果",),
    ),
    "tokyo_political_funds": Phase0SourceRegistryEntry(
        connector=_connector(
            connector_id="jp_tokyo.political_funds.v1",
            source_family="tokyo_political_funds",
            source_system="tokyo_metropolitan_election_administration_commission",
            display_name="東京都選挙管理委員会 政治資金収支報告書",
            start_url=(
                "https://www.senkyo.metro.tokyo.lg.jp/organization/"
                "shuushihoukoku-syokan_this_is_branch"
            ),
            terms_note="official Tokyo election administration political funds pages",
        ),
        source_type="political_fund_report_or_group_registry",
        retrieval_method="static_html_index + pdf_batch",
        evidence_granularity="political_group_or_report_metadata",
        roadmap_source_labels=("東京都選挙管理委員会 政治資金収支報告書",),
    ),
    "tokyo_budget_settlement": Phase0SourceRegistryEntry(
        connector=_connector(
            connector_id="jp_tokyo.budget_settlement.v1",
            source_family="tokyo_budget_settlement",
            source_system="tokyo_metropolitan_finance_bureau",
            display_name="東京都財務局 予算・決算",
            start_url="https://www.zaimu.metro.tokyo.lg.jp/zaisei/",
            terms_note="official Tokyo Metropolitan Government finance bureau pages",
        ),
        source_type="budget_or_settlement_document",
        retrieval_method="static_html_index + pdf_batch",
        evidence_granularity="budget_document_or_table_cell",
        roadmap_source_labels=("東京都財務局・電子調達 契約/予算",),
    ),
    "tokyo_procurement": Phase0SourceRegistryEntry(
        connector=_connector(
            connector_id="jp_tokyo.procurement.v1",
            source_family="tokyo_procurement",
            source_system="tokyo_e_procurement_system",
            display_name="東京都電子調達 契約・入札",
            start_url="https://www.e-procurement.metro.tokyo.lg.jp/index.jsp",
            terms_note="official Tokyo e-procurement public website pages",
        ),
        source_type="procurement_search_result_or_bid_result",
        retrieval_method="search_ui_snapshot",
        evidence_granularity="procurement_search_result_row",
        roadmap_source_labels=("東京都財務局・電子調達 契約/予算",),
    ),
    "tokyo_metro_grants": Phase0SourceRegistryEntry(
        connector=TOKYO_METRO_GRANTS_CONNECTOR,
        source_type="grant_program_page",
        retrieval_method="static_html_index + html_detail",
        evidence_granularity="subsidy_program_candidate",
        roadmap_source_labels=("都庁総合ホームページ 助成・補助金",),
    ),
    "tokyo_audit_reports": Phase0SourceRegistryEntry(
        connector=TOKYO_AUDIT_REPORTS_CONNECTOR,
        source_type="audit_report_or_measure_report",
        retrieval_method="static_html_index + pdf_batch",
        evidence_granularity="audit_finding_or_measure_status",
        roadmap_source_labels=("東京都監査事務局 財政援助団体等監査・包括外部監査",),
    ),
}


PHASE0_ROADMAP_SOURCE_LABELS: tuple[str, ...] = tuple(
    dict.fromkeys(
        label for entry in PHASE0_SOURCE_REGISTRY.values() for label in entry.roadmap_source_labels
    )
)


PHASE0_COVERAGE_TARGETS: dict[str, FixtureCoverageTarget] = {
    source_family: FixtureCoverageTarget(
        source_family=source_family,
        raw_artifact_count=10,
        source_document_candidate_count=10,
        evidence_item_count=10,
    )
    for source_family in PHASE0_SOURCE_REGISTRY
}


PHASE0_FIXTURE_CATALOG: dict[str, FixtureMetadata] = {
    source_family: FixtureMetadata(
        fixture_id=f"{source_family}-fixture-baseline",
        source_family=source_family,
        canonical_url=entry.connector.start_url,
        fetched_at=_FIXTURE_FETCHED_AT,
        media_type="text/html; charset=utf-8",
        byte_size=len(entry.connector.start_url.encode("utf-8")),
        content_hash=_fixture_hash(f"{source_family}-fixture-baseline"),
        source_type=entry.source_type,
        expected_evidence_item_count=10 if source_family == "tokyo_audit_reports" else 1,
    )
    for source_family, entry in PHASE0_SOURCE_REGISTRY.items()
}


def _tokyo_election_fixture(
    *,
    fixture_id: str,
    canonical_url: str,
    media_type: str,
    source_type: str,
) -> FixtureMetadata:
    return FixtureMetadata(
        fixture_id=fixture_id,
        source_family="tokyo_elections",
        canonical_url=canonical_url,
        fetched_at=_FIXTURE_FETCHED_AT,
        media_type=media_type,
        byte_size=len(canonical_url.encode("utf-8")),
        content_hash=_fixture_hash(fixture_id),
        source_type=source_type,
        expected_evidence_item_count=1,
    )


TOKYO_ELECTION_RESULT_FIXTURES: tuple[FixtureMetadata, ...] = (
    _tokyo_election_fixture(
        fixture_id="tokyo-elections-result-html-001",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/election/result/sample-001.html",
        media_type="text/html; charset=utf-8",
        source_type="election_result_html",
    ),
    _tokyo_election_fixture(
        fixture_id="tokyo-elections-result-html-002",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/election/result/sample-002.html",
        media_type="text/html; charset=utf-8",
        source_type="election_result_html",
    ),
    _tokyo_election_fixture(
        fixture_id="tokyo-elections-result-html-003",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/election/result/sample-003.html",
        media_type="text/html; charset=utf-8",
        source_type="election_result_html",
    ),
    _tokyo_election_fixture(
        fixture_id="tokyo-elections-result-pdf-004",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/election/result/sample-004.pdf",
        media_type="application/pdf",
        source_type="election_result_pdf",
    ),
    _tokyo_election_fixture(
        fixture_id="tokyo-elections-result-pdf-005",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/election/result/sample-005.pdf",
        media_type="application/pdf",
        source_type="election_result_pdf",
    ),
    _tokyo_election_fixture(
        fixture_id="tokyo-elections-result-pdf-006",
        canonical_url="https://www.senkyo.metro.tokyo.lg.jp/election/result/sample-006.pdf",
        media_type="application/pdf",
        source_type="election_result_pdf",
    ),
)
TOKYO_ELECTION_BULLETIN_METADATA_FIXTURES: tuple[FixtureMetadata, ...] = tuple(
    _tokyo_election_fixture(
        fixture_id=f"tokyo-elections-bulletin-metadata-{index:03}",
        canonical_url=(
            f"https://www.senkyo.metro.tokyo.lg.jp/election/bulletin/sample-{index:03}.json"
        ),
        media_type="application/json",
        source_type="public_bulletin_metadata",
    )
    for index in range(7, 11)
)


def _extension_from_media_type(media_type: str) -> str:
    if "pdf" in media_type:
        return "pdf"
    if "json" in media_type:
        return "json"
    return "html"


def build_tokyo_election_fixture_manifest_records() -> tuple[FetchManifestRecord, ...]:
    connector = PHASE0_SOURCE_REGISTRY["tokyo_elections"].connector
    fixtures = (*TOKYO_ELECTION_RESULT_FIXTURES, *TOKYO_ELECTION_BULLETIN_METADATA_FIXTURES)

    return tuple(
        FetchManifestRecord(
            connector=connector,
            canonical_url=fixture.canonical_url,
            fetched_at=fixture.fetched_at,
            http_status=200,
            content_hash=fixture.content_hash,
            media_type=fixture.media_type,
            byte_size=fixture.byte_size,
            raw_artifact_path=(
                "raw/jp-tokyo/tokyo_elections/2026/07/"
                f"{fixture.content_hash}.{_extension_from_media_type(fixture.media_type)}"
            ),
            source_document_candidate=SourceDocumentCandidate(
                canonical_url=fixture.canonical_url,
                title=fixture.fixture_id,
                source_type=fixture.source_type,
                jurisdiction_id=connector.jurisdiction.jurisdiction_id,
                source_family=connector.source_family.source_family,
                language="ja",
                retrieved_at=fixture.fetched_at,
                raw_artifact_path=(
                    "raw/jp-tokyo/tokyo_elections/2026/07/"
                    f"{fixture.content_hash}.{_extension_from_media_type(fixture.media_type)}"
                ),
            ),
        )
        for fixture in fixtures
    )


def validate_normal_test_fixture_metadata(fixtures: Iterable[FixtureMetadata]) -> None:
    for fixture in fixtures:
        if fixture.source_family not in PHASE0_SOURCE_REGISTRY:
            msg = f"unknown source_family for fixture metadata: {fixture.source_family}"
            raise ValueError(msg)
        if fixture.byte_size <= 0:
            msg = f"fixture byte_size must be positive: {fixture.fixture_id}"
            raise ValueError(msg)
        if len(fixture.content_hash) != 64:
            msg = f"fixture content_hash must be sha256 hex length: {fixture.fixture_id}"
            raise ValueError(msg)
        if LOCAL_FIXTURE_OPERATION not in fixture.operations:
            msg = f"fixture metadata must use local fixture reads: {fixture.fixture_id}"
            raise ValueError(msg)

        forbidden = sorted(set(fixture.operations) & NORMAL_TEST_FORBIDDEN_OPERATIONS)
        if forbidden:
            msg = (
                "normal tests must not perform " + ", ".join(forbidden) + f": {fixture.fixture_id}"
            )
            raise ValueError(msg)


def build_fixture_coverage_sample(
    *,
    source_family: str,
    raw_artifacts: Iterable[object] = (),
    source_document_candidates: Iterable[object] = (),
    evidence_items: Iterable[object] = (),
) -> FixtureCoverageSample:
    if source_family not in PHASE0_SOURCE_REGISTRY:
        msg = f"unknown source_family for fixture coverage sample: {source_family}"
        raise ValueError(msg)

    raw_artifact_count = sum(1 for _item in raw_artifacts)
    source_document_candidate_count = sum(1 for _item in source_document_candidates)
    evidence_item_count = 0
    warning_count = 0
    review_required_count = 0
    for evidence_item in evidence_items:
        evidence_item_count += 1
        warning_count += len(tuple(getattr(evidence_item, "parse_warnings", ())))
        location_metadata = getattr(evidence_item, "location_metadata", {})
        if isinstance(location_metadata, dict) and location_metadata.get("review_required"):
            review_required_count += 1

    return FixtureCoverageSample(
        source_family=source_family,
        raw_artifact_count=raw_artifact_count,
        source_document_candidate_count=source_document_candidate_count,
        evidence_item_count=evidence_item_count,
        warning_count=warning_count,
        review_required_count=review_required_count,
    )


def summarize_phase0_fixture_coverage(
    samples: Iterable[FixtureCoverageSample],
) -> dict[str, FixtureCoverageSummary]:
    counts = {
        source_family: {
            "raw_artifact_count": 0,
            "source_document_candidate_count": 0,
            "evidence_item_count": 0,
            "warning_count": 0,
            "review_required_count": 0,
        }
        for source_family in PHASE0_SOURCE_REGISTRY
    }

    for sample in samples:
        if sample.source_family not in counts:
            msg = f"unknown source_family for fixture coverage sample: {sample.source_family}"
            raise ValueError(msg)
        counts[sample.source_family]["raw_artifact_count"] += sample.raw_artifact_count
        counts[sample.source_family]["source_document_candidate_count"] += (
            sample.source_document_candidate_count
        )
        counts[sample.source_family]["evidence_item_count"] += sample.evidence_item_count
        counts[sample.source_family]["warning_count"] += sample.warning_count
        counts[sample.source_family]["review_required_count"] += sample.review_required_count

    return {
        source_family: FixtureCoverageSummary(
            source_family=source_family,
            raw_artifact_count=source_counts["raw_artifact_count"],
            source_document_candidate_count=source_counts["source_document_candidate_count"],
            evidence_item_count=source_counts["evidence_item_count"],
            warning_count=source_counts["warning_count"],
            review_required_count=source_counts["review_required_count"],
            target=PHASE0_COVERAGE_TARGETS[source_family],
        )
        for source_family, source_counts in counts.items()
    }


def build_phase0_fixture_report(
    summaries: dict[str, FixtureCoverageSummary],
) -> Phase0FixtureReport:
    missing_source_families = set(PHASE0_SOURCE_REGISTRY) - set(summaries)
    if missing_source_families:
        msg = "missing fixture coverage summaries: " + ", ".join(sorted(missing_source_families))
        raise ValueError(msg)

    rows = tuple(
        _build_phase0_fixture_report_row(summary=summaries[source_family])
        for source_family in PHASE0_SOURCE_REGISTRY
    )
    return Phase0FixtureReport(source_families=rows)


def _build_phase0_fixture_report_row(
    *,
    summary: FixtureCoverageSummary,
) -> Phase0FixtureReportRow:
    source_family = summary.source_family
    registry_entry = PHASE0_SOURCE_REGISTRY[source_family]
    status = "complete" if summary.meets_target else "blocked"
    blocked_reason = None if summary.meets_target else _build_blocked_reason(summary)

    return Phase0FixtureReportRow(
        source_family=source_family,
        roadmap_source_labels=registry_entry.roadmap_source_labels,
        status=status,
        raw_artifact_count=summary.raw_artifact_count,
        source_document_candidate_count=summary.source_document_candidate_count,
        evidence_item_count=summary.evidence_item_count,
        warning_count=summary.warning_count,
        review_required_count=summary.review_required_count,
        target=summary.target,
        non_goal_guard=_SOURCE_NON_GOAL_GUARDS[source_family],
        blocked_reason=blocked_reason,
    )


def _build_blocked_reason(summary: FixtureCoverageSummary) -> str:
    target = summary.target
    deficits: list[str] = []
    if summary.raw_artifact_count < target.raw_artifact_count:
        deficits.append(f"RawArtifact {summary.raw_artifact_count}/{target.raw_artifact_count}")
    if summary.source_document_candidate_count < target.source_document_candidate_count:
        deficits.append(
            "SourceDocumentCandidate "
            f"{summary.source_document_candidate_count}/{target.source_document_candidate_count}"
        )
    if summary.evidence_item_count < target.evidence_item_count:
        deficits.append(f"EvidenceItem {summary.evidence_item_count}/{target.evidence_item_count}")

    source_family_reason = _SOURCE_FAMILY_BLOCKED_REASONS[summary.source_family]
    if (
        summary.raw_artifact_count == 0
        and summary.source_document_candidate_count == 0
        and summary.evidence_item_count == 0
    ):
        return f"{source_family_reason}; target not met: {', '.join(deficits)}"
    return f"target not met: {', '.join(deficits)}; {source_family_reason}"


def render_phase0_feasibility_markdown(report: Phase0FixtureReport) -> str:
    lines = [
        "---",
        "kind: synthesis",
        "created: 2026-07-07",
        "updated: 2026-07-07",
        "epic_id: OPL-PHASE0-REMAINDER-20260707",
        f"status: phase0-{report.phase0_status}",
        "---",
        "",
        "# Phase 0 source probe feasibility report",
        "",
        "## 結論",
        "",
        f"Phase 0 判定: `{report.phase0_status}`",
        "",
        (
            f"- 達成 source family: {report.achieved_source_family_count}/"
            f"{len(report.source_families)}"
        ),
        (
            f"- 最低 gate: {report.minimum_required_source_family_count} source family 以上で "
            "RawArtifact / SourceDocumentCandidate / EvidenceItem が各 10 件以上"
        ),
        (
            "- 必須 source family: "
            + ", ".join(sorted(report.required_source_families))
            + (" は達成済み" if report.required_source_families_goal_met else " は未達を含む")
        ),
        ("- 通常検証では external network / browser automation / PDF download / OCR を実行しない"),
        "",
        "## Roadmap 対象 source",
        "",
        *[f"- {label}" for label in PHASE0_ROADMAP_SOURCE_LABELS],
        "",
        "## Source family coverage",
        "",
        (
            "| source_family | status | RawArtifact | SourceDocumentCandidate | "
            "EvidenceItem | warnings | review_required | blocked_reason |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for row in report.source_families:
        blocked_reason = row.blocked_reason or ""
        lines.append(
            f"| {row.source_family} | {row.status} | {row.raw_artifact_count} | "
            f"{row.source_document_candidate_count} | {row.evidence_item_count} | "
            f"{row.warning_count} | {row.review_required_count} | {blocked_reason} |"
        )

    lines.extend(
        [
            "",
            "## Non-goal guard",
            "",
            "| source_family | non-goal guard |",
            "| --- | --- |",
        ]
    )
    for row in report.source_families:
        lines.append(f"| {row.source_family} | {' / '.join(row.non_goal_guard)} |")

    if report.phase0_status != "complete":
        lines.extend(
            [
                "",
                "## 未達理由",
                "",
            ]
        )
        if not report.coverage_source_family_goal_met:
            lines.append(
                "- 10 RawArtifact / SourceDocumentCandidate / EvidenceItem を満たす "
                f"source family が {report.achieved_source_family_count} 件で、"
                f"必要な {report.minimum_required_source_family_count} 件に届いていない。"
            )
        if report.missing_required_source_families:
            lines.append(
                "- 助成・補助金と監査 source の必須 gate のうち未達: "
                + ", ".join(report.missing_required_source_families)
            )

    lines.extend(
        [
            "",
            "## 出典",
            "",
            "- [Phase 0 残実装設計](phase0-remainder-implementation-design.md)",
            "- [Phase 0 残実装ローカル issue ledger](phase0-remainder-issues.md)",
        ]
    )
    return "\n".join(lines) + "\n"
