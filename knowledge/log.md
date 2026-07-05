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
