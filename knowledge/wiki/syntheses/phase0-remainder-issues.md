---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: implementation-active
spec: phase0-remainder-implementation-design.md
spec_gate_commit: 90a2e00
---

# Phase 0 残実装ローカル issue ledger

## 結論

`OPL-PHASE0-REMAINDER-20260707` では、Roadmap の Phase 0 gate を満たすため、まず RawArtifact / Evidence / source registry の共通 contract を固め、その後 Roadmap 対象 source 7 系統の fixture-first probe を実装する。

`P0R-001` から `P0R-008` は実装レビュー承認済みで local `PR_READY` になった。`P0R-009` と `P0R-010` は実行可能である。GitHub Issue mirror、push、PR 作成、live acquisition は行わない。

## Ledger

| Epic ID | ローカルID | タイトル | レビュー状態 | 実行状態 | ブロック元 | ブロック先 | GitHub Issue | 実装レビュー | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPL-PHASE0-REMAINDER-20260707 | P0R-001 | RawArtifact storage gate を確定する | 承認済み | PR_READY | なし | P0R-002, P0R-003 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-002 | Evidence schema / warning / claim catalog を拡張する | 承認済み | PR_READY | P0R-001 | P0R-003 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-003 | Phase 0 source registry / fixture harness を作る | 承認済み | PR_READY | P0R-001, P0R-002 | P0R-004, P0R-005, P0R-006, P0R-007, P0R-008, P0R-009, P0R-010 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-004 | 都議会 会議録・速記録 probe を実装する | 承認済み | PR_READY | P0R-003 | P0R-012 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-005 | 都議会 提出議案・議決結果 probe を実装する | 承認済み | PR_READY | P0R-003 | P0R-012 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-006 | 選挙公報・選挙結果 probe を実装する | 承認済み | PR_READY | P0R-003 | P0R-012 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-007 | 政治資金収支報告書 probe を実装する | 承認済み | PR_READY | P0R-003 | P0R-012 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-008 | 財務局・電子調達 契約/予算 probe を実装する | 承認済み | PR_READY | P0R-003 | P0R-012 | 未作成 | 承認済み | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-009 | 助成・補助金 `SubsidyProgramCandidate` probe を実装する | 承認済み | 実行可能 | P0R-003 | P0R-012 | 未作成 | 未実施 | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-010 | 監査 source / `AuditFindingCandidate` probe を実装する | 承認済み | 実行可能 | P0R-003 | P0R-011, P0R-012 | 未作成 | 未実施 | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-011 | 監査指摘とアプリ計算 signal の保存分離 contract を作る | 承認済み | ブロック中 | P0R-010 | P0R-012 | 未作成 | 未実施 | 未作成 |
| OPL-PHASE0-REMAINDER-20260707 | P0R-012 | Phase 0 feasibility report / coverage CLI を作る | 承認済み | ブロック中 | P0R-004, P0R-005, P0R-006, P0R-007, P0R-008, P0R-009, P0R-010, P0R-011 | なし | 未作成 | 未実施 | 未作成 |

## Blocker graph

```text
P0R-001 -> P0R-002 -> P0R-003
P0R-001 -> P0R-003
P0R-003 -> P0R-004 -> P0R-012
P0R-003 -> P0R-005 -> P0R-012
P0R-003 -> P0R-006 -> P0R-012
P0R-003 -> P0R-007 -> P0R-012
P0R-003 -> P0R-008 -> P0R-012
P0R-003 -> P0R-009 -> P0R-012
P0R-003 -> P0R-010 -> P0R-011 -> P0R-012
P0R-010 -> P0R-012
```

cycle はない。`P0R-001` から `P0R-008` は local `PR_READY` になったため、`P0R-009` と `P0R-010` が実行可能である。`P0R-004` から `P0R-010` は `P0R-003` 完了後に並列実行できるが、worker slot は 1 のため coordinator は 1 issue ずつ dispatch する。`P0R-011` は `P0R-010` 完了後、`P0R-012` は source probe と保存分離 contract 完了後に実行する。

## P0R-001: RawArtifact storage gate を確定する

### 目的

Phase 0 の RawArtifact 保存を、S3 互換 object storage と RDB `raw_artifacts` payload の共通 gate として固定する。

### 実装範囲

- `.env.local` と `docker compose --env-file .env.local up -d minio minio-init` を local MinIO 起動入口として扱う。
- `openpolitics-raw` bucket、versioning、path-style access、host endpoint / internal endpoint の contract を verification 可能にする。
- `ObjectStorageOutputWriter` と `FetchManifestRecord` から、`object_bucket`、`object_key`、`raw_artifact_path`、`canonical_url`、`fetched_at`、`content_hash`、`media_type`、`byte_size`、`connector_version`、`terms_note` を含む RDB payload を作る。
- local MinIO smoke command を追加または固定する。Docker / MinIO がない環境では通常 test を失敗させない。

### 受け入れ条件

- fake object storage test が object key `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}`、metadata、reserved metadata guard を確認する。
- local MinIO smoke が利用可能な環境で 1 artifact の put / metadata / RDB payload 照合を実行できる。
- `minio-init` は one-shot initializer として扱われ、常駐前提にならない。
- `.env.local` は git 管理外のまま維持される。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

手動 integration:

```bash
docker compose --env-file .env.local up -d minio minio-init
docker compose --env-file .env.local ps minio minio-init
cd services
uv run python -m ingest storage-smoke \
  --bucket openpolitics-raw \
  --endpoint http://localhost:9000
```

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-001-rawartifact-storage-gate`
- base: `f63f6afefadc4da323cc2a11d5eea53a3f472f81`
- head: `9045c8fd6aef5b41d29386e5514310c77f12f100`
- review range: `f63f6afefadc4da323cc2a11d5eea53a3f472f81..9045c8fd6aef5b41d29386e5514310c77f12f100`
- 実装レビュー: 承認済み。初回レビューで `storage-smoke` が任意の外部 S3 endpoint / AWS credential fallback を採用できる点と、PUT 後の metadata verification 不可を `skipped` にしていた点を修正した。再レビューで Critical / Important / Minor なし。
- 実装内容: `compose.yaml` の `minio-init` one-shot 化、local MinIO smoke CLI、S3 互換 PUT / HEAD metadata verification、RDB `raw_artifacts` payload 照合、local endpoint guard、fake object storage tests、README / local infrastructure docs を追加した。
- verification: `uv run pytest -q` は 54 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。外部 endpoint guard は `storage-smoke --endpoint https://s3.ap-northeast-1.amazonaws.com` が PUT 前に `status: failed` で終了することを確認した。
- 残リスク: この sandbox では live MinIO PUT / HEAD は未実行。`docker compose --env-file .env.local up -d minio minio-init` 後の手動 smoke は local Docker / MinIO 環境依存として残る。
- blocker release: `P0R-002` を次の実行可能 issue とする。

## P0R-002: Evidence schema / warning / claim catalog を拡張する

### 目的

HTML title だけでなく、PDF、table、search snapshot、OCR 由来の EvidenceItem を Phase 0 source family 横断で表現できるようにする。

### 実装範囲

- `EvidenceItem` Python contract と DB migration に `location_metadata`、`parse_warnings`、`extraction_artifact_path` を追加する。
- warning catalog を code-side に定義し、serialized contract / test で検証する。
- `EvidenceClaim` の claim type / predicate catalog を source family 横断で扱えるようにする。
- locator 不足または low confidence の場合、EvidenceClaim へ昇格しない guard を入れる。

### 受け入れ条件

- `parse_warnings` と locator metadata が Python contract、DB migration、serialized contract、tests に反映される。
- `grant_program_page_title_observed` だけに閉じた claim type 制限を外し、catalog 管理になる。
- 既存 `grant_program_page` normalize test は後方互換で通る。
- PDF / table / search snapshot 用の warning と locator の最小 fixture test がある。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-002-evidence-schema-warning-catalog`
- base: `9045c8fd6aef5b41d29386e5514310c77f12f100`
- head: `a66fca34b24a965fae35d2611abf023a1b69c941`
- review range: `9045c8fd6aef5b41d29386e5514310c77f12f100..a66fca34b24a965fae35d2611abf023a1b69c941`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `EvidenceItem` に `location_metadata`、`parse_warnings`、`extraction_artifact_path` を追加し、PDF / table / search snapshot の locator と warning を serialized contract / tests で確認した。`EvidenceClaim` は claim type / predicate catalog を code-side に持ち、`grant_program_page_title_observed` だけに閉じた制限を外した。low confidence、blocking warning、locator 不足では claim 昇格しない guard を追加した。
- verification: `uv run pytest -q` は 60 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: live database migration apply は未実施。P0R-002 は contract / SQL text inspection / unit test までの scope とする。
- blocker release: `P0R-003` を次の実行可能 issue とする。

## P0R-003: Phase 0 source registry / fixture harness を作る

### 目的

Roadmap 対象 source 7 系統を、source family registry、fixture metadata、coverage target から一貫して参照できるようにする。

### 実装範囲

- Roadmap 対象 source 7 系統の `jurisdiction_id`、`source_system`、`source_family`、`connector_id`、`source_type`、`retrieval_method`、`terms_note`、`evidence_granularity` を registry 化する。
- fixture catalog に `canonical_url`、`fetched_at` / `retrieved_at`、`media_type`、`byte_size`、expected evidence count を持たせる。
- source family ごとの coverage target を定義する。
- 通常 test が外部 network、browser automation、PDF download、OCR 実行を行わないことを guard する。

### 受け入れ条件

- Roadmap 対象 source 7 系統すべてが registry に現れる。
- fixture harness が source family ごとの RawArtifact / SourceDocumentCandidate / EvidenceItem 件数を集計できる。
- `P0R-004` から `P0R-010` が同じ registry / fixture harness を使える。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-003-source-registry-fixture-harness`
- base: `a66fca34b24a965fae35d2611abf023a1b69c941`
- head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- review range: `a66fca34b24a965fae35d2611abf023a1b69c941..7fb7c999aa4f67410379da2fa25a0cf248de2975`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `services/ingest/phase0_sources.py` を追加し、Roadmap 対象 source 7 系統の registry、fixture metadata、coverage target、fixture coverage summary、通常 test の forbidden operation guard を実装した。`ingest.__all__` から後続 issue が同じ registry / harness を参照できるようにした。
- verification: `uv run pytest -q` は 65 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: `P0R-004` から `P0R-010` の individual source probe fixture / parser は未実装。
- blocker release: `P0R-004` から `P0R-010` を実行可能 issue とする。

## P0R-004: 都議会 会議録・速記録 probe を実装する

### 目的

会議録・速記録から、検索条件と発言 locator に戻れる EvidenceItem を作る。

### 実装範囲

- 会議録検索 snapshot fixture を追加する。
- 検索 form URL、query parameters、対象期間、page number、sort order、snapshot timestamp を metadata として保持する。
- meeting、speaker、speech block locator を `location_metadata` に保存する。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。

### 受け入れ条件

- speech text の直接観測 claim は作れるが、政策 stance や意味分類は生成しない。
- browser automation / live search は通常 test に入らない。
- EvidenceItem から raw artifact と search snapshot 条件へ戻れる。

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-004-assembly-records-probe`
- base: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- head: `73931c27f20628a58318c0a07db92ef42507b6fa`
- review range: `7fb7c999aa4f67410379da2fa25a0cf248de2975..73931c27f20628a58318c0a07db92ef42507b6fa`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `services/ingest/tokyo_assembly_records.py` を追加し、都議会 会議録・速記録の fixture-only probe、検索 snapshot metadata、meeting / speaker / speech block locator、10 RawArtifact / SourceDocumentCandidate を生成できるようにした。`normalize_assembly_records_search_snapshot` で 10 EvidenceItem と `speech_text_observed` direct claim を生成し、政策 stance / 意味分類は生成しない guard を追加した。
- verification: `uv run pytest -q` は 69 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: fixture contents は deterministic synthetic snapshot であり、live Tokyo Assembly search result ではない。live search は明示的に非対象。
- blocker release: `P0R-012` はまだ `P0R-005` から `P0R-011` 待ち。次は `P0R-005` から `P0R-010` のいずれかを実行可能 issue とする。

## P0R-005: 都議会 提出議案・議決結果 probe を実装する

### 目的

提出議案と議決結果から、議案番号、件名、議決結果の observed claim を作る。

### 実装範囲

- 年度・定例会別の bill / decision fixture を追加する。
- `bill_decision_observed` などの claim type を catalog に追加する。
- 議案番号、件名、議決結果、会期、source URL を locator 付きで保存する。

### 受け入れ条件

- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。
- source に個人別賛否がない場合、`VotePosition` を生成しない guard がある。

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-005-assembly-bills-decisions-probe`
- base: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- head: `240bd37c26eda7ffdac5002a7ad21cda251c70cf`
- review range: `7fb7c999aa4f67410379da2fa25a0cf248de2975..240bd37c26eda7ffdac5002a7ad21cda251c70cf`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `services/ingest/tokyo_assembly_bills.py` を追加し、都議会 提出議案・議決結果の fixture-only probe、年度・定例会別 bill / decision fixture、10 RawArtifact / SourceDocumentCandidate を生成できるようにした。`normalize_assembly_bill_decision` で 10 EvidenceItem と `bill_decision_observed` direct claim を生成し、`VotePosition` を生成しない guard を追加した。
- verification: `uv run pytest -q` は 68 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: fixture HTML と source URL は deterministic fixture data であり、live Tokyo Assembly retrieval result ではない。`P0R-004` と `P0R-005` はいずれも `P0R-003` head から `normalize/normalizer.py` を拡張しているため、final integration 時に統合対応が必要。
- blocker release: `P0R-012` はまだ `P0R-008` から `P0R-011` 待ち。次は `P0R-008` から `P0R-010` のいずれかを実行可能 issue とする。

## P0R-006: 選挙公報・選挙結果 probe を実装する

### 目的

選挙結果と選挙公報 metadata から、Candidate / ElectionResult candidate の anchor になる EvidenceItem を作る。

### 実装範囲

- election result HTML/PDF fixture と public bulletin metadata fixture を分ける。
- Candidate / ElectionResult candidate claim を direct observation に限定して作る。
- election name、district、candidate name、votes、source URL、retrieved_at を保持する。

### 受け入れ条件

- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。
- 人物、政治団体、政党支部、後援会を自動 merge しない guard がある。

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-006-election-results-bulletins-probe`
- base: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- head: `f7ec31dd23f5ac839a8efc30d45726b3affa0675`
- review range: `7fb7c999aa4f67410379da2fa25a0cf248de2975..f7ec31dd23f5ac839a8efc30d45726b3affa0675`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `services/ingest/phase0_sources.py` に `tokyo_elections` fixture harness を追加し、選挙結果 HTML / PDF fixture と選挙公報 metadata fixture を分けて 10 FetchManifestRecord / SourceDocumentCandidate を生成できるようにした。`normalize_tokyo_election_candidate_observation` で 10 EvidenceItem、Candidate direct claim、選挙結果がある 6 件の ElectionResult direct claim を生成し、entity merge refs を拒否する guard を追加した。
- verification: `uv run pytest -q` は 68 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: fixture-only のため、実際の東京都選挙 source parsing、PDF/OCR 挙動、live retrieval は未検証。`P0R-004`、`P0R-005`、`P0R-006` はいずれも `P0R-003` head から `normalize/normalizer.py` を拡張しているため、final integration 時に統合対応が必要。
- blocker release: `P0R-012` はまだ `P0R-007` から `P0R-011` 待ち。次は `P0R-007` から `P0R-010` のいずれかを実行可能 issue とする。

## P0R-007: 政治資金収支報告書 probe を実装する

### 目的

政治資金収支報告書の PDF/OCR risk を Phase 1 前に可視化し、PoliticalGroup / FinanceReport candidate の入口を作る。

### 実装範囲

- report index、政治団体名簿、PDF sample fixture を追加する。
- text layer / OCR 要否、table locator、warning を保存する。
- `political_group_registry_observed` と `political_fund_report_metadata_observed` を direct observation として扱う。

### 受け入れ条件

- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。
- 金額、氏名、団体名の抽出には warning / confidence / review required が付く。
- `FundingContact` は生成しない guard がある。

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-007-political-fund-reports-probe`
- base: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- head: `2d29d777e2898f6e5a13a6de0560fe8581bae917`
- review range: `7fb7c999aa4f67410379da2fa25a0cf248de2975..2d29d777e2898f6e5a13a6de0560fe8581bae917`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `services/ingest/political_funds.py` を追加し、政治資金収支報告書の report index、政治団体名簿、PDF sample fixture metadata、text layer / OCR 要否、table locator、warning、confidence、review required を fixture-only probe として扱えるようにした。10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を生成し、`political_group_registry_observed` と `political_fund_report_metadata_observed` の direct claim を扱い、`FundingContact` などの非対象生成を拒否する guard を追加した。
- verification: `uv run pytest -q` は 69 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: fixture-only のため、実際の東京都政治資金 source parsing、PDF download、OCR 挙動、live retrieval は未検証。`P0R-007` は `P0R-003` base から政治資金 probe entrypoint のみを追加しており、sibling source probe との統合は後続 integration work item で扱う。
- blocker release: `P0R-012` はまだ `P0R-008` から `P0R-011` 待ち。次は `P0R-008` から `P0R-010` のいずれかを実行可能 issue とする。

## P0R-008: 財務局・電子調達 契約/予算 probe を実装する

### 目的

PublicMoneyFlow の前段として、予算・決算 document と電子調達 search snapshot を source として保存できるようにする。

### 実装範囲

- budget / settlement index fixture と procurement search snapshot fixture を追加する。
- amount unit、税込・税抜、vendor 名寄せ、契約案との突合に warning / guard を付ける。
- `budget_document_metadata_observed`、`budget_table_cell_observed`、`procurement_search_row_observed` を扱う。

### 受け入れ条件

- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。
- `BudgetLine` / `ContractAward` は確定 entity として生成しない guard がある。

### 実装結果

- branch: `codex/opl-phase0-remainder-20260707/P0R-008-procurement-budget-probe`
- base: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- head: `2aec47df033bcfdf1b0baeebba9807a115136624`
- review range: `7fb7c999aa4f67410379da2fa25a0cf248de2975..2aec47df033bcfdf1b0baeebba9807a115136624`
- 実装レビュー: 承認済み。独立レビューで Critical / Important / Minor なし。
- 実装内容: `services/ingest/phase0_sources.py` と `services/normalize/normalizer.py` を拡張し、budget / settlement index fixture と procurement search snapshot fixture を fixture-only で扱えるようにした。`budget_document_metadata_observed`、`budget_table_cell_observed`、`procurement_search_row_observed` を生成し、amount unit、税込・税抜、vendor 名寄せ、契約案との突合は warning / metadata / non-goal guard として扱う。
- verification: `uv run pytest -q` は 69 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。
- 残リスク: fixture-only のため、実際の東京都予算・決算・電子調達 source parsing は未検証。`P0R-008` は `P0R-003` head から `normalize/normalizer.py` を拡張しているため、final integration 時に sibling source probe との統合対応が必要。
- blocker release: `P0R-012` はまだ `P0R-009` から `P0R-011` 待ち。次は `P0R-009` または `P0R-010` を実行可能 issue とする。

## P0R-009: 助成・補助金 `SubsidyProgramCandidate` probe を実装する

### 目的

`tokyo_metro_grants` を Phase 0 sample baseline に引き上げ、教育・子育ての `SubsidyProgramCandidate` を evidence trace 付きで作る。

### 実装範囲

- fixture HTML を 10 candidate 以上に拡張する。
- title、h1、所管局、対象者、申請期間など locator が安定する field だけを candidate claim にする。
- `subsidy_program_candidate_observed` を claim catalog に追加する。

### 受け入れ条件

- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。
- `SubsidyProgramCandidate` 10 件以上を evidence trace 付きで作れる。
- 個別交付先、金額、成果、`PublicMoneyFlow` は生成しない guard がある。

## P0R-010: 監査 source / `AuditFindingCandidate` probe を実装する

### 目的

東京都監査 source から、公式監査指摘をアプリ計算 signal と分けて保存する前段を作る。

### 実装範囲

- 監査 report index / report fixture を追加する。
- 財政援助団体等監査、包括外部監査、措置状況を source type で分ける。
- 指摘本文、対象団体、年度、措置状況を official wording のまま locator 付きで保存する。

### 受け入れ条件

- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成する。
- `AuditFindingCandidate` 5 件以上を evidence trace 付きで作れる。
- 監査指摘を「無駄遣い」「不正」「違法」と分類しない guard がある。

## P0R-011: 監査指摘とアプリ計算 signal の保存分離 contract を作る

### 目的

Roadmap gate の「監査指摘とアプリ計算 signal を分けて保存できる」を、storage contract と test で満たす。

### 実装範囲

- `AuditFindingCandidate` と `SpendingReviewSignalCandidate` を別 contract / table / claim type として定義する。
- `AuditFindingCandidate` には公式文言と source evidence を保持し、アプリ側評価語を混ぜない。
- `SpendingReviewSignalCandidate` には method version、supporting / counter evidence、limitations、review state を持たせる。
- public UI / score に出ない guard を入れる。

### 受け入れ条件

- 監査 source 由来の official finding と app-calculated signal candidate が同じ table / claim type に入らない。
- `SpendingReviewSignalCandidate` は public 表示用 `SpendingReviewSignal` ではないことが test で確認される。
- `P0R-010` の `AuditFindingCandidate` と接続できる。

## P0R-012: Phase 0 feasibility report / coverage CLI を作る

### 目的

Roadmap の Phase 0 完了可否を、source family 別の sample artifact、EvidenceItem、warning、blocked reason で判断できるようにする。

### 実装範囲

- coverage CLI を追加する。
- source family 別に RawArtifact / SourceDocumentCandidate 件数、EvidenceItem 件数、warning 件数、review required 件数、non-goal guard、blocked reason を出す。
- `knowledge/wiki/syntheses/phase0-source-probe-feasibility-report.md` を生成または更新する。

### 受け入れ条件

- Roadmap 対象 source 7 系統すべてが report に現れる。
- 5 source family 以上で 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を満たすか、未達理由が明示される。
- 助成・補助金と監査 source が達成 source に含まれない場合、Phase 0 は incomplete と判定される。
- coverage report は通常 test と同じく外部 network、browser automation、PDF download、OCR 実行に依存しない。

### 検証

```bash
cd services
uv run python -m ingest phase0 fixture-report --fixtures tests/fixtures --output-dir ingest/out
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

## リモート方針

- local issue ledger が canonical。
- GitHub Issue mirror は未作成。
- GitHub Issue mirror、push、PR 作成は Issue Gate では行わない。
- Remote Gate が別途承認されるまで、external write は行わない。
- live source 取得、PDF download、browser automation、OCR 実行、production S3 / managed object storage、secret 操作は承認しない。

## Issue Gate 承認内容

2026-07-07 に承認済み。

- `P0R-001` から `P0R-012` の issue 分解でよいか。
- `P0R-001` だけを初期実行可能 issue とし、`P0R-002` 以降を blocker graph に従って進めてよいか。
- `P0R-004` から `P0R-010` を Roadmap 対象 source 7 系統の probe として扱ってよいか。
- `P0R-011` で監査指摘と app-calculated signal candidate の保存分離を Phase 0 scope に含めてよいか。
- `P0R-012` で coverage CLI と feasibility report を Phase 0 completion gate にしてよいか。
- GitHub Issue mirror / PR / live acquisition を行わず、local-only のまま進めてよいか。

## 関連ページ

- [Phase 0 残実装設計](phase0-remainder-implementation-design.md) — 承認済み Spec Gate。
- [Roadmap](../../roadmap.md) — Phase 0 gate。
- [Local Infrastructure](../../local-infrastructure.md) — `.env.local` と local MinIO 起動契約。
- [Tokyo Source Connector Design](tokyo-source-connector-design.md) — source family connector 設計。
- [Tokyo Subsidy PDF/OCR Feasibility](tokyo-subsidy-pdf-ocr-feasibility.md) — PDF/OCR と warning 方針。

## 出典

- [Phase 0 残実装設計](phase0-remainder-implementation-design.md)
