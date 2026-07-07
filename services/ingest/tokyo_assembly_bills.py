from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from html import escape

from ingest.contracts import ConnectorDefinition, FetchManifestRecord, SourceDocumentCandidate
from ingest.filesystem import FileSystemOutputWriter
from ingest.phase0_sources import PHASE0_SOURCE_REGISTRY

TOKYO_ASSEMBLY_BILLS_CONNECTOR: ConnectorDefinition = PHASE0_SOURCE_REGISTRY[
    "tokyo_assembly_records_bills"
].connector


@dataclass(frozen=True, slots=True)
class TokyoAssemblyBillDecisionFixture:
    fixture_id: str
    fiscal_year: int
    regular_session: str
    session_period: str
    bill_number: str
    subject: str
    decision_result: str
    source_url: str
    row_locator: str
    has_individual_vote_positions: bool = False

    @property
    def title(self) -> str:
        return f"{self.regular_session} {self.bill_number} 議決結果"

    @property
    def evidence_quote_text(self) -> str:
        return (
            f"{self.bill_number} {self.subject} {self.decision_result} "
            f"会期 {self.session_period} 出典 {self.source_url}"
        )

    def to_html_bytes(self) -> bytes:
        quote = escape(self.evidence_quote_text)
        return (
            '<!doctype html><html lang="ja"><head>'
            f"<title>{escape(self.title)}</title>"
            "</head><body>"
            f"<h1>{escape(self.regular_session)} 提出議案・議決結果</h1>"
            '<table id="bill-decisions">'
            f'<tr data-fixture-id="{escape(self.fixture_id)}">'
            f'<td class="bill-number">{escape(self.bill_number)}</td>'
            f'<td class="subject">{escape(self.subject)}</td>'
            f'<td class="decision-result">{escape(self.decision_result)}</td>'
            f'<td class="session-period">{escape(self.session_period)}</td>'
            "</tr></table>"
            f'<p class="decision-summary" data-fixture-id="{escape(self.fixture_id)}">'
            f"{quote}"
            "</p>"
            "</body></html>"
        ).encode()


TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES: tuple[TokyoAssemblyBillDecisionFixture, ...] = (
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r1-001",
        fiscal_year=2024,
        regular_session="令和6年第1回定例会",
        session_period="2024-02-20/2024-03-28",
        bill_number="第1号議案",
        subject="東京都一般会計予算",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-1.html#bill-001",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r1-001']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r1-002",
        fiscal_year=2024,
        regular_session="令和6年第1回定例会",
        session_period="2024-02-20/2024-03-28",
        bill_number="第2号議案",
        subject="東京都特別区財政調整会計予算",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-1.html#bill-002",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r1-002']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r1-025",
        fiscal_year=2024,
        regular_session="令和6年第1回定例会",
        session_period="2024-02-20/2024-03-28",
        bill_number="第25号議案",
        subject="東京都職員定数条例の一部を改正する条例",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-1.html#bill-025",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r1-025']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r1-042",
        fiscal_year=2024,
        regular_session="令和6年第1回定例会",
        session_period="2024-02-20/2024-03-28",
        bill_number="第42号議案",
        subject="東京都立学校設置条例の一部を改正する条例",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-1.html#bill-042",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r1-042']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r1-058",
        fiscal_year=2024,
        regular_session="令和6年第1回定例会",
        session_period="2024-02-20/2024-03-28",
        bill_number="第58号議案",
        subject="東京都児童福祉施設条例の一部を改正する条例",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-1.html#bill-058",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r1-058']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r2-090",
        fiscal_year=2024,
        regular_session="令和6年第2回定例会",
        session_period="2024-06-04/2024-06-12",
        bill_number="第90号議案",
        subject="東京都都税条例の一部を改正する条例",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-2.html#bill-090",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r2-090']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r2-091",
        fiscal_year=2024,
        regular_session="令和6年第2回定例会",
        session_period="2024-06-04/2024-06-12",
        bill_number="第91号議案",
        subject="東京都公園条例の一部を改正する条例",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-2.html#bill-091",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r2-091']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r2-101",
        fiscal_year=2024,
        regular_session="令和6年第2回定例会",
        session_period="2024-06-04/2024-06-12",
        bill_number="第101号議案",
        subject="都立施設改修工事請負契約",
        decision_result="原案可決",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-2.html#bill-101",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r2-101']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r2-112",
        fiscal_year=2024,
        regular_session="令和6年第2回定例会",
        session_period="2024-06-04/2024-06-12",
        bill_number="第112号議案",
        subject="東京都教育委員会委員の任命の同意",
        decision_result="同意",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-2.html#bill-112",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r2-112']",
    ),
    TokyoAssemblyBillDecisionFixture(
        fixture_id="tokyo-assembly-bill-decision-2024-r2-120",
        fiscal_year=2024,
        regular_session="令和6年第2回定例会",
        session_period="2024-06-04/2024-06-12",
        bill_number="第120号議案",
        subject="東京都監査委員の選任の同意",
        decision_result="同意",
        source_url="https://www.gikai.metro.tokyo.lg.jp/bill/2024/regular-2.html#bill-120",
        row_locator="p.decision-summary[data-fixture-id='tokyo-assembly-bill-decision-2024-r2-120']",
    ),
)


def build_tokyo_assembly_bill_decision_fixture_records(
    *,
    output_writer: FileSystemOutputWriter,
    run_id: str,
    fetched_at: datetime,
    fixtures: Iterable[TokyoAssemblyBillDecisionFixture] = TOKYO_ASSEMBLY_BILL_DECISION_FIXTURES,
) -> tuple[FetchManifestRecord, ...]:
    records: list[FetchManifestRecord] = []
    for fixture in fixtures:
        content = fixture.to_html_bytes()
        raw_artifact = output_writer.write_raw_artifact(
            content=content,
            jurisdiction_id=TOKYO_ASSEMBLY_BILLS_CONNECTOR.jurisdiction.jurisdiction_id,
            source_family=TOKYO_ASSEMBLY_BILLS_CONNECTOR.source_family.source_family,
            fetched_at=fetched_at,
            extension="html",
        )
        raw_artifact_path = raw_artifact.relative_path.as_posix()
        source_document_candidate = SourceDocumentCandidate(
            canonical_url=fixture.source_url,
            title=fixture.title,
            source_type="assembly_bill_decision",
            jurisdiction_id=TOKYO_ASSEMBLY_BILLS_CONNECTOR.jurisdiction.jurisdiction_id,
            source_family=TOKYO_ASSEMBLY_BILLS_CONNECTOR.source_family.source_family,
            language="ja",
            retrieved_at=fetched_at,
            raw_artifact_path=raw_artifact_path,
        )
        record = FetchManifestRecord(
            connector=TOKYO_ASSEMBLY_BILLS_CONNECTOR,
            canonical_url=fixture.source_url,
            fetched_at=fetched_at,
            http_status=200,
            content_hash=raw_artifact.content_hash,
            media_type="text/html; charset=utf-8",
            byte_size=raw_artifact.byte_size,
            raw_artifact_path=raw_artifact_path,
            source_document_candidate=source_document_candidate,
        )
        output_writer.append_jsonl(run_id=run_id, name="fetched", record=record)
        records.append(record)

    return tuple(records)
