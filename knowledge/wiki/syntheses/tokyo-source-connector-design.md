---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
issue_id: G2PR-007
status: connector-design-synthesis
spec: tokyo-subsidy-ingest-spec.md
---

# 東京都 source connector 設計

## 結論

`tokyo_metro_grants` で固定した `Jurisdiction Profile`、RawArtifact、Fetch Manifest、Source Document Candidate の分離規約を、契約・入札、予算・決算、監査、政治資金、会議録・議案の後続 source family に広げる。

この synthesis は docs-first の設計記録である。connector 実装、parser 実装、browser automation、live source 取得、PDF download、OCR 実行、DB migration、API、UI、GitHub write は行っていない。各 entrypoint は既存 inventory と既存 synthesis に記録済みの公式入口に基づく設計候補であり、検索 UI の挙動、PDF layout、OCR 要否、安定 URL、ページング、利用条件の詳細をこの作業で追加検証したものではない。

## 証拠境界

- source family と entrypoint は、既存の [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md)、[Data Sources](../../data-sources.md)、[Tokyo Subsidy PDF/OCR Feasibility](tokyo-subsidy-pdf-ocr-feasibility.md) に記録された公式入口と設計メモに限定する。
- live acquisition は、後続実装で robots、利用条件、rate limit、検索条件、ページング、保存先、取得件数、fixture との構造差を明示したうえで、手動 gate として扱う。
- fixture は、live acquisition の代替ではなく、connector contract、manifest、RawArtifact path、Source Document Candidate、parser locator の deterministic test 用入力として扱う。
- 金額、氏名、団体名、監査指摘、契約先、交付先、発言、議案の意味解釈は本 synthesis では行わない。

## Jurisdiction Profile 分離

すべての connector は次を registry key として分ける。

- `jurisdiction_id`: 政治・行政単位。東京都は `jp-tokyo`。
- `jurisdiction_level`: 東京都は `prefecture`。
- `source_system`: 公式 source の運営主体。
- `source_family`: 同じ公開構造を持つ source 群。
- `connector_id`: 実装単位。`jurisdiction_id` と `source_family` を含む namespace にする。

この分離により、東京都固有の allowlist、rate limit policy、terms note、fixture、output path は `jp-tokyo` profile と source family local config に閉じる。将来 `jp`、`jp-yokohama`、`jp-osaka`、他自治体を追加しても、東京都の keyword、domain allowlist、検索条件、fixture HTML/PDF、RawArtifact path、manifest output が別 jurisdiction の connector に混ざらない。

path と record は最低限、次の形で分離する。

```text
raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}
manifests/{run_id}/discovered.jsonl
manifests/{run_id}/fetched.jsonl
```

manifest record には `jurisdiction_id`、`jurisdiction_level`、`source_system`、`source_family`、`connector_id`、`connector_version`、`rate_limit_policy`、`terms_note`、`raw_artifact_path` を必ず含める。allowlist、rate limit、terms note は connector global ではなく `ConnectorDefinition` または source family local config に置く。

## Registry baseline

`tokyo_metro_grants` は本 synthesis の対象 family ではないが、registry consistency の baseline として置く。

| field | value |
| --- | --- |
| `jurisdiction_id` | `jp-tokyo` |
| `jurisdiction_level` | `prefecture` |
| `source_system` | `tokyo_metropolitan_government` |
| `source_family` | `tokyo_metro_grants` |
| `connector_id` | `jp_tokyo.metro_grants.v1` |
| discovery entrypoint | `https://www.metro.tokyo.lg.jp/purpose/grant` |
| fetch entrypoint | discovered grant / subsidy candidate page |
| `retrieval_method` | `static_html_index` + `html_detail`; live fetch 実装後は `run`、local verification は `fixture` |
| `candidate_type` | `grant_program_page_candidate` |
| `source_type` | `grant_program_page` |
| `normalization_target` | SourceDocument / EvidenceItem / EvidenceClaim。SubsidyProgram、PublicMoneyFlow、SpendingReviewSignal は後続 |
| fixture strategy | grant index と制度 page の fixture HTML、fake fetcher、deterministic manifest |
| live acquisition conditions | allowlist、rate limit、terms note、件数、保存先を明示し、通常 test / CI では外部 request しない |

## Source family registry

| source_family | jurisdiction_id | jurisdiction_level | source_system | connector_id | discovery / fetch entrypoints | retrieval_method | candidate_type | source_type | normalization_target |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tokyo_procurement` | `jp-tokyo` | `prefecture` | `tokyo_e_procurement_system` | `jp_tokyo.procurement.v1` | discovery: 東京都契約・入札情報、東京都電子調達システム入口。fetch: 入札予定情報、落札結果情報、入札結果の検索結果 snapshot と detail page 候補 | `search_ui_snapshot`。添付 PDF は後続 PDF path | `procurement_search_result_candidate`, `procurement_detail_candidate` | `procurement_notice`, `bid_result`, `contract_award` | ProcurementNotice、BidResult、ContractAward、Company candidate。契約案や議案とは自動同一視しない |
| `tokyo_budget_settlement` | `jp-tokyo` | `prefecture` | `tokyo_metropolitan_finance_bureau` | `jp_tokyo.budget_settlement.v1` | discovery: 財務局の財政情報、予算・決算 index。fetch: HTML index、予算書・決算書 PDF/HTML/CSV 候補 | `static_html_index` + `pdf_batch`; CSV/HTML があれば優先 | `budget_document_candidate`, `settlement_document_candidate` | `budget_document`, `settlement_document` | BudgetDocument、BudgetLine candidate、PublicMoneyFlow candidate。金額単位と表構造は review 前提 |
| `tokyo_audit_reports` | `jp-tokyo` | `prefecture` | `tokyo_audit_and_inspection_office` | `jp_tokyo.audit_reports.v1` | discovery: 監査事務局、財政援助団体等監査、包括外部監査、監査結果に基づく措置。fetch: 年度・監査種別 index、報告書 HTML/PDF/CSV 候補 | `static_html_index` + `pdf_batch`; CSV があれば優先 | `audit_report_candidate`, `audit_measure_candidate` | `audit_report`, `audit_measure_report` | AuditFinding candidate、measure status candidate。SpendingReviewSignal とは分ける |
| `tokyo_political_funds` | `jp-tokyo` | `prefecture` | `tokyo_metropolitan_election_administration_commission` | `jp_tokyo.political_funds.v1` | discovery: 政治資金収支報告書、政治団体名簿。fetch: report index、政治団体名簿、収支報告書 PDF 候補 | `static_html_index` + `pdf_batch`; OCR 要否は sample ごとに後続判定 | `political_fund_report_candidate`, `political_group_registry_candidate` | `political_fund_report`, `political_group_registry` | PoliticalGroup、FinanceReport、FundingContact candidate。人物・後援会・政党支部・資金管理団体を自動 merge しない |
| `tokyo_assembly_records_bills` | `jp-tokyo` | `prefecture` | `tokyo_metropolitan_assembly` | `jp_tokyo.assembly_records_bills.v1` | discovery: 会議録・速記録、会議録検索、提出議案と議決結果、請願・陳情。fetch: 年度・定例会 page、議案 page、会議録検索 snapshot、speech/detail 候補 | `static_html_index` + `html_detail` + `search_ui_snapshot` | `assembly_record_candidate`, `bill_candidate`, `petition_candidate` | `meeting_record`, `speech_record`, `bill`, `bill_decision`, `petition` | Meeting、Speech、Bill、BillEvent、DecisionEvent、Petition candidate。個人別賛否が source にない場合 VotePosition を作らない |

## Fixture strategy と live acquisition conditions

### `tokyo_procurement`

fixture strategy:

- 電子調達検索 UI の保存済み検索結果 HTML snapshot を fixture にする。
- fixture には検索条件、取得日時、sort order、ページ番号、row / cell locator を metadata として添える。
- detail page がある場合は、検索結果 fixture と detail fixture を分ける。
- 添付 PDF は本 connector fixture に混ぜず、PDF/OCR 後続 issue の fixture として別扱いにする。

live acquisition conditions:

- live 取得は、電子調達検索 UI の利用条件、robots、セッション、CSRF、検索条件固定、ページング、rate limit、保存件数、retry 禁止条件を確認してから手動実行する。
- browser automation が必要な場合も、通常 test / CI では実行しない。
- `search_ui_snapshot` 由来の claim は、検索条件とページングを RawArtifact metadata に残せる場合だけ normalize へ渡す。

non-goals:

- 入札結果と議案上の契約案を同一契約として自動結合しない。
- vendor / company の名寄せ、税込・税抜判定、随意契約の評価、単独応札の意味解釈は行わない。

parse / OCR uncertainties:

- 初期検索結果 HTML は OCR 不要の想定だが、添付 PDF の layout、text layer、OCR 要否は未検証。
- amount unit、落札者名、契約件名、所管組織の列構造とページング再現性は未検証。

follow-up implementation issues:

- 電子調達検索 UI fixture と snapshot reproducibility を作る。
- pagination / search condition contract を manifest に追加する。
- ContractAward 生成前の parser issue と review gate を切る。

### `tokyo_budget_settlement`

fixture strategy:

- 財務局の予算・決算 index HTML fixture と、代表的な予算書・決算書 PDF fixture を分ける。
- HTML/CSV が存在する場合はそれを primary fixture にし、PDF は補助 EvidenceItem 用 fixture にする。
- PDF table extraction fixture は page、table、row、column、bbox または text span に戻れる形を前提にする。

live acquisition conditions:

- live 取得は、対象年度、予算/決算/補正の区分、PDF/CSV/HTML の保存件数、rate limit、terms note、保存先を明示した手動実行に限る。
- PDF download は通常 verification に含めない。

non-goals:

- BudgetLine、SettlementLine、PublicMoneyFlow の確定生成は行わない。
- 予算増減、執行率、不用額、繰越の評価や SpendingReviewSignal 生成は行わない。

parse / OCR uncertainties:

- PDF の text layer、scan 率、表の複数 page 跨ぎ、単位行、前年差、脚注、合計行の扱いは未検証。
- 金額単位が確定しない場合は EvidenceClaim に昇格しない。

follow-up implementation issues:

- 予算・決算 PDF sample と table schema mapping を作る。
- amount unit detector と `amount_unit_ambiguous` warning を contract 化する。
- BudgetLine 生成前 review gate を設計する。

### `tokyo_audit_reports`

fixture strategy:

- 監査種別別の index HTML fixture と、監査報告書 PDF/CSV fixture を分ける。
- 財政援助団体等監査、包括外部監査、措置状況は source_type を分け、同じ parser に押し込まない。
- 指摘本文、対象団体、措置状況表は page/span/table location に戻れる fixture だけを parser evaluator に使う。

live acquisition conditions:

- live 取得は、対象年度、監査種別、取得する report 数、CSV 優先可否、PDF 保存可否、rate limit、terms note を明示した手動実行に限る。
- 監査指摘の要約や AuditFinding 生成は live acquisition の条件に含めない。

non-goals:

- 公式監査の指摘とアプリ側の SpendingReviewSignal を混ぜない。
- 指摘の重大性、違法性、不正、無駄遣いの自動判定は行わない。

parse / OCR uncertainties:

- HTML/PDF/CSV の混在、古い scan PDF、multi-page table、措置状況表の構造は未検証。
- OCR 由来の団体名、金額、指摘文は warning 必須で review queue 行きにする。

follow-up implementation issues:

- 監査 report fixture、page/span locator、指摘/措置状況 table extraction evaluator を作る。
- AuditFinding 生成前の review gate と official wording preservation rule を設計する。

### `tokyo_political_funds`

fixture strategy:

- 政治資金収支報告書 index fixture、政治団体名簿 fixture、収支報告書 PDF fixture を分ける。
- PDF fixture は text layer あり/なしを後続判定できるよう、page 単位の metadata を持つ。
- 寄附、収入、支出、資産等の表は page / table / row / column location に戻れる fixture だけを使う。

live acquisition conditions:

- live 取得は、対象年度、政治団体名簿との対応、PDF 件数、download 可否、rate limit、terms note、保存先を明示した手動実行に限る。
- PDF download、OCR 実行、table extraction 実行は通常 test / CI では行わない。
- OCR 要否は sample ごとの text layer 判定後に決める。政治資金 PDF 全体を一律 OCR 必須とは扱わない。

non-goals:

- 政治家本人、後援会、政党支部、資金管理団体を同一 entity にしない。
- 氏名、団体名、金額から FundingContact や RelationshipEdge を自動確定しない。
- 寄附や支出の政治的意味解釈は行わない。

parse / OCR uncertainties:

- PDF layout、text layer、scan 率、表構造、氏名・団体名 OCR 精度、金額単位は未検証。
- 金額、氏名、団体名は confidence、parse warning、page/table/cell location が揃う場合だけ machine extracted とする。

follow-up implementation issues:

- 政治資金 PDF sample set、OCR/text-layer 判定、table extraction evaluator を作る。
- PoliticalGroup anchor と FinanceReport の接続 contract を作る。
- FundingContact 生成前の review gate と entity-resolution policy を設計する。

### `tokyo_assembly_records_bills`

fixture strategy:

- 年度・定例会別の議案 page fixture、議決結果 fixture、請願・陳情 fixture、会議録検索 snapshot fixture を分ける。
- 会議録検索 fixture には検索条件、対象期間、会議種別、ページング、sort order、取得日時を metadata として残す。
- speech extraction fixture は meeting / speaker / speech block locator に戻れるものだけを使う。

live acquisition conditions:

- live 取得は、会議録検索システムの利用条件、robots、検索条件固定、ページング、rate limit、保存件数、対象期間、検索語なし取得の可否を確認してから手動実行する。
- 議案 page の static HTML fetch と会議録検索 snapshot は別 connector step として扱う。
- browser automation が必要な検索 UI は通常 test / CI では実行しない。

non-goals:

- 個人別賛否が source にない議案から VotePosition を推定生成しない。
- 議案上の契約案、電子調達の契約先、PublicMoneyFlow を自動同一視しない。
- 発言の評価、政策スタンス分類、意味解釈は行わない。

parse / OCR uncertainties:

- 初期対象の HTML page / search snapshot は OCR 不要の想定だが、添付 PDF や PDF 本文の有無は未検証。
- 会議録検索の安定 URL、検索条件再現、speech block の構造、過去分の layout 差は未検証。

follow-up implementation issues:

- 会議録検索 acquisition 条件と snapshot fixture を作る。
- 議案 / bill parser fixture、speech locator、DecisionEvent 生成 guard を作る。
- VotePosition 非生成 guard と契約案・PublicMoneyFlow 非同一視 guard をテスト化する。

## 共通 non-goals

- connector 実装、parser 実装、browser automation、PDF/OCR engine、table extraction 実装。
- live source 取得、外部 network、PDF download、OCR 実行。
- 金額、氏名、団体名、監査指摘、交付先、契約先、発言、議案の意味解釈。
- SubsidyProgram、PublicMoneyFlow、SpendingReviewSignal、AuditFinding、BudgetLine、ContractAward、FundingContact、Speech、Bill の生成。
- DB migration、API、Web UI、GitHub Issue mirror、PR 作成、push。

## 共通 follow-up issue list

1. source family ごとの `ConnectorDefinition` fixture registry を作る。
2. `search_ui_snapshot` の検索条件、ページング、sort order、取得日時、再現性 metadata を manifest contract に追加する。
3. PDF/text-layer/OCR 判定と table extraction evaluator を source family 別 fixture で作る。
4. `parse_warnings`、`confidence`、page / bbox / table cell locator を normalize contract に追加する。
5. entity-resolution と review gate が揃うまで、Company、PoliticalGroup、FundingContact、ContractAward、BudgetLine、AuditFinding、Speech、Bill を確定生成しない guard を作る。
6. live acquisition は source family ごとに conditions checklist を作り、通常 test / CI から分離する。

## 関連ページ

- [東京都補助金・助成金 ingest 初期仕様](tokyo-subsidy-ingest-spec.md) — Jurisdiction Profile と ingest/normalize 分離の基準。
- [東京都補助金・助成金 ingest ローカル issue ledger](tokyo-subsidy-ingest-issues.md) — `G2PR-007` の受け入れ条件と非対象。
- [東京都 PDF/OCR・表抽出 feasibility](tokyo-subsidy-pdf-ocr-feasibility.md) — PDF/OCR、confidence、parse warning の前提。
- [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md) — 公式入口と未解決点。
- [Data Sources](../../data-sources.md) — source family と acquisition / structuring design。
- [Spending Review](../../spending-review.md) — 支出検証 signal と断定回避の設計。

## 出典

- [Tokyo Subsidy Ingest Follow-up Connector Design Input Packet](tokyo-subsidy-ingest-followup-connector-design-input-packet.json)
- [Tokyo Subsidy Ingest Follow-up Connector Design Execution Handoff](tokyo-subsidy-ingest-followup-connector-design-execution-handoff.md)
- [東京都補助金・助成金 ingest 初期仕様](tokyo-subsidy-ingest-spec.md)
- [東京都補助金・助成金 ingest ローカル issue ledger](tokyo-subsidy-ingest-issues.md)
- [東京都 PDF/OCR・表抽出 feasibility](tokyo-subsidy-pdf-ocr-feasibility.md)
- [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md)
- [Data Sources](../../data-sources.md)
- [Spending Review](../../spending-review.md)
