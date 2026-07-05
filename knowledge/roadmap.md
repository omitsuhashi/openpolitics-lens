# Roadmap

## 結論

最初の自治体は東京都にする。理由は、都議会、選挙管理委員会、財務局、電子調達システムの公式入口が揃い、議会・議案・政治資金・選挙・予算・契約を同一自治体内で結びやすいから。

## Phase 0: Source Probe

期間目安: 1-2 週間。

成果:

- 東京都 source connector の feasibility report
- 5 種類の source から各 10 件の sample artifact
- parser warning taxonomy
- Evidence Item schema の確定
- 教育・子育ての SubsidyProgram と監査 source の sample artifact

対象 source:

- 東京都議会 会議録・速記録
- 東京都議会 提出議案と議決結果
- 東京都選挙管理委員会 選挙公報・選挙結果
- 東京都選挙管理委員会 政治資金収支報告書
- 東京都財務局・電子調達 契約/予算
- 都庁総合ホームページ 助成・補助金
- 東京都監査事務局 財政援助団体等監査・包括外部監査

Gate:

- 各 source で raw artifact を保存できる。
- source URL、取得日時、content hash を記録できる。
- Evidence Item を 1 source 10 件以上作れる。
- SpendingReviewSignal を public UI に出す前に、監査指摘とアプリ計算 signal を分けて保存できる。

## Phase 1: Evidence-first MVP

期間目安: 4-6 週間。

成果:

- 1 人の都議ページ
- 1 Policy Theme ページ
- 根拠付きタイムライン
- source viewer
- correction request の最小導線
- 教育・子育ての支出検証ページ

技術:

- PostgreSQL
- S3 compatible object storage
- Python ingest/normalize/API
- TypeScript Web
- monorepo service layout

GraphDB はこの段階では read-only projection の検証に留めてもよい。

Gate:

- 画面上のすべての claim から source URL と Evidence Item に戻れる。
- AI 要約を消してもアプリの主要価値が成立する。
- low-confidence extraction が public UI に混ざらない。
- `無駄遣い` と断定せず、支出検証シグナルとして表示できる。

## Phase 2: Graph Projection

期間目安: 3-5 週間。

成果:

- Public Actor、Policy Theme、FundingContact、PublicMoneyFlow、DecisionEvent の graph 表示
- `is_inferred=false` の確認済み edge 表示
- `is_inferred=true` の推定 edge を別 layer として表示

技術:

- Neo4j など GraphDB
- graph-builder batch job
- projection rebuild job

Gate:

- GraphDB を空にしても RDB から再生成できる。
- edge ごとに evidence list を表示できる。
- inferred edge の説明と limitations を表示できる。

## Phase 3: Scoring And Review Workflow

期間目安: 4-6 週間。

成果:

- Policy Involvement Score
- Funding Proximity Score
- Timeline Alignment Score
- Spending Review Signal Score
- admin review queue
- score run versioning

Gate:

- score factor から Evidence Item に戻れる。
- score method version を変更して再計算できる。
- correction request によって score が再計算される。

## Phase 4: Municipality Expansion

順序:

1. 横浜市
2. 大阪市
3. 神奈川県または他の政令市
4. 国会 data との横断

横展開の判断基準:

- 会議録・議案・採決の取得形式が安定している。
- 政治資金・選挙情報の管轄が明確。
- 契約・補助金 data の公式入口がある。
- 既存 schema に無理なく mapping できる。

## Recommended MVP Policy Theme

第一候補: 教育・子育て。

理由:

- 都議会議案、予算、委員会、選挙公報に出やすい。
- 契約・補助金・施設整備とも接続しやすい。
- 有権者にとって読みやすい。
- 将来的な補助金・契約・監査の支出検証に進めやすい。

第二候補: 公共事業。

理由:

- 契約案、入札、補正予算、委員会議論に接続しやすい。
- Public Money Flow の検証に向く。

最初に選ぶなら、教育・子育てを推奨する。公共事業は契約・業者・JV・入札制度の名寄せが重く、初期 MVP では誤解リスクも高い。

## 関連ページ

- [Data Sources](data-sources.md) — source 候補。
- [Spending Review](spending-review.md) — 補助金・契約・予算の検証設計。
- [Grand Design](architecture.md) — system design。
- [Service Layout](service-layout.md) — monorepo の実装 directory 構成。
- [ADR 0002: Tokyo first MVP](adr/0002-tokyo-first-mvp.md) — 東京都 first の判断。

## 出典

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md)
