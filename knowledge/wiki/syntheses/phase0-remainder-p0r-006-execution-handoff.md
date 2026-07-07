---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-006-input-packet.json
execution_envelope: phase0-remainder-p0r-006-execution-envelope.json
---

# Phase 0 P0R-006 実行ハンドオフ

## 結論

`P0R-003` が local `PR_READY` になったため、`P0R-006` は実行可能である。`P0R-004`、`P0R-005` とは独立 source probe として扱い、`P0R-003` head から branch を作る。

`P0R-006` は選挙公報・選挙結果 source probe を fixture-only で実装する issue である。目的は、選挙結果と選挙公報 metadata から Candidate / ElectionResult candidate の anchor になる EvidenceItem を作ること。

## 実行対象

- `P0R-006`: 選挙公報・選挙結果 probe を実装する。

Execution Envelope には dependency validation と runtime reconciliation のため、完了済み prerequisite として `P0R-001`、`P0R-002`、`P0R-003` を、既完了 sibling として `P0R-004`、`P0R-005` も含める。新たに実装 dispatch する対象は `P0R-006` のみである。

## 非対象

- `P0R-004`、`P0R-005`、`P0R-007` 以降の individual source probe。
- live source 取得、external network、browser automation、PDF download、OCR 実行。
- entity resolution、自動 merge、人物・政治団体・政党支部・後援会の同一視。
- `VotePosition`、政策 stance、意味分類、PublicMoneyFlow、SpendingReviewSignal の生成。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-003`
- blocker head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- base policy: `blocker_head(P0R-003)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-006-election-results-bulletins-probe`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-006`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- election result HTML/PDF fixture と public bulletin metadata fixture を分ける。
- Candidate / ElectionResult candidate claim を direct observation に限定して作る。
- election name、district、candidate name、votes、source URL、retrieved_at を保持する。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成できる。
- 人物、政治団体、政党支部、後援会を自動 merge しない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-006-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-006-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-006-input-packet.json --json`

通常検証:

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

repository root:

```bash
git diff --check
```

## リモート方針

- `local_only`。
- GitHub Issue mirror、push、PR 作成は行わない。
- remote delivery が必要になった場合は別途 Remote Gate を開く。
