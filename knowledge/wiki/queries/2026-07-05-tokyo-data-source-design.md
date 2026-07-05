---
kind: query
created: 2026-07-05
updated: 2026-07-05
source_files: []
---

# 2026-07-05 Tokyo Data Source Design

## 結論

東京都を最初のターゲットにする場合、現在の data source 設計は「東京都の政治過程を Evidence-first に追う」には足りている。ただし「教育・子育て Policy Theme を、議会発言、議案、予算、契約、行政実施、成果指標まで横断して説明する」には足りない。

補うべき source family は、都議会の基礎名簿、請願・陳情、都庁の意見募集・審議会・計画、東京都教育委員会、子供政策連携室、東京都オープンデータである。

## 1. 現在のデータソースで情報は足りているか

足りているもの:

- 東京都議会の会議録・速記録、提出議案と議決結果。
- 東京都選挙管理委員会の選挙結果、選挙公報、政治資金収支報告書。
- 東京都財務局と電子調達システムの予算、決算、契約・入札入口。

不足しているもの:

- 議員名簿、会派構成、委員会名簿。人物・会派・委員会の anchor がないと発言や議案を安定して結べない。
- 請願・陳情、意見募集、審議会・検討会。市民・団体・専門家から行政・議会への入力が欠ける。
- 東京都教育委員会、子供政策連携室、福祉局などの政策実施 source。教育・子育ての Policy Measure を説明できない。
- 東京都オープンデータと統計・調査。背景値と成果指標が欠ける。

判断:

- 人物ページ MVP: 追加 source を含めれば成立する。
- 政策テーマページ MVP: 教育・子育て source を追加しないと弱い。
- 資金・契約 graph: P0 では限定表示に留める。政治資金 PDF/OCR、電子調達検索、事業者名寄せの検証が必要。

## 2. どのように情報を取得するのか

取得 pipeline は `discover -> fetch -> parse` に分ける。

### discover

Source Family ごとの入口 page から candidate URL を集める。

例:

- 東京都議会の年度・定例会 page。
- 東京都選管の公表年度 page。
- 財務局の予算・決算 page。
- 電子調達の検索条件付き result。
- 東京都教育委員会の政策・予算、計画、審議会、統計 page。
- 都庁総合ホームページの意見募集、審議会・検討会、計画・財政・予算 category。

### fetch

HTML、PDF、CSV、JSON、XML を RawArtifact として不変保存する。

必須 metadata:

- `source_system`
- `source_family`
- `canonical_url`
- `fetched_at`
- `content_hash`
- `media_type`
- `connector_version`
- `rate_limit_policy`
- `terms_note`
- `raw_artifact_uri`

### parse

RawArtifact から SourceDocument、EvidenceItem、EvidenceClaim、正規化済み entity/event を作る。

connector 型:

- `static_html_index`: 議員名簿、会派構成、議案一覧、請願・陳情、計画一覧。
- `html_detail`: 議案詳細、施策記事、審議会詳細。
- `search_ui_snapshot`: 会議録検索、電子調達。
- `pdf_batch`: 選挙公報、政治資金、予算・決算 PDF。
- `api_json_xml`: 国会 API、e-Stat、公開 API。
- `catalog_api_or_html`: 東京都オープンデータ。

## 3. どのように構造化していくのか

構造化は SourceDocument から直接言える claim を最小単位にする。

| Source Family | 構造化対象 | 注意点 |
|---|---|---|
| 都議会名簿 | Person, Faction, CouncilCommittee, Membership | 所属・役職は期間付き |
| 会議録・速記録 | Meeting, Speech, PoliticalStatement | 発言者名だけで自動名寄せしない |
| 議案・議決 | Bill, BillEvent, DecisionEvent | 個人別採決がなければ VotePosition は作らない |
| 請願・陳情 | Petition, PetitionEvent, PublicConsultation | 議案とは別 entity |
| 選挙 | Election, District, Candidate, ElectionResult, PoliticalStatement | 選挙公報は公約 source |
| 政治資金 | PoliticalGroup, FinanceReport, FundingContact | 本人と政治団体を同一視しない |
| 予算・契約 | BudgetLine, ProcurementNotice, BidResult, ContractAward, Company | 契約議案と落札結果を Evidence で結ぶ |
| 教育・子供施策 | PolicyMeasure, Plan, PerformanceIndicator, PublicConsultation | 成果や因果は自動 claim にしない |
| Open Data | IndicatorDataset, Facility, RegionStatistic | 背景値・補助 source として扱う |

不変条件:

- すべての表示は EvidenceItem に戻れる。
- AI 要約と原文は混ぜない。
- 推定 edge は `is_inferred=true` とし、確認済み edge と分ける。
- PDF/OCR 由来の金額・氏名・団体名は parse warning と confidence を必須にする。

## Grill Question 1

質問: 最初の Policy Theme を「教育・子育て」に固定し、東京都教育委員会と子供政策連携室を P0.5 source family として扱うか。

決定: 固定する。

理由:

- 東京都 first の ADR では、政策テーマ第一候補が教育・子育てになっている。
- 都議会議案、委員会、予算、選挙公報、教育委員会資料、子供政策連携室資料、open data が接続しやすい。
- 公共事業より、契約先・JV・法人名寄せの誤解リスクが低い。

固定しない場合:

- P0 source は政治過程一般に留まり、政策テーマページの具体性が下がる。
- connector は広くなるが、初期 MVP の検証対象が散る。

## Follow-up: Spending Review Orientation

追加方針:

- 将来的な主戦場は、補助金、契約、予算、決算、監査を横断した PublicMoneyFlow の検証である。
- 教育・子育ては、その足掛かりとして採用する。
- `無駄遣い` はユーザー課題として重要だが、domain model と UI では断定語にしない。canonical term は `SpendingReviewSignal`、日本語表示は「支出検証シグナル」または「追加確認が必要な支出」とする。
- 公式監査の指摘は `AuditFinding`、アプリが計算する注意 signal は `SpendingReviewSignal` として分ける。

次の設計質問:

教育・子育ての支出検証 MVP で、最初に深掘りする PublicMoneyFlow はどれにするか。

推奨: 補助金・助成金を最初にする。

理由:

- 都庁総合ホームページに助成・補助金の目的別入口がある。
- 財政援助団体等監査が補助金等を受ける団体の検証 source として接続しやすい。
- 契約・入札よりも、制度目的、対象者、交付先、実績、監査指摘を政策テーマに結びやすい。

代替:

- 契約・入札 first: 金額と事業者は追いやすいが、検索 UI、単独応札、随意契約、法人名寄せが重い。
- 予算・決算 first: 制度全体を把握しやすいが、個別の受益者や団体まで下りにくい。

## 関連ページ

- [Data Sources](../../data-sources.md) — canonical source design。
- [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md) — 公式 source の追加確認。
- [Tokyo first MVP ADR](../../adr/0002-tokyo-first-mvp.md) — 東京都 first の判断。
- [Spending Review](../../spending-review.md) — 補助金・契約・予算の検証設計。

## 出典

- [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md)
