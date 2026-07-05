---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: issue-gate-approved
spec: tokyo-subsidy-ingest-spec.md
---

# 東京都補助金・助成金 ingest ローカル issue ledger

## 結論

`OPL-INGEST-SUBSIDY-20260705` の初回 PR は、`G2PR-001` から `G2PR-003` までを実装対象にする。`G2PR-004` 以降は、Spec Gate で非目標化した深掘り項目を後続 issue として残す。

## Ledger

| Epic ID | ローカルID | タイトル | レビュー状態 | 実行状態 | ブロック元 | ブロック先 | GitHub Issue | 実装レビュー | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-001 | Jurisdiction Profile と ingest contract / filesystem output の土台を作る | 承認済み | PR_READY | なし | G2PR-002, G2PR-004 | 未作成 | 承認済み | 未作成 |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-002 | 都庁助成・補助金 connector の fixture discovery/fetch を実装する | 承認済み | PR_READY | G2PR-001 | G2PR-003, G2PR-005, G2PR-006, G2PR-007 | 未作成 | 承認済み | 未作成 |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-003 | CLI と README を整備し、fixture 検証を通す | 承認済み | 実行可能 | G2PR-002 | なし | 未作成 | 未実施 | 未作成 |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-004 | PostgreSQL / MinIO 永続化を設計・実装する | 承認済み | ブロック中 | G2PR-001 | なし | 未作成 | 未実施 | 未作成 |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-005 | normalize で EvidenceItem / EvidenceClaim 生成を実装する | 承認済み | ブロック中 | G2PR-002 | なし | 未作成 | 未実施 | 未作成 |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-006 | PDF/OCR と表抽出の source family 別 feasibility を行う | 承認済み | ブロック中 | G2PR-002 | なし | 未作成 | 未実施 | 未作成 |
| OPL-INGEST-SUBSIDY-20260705 | G2PR-007 | 契約・入札、予算・決算、監査、政治資金、会議録 source を後続 connector として設計する | 承認済み | ブロック中 | G2PR-002 | なし | 未作成 | 未実施 | 未作成 |

## Blocker graph

```text
G2PR-001
  -> G2PR-002
       -> G2PR-003
       -> G2PR-005
       -> G2PR-006
       -> G2PR-007
  -> G2PR-004
```

cycle はない。Issue Gate 承認後、`G2PR-001` だけが直ちに実行可能で、`G2PR-002` 以降は依存 issue の完了後に実行可能になる。

`G2PR-001` と `G2PR-002` は実装レビュー承認済みで、`G2PR-003` の blocker を解除した。`G2PR-004` 以降は初回 PR の非目標であるため、依存の一部が満たされても後続 scope として `ブロック中` のまま残す。

## 初回 PR 実装範囲

- `G2PR-001`
- `G2PR-002`
- `G2PR-003`

初回 PR では、filesystem-first の ingest contract と fixture-driven connector を実装する。PostgreSQL、MinIO、normalize、PDF/OCR、SpendingReviewSignal、他 source family は実装しない。

## G2PR-001: Jurisdiction Profile と ingest contract / filesystem output の土台を作る

### 目的

国・自治体横展開に耐える ingest contract を先に固定し、東京都固有設定が他 jurisdiction に漏れないようにする。

### 実装範囲

- `services/ingest` を import 可能な Python package にする。
- `JurisdictionProfile`, `SourceFamily`, `ConnectorDefinition`, `DiscoveryRecord`, `FetchManifestRecord`, `SourceDocumentCandidate` 相当の型を定義する。
- `jurisdiction_id`, `source_system`, `source_family`, `connector_id` を manifest に含める。
- filesystem output writer を作る。
- output path を `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.html` にする。
- `services/ingest/out/` を git 管理対象外にする。

### 受け入れ条件

- 型定義は unit test で serialize できる。
- 同一 content から同じ `sha256` と output path が得られる。
- `jurisdiction_id` と `source_family` を入れ替えると output path が分離される。
- `git diff --check` が通る。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

### 実装結果

- branch: `codex/opl-ingest-subsidy-20260705/G2PR-001-ingest-contract`
- base: `c968b79c9c5da1cd66b82eb8290ab42bb2a924a4`
- head: `c539566450bcaf7aab265cd5f4568fcd9c687934`
- review range: `c968b79c9c5da1cd66b82eb8290ab42bb2a924a4..c539566450bcaf7aab265cd5f4568fcd9c687934`
- 実装レビュー: 承認済み。初回レビューの Important 指摘に従い、filesystem writer に manifest path construction と JSONL append helper を追加した。
- verification: `uv run pytest -q` は 6 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。

## G2PR-002: 都庁助成・補助金 connector の fixture discovery/fetch を実装する

### 目的

`tokyo_metro_grants` connector の fixture-driven `discover` / `fetch` を実装し、live network に依存せず contract を検証できるようにする。

### 実装範囲

- `jurisdiction_id`: `jp-tokyo`
- `source_family`: `tokyo_metro_grants`
- `connector_id`: `jp_tokyo.metro_grants.v1`
- fixture HTML から教育・子育て関連 candidate URL を抽出する。
- keyword / allowlist は connector local config に閉じる。
- fake fetcher で RawArtifact と fetch manifest を生成する。

### 受け入れ条件

- fixture から deterministic な `discovered.jsonl` 相当の record が生成される。
- fixture fetch から deterministic な `fetched.jsonl` 相当の record と raw artifact が生成される。
- `source_document_candidate` が fetch manifest に含まれる。
- 通常 test は外部 network に出ない。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

### 実装結果

- branch: `codex/opl-ingest-subsidy-20260705/G2PR-002-tokyo-grants-connector`
- base: `c539566450bcaf7aab265cd5f4568fcd9c687934`
- head: `d6c9cfca93a3bfb07c10117deba9d3ebe3bd62bd`
- review range: `c539566450bcaf7aab265cd5f4568fcd9c687934..d6c9cfca93a3bfb07c10117deba9d3ebe3bd62bd`
- 実装レビュー: 承認済み。fixture HTML discovery、fake fetch、RawArtifact 書き込み、fetch manifest と `source_document_candidate` 生成を確認した。
- verification: `uv run pytest -q` は 8 passed、`uv run ruff check .` は passed、`uv run ruff format --check .` は passed、`git diff --check` は passed。

## G2PR-003: CLI と README を整備し、fixture 検証を通す

### 目的

developer が `services/ingest` の fixture ingest を再現できる CLI と README を用意する。

### 実装範囲

- fixture 入力と output directory を受け取る CLI を追加する。
- live fetch は明示 option にし、通常 command と test では使わない。
- README に ingest/normalize 境界、Jurisdiction Profile、output layout、検証 command を書く。

### 受け入れ条件

- CLI の fixture mode が local file だけで動く。
- README の command が現在の package layout と一致する。
- generated output は git 管理されない。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-004: PostgreSQL / MinIO 永続化を設計・実装する

### 目的

filesystem-first で固めた RawArtifact / manifest contract を、RDB 正本と immutable object storage へ移す。

### ブロック元

- `G2PR-001`

### 後続受け入れ条件案

- `raw_artifacts` と source candidate registry の migration がある。
- MinIO key が `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}` に沿う。
- filesystem writer と object storage writer が同じ manifest contract を使う。

## G2PR-005: normalize で EvidenceItem / EvidenceClaim 生成を実装する

### 目的

ingest が作った Source Document Candidate と RawArtifact から、EvidenceItem / EvidenceClaim / 正規化 fact を生成する。

### ブロック元

- `G2PR-002`

### 後続受け入れ条件案

- `SourceDocument` への昇格 rule が明示される。
- `EvidenceItem` は source span と `raw_artifact_path` へ戻れる。
- `EvidenceClaim` は直接言える最小 claim に限定される。

## G2PR-006: PDF/OCR と表抽出の source family 別 feasibility を行う

### 目的

補助金交付実績、政治資金、監査報告など、PDF/OCR と表抽出が必要な source family の実装可能性を評価する。

### ブロック元

- `G2PR-002`

### 後続受け入れ条件案

- source family ごとに OCR 不要 / 必要、表抽出方法、confidence、parse warning 方針が記録される。
- PDF/OCR 由来の金額・氏名・団体名には confidence と warning が必須になる。

## G2PR-007: 契約・入札、予算・決算、監査、政治資金、会議録 source を後続 connector として設計する

### 目的

補助金 first で固定した ingest contract を、PublicMoneyFlow と政治過程の他 source family に広げる。

### ブロック元

- `G2PR-002`

### 後続受け入れ条件案

- 契約・入札、予算・決算、監査、政治資金、会議録・議案の source family ごとに `jurisdiction_id`, `source_system`, `source_family`, `connector_id` が定義される。
- 電子調達検索 UI、政治資金 PDF、会議録検索は live acquisition 条件と fixture strategy を分けて記録される。

## リモート方針

GitHub Issue mirror は未作成。現時点では local issue ledger を canonical とし、GitHub issue 作成は行わない。

PR 作成は Remote Gate で扱う。`gh` CLI は利用可能だが、現 token は invalid。remote `origin` は `git@github.com:omitsuhashi/openpolitics-lens.git` として存在する。

## Issue Gate で確認すること

- `G2PR-001` から `G2PR-003` を初回 PR の実装対象にしてよいか。
- `G2PR-004` から `G2PR-007` を後続深掘り issue として `ブロック中` のまま残してよいか。
- blocker graph に cycle がないこと。
- GitHub Issue mirror を行わず local ledger を canonical とすること。

## 関連ページ

- [Tokyo Subsidy Ingest Spec](tokyo-subsidy-ingest-spec.md) — 承認済み Spec Gate。
- [Data Sources](../../data-sources.md) — source family と connector contract。
- [Service Layout](../../service-layout.md) — service 境界。

## 出典

- [Tokyo Subsidy Ingest Spec](tokyo-subsidy-ingest-spec.md)
