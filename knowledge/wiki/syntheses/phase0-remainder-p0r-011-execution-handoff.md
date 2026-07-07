---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-011-input-packet.json
execution_envelope: phase0-remainder-p0r-011-execution-envelope.json
---

# Phase 0 P0R-011 実行ハンドオフ

## 結論

`P0R-010` が local `PR_READY` になったため、`P0R-011` は実行可能である。`P0R-011` は `P0R-010` head から branch を作り、監査指摘とアプリ計算 signal candidate の保存分離 contract だけを実装する。

## 実行対象

- `P0R-011`: 監査指摘とアプリ計算 signal の保存分離 contract を作る。

Execution Envelope には直接 prerequisite の `P0R-010` と、新規 dispatch 対象の `P0R-011` を含める。`P0R-001` から `P0R-009` は runtime / ledger 上で完了済みとして扱う。

## 非対象

- public UI、score、ranking、政治的評価、断定分類。
- public-facing `SpendingReviewSignal` entity。
- live source 取得、external network、browser automation、PDF download、OCR 実行。
- `P0R-004` から `P0R-010` の source probe 実装変更。
- `P0R-012` coverage CLI / feasibility report。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-010`
- blocker head: `ba3fd23e125ed1c502f1487a3b79258fd447b970`
- base policy: `blocker_head(P0R-010)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-011-audit-signal-storage-separation`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-011`

## Write Scope

- `services/normalize`
- `services/tests`
- `packages/db`

## Acceptance

- `AuditFindingCandidate` と `SpendingReviewSignalCandidate` を別 contract / table / claim type として定義する。
- `AuditFindingCandidate` には公式文言と source evidence を保持し、アプリ側評価語を混ぜない。
- `SpendingReviewSignalCandidate` には method version、supporting / counter evidence、limitations、review state を持たせる。
- public UI / score に出ない guard を入れる。
- 監査 source 由来の official finding と app-calculated signal candidate が同じ table / claim type に入らない。
- `SpendingReviewSignalCandidate` は public 表示用 `SpendingReviewSignal` ではないことが test で確認される。
- `P0R-010` の `AuditFindingCandidate` と接続できる。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-011-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-011-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-011-input-packet.json --json`

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
