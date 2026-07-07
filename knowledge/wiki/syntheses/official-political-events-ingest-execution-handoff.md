---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-OFFICIAL-POLITICAL-EVENTS-20260707
status: execution-plan-ready
---

# 公式政治イベント ingest 実行ハンドオフ

## Canonical artifacts

- Spec: [official-political-events-ingest-spec.md](official-political-events-ingest-spec.md)
- Local issue ledger: [official-political-events-ingest-issues.md](official-political-events-ingest-issues.md)
- Input packet: [official-political-events-ingest-input-packet.json](official-political-events-ingest-input-packet.json)
- Execution envelope: [official-political-events-ingest-execution-envelope.json](official-political-events-ingest-execution-envelope.json)

## Approved execution scope

今回の実装対象は `G2PR-008`、`G2PR-009`、`G2PR-010` のみ。

- `G2PR-008`: Source Registry と Coverage Ledger の contract を作る。
- `G2PR-009`: `OfficialPoliticalEventCandidate` と `EventSourceAssertion` の normalize contract を作る。
- `G2PR-010`: 選挙・会議の coverage guard と欠落可視化を実装する。

`G2PR-011` から `G2PR-018` は local ledger に残すが、この execution packet では実装しない。

## Dependency order

```text
G2PR-008 -> G2PR-009 -> G2PR-010
```

`G2PR-009` は `G2PR-008` の review approval 後、`G2PR-010` は `G2PR-009` の review approval 後に release する。`G2PR-010` は `G2PR-008` への hard dependency も持つが、branch base は `G2PR-009` head とする。

## Write scopes

- `G2PR-008`: `services/ingest`, `services/tests`
- `G2PR-009`: `services/normalize`, `services/tests`, `packages/db/migrations`
- `G2PR-010`: `services/ingest`, `services/normalize`, `services/tests`

Coordinator は envelope、runtime snapshot、event log、local issue ledger、planning artifacts の整合性だけを管理する。planning/grill session は worker の代わりに実装しない。

## Verification

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
```

`git diff --check` は repo root で実行する。

## Remote policy

remote `origin` は `git@github.com:omitsuhashi/openpolitics-lens.git` として存在するが、`gh` CLI は見つからない。Execution envelope は `local_only` とし、push、GitHub Issue 作成、PR 作成は行わない。

PR delivery は Remote Gate で扱う。最終 PR merge は常に human-only。

## Execution Plan Gate evidence

- `validate_input_packet.py knowledge/wiki/syntheses/official-political-events-ingest-input-packet.json --json`: ok
- `validate_execution_envelope.py knowledge/wiki/syntheses/official-political-events-ingest-execution-envelope.json --json`: ok
- `check_capabilities.py --input knowledge/wiki/syntheses/official-political-events-ingest-input-packet.json --repo . --json`: ok
- `reconcile_git_state.py knowledge/wiki/syntheses/official-political-events-ingest-execution-envelope.json --repo . --json`: ok, collisions none
- `git diff --check`: ok
- Execution envelope schema: `3`
- Execution envelope revision: `1`
- `epic_base.sha`: `c870f7a1e485d62fb413c59084bb2d7cfd61640e`

Observed local state:

- git common dir: `/Users/omitsuhashi/repos/omitsuhashi/openpolitics-lens/.git`
- `epic_base.ref`: `codex/opl-official-political-events-20260707/epic-base`
- `G2PR-008` branch reservation: `codex/opl-official-political-events-20260707/G2PR-008-source-registry-coverage-ledger`
- `G2PR-009` branch reservation: `codex/opl-official-political-events-20260707/G2PR-009-official-event-normalize-contract`
- `G2PR-010` branch reservation: `codex/opl-official-political-events-20260707/G2PR-010-election-meeting-coverage-guard`

## Stop conditions

- scope が `G2PR-008` から `G2PR-010` の外へ広がる。
- coordinator が worker の代わりに実装する必要が出る。
- worker context が使えない。
- write scope 外の編集が必要になる。
- external write、credential、permission、billing、destructive action が必要になる。
- 選挙・会議の coverage gap を silent omission する設計に変わる。
- verification または implementation review の Critical / Important finding が 2 review cycle 後も残る。

## 出典

- [Official Political Events Ingest Spec](official-political-events-ingest-spec.md)
- [Official Political Events Ingest Issues](official-political-events-ingest-issues.md)
