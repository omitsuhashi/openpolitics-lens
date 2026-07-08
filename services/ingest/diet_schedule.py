from dataclasses import dataclass
from datetime import datetime

from ingest.contracts import (
    ConnectorDefinition,
    FetchManifestRecord,
    JurisdictionProfile,
    SourceCoverageRecord,
    SourceDocumentCandidate,
    SourceFamily,
    SourceRegistryRecord,
    source_coverage_failure_record,
)
from ingest.filesystem import FileSystemOutputWriter

DIET_SCHEDULE_JURISDICTION = JurisdictionProfile(
    jurisdiction_id="jp",
    jurisdiction_level="country",
    country_code="JP",
    subdivision_code=None,
    municipality_code=None,
    display_name="日本",
)

DIET_SCHEDULE_SOURCE_FAMILY = SourceFamily(
    source_family="jp_diet_schedule",
    source_system="house_of_representatives",
    display_name="国会会議予定",
)

HOUSE_OF_REPRESENTATIVES_DIET_SCHEDULE_CONNECTOR = ConnectorDefinition(
    connector_id="jp.diet_schedule.house_of_representatives.v1",
    connector_version="2026-07-08",
    jurisdiction=DIET_SCHEDULE_JURISDICTION,
    source_family=DIET_SCHEDULE_SOURCE_FAMILY,
    start_url="https://www.shugiin.go.jp/internet/index.nsf/html/index.htm",
    rate_limit_policy="fixture-only; live network fetch is disabled by default",
    terms_note="official House of Representatives public schedule pages",
)

HOUSE_OF_COUNCILLORS_DIET_SCHEDULE_CONNECTOR = ConnectorDefinition(
    connector_id="jp.diet_schedule.house_of_councillors.v1",
    connector_version="2026-07-08",
    jurisdiction=DIET_SCHEDULE_JURISDICTION,
    source_family=SourceFamily(
        source_family="jp_diet_schedule",
        source_system="house_of_councillors",
        display_name="国会会議予定",
    ),
    start_url="https://www.sangiin.go.jp/",
    rate_limit_policy="fixture-only; live network fetch is disabled by default",
    terms_note="official House of Councillors public schedule pages",
)


@dataclass(frozen=True, slots=True)
class DietScheduleFixturePage:
    canonical_url: str
    title: str
    source_type: str
    content: bytes
    media_type: str = "text/html; charset=utf-8"


class DietScheduleConnector:
    def __init__(
        self,
        *,
        definition: ConnectorDefinition,
        retrieval_method: str = "static_html_index",
        coverage_scope: str = "diet_meeting_schedule",
    ) -> None:
        self.definition = definition
        self.retrieval_method = retrieval_method
        self.coverage_scope = coverage_scope

    def fetch_fixture_page(
        self,
        page: DietScheduleFixturePage,
        *,
        output_writer: FileSystemOutputWriter,
        run_id: str,
        fetched_at: datetime,
    ) -> FetchManifestRecord:
        raw_artifact = output_writer.write_raw_artifact(
            content=page.content,
            jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
            source_family=self.definition.source_family.source_family,
            fetched_at=fetched_at,
            extension="html",
        )
        record = FetchManifestRecord(
            connector=self.definition,
            canonical_url=page.canonical_url,
            fetched_at=fetched_at,
            http_status=200,
            content_hash=raw_artifact.content_hash,
            media_type=page.media_type,
            byte_size=raw_artifact.byte_size,
            raw_artifact_path=raw_artifact.relative_path.as_posix(),
            source_document_candidate=SourceDocumentCandidate(
                canonical_url=page.canonical_url,
                title=page.title,
                source_type=page.source_type,
                jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
                source_family=self.definition.source_family.source_family,
                language="ja",
                retrieved_at=fetched_at,
                raw_artifact_path=raw_artifact.relative_path.as_posix(),
            ),
        )
        output_writer.append_jsonl(run_id=run_id, name="fetched", record=record)
        return record

    def fetch_fixture_pages(
        self,
        pages: tuple[DietScheduleFixturePage, ...],
        *,
        output_writer: FileSystemOutputWriter,
        run_id: str,
        fetched_at: datetime,
    ) -> tuple[FetchManifestRecord, ...]:
        return tuple(
            self.fetch_fixture_page(
                page,
                output_writer=output_writer,
                run_id=run_id,
                fetched_at=fetched_at,
            )
            for page in pages
        )

    def coverage_record_for_observed_page(
        self,
        *,
        checked_at: datetime,
        observed_event_count: int,
    ) -> SourceCoverageRecord:
        if observed_event_count < 0:
            raise ValueError("observed_event_count must be non-negative")
        if observed_event_count == 0:
            manual_notes = "schedule page を確認したが予定掲載なし。event absence は断定しない。"
            next_action = "次回 fixture refresh で schedule page を再確認する"
        else:
            manual_notes = f"fixture page から {observed_event_count} 件の会議予定を確認した。"
            next_action = "同 source family の fixture coverage を拡張する"
        return SourceCoverageRecord(
            jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
            jurisdiction_level=self.definition.jurisdiction.jurisdiction_level,
            source_system=self.definition.source_family.source_system,
            source_family=self.definition.source_family.source_family,
            connector_id=self.definition.connector_id,
            retrieval_method=self.retrieval_method,
            coverage_scope=self.coverage_scope,
            coverage_status="supported",
            entrypoint_url=self.definition.start_url,
            last_checked_at=checked_at,
            last_successful_fetch_at=checked_at,
            last_verified_at=checked_at,
            last_error=None,
            terms_note=self.definition.terms_note,
            manual_notes=manual_notes,
            next_action=next_action,
        )

    def coverage_record_for_parse_failure(
        self,
        *,
        checked_at: datetime,
        error: str,
    ) -> SourceCoverageRecord:
        return source_coverage_failure_record(
            self.registry_record(last_verified_at=checked_at),
            failure_kind="parser_failure",
            checked_at=checked_at,
            error=error,
            next_action="HTML structure を見直し、fixture parser を更新する",
            manual_notes="HTML structure が不安定なため manual review が必要。",
        )

    def registry_record(
        self,
        *,
        last_verified_at: datetime,
        coverage_status: str = "supported",
        connector_status: str = "implemented",
    ) -> SourceRegistryRecord:
        return SourceRegistryRecord(
            jurisdiction_id=self.definition.jurisdiction.jurisdiction_id,
            jurisdiction_level=self.definition.jurisdiction.jurisdiction_level,
            country_code=self.definition.jurisdiction.country_code,
            subdivision_code=self.definition.jurisdiction.subdivision_code,
            municipality_code=self.definition.jurisdiction.municipality_code,
            source_system=self.definition.source_family.source_system,
            source_family=self.definition.source_family.source_family,
            connector_id=self.definition.connector_id,
            officiality_level="official_primary",
            operator_name=(
                "衆議院"
                if self.definition.source_family.source_system == "house_of_representatives"
                else "参議院"
            ),
            entrypoint_url=self.definition.start_url,
            retrieval_method=self.retrieval_method,
            coverage_scope=self.coverage_scope,
            coverage_status=coverage_status,
            rate_limit_policy=self.definition.rate_limit_policy,
            terms_note=self.definition.terms_note,
            last_verified_at=last_verified_at,
            connector_status=connector_status,
        )
