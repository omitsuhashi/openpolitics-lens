# ログ

append-only で使う。verified claim、canonical page、`index.md`、draft decision、canonicalization action に影響する変更を追跡する。

## [2026-07-03] bootstrap | Initialize OpenPolitics Lens docs wiki

- `docs/` を single-root knowledge root として初期化。
- `docs/AGENTS.md`, `docs/index.md`, `docs/log.md`, `docs/raw/`, `docs/wiki/` を作成。
- repo root `AGENTS.md` を thin router として追加。
- `CONTEXT.md` に初期 glossary を追加。

## [2026-07-03] design | Grand design for political transparency application

- `architecture.md`, `domain-model.md`, `data-sources.md`, `scoring.md`, `legal-risk.md`, `roadmap.md` を追加。
- `wiki/sources/2026-07-03-official-data-source-check.md` を追加。
- `adr/0001-evidence-first-hybrid-store.md`, `adr/0002-tokyo-first-mvp.md` を追加。
- `index.md` に active page catalog と目的別入口を登録。
- repo root `README.md` から `docs/index.md` へ辿れる入口を追加。

## [2026-07-03] query | LLM Wiki documentation package

- `wiki/queries/2026-07-03-llm-wiki-documentation-package.md` を追加。
- `docs/` knowledge root の canonical page、local override、更新手順を明文化。
- `index.md` に LLM Wiki 用の目的別入口と Active Page Catalog entry を追加。

## [2026-07-04] canonicalize | Rehome knowledge root references

- Action: rehome
- Current knowledge root を `knowledge/` として明文化。
- repo root `AGENTS.md` と `README.md` の入口を `knowledge/` へ更新。
- `knowledge/AGENTS.md`, `knowledge/index.md`, `wiki/queries/2026-07-03-llm-wiki-documentation-package.md` の active reference を `knowledge/` に統一。

## [2026-07-05] query | Tokyo data source design

- `data-sources.md` を東京都 first の source family、coverage assessment、取得 pipeline、構造化方針で更新。
- `CONTEXT.md` に Source Family、Policy Measure、Public Consultation を追加。
- `wiki/sources/2026-07-05-tokyo-data-source-inventory.md` を追加し、東京都議会、選管、財務局、電子調達、教育委員会、子供政策連携室、都庁総合、open data の公式 source を記録。
- `wiki/queries/2026-07-05-tokyo-data-source-design.md` を追加し、現在の source 充足、取得方式、構造化方針、次の grilling 質問を記録。
- `index.md` に新しい source note と query note を追加。

## [2026-07-05] design | Spending review orientation

- 教育・子育てを最初の Policy Theme として確定し、将来的な PublicMoneyFlow 検証の足掛かりにする方針を記録。
- `spending-review.md` を追加し、補助金、契約、予算、決算、監査を横断する支出検証設計を定義。
- `CONTEXT.md` に Subsidy Program、Spending Review Signal、Audit Finding を追加。
- `domain-model.md`, `scoring.md`, `legal-risk.md`, `data-sources.md`, `roadmap.md`, `wiki/sources/2026-07-05-tokyo-data-source-inventory.md`, `wiki/queries/2026-07-05-tokyo-data-source-design.md`, `index.md` を支出検証方針に合わせて更新。

## [2026-07-05] design | Local datastore Docker Compose stack

- `compose.yaml` と `.env.example` を追加。
- ローカル datastore を PostgreSQL 18、MinIO、Neo4j、Meilisearch で固定。
- `local-infrastructure.md` を追加し、service、endpoint、volume、data ownership を明文化。
- `architecture.md`, `adr/0001-evidence-first-hybrid-store.md`, `index.md`, `README.md` から local datastore 構成へ辿れるように更新。

## [2026-07-05] design | Monorepo service layout

- `service-layout.md` を追加し、`apps/`, `services/`, `packages/`, `infra/` の責務と依存方向を定義。
- `apps/web`, `services/api`, `services/ingest`, `services/normalize`, `services/graph-builder`, `services/worker`, `packages/contracts`, `packages/db`, `packages/domain`, `infra/local`, `infra/scripts` を初期 directory として追加。
- 各 directory に責務 README を置き、runtime package は実装開始時に追加する方針を明記。
- `architecture.md`, `roadmap.md`, `index.md`, `README.md` から monorepo service layout へ辿れるように更新。

## [2026-07-05] design | Tokyo subsidy ingest spec draft

- `wiki/syntheses/tokyo-subsidy-ingest-spec.md` を追加し、`OPL-INGEST-SUBSIDY-20260705` の Spec Gate draft を作成。
- 補助金・助成金 first、ingest/normalize 分離、都庁助成・補助金入口 connector、filesystem first、fixture-first verification、jurisdiction/source family/connector 分離を採用判断として記録。
- `data-sources.md`, `service-layout.md`, `services/ingest/README.md`, `CONTEXT.md`, `index.md` を Source Document Candidate と ingest 責務境界に合わせて更新。

## [2026-07-05] gate | Approve Tokyo subsidy ingest spec

- `OPL-INGEST-SUBSIDY-20260705` の Spec Gate を承認済みに更新。
- 承認範囲は補助金・助成金 first、ingest/normalize 分離、filesystem first、jurisdiction/source family/connector 分離、後続深掘り項目の local issue 化。

## [2026-07-05] issue-gate | Draft Tokyo subsidy ingest local issue ledger

- `wiki/syntheses/tokyo-subsidy-ingest-issues.md` を追加し、`OPL-INGEST-SUBSIDY-20260705` の local issue ledger draft を作成。
- `G2PR-001` から `G2PR-003` を初回 PR 実装範囲、`G2PR-004` から `G2PR-007` を後続深掘り issue として記録。
- `index.md` に local issue ledger の catalog entry を追加。

## [2026-07-05] gate | Approve Tokyo subsidy ingest local issues

- `OPL-INGEST-SUBSIDY-20260705` の Issue Gate を承認済みに更新。
- `G2PR-001` から `G2PR-003` を初回 PR の実装対象、`G2PR-004` から `G2PR-007` を後続深掘り issue として承認。

## [2026-07-05] execution-plan | Draft Tokyo subsidy ingest packet

- `tokyo-subsidy-ingest-input-packet.json`, `tokyo-subsidy-ingest-execution-envelope.json`, `tokyo-subsidy-ingest-execution-handoff.md` を追加。
- 実行対象を `G2PR-001` から `G2PR-003` に限定し、execution envelope は `local_only` とした。
- remote `origin` は存在するが `gh` token invalid のため、push、GitHub Issue 作成、PR 作成は Remote Gate に残す。
- input packet、execution envelope、capability preflight、git reservation reconcile、`git diff --check` が通過。

## [2026-07-05] execution-plan | Update execution envelope base

- packet/evidence boundary commit `c968b79c9c5da1cd66b82eb8290ab42bb2a924a4` を `epic_base.sha` として execution envelope revision 3 に更新。

## [2026-07-05] implementation | G2PR-001 ingest contract foundation

- `G2PR-001` の worker 実装を review gate に通し、head `c539566450bcaf7aab265cd5f4568fcd9c687934` を `PR_READY` として記録。
- 初回レビューで manifest JSONL writer 欠落の Important 指摘があり、`manifest_relative_path()` と `append_jsonl()` を追加して再レビュー承認済み。
- `G2PR-002` の blocker を解除し、都庁助成・補助金 connector の fixture discovery/fetch 実装へ進める状態に更新。
