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

## [2026-07-05] implementation | G2PR-002 Tokyo grants fixture connector

- `G2PR-002` の worker 実装を review gate に通し、head `d6c9cfca93a3bfb07c10117deba9d3ebe3bd62bd` を `PR_READY` として記録。
- `tokyo_metro_grants` connector は fixture HTML discovery と fake fetch に限定し、live network、DB/MinIO、normalize、Evidence、SpendingReviewSignal には踏み込まない。
- `G2PR-003` の blocker を解除し、CLI と README 整備へ進める状態に更新。

## [2026-07-05] implementation | G2PR-003 ingest CLI and README

- `G2PR-003` の worker 実装を review gate に通し、head `145ef85478362b4df279bc2f75e6b210ac091419` を `PR_READY` として記録。
- fixture CLI は local HTML、output directory、run id を受け取り、manifest と raw artifact を filesystem に生成する。
- `--live` は明示 option として残し、初回 PR では network request を行わない guard に留めた。

## [2026-07-05] remote | Open Tokyo subsidy ingest draft PR

- remote `main` と `codex/ingestpr` を push し、draft PR [#1](https://github.com/omitsuhashi/openpolitics-lens/pull/1) を作成。
- PR は `main` base、`codex/ingestpr` head、draft/open/mergeable として確認済み。

## [2026-07-05] execution-plan | Draft G2PR-004 persistence packet

- `tokyo-subsidy-ingest-followup-persistence-input-packet.json`, `tokyo-subsidy-ingest-followup-persistence-execution-envelope.json`, `tokyo-subsidy-ingest-followup-persistence-execution-handoff.md` を追加。
- 初回 PR [#1](https://github.com/omitsuhashi/openpolitics-lens/pull/1) の head を土台に、`G2PR-004` を後続 issue の最初の実行対象にした。
- live PostgreSQL / MinIO 接続ではなく、migration SQL、object storage key contract、fake writer、DB row payload 生成の contract 固定に scope を限定した。

## [2026-07-05] implementation | G2PR-004 ingest persistence contract

- `G2PR-004` の worker 実装を review gate に通し、worker head `406f65cdc3a78782b37ac1974e9eb67dcb39a9c9` を `COMPLETE` として記録。
- `packages/db` に `raw_artifacts` と `source_document_candidates` の migration SQL を追加し、`raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}` の object key contract を固定。
- `services/ingest` に S3 / MinIO 互換 object storage writer contract と `FetchManifestRecord` から DB row payload を作る helper を追加。
- review 指摘に従い、candidate と raw artifact の invariant、object metadata reserved key の case-insensitive collision check、SQL text inspection を強化。
- verification は `uv run pytest -q` 26 passed、`uv run ruff check .` passed、`uv run ruff format --check .` passed、`git diff --check` passed。

## [2026-07-05] execution-plan | Draft G2PR-005 normalize packet

- `tokyo-subsidy-ingest-followup-normalize-input-packet.json`, `tokyo-subsidy-ingest-followup-normalize-execution-envelope.json`, `tokyo-subsidy-ingest-followup-normalize-execution-handoff.md` を追加。
- `G2PR-004` 完了後の head を土台に、`G2PR-005` を次の後続 issue として実行対象にした。
- 初期 normalize は SourceDocument / EvidenceItem / EvidenceClaim の最小 contract と grant program page title の観測 claim に限定した。
- SubsidyProgram、PublicMoneyFlow、SpendingReviewSignal、entity resolution、PDF/OCR、live PostgreSQL / MinIO は非対象として残した。

## [2026-07-05] implementation | G2PR-005 normalize evidence contract

- `G2PR-005` の worker 実装を review gate に通し、worker head `c4402becf6bf6f2c2adcfd3cbbbc59a6ee3dc06e` を `COMPLETE` として記録。
- `services/normalize` に SourceDocument、EvidenceItem、EvidenceClaim、NormalizeResult の最小 contract と grant program page HTML title normalizer を追加。
- `packages/db` に `source_documents`, `evidence_items`, `evidence_claims` の migration SQL を追加。
- review 指摘に従い、`raw_artifact_id` の normalize contract 反映、observed title semantics、source type / media type validation、quote text と normalized text の分離、non-goal boundary test を強化。
- verification は `uv run pytest -q` 39 passed、`uv run ruff check .` passed、`uv run ruff format --check .` passed、`git diff --check` passed。

## [2026-07-05] execution-plan | Draft G2PR-006 PDF/OCR feasibility packet

- `tokyo-subsidy-ingest-followup-pdf-ocr-input-packet.json`, `tokyo-subsidy-ingest-followup-pdf-ocr-execution-envelope.json`, `tokyo-subsidy-ingest-followup-pdf-ocr-execution-handoff.md` を追加。
- `G2PR-006` を docs-first の feasibility issue とし、source family 別に OCR 要否、表抽出、confidence、parse warning 方針を記録する scope に限定した。
- PDF/OCR engine、parser 実装、live source 取得、意味解釈、DB migration、API、Web UI は非対象として残した。

## [2026-07-05] implementation | G2PR-006 PDF/OCR feasibility

- `G2PR-006` の worker 実装を review gate に通し、worker head `be9b9409af2d97247cd25bd68ab3649ce32d17ea` を `COMPLETE` として記録。
- `wiki/syntheses/tokyo-subsidy-pdf-ocr-feasibility.md` を追加し、補助金、政治資金、監査、契約・入札、予算・決算、会議録・議案の source family 別 feasibility を整理。
- OCR 要否、parser approach、table extraction、confidence policy、parse warning policy、後続 implementation issue を記録。
- review 指摘に従い、政治資金、契約・入札、会議録・議案の OCR 判定を「未検証」と「初期対象では不要」に分けて明確化。
- verification は `git diff --check` passed。

## [2026-07-05] execution-plan | Draft G2PR-007 connector design packet

- `tokyo-subsidy-ingest-followup-connector-design-input-packet.json`, `tokyo-subsidy-ingest-followup-connector-design-execution-envelope.json`, `tokyo-subsidy-ingest-followup-connector-design-execution-handoff.md` を追加。
- `G2PR-007` を docs-first の connector design issue とし、契約・入札、予算・決算、監査、政治資金、会議録・議案の source family registry を固定する scope に限定した。
- live source 取得、browser automation、PDF download、OCR 実行、connector / parser / DB / API / UI 実装、GitHub Issue mirror は非対象として残した。

## [2026-07-05] implementation | G2PR-007 source connector design

- `G2PR-007` の worker 実装を review gate に通し、worker head `06b52e1aac2a0d088377669c6ef14fabbe6e8a5b` を `COMPLETE` として記録。
- `wiki/syntheses/tokyo-source-connector-design.md` を追加し、`tokyo_procurement`、`tokyo_budget_settlement`、`tokyo_audit_reports`、`tokyo_political_funds`、`tokyo_assembly_records_bills` の registry、fixture strategy、live acquisition conditions、non-goals、parse / OCR uncertainties、後続 implementation issue を整理。
- jurisdiction 分離により、東京都固有の allowlist、rate limit、terms note、fixture、output path を future national / Yokohama / Osaka / other municipality connector へ漏らさない方針を明記。
- verification は `git diff --check` passed。独立レビューで Critical / Important / Minor なし。

## [2026-07-07] implementation | Remove ingest `--live` flag

- `tokyo-metro-grants` CLI から `--live` option を廃止し、`fixture` と `run` subcommand に分離。
- `fixture` は local HTML と fake fetcher だけを使う deterministic verification path とした。
- `run` は将来の cron / daily ingest 用 entrypoint として予約し、live fetch 実装前は network request を行わず status 2 で終了する。
- `services/ingest/README.md` と `tokyo-subsidy-ingest-spec.md` / issue ledger を `--live` 廃止後の方針へ更新。

## [2026-07-07] review-fix | Align ingest packets with current spec

- code review 指摘に従い、ingest input packet と follow-up input packet の `approved_hash` を現行 `tokyo-subsidy-ingest-spec.md` の hash に更新。
- `G2PR-003` の input packet acceptance criteria を `tokyo-metro-grants fixture` / `run` 分離と `--live` 廃止後の CLI 方針へ揃えた。

## [2026-07-07] design | Phase 0 remainder implementation draft

- `wiki/syntheses/phase0-remainder-implementation-design.md` を追加し、`OPL-PHASE0-REMAINDER-20260707` の Spec Gate draft を作成。
- Phase 0 残実装を common contract first、fixture-only verification、source family 横断 sample coverage、parse warning / locator contract、candidate-first の `SubsidyProgram` / `AuditFinding` として設計した。
- `SpendingReviewSignal`、public UI、score、GraphDB projection、live acquisition、GitHub mirror / PR は非目標として残した。
- `index.md` に discovery entry を追加した。

## [2026-07-07] review-fix | Align Phase 0 draft with roadmap storage gate

- `roadmap.md` の Phase 0 gate に照らし、RawArtifact の S3 互換 object storage 保存、RDB `raw_artifacts` payload、source URL、取得日時、content hash を `phase0-remainder-implementation-design.md` の受け入れ条件へ追加した。
- local MinIO bucket `openpolitics-raw` の smoke verification を通常 test から分ける方針を追記した。
- `local-infrastructure.md` と `architecture.md` の object key 表記を、実装済み migration / object writer と同じ `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}` へ揃えた。

## [2026-07-07] design | Re-scope Phase 0 remainder against roadmap

- `phase0-remainder-implementation-design.md` に Roadmap 対照表を追加し、Phase 0 の成果、対象 source、Gate を現状・不足・実装設計・対応 issue に分解した。
- Roadmap 対象 source 7 系統をすべて Phase 0 probe 対象として扱い、`P0R-001` から `P0R-012` へ issue 分解を組み替えた。
- `SpendingReviewSignal` を完全非対象にせず、public 表示と score は非目標のまま、`AuditFindingCandidate` と app-calculated signal candidate の保存分離 contract を Phase 0 scope に戻した。

## [2026-07-07] design | Fix local MinIO runtime contract

- `.env.local` を local runtime file とし、Compose command は `--env-file .env.local` を明示する方針に更新。
- Phase 0 RawArtifact smoke の MinIO 起動入口を `docker compose --env-file .env.local up -d minio minio-init` に固定。

## [2026-07-07] gate | Approve Phase 0 remainder spec

- `OPL-PHASE0-REMAINDER-20260707` の Spec Gate を承認済みに更新。
- 承認範囲は common contract first、fixture-only verification、source family 横断 sample coverage、S3 互換 RawArtifact storage gate、`.env.local` + local MinIO smoke、candidate-first の `SubsidyProgram` / `AuditFinding`、監査指摘と app-calculated signal candidate の保存分離。
- リモート方針は `local_only` のまま維持し、GitHub mirror / PR / live acquisition は別 gate に残す。

## [2026-07-07] issue-gate | Draft Phase 0 remainder local issue ledger

- `wiki/syntheses/phase0-remainder-issues.md` を追加し、`OPL-PHASE0-REMAINDER-20260707` の local issue ledger draft を作成。
- `P0R-001` から `P0R-012` を RawArtifact storage、Evidence schema、source registry、Roadmap 対象 source 7 系統、監査 signal 分離、coverage report に分解した。
- `P0R-001` だけを `実行可能` とし、`P0R-002` 以降は blocker graph に従って `ブロック中` にした。
- `index.md` に Phase 0 remainder issues の discovery entry を追加した。

## [2026-07-07] gate | Approve Phase 0 remainder local issues

- `OPL-PHASE0-REMAINDER-20260707` の Issue Gate を承認済みに更新。
- `P0R-001` から `P0R-012` の local issue ledger、blocker graph、依存順、実行可能 / ブロック中 status、acceptance criteria を承認済みとした。
- `P0R-001` だけを初期実行可能 issue とし、GitHub Issue mirror / PR / live acquisition は別 gate に残した。

## [2026-07-07] execution-plan | Approve P0R-001 storage gate packet

- `phase0-remainder-p0r-001-input-packet.json`、`phase0-remainder-p0r-001-execution-envelope.json`、`phase0-remainder-p0r-001-execution-handoff.md` を追加。
- Execution Envelope は schema version 3 とし、`phase_branch_policy`、worker-only execution、local-only remote policy を明示した。
- 実行対象は最初の runnable issue である `P0R-001` に限定し、`P0R-002` 以降は blocker graph に残した。
- execution prereq、input packet validation、execution envelope validation、capability preflight、`git diff --check` は通過。

## [2026-07-07] implementation | P0R-001 RawArtifact storage gate

- `P0R-001` の worker 実装を review gate に通し、head `9045c8fd6aef5b41d29386e5514310c77f12f100` を local `PR_READY` として記録。
- local MinIO smoke CLI、S3 互換 PUT / HEAD metadata verification、RDB `raw_artifacts` payload 照合、`minio-init` one-shot contract、README / local infrastructure docs を追加した。
- review 指摘に従い、外部 S3 endpoint / AWS credential fallback を PUT 前に拒否し、PUT 後の `head_object` unavailable を `skipped` ではなく failure として扱うようにした。
- verification は `uv run pytest -q` 54 passed、`uv run ruff check .` passed、`uv run ruff format --check .` passed、`git diff --check` passed。外部 endpoint guard は PUT 前の `status: failed` を確認した。
- live MinIO PUT / HEAD は sandbox では未実行のため、`.env.local` と Docker Compose による手動 smoke は local 環境依存として残る。`P0R-002` の blocker を解除し、次の実行可能 issue とした。

## [2026-07-07] execution-plan | Approve P0R-002 evidence contract packet

- `phase0-remainder-p0r-002-input-packet.json`、`phase0-remainder-p0r-002-execution-envelope.json`、`phase0-remainder-p0r-002-execution-handoff.md` を追加。dependency validation のため、完了済み prerequisite として `P0R-001` も packet / envelope に含めた。
- `P0R-001` head `9045c8fd6aef5b41d29386e5514310c77f12f100` を blocker head base とし、`P0R-002` branch をそこから作る方針にした。
- 実行対象は EvidenceItem / EvidenceClaim の schema、warning、locator、claim catalog 拡張に限定し、source registry、source probe、PDF/OCR 実行、live DB apply は非対象に残した。

## [2026-07-07] implementation | P0R-002 evidence warning catalog

- `P0R-002` の worker 実装を review gate に通し、head `a66fca34b24a965fae35d2611abf023a1b69c941` を local `PR_READY` として記録。
- `EvidenceItem` に `location_metadata`、`parse_warnings`、`extraction_artifact_path` を追加し、PDF / table / search snapshot の locator と warning を serialized contract / tests に反映した。
- `EvidenceClaim` は claim type / predicate catalog を code-side に持つようにし、`grant_program_page_title_observed` だけに閉じた制限を外した。low confidence、blocking warning、locator 不足では claim 昇格しない guard を追加した。
- verification は `uv run pytest -q` 60 passed、`uv run ruff check .` passed、`uv run ruff format --check .` passed、`git diff --check` passed。独立レビューで Critical / Important / Minor なし。
- live database migration apply は未実施のまま残し、`P0R-003` の blocker を解除して次の実行可能 issue とした。
