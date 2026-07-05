---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
issue_id: G2PR-006
status: feasibility-synthesis
spec: tokyo-subsidy-ingest-spec.md
---

# 東京都 PDF/OCR・表抽出 feasibility

## 結論

PDF/OCR と表抽出は `services/ingest` では実装しない。ingest は HTML、PDF、CSV、JSON、XML を RawArtifact として保存し、`raw_artifact_path` を含む Source Document Candidate を normalize に渡すところまでに留める。

`services/normalize` は、SourceDocument、EvidenceItem、EvidenceClaim を作るときに、必ず SourceDocument と EvidenceItem から `raw_artifact_path` へ戻れるようにする。EvidenceItem は `location_type`、`location_value`、`source_span_start`、`source_span_end`、`quote_text`、`normalized_text`、`extraction_method`、`confidence` を保持し、PDF/OCR 由来の金額、氏名、団体名には confidence と parse warning を必須にする。

この synthesis は feasibility と後続 issue 分離だけを扱う。PDF/OCR engine、parser、table extraction、live source 取得、PDF download、OCR 実行、金額・氏名・団体名・監査指摘・交付先の意味解釈、SubsidyProgram / PublicMoneyFlow / SpendingReviewSignal / AuditFinding 生成、DB migration、API、Web UI は扱わない。

## 前提 contract

- `SourceDocument.raw_artifact_path` は ingest の Fetch Manifest / Source Document Candidate から引き継ぐ。
- `EvidenceItem.raw_artifact_path` は SourceDocument と同じ原本へ戻す。HTML では raw HTML、PDF では raw PDF を指す。
- HTML parser は、既存 G2PR-005 と同じく `source_span_start` / `source_span_end` を raw HTML bytes の offset として扱う。
- PDF parser は後続実装で、deterministic な text/table extraction artifact を作り、その text offset と original PDF の page / bbox / table cell を `location_value` に保存する。page / bbox に戻れない抽出結果から EvidenceClaim を作らない。
- EvidenceClaim は EvidenceItem から直接言える最小 claim に留める。推定 relation、名寄せ、支出検証 signal は後段 projection と review に分ける。
- PDF/OCR 由来の金額、氏名、団体名は、`confidence`、`parse_warnings`、`extraction_method`、`raw_artifact_path`、page / span / cell location が揃う場合だけ machine extracted とする。

## 共通 confidence policy

| 抽出元 | 初期 confidence 方針 |
| --- | --- |
| 公式 HTML の安定 selector / table cell | 原則 high。DOM selector と raw byte span に戻れる場合だけ `machine_extracted` にする。 |
| PDF text layer の連続 text span | medium-high。page と text offset に戻れる場合だけ claim 化する。縦書き、段組、脚注、単位省略は warning を付ける。 |
| PDF table extraction | medium。row / column / page / bbox に戻れる場合だけ claim 化する。merged cell、multi-page table、単位行、注記分離は warning を付ける。 |
| OCR text / OCR table | low-medium。金額、氏名、団体名は warning 必須、原則 review queue 行き。confidence が低いものは EvidenceItem までに留める。 |
| search UI snapshot | medium。検索条件、取得日時、ページング、sort order を location と metadata に残せる場合だけ claim 化する。 |

## 共通 parse warning policy

後続実装では、少なくとも次の warning category を持つ。

| warning | 用途 |
| --- | --- |
| `pdf_text_layer_missing` | PDF に text layer がなく OCR が必要。 |
| `ocr_required` | OCR を使った抽出である。 |
| `ocr_low_confidence` | OCR confidence が低い、または文字候補が複数ある。 |
| `table_structure_inferred` | 表構造を layout から推定した。 |
| `merged_cell_or_header_inferred` | 結合セル、上位 header、単位行を推定した。 |
| `multi_page_table` | 表が複数 page にまたがる。 |
| `amount_unit_ambiguous` | 千円、百万円、税込、税抜など金額単位が曖昧。 |
| `name_or_org_ocr_ambiguous` | 氏名・団体名の OCR / 表記揺れが曖昧。 |
| `entity_resolution_required` | 文字列抽出はできたが、人物・団体・法人への名寄せが必要。 |
| `search_ui_snapshot` | 検索 UI の snapshot 由来で、検索条件とページング再現が必要。 |
| `meaning_not_interpreted` | 金額、交付先、監査指摘、契約先などの意味解釈をまだ行っていない。 |

## Source family 別 feasibility

source_family id は G2PR-007 で確定する。ここでは後続設計へ渡すための暫定名として記録する。

| source family | OCR 判定 | 初期 parser approach | table extraction approach | confidence policy | parse warning policy | 後続 implementation issue |
| --- | --- | --- | --- | --- | --- | --- |
| 補助金（暫定 `tokyo_metro_grants`） | 未検証。制度ページ HTML は OCR 不要。交付実績、募集要項、実績報告 PDF は text layer / OCR 要否が未検証。 | `tokyo_metro_grants` の HTML 制度ページは DOM selector と main content extraction から始める。PDF 添付は metadata、page text、section heading を EvidenceItem に留め、交付先や金額の意味解釈はしない。 | HTML table は DOM table cell。PDF table は text layer table extraction を優先し、OCR table は review 前提。交付実績一覧は row / column / page / bbox に戻れない限り claim 化しない。 | HTML title / heading は high。PDF text layer は medium-high。OCR 由来の金額、交付先名、団体名は low-medium かつ warning 必須。 | `pdf_text_layer_missing`, `ocr_required`, `amount_unit_ambiguous`, `name_or_org_ocr_ambiguous`, `entity_resolution_required`, `meaning_not_interpreted`。 | 補助金 PDF attachment fixture と text/table extraction contract を作る。交付実績 parser は PublicMoneyFlow 生成 issue へ分離する。 |
| 政治資金（暫定 `tokyo_political_funds`） | 必要。政治資金収支報告書は PDF/OCR と表抽出の品質検査が必須。text layer の有無は source sample ごとに検証する。 | 東京都選管の report index から RawArtifact 化した PDF を、page 単位の report section と表単位に分ける。政治家本人、後援会、政党支部、資金管理団体を同一 entity にしない。 | 寄附、収入、支出、資産等の表は page / table / row / column を location に持つ。OCR table は review queue に送り、氏名・団体名・金額を自動 merge しない。 | 金額、氏名、団体名は confidence と warning 必須。公式 ID または政治団体名簿 anchor がない場合は RelationshipEdge を作らない。 | `ocr_required`, `ocr_low_confidence`, `table_structure_inferred`, `amount_unit_ambiguous`, `name_or_org_ocr_ambiguous`, `entity_resolution_required`。 | 政治資金 PDF sample set、OCR/text-layer 判定、table extraction evaluator、PoliticalGroup anchor 連携を別 issue 化する。 |
| 監査（暫定 `tokyo_audit_reports`） | 未検証。HTML / PDF / CSV が混在し、PDF text layer で足りる可能性がある。古い scan PDF は OCR が必要になる。 | 監査事務局の年度・監査種別 index から report 単位 SourceDocument を作る。報告書本文は page heading、指摘、措置状況を原文 span として抽出するが、AuditFinding 生成や要約はしない。 | PDF の指摘一覧、措置状況表、対象団体表は table extraction 候補。CSV がある場合は CSV を優先し、PDF table は補助 EvidenceItem にする。 | 公式 HTML/CSV は high。PDF text layer は medium-high。OCR 由来の団体名、金額、指摘文は warning 必須で review 前提。 | `pdf_text_layer_missing`, `ocr_required`, `multi_page_table`, `merged_cell_or_header_inferred`, `name_or_org_ocr_ambiguous`, `meaning_not_interpreted`。 | 監査 report fixture、page/span locator、指摘/措置状況 table extraction、AuditFinding 生成前 review gate を別 issue 化する。 |
| 契約・入札（暫定 `tokyo_procurement`） | OCR 不要。初期対象は電子調達検索 UI snapshot と HTML table。添付 PDF の有無は未検証として扱う。 | 検索条件を固定した `search_ui_snapshot` connector で入札予定、落札結果、入札結果を RawArtifact 化する。contract title、organization、amount、vendor、published_at は文字列 EvidenceClaim までに留める。 | HTML search result table を primary にする。ページング、sort order、検索条件を location / metadata に残す。添付 PDF が出た場合は後続 PDF path に分離する。 | 検索条件と row / cell に戻れる HTML table は medium-high。vendor や amount は名寄せ・税込判定をしない限り review_state を machine_extracted に留める。 | `search_ui_snapshot`, `table_structure_inferred`, `amount_unit_ambiguous`, `entity_resolution_required`, `meaning_not_interpreted`。 | 電子調達 search fixture、snapshot reproducibility、pagination contract、ContractAward 生成前の parser issue を G2PR-007 後に切る。 |
| 予算・決算（暫定 `tokyo_budget_settlement`） | 未検証。HTML index は OCR 不要。予算書・決算書 PDF は text layer table extraction が必要で、scan PDF は OCR が必要。 | 財務局の予算・決算 index から document metadata を取る。PDF は章、款項目、事業名、金額列を page span / table cell EvidenceItem として保持し、BudgetLine 生成は後続にする。 | PDF table extraction が中心。単位行、前年差、補正、合計行、脚注を区別する。CSV/HTML がある場合は PDF より優先する。 | HTML/CSV は high。PDF text layer table は medium。OCR 由来の金額と事業名は warning 必須で、単位が確定しない場合は claim 化しない。 | `pdf_text_layer_missing`, `ocr_required`, `multi_page_table`, `amount_unit_ambiguous`, `merged_cell_or_header_inferred`, `meaning_not_interpreted`。 | 予算・決算 PDF sample、table schema mapping、amount unit detector、BudgetLine 生成前 review gate を別 issue 化する。 |
| 会議録・議案（暫定 `tokyo_assembly_records_bills`） | OCR 不要。初期対象は都議会 HTML、会議録検索結果、議案ページ。PDF 本文が出る場合は未検証として後続扱い。 | 会議録・速記録は meeting / speech 単位、提出議案と議決結果は bill / decision event 単位で HTML parser を作る。個人別賛否が source にない場合は VotePosition を生成しない。 | 議案一覧、議決結果、請願・陳情一覧は HTML table / list parser。会議録本文は table extraction ではなく speech block extraction を使う。 | 公式 HTML selector と speech / bill anchor に戻れる場合は high。検索 UI snapshot 由来は medium。議案上の契約案と電子調達の契約先は同一視しない。 | `search_ui_snapshot`, `table_structure_inferred`, `entity_resolution_required`, `meaning_not_interpreted`。 | 会議録検索 acquisition 条件、議案/bill parser fixture、speech locator、契約案と PublicMoneyFlow を結ばない guard を G2PR-007 後に実装する。 |

## 後続 issue 分離

G2PR-006 から実装 issue に切り出す項目:

1. PDF / OCR 抽出 contract を normalize に追加する。対象は parser result schema、page / bbox / table cell locator、parse warning 保存、confidence 保存まで。EvidenceClaim 生成は最小 claim に限定する。
2. source family ごとの fixture を作る。live fetch や PDF download は行わず、保存済み fixture RawArtifact で parser evaluator を作る。
3. PDF text layer 判定と OCR 要否判定を作る。OCR engine 選定と実行はさらに別 issue に分ける。
4. table extraction evaluator を作る。row / column / page / bbox に戻れない抽出結果は claim 化しない。
5. 政治資金、監査、予算・決算、契約・入札、会議録・議案の connector 設計は G2PR-007 で `jurisdiction_id`、`source_system`、`source_family`、`connector_id` を確定する。
6. SubsidyProgram、PublicMoneyFlow、AuditFinding、SpendingReviewSignal の生成は、parser confidence / warning と human review policy が揃ってから別 issue で扱う。

## 残リスク

- 実 source の PDF layout、text layer、scan 率は未検証である。live source 取得、PDF download、OCR 実行をしていないため、OCR 判定は既存 inventory と source family 性質に基づく feasibility に留まる。
- 現在の `EvidenceItem` dataclass は `parse_warnings` field をまだ持たない。後続 normalize issue で warning 保存先を contract 化する必要がある。
- PDF の `source_span_start` / `source_span_end` を何の byte sequence に対する offset とするかは、後続 parser result schema で固定する必要がある。少なくとも `raw_artifact_path`、page、bbox、table cell へ戻れない抽出は EvidenceClaim にしない。
- 金額、氏名、団体名、監査指摘、交付先の意味解釈は本 synthesis では行っていない。

## 関連ページ

- [東京都補助金・助成金 ingest 初期仕様](tokyo-subsidy-ingest-spec.md)
- [東京都補助金・助成金 ingest ローカル issue ledger](tokyo-subsidy-ingest-issues.md)
- [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md)
- [Data Sources](../../data-sources.md)
- [Domain Model](../../domain-model.md)
- [Spending Review](../../spending-review.md)
