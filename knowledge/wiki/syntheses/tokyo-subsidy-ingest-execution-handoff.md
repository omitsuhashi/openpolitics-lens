---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: execution-plan-ready
---

# 東京都補助金・助成金 ingest 実行ハンドオフ

## Canonical artifacts

- Spec: [tokyo-subsidy-ingest-spec.md](tokyo-subsidy-ingest-spec.md)
- Local issue ledger: [tokyo-subsidy-ingest-issues.md](tokyo-subsidy-ingest-issues.md)
- Input packet: [tokyo-subsidy-ingest-input-packet.json](tokyo-subsidy-ingest-input-packet.json)
- Execution envelope: [tokyo-subsidy-ingest-execution-envelope.json](tokyo-subsidy-ingest-execution-envelope.json)

## Approved execution scope

今回の実装対象は `G2PR-001`、`G2PR-002`、`G2PR-003` のみ。

- `G2PR-001`: Jurisdiction Profile と ingest contract / filesystem output の土台を作る。
- `G2PR-002`: 都庁助成・補助金 connector の fixture discovery/fetch を実装する。
- `G2PR-003`: CLI と README を整備し、fixture 検証を通す。

`G2PR-004` から `G2PR-007` は local ledger に残すが、この execution packet では実装しない。

## Dependency order

```text
G2PR-001 -> G2PR-002 -> G2PR-003
```

`G2PR-002` は `G2PR-001` の review approval 後、`G2PR-003` は `G2PR-002` の review approval 後に release する。

## Write scopes

- `G2PR-001`: `.gitignore`, `services/ingest`, `services/tests`, `services/pyproject.toml`
- `G2PR-002`: `services/ingest`, `services/tests`
- `G2PR-003`: `services/ingest`, `services/tests`, `services/pyproject.toml`

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

remote `origin` は `git@github.com:omitsuhashi/openpolitics-lens.git` として存在するが、`gh auth status` は token invalid。Execution envelope は `local_only` とし、push、GitHub Issue 作成、PR 作成は行わない。

PR delivery は Remote Gate で扱う。最終 PR merge は常に human-only。

## Execution Plan Gate evidence

- `validate_input_packet.py knowledge/wiki/syntheses/tokyo-subsidy-ingest-input-packet.json --json`: ok
- `validate_execution_envelope.py knowledge/wiki/syntheses/tokyo-subsidy-ingest-execution-envelope.json --json`: ok
- `check_capabilities.py --input knowledge/wiki/syntheses/tokyo-subsidy-ingest-input-packet.json --repo . --json`: ok
- `reconcile_git_state.py knowledge/wiki/syntheses/tokyo-subsidy-ingest-execution-envelope.json --repo . --json`: ok, collisions none
- `git diff --check`: ok
- Execution envelope revision: `2`
- `epic_base.sha`: `c968b79452761b133259ccda16b92e3dfaaed062`

Observed remote state:

- `origin`: `git@github.com:omitsuhashi/openpolitics-lens.git`
- `gh auth status`: token invalid

## Stop conditions

- scope が `G2PR-001` から `G2PR-003` の外へ広がる。
- coordinator が worker の代わりに実装する必要が出る。
- worker context が使えない。
- write scope 外の編集が必要になる。
- external write、credential、permission、billing、destructive action が必要になる。
- verification または implementation review の Critical / Important finding が 2 review cycle 後も残る。

## 出典

- [Tokyo Subsidy Ingest Spec](tokyo-subsidy-ingest-spec.md)
- [Tokyo Subsidy Ingest Issues](tokyo-subsidy-ingest-issues.md)
