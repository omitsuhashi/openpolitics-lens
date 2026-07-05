# Spending Review

## 結論

OpenPolitics Lens は将来的に、補助金、契約、予算、決算、指定管理、監査指摘を横断し、公金の流れに「追加確認すべき支出」がないかを見つけられる設計にする。

ただし、アプリは「無駄遣い」「不正」「便宜供与」を自動認定しない。表示上の canonical term は `SpendingReviewSignal` とし、日本語 UI では「支出検証シグナル」または「追加確認が必要な支出」と表現する。

教育・子育てを最初の Policy Theme にするのは妥当である。都議会、予算、教育委員会、子供政策連携室、福祉局、補助金、契約、監査が同一テーマでつながりやすく、公共事業よりも初期の名寄せと誤解リスクを抑えやすい。

## Scope

対象に含める。

- 補助金、助成金、給付金、交付金
- 委託、入札、随意契約、指定管理
- 予算、決算、執行率、不用額、繰越
- 監査報告、包括外部監査、財政援助団体等監査、住民監査請求結果
- 成果指標、実績報告、事業評価、政策計画

対象外にする。

- source がない無駄遣い認定
- 個別団体や人物への違法性断定
- 政策効果の因果関係の自動推定
- 私生活、住所、家族、未確認の噂

## Education And Childcare Entry Point

教育・子育てから切り込む理由:

- 子供政策連携室、教育委員会、福祉局、都議会、予算、補助金、open data が同一テーマで接続しやすい。
- 補助金や委託が施設、相談、事業者支援、学校・地域事業に現れやすい。
- 成果指標や統計が比較的見つけやすく、支出額だけでなく実績との比較ができる。
- 公共事業よりも、初期 MVP で業者、JV、下請、工事種別の重い名寄せに入りにくい。

最初の切り口:

1. 子育て・教育の SubsidyProgram を 10 件抽出する。
2. 各制度について、予算項目、所管局、対象者、申請期間、交付先公開有無、成果指標を紐付ける。
3. 公開されている場合だけ、個別交付先・契約先を PublicMoneyFlow として保持する。
4. 監査報告や包括外部監査で同一局・同一事業・同一団体の指摘があるかを結ぶ。

## Signal Model

SpendingReviewSignal は、次のような要素を evidence 付きで束ねる。

| signal_type | 内容 | 注意 |
|---|---|---|
| `budget_growth_without_indicator` | 予算増加に対して成果指標や実績報告が見つからない | 成果がないとは断定しない |
| `low_execution_or_large_carryover` | 執行率が低い、不用額や繰越が大きい | 予算技術上の理由を確認する |
| `repeat_vendor_or_recipient` | 同一事業者・団体への支出が続く | 不正や便宜を意味しない |
| `single_bid_or_no_competition` | 単独応札、随意契約、入札不調が続く | 契約制度上正当な場合がある |
| `audit_finding_linked` | 監査報告で同一事業・団体・所管に指摘がある | 公式監査の文言に限定する |
| `theme_money_political_proximity` | 政策テーマ、資金接点、公金支出が時系列上近い | 因果関係を示さない |

## Source Chain

支出検証では、単一 source で結論を出さない。

```text
Policy Theme
  -> PolicyMeasure / SubsidyProgram
  -> BudgetLine / SettlementLine
  -> ProcurementNotice / ContractAward / SubsidyGranted
  -> Company / Nonprofit / PoliticalGroup
  -> AuditFinding / PerformanceIndicator
  -> SpendingReviewSignal
```

各段階で SourceDocument と EvidenceItem を保持する。途中が欠ける場合、UI では「未接続」「未確認」と表示する。

## UI Rules

表示する:

- 「支出検証シグナル」
- 「追加確認が必要な支出」
- 「公式監査に基づく指摘」
- 「支出と成果指標の接続状況」
- 「未確認点」

表示しない:

- 「無駄遣い」
- 「不正」
- 「癒着」
- 「利益供与」
- 「税金を食い物にした」

監査報告に公式な指摘がある場合でも、アプリ側の要約は原文と分ける。監査の指摘、行政の措置、アプリの signal を別々に表示する。

## MVP Gate

最初の gate:

- 教育・子育ての SubsidyProgram を 10 件保存できる。
- そのうち 5 件以上で BudgetLine または PublicMoneyFlow に接続できる。
- 監査報告から AuditFinding を 5 件抽出できる。
- SpendingReviewSignal を 3 種類以上生成し、すべて EvidenceItem に戻せる。
- `無駄遣い` という断定ラベルを使わずに、ユーザーが「なぜ追加確認すべきか」を理解できる。

## 関連ページ

- [Data Sources](data-sources.md) — source family と取得方式。
- [Domain Model](domain-model.md) — SubsidyProgram、AuditFinding、SpendingReviewSignal。
- [Scoring](scoring.md) — Spending Review Signal Score。
- [Legal And Evidence Risk](legal-risk.md) — 表示文言と断定回避。
- [Roadmap](roadmap.md) — MVP gate。

## 出典

- [Tokyo Data Source Inventory](wiki/sources/2026-07-05-tokyo-data-source-inventory.md)
- [東京都監査事務局 財政援助団体等監査](https://www.kansa.metro.tokyo.lg.jp/kansaiin/zaiseienzyo)
- [東京都監査事務局 包括外部監査](https://www.kansa.metro.tokyo.lg.jp/houkatsugaibu)
- [都庁総合ホームページ 助成・補助金](https://www.metro.tokyo.lg.jp/purpose/grant)
