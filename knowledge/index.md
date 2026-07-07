# インデックス

OpenPolitics Lens の設計・根拠・判断履歴に辿るための discovery surface。

## 目的別入口

### 全体設計を確認する

- [Grand Design](architecture.md) — システム境界、データパイプライン、保存方式、MVP の全体像。
- [Service Layout](service-layout.md) — monorepo の `apps/`, `services/`, `packages/`, `infra/` 構成と依存方向。
- [Local Infrastructure](local-infrastructure.md) — Docker Compose で起動する datastore service、endpoint、volume、初期 bucket。
- [Repository README](../README.md) — repo root からこの knowledge root への入口。

### データ取得方針を確認する

- [Data Sources](data-sources.md) — 取得対象、優先順位、自治体候補、取得難度。
- [Tokyo Subsidy Ingest Spec](wiki/syntheses/tokyo-subsidy-ingest-spec.md) — 東京都補助金・助成金 first の ingest 初期仕様と後続 issue 方針。
- [Phase 0 Remainder Implementation Design](wiki/syntheses/phase0-remainder-implementation-design.md) — Phase 0 残実装の承認済み Spec Gate、source family 横断 sample coverage、warning / locator contract 設計。
- [Phase 0 Remainder Issues](wiki/syntheses/phase0-remainder-issues.md) — Phase 0 残実装の承認済み local issue ledger、blocker graph、P0R-001 / P0R-002 実装結果。
- [Phase 0 P0R-001 Execution Handoff](wiki/syntheses/phase0-remainder-p0r-001-execution-handoff.md) — RawArtifact storage gate の Execution Plan Gate artifact と実行境界。
- [Phase 0 P0R-002 Execution Handoff](wiki/syntheses/phase0-remainder-p0r-002-execution-handoff.md) — Evidence schema / warning / claim catalog の Execution Plan Gate artifact と実行境界。
- [Tokyo Source Connector Design](wiki/syntheses/tokyo-source-connector-design.md) — 東京都の契約・入札、予算・決算、監査、政治資金、会議録・議案 connector 設計。
- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md) — 2026-07-03 時点で確認した公式ページの要点。
- [Tokyo Data Source Inventory](wiki/sources/2026-07-05-tokyo-data-source-inventory.md) — 東京都 source family の追加確認。

### ドメインとスコアを確認する

- [Domain Model](domain-model.md) — Source Document、Evidence、Public Actor、Decision Event、Relationship Edge の構造。
- [Scoring](scoring.md) — 政策関与度、資金近接度、時系列一致などの計算方針。
- [Spending Review](spending-review.md) — 補助金・契約・予算・監査を横断する支出検証設計。

### 法務・表示リスクを確認する

- [Legal And Evidence Risk](legal-risk.md) — 断定回避、出典表示、AI 要約、訂正申請、私生活除外の運用ルール。

### 導入順序を確認する

- [Roadmap](roadmap.md) — 東京都から始める理由、MVP scope、拡張順序。

### 戻しにくい判断を確認する

- [ADR 0001: Evidence-first hybrid store](adr/0001-evidence-first-hybrid-store.md) — RDB 正本、GraphDB projection、全文検索、原本保存の判断。
- [ADR 0002: Tokyo first MVP](adr/0002-tokyo-first-mvp.md) — 最初の自治体として東京都を選ぶ判断。

### LLM Wiki として読む

- [LLM Wiki Documentation Package](wiki/queries/2026-07-03-llm-wiki-documentation-package.md) — この文書群の knowledge root、canonical page、local override、更新手順。
- [Tokyo Data Source Design Query](wiki/queries/2026-07-05-tokyo-data-source-design.md) — 東京都 source の不足、取得方式、構造化方針。

## 現役ページ一覧

### Project Docs

- [Grand Design](architecture.md) — 政治過程を根拠付きで追跡するアプリケーションの全体設計。
  検索語: grand design, architecture, module, pipeline, data store, 設計, アーキテクチャ
- [Service Layout](service-layout.md) — monorepo の app/service/package/infra 境界と依存方向を定義する。
  検索語: service layout, monorepo, apps, services, packages, infra, folder, directory, フォルダ構成, ディレクトリ構成
- [Local Infrastructure](local-infrastructure.md) — ローカル Docker Compose の PostgreSQL、MinIO、Neo4j、Meilisearch 構成。
  検索語: docker compose, local infrastructure, PostgreSQL, MinIO, Neo4j, Meilisearch, datastore, ローカル, インフラ
- [Domain Model](domain-model.md) — ドメイン概念、正規化単位、関係 graph の境界を定義する。
  検索語: domain model, glossary, evidence, actor, vote, funding, contract, ドメイン, 証拠, 関係
- [Data Sources](data-sources.md) — 国会・自治体・政治資金・契約・予算・選挙公報の取得設計。
  検索語: data source, ingest, API, crawler, municipality, 自治体, データ取得
- [Spending Review](spending-review.md) — 補助金、契約、予算、決算、監査指摘から支出検証シグナルを作る設計。
  検索語: spending review, subsidy, contract, audit, public money, 支出検証, 補助金, 監査
- [Scoring](scoring.md) — 断定を避けたスコアと explainability の設計。
  検索語: scoring, confidence, influence, proximity, timeline, スコア, 信頼度
- [Legal And Evidence Risk](legal-risk.md) — 名誉毀損、著作権、出典表示、訂正申請、推定表現のルール。
  検索語: legal, risk, correction, citation, defamation, 法務, 訂正, 出典
- [Roadmap](roadmap.md) — MVP、自治体選定、拡張順序、検証 gate をまとめる。
  検索語: roadmap, MVP, Tokyo, rollout, 自治体選定, 導入計画
- [Tokyo Subsidy Ingest Spec](wiki/syntheses/tokyo-subsidy-ingest-spec.md) — 東京都の補助金・助成金 source を jurisdiction 分離と filesystem-first で ingest する初期仕様。
  検索語: ingest, subsidy, grants, Tokyo, jurisdiction, connector, filesystem, manifest, Source Document Candidate, 補助金, 助成金, 取得仕様
- [Tokyo Subsidy Ingest Issues](wiki/syntheses/tokyo-subsidy-ingest-issues.md) — 東京都補助金・助成金 ingest の local issue ledger と blocker graph。
  検索語: ingest, issue ledger, blocker graph, G2PR, subsidy, grants, jurisdiction, イシュー, 実装計画, 補助金, 助成金
- [Phase 0 Remainder Implementation Design](wiki/syntheses/phase0-remainder-implementation-design.md) — Phase 0 残実装の承認済み Spec Gate と source family 横断 sample / EvidenceItem / warning contract 設計。
  検索語: Phase 0, source probe, sample artifact, EvidenceItem, parse warning, locator, OPL-PHASE0-REMAINDER-20260707, 残実装, 実装設計
- [Phase 0 Remainder Issues](wiki/syntheses/phase0-remainder-issues.md) — Phase 0 残実装の承認済み local issue ledger、P0R-001 / P0R-002 実装結果、blocker graph。
  検索語: Phase 0, issue ledger, blocker graph, P0R, sample artifact, EvidenceItem, RawArtifact, MinIO, 残実装, 実装計画
- [Phase 0 P0R-001 Execution Handoff](wiki/syntheses/phase0-remainder-p0r-001-execution-handoff.md) — `P0R-001` RawArtifact storage gate の input packet / execution envelope への入口。
  検索語: Phase 0, P0R-001, execution packet, execution envelope, RawArtifact, MinIO, storage smoke, 実行計画, ハンドオフ
- [Phase 0 P0R-002 Execution Handoff](wiki/syntheses/phase0-remainder-p0r-002-execution-handoff.md) — `P0R-002` Evidence schema / warning / claim catalog の input packet / execution envelope への入口。
  検索語: Phase 0, P0R-002, execution packet, execution envelope, EvidenceItem, EvidenceClaim, parse warning, locator, claim catalog, 実行計画, ハンドオフ
- [Tokyo Subsidy PDF/OCR Feasibility](wiki/syntheses/tokyo-subsidy-pdf-ocr-feasibility.md) — PDF/OCR と表抽出の source family 別 feasibility、confidence、parse warning 方針。
  検索語: PDF, OCR, table extraction, confidence, parse warning, source family, G2PR-006, 表抽出, OCR方針
- [Tokyo Source Connector Design](wiki/syntheses/tokyo-source-connector-design.md) — 東京都の後続 source family connector registry と fixture / live acquisition 分離方針。
  検索語: connector, source family, procurement, budget, audit, political funds, assembly records, jurisdiction, G2PR-007, 契約, 入札, 予算, 決算, 監査, 政治資金, 会議録
- [Tokyo Subsidy Ingest Execution Handoff](wiki/syntheses/tokyo-subsidy-ingest-execution-handoff.md) — approved packet と execution envelope への実行ハンドオフ。
  検索語: ingest, execution packet, execution envelope, handoff, worker, local_only, 実行計画, ハンドオフ
- [Tokyo Subsidy Ingest Follow-up Persistence Handoff](wiki/syntheses/tokyo-subsidy-ingest-followup-persistence-execution-handoff.md) — `G2PR-004` の永続化 contract 実行ハンドオフ。
  検索語: ingest, persistence, PostgreSQL, MinIO, RawArtifact, migration, G2PR-004, 永続化, 実行計画
- [Tokyo Subsidy Ingest Follow-up Normalize Handoff](wiki/syntheses/tokyo-subsidy-ingest-followup-normalize-execution-handoff.md) — `G2PR-005` の EvidenceItem / EvidenceClaim normalize contract 実行ハンドオフ。
  検索語: ingest, normalize, EvidenceItem, EvidenceClaim, SourceDocument, G2PR-005, 正規化, 実行計画
- [Tokyo Subsidy Ingest Follow-up PDF/OCR Handoff](wiki/syntheses/tokyo-subsidy-ingest-followup-pdf-ocr-execution-handoff.md) — `G2PR-006` の PDF/OCR と表抽出 feasibility 実行ハンドオフ。
  検索語: ingest, PDF, OCR, table extraction, feasibility, G2PR-006, 表抽出, 実行計画
- [Tokyo Subsidy Ingest Follow-up Connector Design Handoff](wiki/syntheses/tokyo-subsidy-ingest-followup-connector-design-execution-handoff.md) — `G2PR-007` の source connector design 実行ハンドオフ。
  検索語: ingest, connector design, source family, G2PR-007, fixture, live acquisition, 実行計画, ハンドオフ

### Sources

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md) — 公式ソースの確認結果と採用上の留保。
  検索語: official source, NDL, Shugiin, e-Stat, Tokyo, Yokohama, Osaka, 公式資料
- [Tokyo Data Source Inventory](wiki/sources/2026-07-05-tokyo-data-source-inventory.md) — 東京都議会、選管、財務局、教育委員会、子供政策、open data の追加 source 確認。
  検索語: Tokyo data source, 東京都, 東京都議会, 選管, 教育委員会, 子供政策, open data

### Queries

- [LLM Wiki Documentation Package](wiki/queries/2026-07-03-llm-wiki-documentation-package.md) — `knowledge/` knowledge root の canonical page、local override、更新手順をまとめる。
  検索語: llm-wiki, knowledge root, canonical page, local override, query note, wiki運用, 文書化
- [Tokyo Data Source Design Query](wiki/queries/2026-07-05-tokyo-data-source-design.md) — 東京都 source の充足判断、取得 pipeline、構造化単位、次の grilling 質問をまとめる。
  検索語: Tokyo source design, data source, discover, fetch, parse, source family, 構造化, 取得設計

### ADR

- [ADR 0001: Evidence-first hybrid store](adr/0001-evidence-first-hybrid-store.md) — 保存技術の分担を RDB 正本、GraphDB projection、object storage、全文検索で定義。
  検索語: ADR, Postgres, graph database, OpenSearch, object storage, ハイブリッド構成
- [ADR 0002: Tokyo first MVP](adr/0002-tokyo-first-mvp.md) — 最初の自治体として東京都を採用する理由を記録。
  検索語: ADR, Tokyo, municipality, MVP, 東京都, 自治体
