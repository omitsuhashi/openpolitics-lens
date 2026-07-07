import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from html import escape

from ingest.contracts import FetchManifestRecord, JsonDict, SourceDocumentCandidate
from ingest.phase0_sources import (
    LOCAL_FIXTURE_OPERATION,
    PHASE0_SOURCE_REGISTRY,
    FixtureMetadata,
)

TOKYO_ASSEMBLY_RECORDS_SOURCE_FAMILY = "tokyo_assembly_records_bills"
TOKYO_ASSEMBLY_RECORDS_SOURCE_TYPE = "assembly_meeting_record_search_snapshot"
TOKYO_ASSEMBLY_RECORDS_MEDIA_TYPE = "text/html; charset=utf-8"


def _datetime_to_json(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _content_hash(content: bytes) -> str:
    return sha256(content).hexdigest()


@dataclass(frozen=True, slots=True)
class AssemblyRecordsSearchSnapshot:
    search_form_url: str
    canonical_url: str
    query_parameters: JsonDict
    target_period: JsonDict
    page_number: int
    sort_order: str
    snapshot_timestamp: datetime
    operations: tuple[str, ...] = (LOCAL_FIXTURE_OPERATION,)

    @property
    def snapshot_timestamp_json(self) -> str:
        return _datetime_to_json(self.snapshot_timestamp)

    def to_json_dict(self) -> JsonDict:
        return {
            "search_form_url": self.search_form_url,
            "canonical_url": self.canonical_url,
            "query_parameters": dict(self.query_parameters),
            "target_period": dict(self.target_period),
            "page_number": self.page_number,
            "sort_order": self.sort_order,
            "snapshot_timestamp": self.snapshot_timestamp_json,
            "operations": list(self.operations),
        }

    def location_metadata_for(self, record: "AssemblySpeechFixtureRecord") -> JsonDict:
        return {
            "search_form_url": self.search_form_url,
            "query_parameters": dict(self.query_parameters),
            "target_period": dict(self.target_period),
            "page_number": self.page_number,
            "sort_order": self.sort_order,
            "snapshot_timestamp": self.snapshot_timestamp_json,
            "result_row_locator": record.result_row_locator,
            "meeting_id": record.meeting_id,
            "meeting_name": record.meeting_name,
            "meeting_date": record.meeting_date,
            "speaker_name": record.speaker_name,
            "speaker_role": record.speaker_role,
            "speech_block_id": record.speech_block_id,
            "speech_block_locator": f"#{record.speech_block_id}",
        }


@dataclass(frozen=True, slots=True)
class AssemblySpeechFixtureRecord:
    fixture_id: str
    canonical_url: str
    title: str
    meeting_id: str
    meeting_name: str
    meeting_date: str
    speaker_name: str
    speaker_role: str
    speech_block_id: str
    speech_text: str
    result_row_locator: str

    def raw_html(self, search_snapshot: AssemblyRecordsSearchSnapshot) -> bytes:
        metadata_json = json.dumps(
            search_snapshot.location_metadata_for(self),
            ensure_ascii=False,
            sort_keys=True,
        )
        html = (
            '<!doctype html><html lang="ja"><head>'
            f'<meta charset="utf-8"><title>{escape(self.title)}</title>'
            '<script id="assembly-speech-metadata" type="application/json">'
            f"{metadata_json}"
            "</script></head><body>"
            f'<article data-meeting-id="{escape(self.meeting_id)}" '
            f'data-speaker-name="{escape(self.speaker_name)}">'
            f"<h1>{escape(self.meeting_name)}</h1>"
            f'<p class="speaker-name">{escape(self.speaker_name)}</p>'
            f'<section id="{escape(self.speech_block_id)}" class="speech-block">'
            f'<p class="speech-text">{escape(self.speech_text)}</p>'
            "</section></article></body></html>"
        )
        return html.encode("utf-8")


@dataclass(frozen=True, slots=True)
class AssemblyFixtureRawArtifact:
    fixture_id: str
    canonical_url: str
    raw_artifact_path: str
    content_hash: str
    media_type: str
    byte_size: int
    content: bytes


@dataclass(frozen=True, slots=True)
class AssemblyRecordsFixtureProbe:
    search_snapshot: AssemblyRecordsSearchSnapshot
    fixture_records: tuple[AssemblySpeechFixtureRecord, ...]
    raw_artifacts: tuple[AssemblyFixtureRawArtifact, ...]
    fetch_manifests: tuple[FetchManifestRecord, ...]
    fixture_metadata: FixtureMetadata

    @property
    def source_document_candidates(self) -> tuple[SourceDocumentCandidate, ...]:
        return tuple(record.source_document_candidate for record in self.fetch_manifests)


TOKYO_ASSEMBLY_RECORDS_SEARCH_SNAPSHOT = AssemblyRecordsSearchSnapshot(
    search_form_url="https://www.gikai.metro.tokyo.lg.jp/record/proceedings/search",
    canonical_url=(
        "https://www.gikai.metro.tokyo.lg.jp/record/proceedings/search"
        "?keyword=fixture-speech&page=1"
    ),
    query_parameters={
        "keyword": "fixture-speech",
        "speaker": "",
        "committee": "",
        "search_target": "speech",
    },
    target_period={"from": "2024-01-01", "to": "2024-12-31"},
    page_number=1,
    sort_order="meeting_date_asc",
    snapshot_timestamp=datetime(2026, 7, 7, 0, 0, tzinfo=UTC),
)

_FIXTURE_SPEECHES: tuple[tuple[str, str, str, str], ...] = (
    (
        "assembly-speech-001",
        "令和6年第一回定例会 本会議",
        "議員A",
        "子育て支援の相談窓口について伺います。",
    ),
    (
        "assembly-speech-002",
        "令和6年第一回定例会 本会議",
        "議員B",
        "学校施設の改修予定について説明を求めます。",
    ),
    (
        "assembly-speech-003",
        "令和6年第一回定例会 文教委員会",
        "議員C",
        "都立学校の教材整備状況を確認します。",
    ),
    (
        "assembly-speech-004",
        "令和6年第二回定例会 本会議",
        "議員D",
        "保育サービスの利用状況について質問します。",
    ),
    (
        "assembly-speech-005",
        "令和6年第二回定例会 厚生委員会",
        "議員E",
        "福祉相談体制の周知方法について伺います。",
    ),
    (
        "assembly-speech-006",
        "令和6年第三回定例会 本会議",
        "議員F",
        "防災訓練の実施状況について確認します。",
    ),
    (
        "assembly-speech-007",
        "令和6年第三回定例会 総務委員会",
        "議員G",
        "行政手続のオンライン化について質問します。",
    ),
    (
        "assembly-speech-008",
        "令和6年第四回定例会 本会議",
        "議員H",
        "地域交通の安全対策について伺います。",
    ),
    (
        "assembly-speech-009",
        "令和6年第四回定例会 経済・港湾委員会",
        "議員I",
        "中小企業支援策の案内方法について確認します。",
    ),
    (
        "assembly-speech-010",
        "令和6年第四回定例会 環境・建設委員会",
        "議員J",
        "公園施設の維持管理状況について質問します。",
    ),
)


def _fixture_records() -> tuple[AssemblySpeechFixtureRecord, ...]:
    return tuple(
        AssemblySpeechFixtureRecord(
            fixture_id=fixture_id,
            canonical_url=(f"https://www.gikai.metro.tokyo.lg.jp/record/fixture/{fixture_id}.html"),
            title=f"{meeting_name} {speaker_name} 発言 fixture",
            meeting_id=f"meeting-{index:03d}",
            meeting_name=meeting_name,
            meeting_date=f"2024-{index:02d}-01",
            speaker_name=speaker_name,
            speaker_role="東京都議会議員",
            speech_block_id=f"speech-block-{index:03d}",
            speech_text=speech_text,
            result_row_locator=f"table.search-results tbody tr:nth-child({index})",
        )
        for index, (fixture_id, meeting_name, speaker_name, speech_text) in enumerate(
            _FIXTURE_SPEECHES,
            start=1,
        )
    )


def _raw_artifact_path(*, content_hash: str, fetched_at: datetime) -> str:
    return (
        "raw/jp-tokyo/"
        f"{TOKYO_ASSEMBLY_RECORDS_SOURCE_FAMILY}/"
        f"{fetched_at:%Y}/{fetched_at:%m}/{content_hash}.html"
    )


def build_tokyo_assembly_records_fixture_probe(
    *,
    search_snapshot: AssemblyRecordsSearchSnapshot = TOKYO_ASSEMBLY_RECORDS_SEARCH_SNAPSHOT,
) -> AssemblyRecordsFixtureProbe:
    connector = PHASE0_SOURCE_REGISTRY[TOKYO_ASSEMBLY_RECORDS_SOURCE_FAMILY].connector
    raw_artifacts: list[AssemblyFixtureRawArtifact] = []
    fetch_manifests: list[FetchManifestRecord] = []
    fixture_records = _fixture_records()

    for fixture_record in fixture_records:
        content = fixture_record.raw_html(search_snapshot)
        content_hash = _content_hash(content)
        raw_artifact_path = _raw_artifact_path(
            content_hash=content_hash,
            fetched_at=search_snapshot.snapshot_timestamp,
        )
        raw_artifact = AssemblyFixtureRawArtifact(
            fixture_id=fixture_record.fixture_id,
            canonical_url=fixture_record.canonical_url,
            raw_artifact_path=raw_artifact_path,
            content_hash=content_hash,
            media_type=TOKYO_ASSEMBLY_RECORDS_MEDIA_TYPE,
            byte_size=len(content),
            content=content,
        )
        candidate = SourceDocumentCandidate(
            canonical_url=fixture_record.canonical_url,
            title=fixture_record.title,
            source_type=TOKYO_ASSEMBLY_RECORDS_SOURCE_TYPE,
            jurisdiction_id=connector.jurisdiction.jurisdiction_id,
            source_family=connector.source_family.source_family,
            language="ja",
            retrieved_at=search_snapshot.snapshot_timestamp,
            raw_artifact_path=raw_artifact_path,
        )
        fetch_manifest = FetchManifestRecord(
            connector=connector,
            canonical_url=fixture_record.canonical_url,
            fetched_at=search_snapshot.snapshot_timestamp,
            http_status=200,
            content_hash=content_hash,
            media_type=TOKYO_ASSEMBLY_RECORDS_MEDIA_TYPE,
            byte_size=len(content),
            raw_artifact_path=raw_artifact_path,
            source_document_candidate=candidate,
        )
        raw_artifacts.append(raw_artifact)
        fetch_manifests.append(fetch_manifest)

    aggregate_hash = _content_hash(
        "\n".join(artifact.content_hash for artifact in raw_artifacts).encode("utf-8")
    )
    fixture_metadata = FixtureMetadata(
        fixture_id="tokyo-assembly-records-search-snapshot-fixture",
        source_family=TOKYO_ASSEMBLY_RECORDS_SOURCE_FAMILY,
        canonical_url=search_snapshot.canonical_url,
        fetched_at=search_snapshot.snapshot_timestamp,
        media_type=TOKYO_ASSEMBLY_RECORDS_MEDIA_TYPE,
        byte_size=sum(artifact.byte_size for artifact in raw_artifacts),
        content_hash=aggregate_hash,
        source_type=TOKYO_ASSEMBLY_RECORDS_SOURCE_TYPE,
        expected_evidence_item_count=len(fixture_records),
        operations=search_snapshot.operations,
    )

    return AssemblyRecordsFixtureProbe(
        search_snapshot=search_snapshot,
        fixture_records=fixture_records,
        raw_artifacts=tuple(raw_artifacts),
        fetch_manifests=tuple(fetch_manifests),
        fixture_metadata=fixture_metadata,
    )
