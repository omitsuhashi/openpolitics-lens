# インデックス

OpenPolitics Lens の設計・根拠・判断履歴に辿るための discovery surface。

## 目的別入口

### 全体設計を確認する

- [Grand Design](architecture.md) — システム境界、データパイプライン、保存方式、MVP の全体像。
- [Repository README](../README.md) — repo root からこの knowledge root への入口。

### データ取得方針を確認する

- [Data Sources](data-sources.md) — 取得対象、優先順位、自治体候補、取得難度。
- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md) — 2026-07-03 時点で確認した公式ページの要点。

### ドメインとスコアを確認する

- [Domain Model](domain-model.md) — Source Document、Evidence、Public Actor、Decision Event、Relationship Edge の構造。
- [Scoring](scoring.md) — 政策関与度、資金近接度、時系列一致などの計算方針。

### 法務・表示リスクを確認する

- [Legal And Evidence Risk](legal-risk.md) — 断定回避、出典表示、AI 要約、訂正申請、私生活除外の運用ルール。

### 導入順序を確認する

- [Roadmap](roadmap.md) — 東京都から始める理由、MVP scope、拡張順序。

### 戻しにくい判断を確認する

- [ADR 0001: Evidence-first hybrid store](adr/0001-evidence-first-hybrid-store.md) — RDB 正本、GraphDB projection、全文検索、原本保存の判断。
- [ADR 0002: Tokyo first MVP](adr/0002-tokyo-first-mvp.md) — 最初の自治体として東京都を選ぶ判断。

### LLM Wiki として読む

- [LLM Wiki Documentation Package](wiki/queries/2026-07-03-llm-wiki-documentation-package.md) — この文書群の knowledge root、canonical page、local override、更新手順。

## 現役ページ一覧

### Project Docs

- [Grand Design](architecture.md) — 政治過程を根拠付きで追跡するアプリケーションの全体設計。
  検索語: grand design, architecture, module, pipeline, data store, 設計, アーキテクチャ
- [Domain Model](domain-model.md) — ドメイン概念、正規化単位、関係 graph の境界を定義する。
  検索語: domain model, glossary, evidence, actor, vote, funding, contract, ドメイン, 証拠, 関係
- [Data Sources](data-sources.md) — 国会・自治体・政治資金・契約・予算・選挙公報の取得設計。
  検索語: data source, ingest, API, crawler, municipality, 自治体, データ取得
- [Scoring](scoring.md) — 断定を避けたスコアと explainability の設計。
  検索語: scoring, confidence, influence, proximity, timeline, スコア, 信頼度
- [Legal And Evidence Risk](legal-risk.md) — 名誉毀損、著作権、出典表示、訂正申請、推定表現のルール。
  検索語: legal, risk, correction, citation, defamation, 法務, 訂正, 出典
- [Roadmap](roadmap.md) — MVP、自治体選定、拡張順序、検証 gate をまとめる。
  検索語: roadmap, MVP, Tokyo, rollout, 自治体選定, 導入計画

### Sources

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md) — 公式ソースの確認結果と採用上の留保。
  検索語: official source, NDL, Shugiin, e-Stat, Tokyo, Yokohama, Osaka, 公式資料

### Queries

- [LLM Wiki Documentation Package](wiki/queries/2026-07-03-llm-wiki-documentation-package.md) — `knowledge/` knowledge root の canonical page、local override、更新手順をまとめる。
  検索語: llm-wiki, knowledge root, canonical page, local override, query note, wiki運用, 文書化

### ADR

- [ADR 0001: Evidence-first hybrid store](adr/0001-evidence-first-hybrid-store.md) — 保存技術の分担を RDB 正本、GraphDB projection、object storage、全文検索で定義。
  検索語: ADR, Postgres, graph database, OpenSearch, object storage, ハイブリッド構成
- [ADR 0002: Tokyo first MVP](adr/0002-tokyo-first-mvp.md) — 最初の自治体として東京都を採用する理由を記録。
  検索語: ADR, Tokyo, municipality, MVP, 東京都, 自治体
