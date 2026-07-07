---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-010-input-packet.json
execution_envelope: phase0-remainder-p0r-010-execution-envelope.json
---

# Phase 0 P0R-010 実行ハンドオフ

## 結論

`P0R-003` が local `PR_READY` になったため、`P0R-010` は実行可能である。`P0R-004` から `P0R-009` とは独立 source probe として扱い、`P0R-003` head から branch を作る。

`P0R-010` は東京都監査 source から、公式監査指摘をアプリ計算 signal と分けて保存する前段を作る issue である。

## 実行対象

- `P0R-010`: 監査 source / `AuditFindingCandidate` probe を実装する。

Execution Envelope には dependency validation と runtime reconciliation のため、完了済み prerequisite として `P0R-001` から `P0R-003` を、既完了 sibling として `P0R-004` から `P0R-009` も含める。新たに実装 dispatch する対象は `P0R-010` のみである。

## 非対象

- `P0R-004` から `P0R-009`、`P0R-011` 以降の source probe / storage separation contract。
- live source 取得、external network、browser automation、PDF download、OCR 実行。
- 監査指摘の「無駄遣い」「不正」「違法」分類、政治的評価、アプリ計算 signal 化。
- SpendingReviewSignal、PublicMoneyFlow、BudgetLine、ContractAward の生成。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-003`
- blocker head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- base policy: `blocker_head(P0R-003)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-010-audit-finding-candidates-probe`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-010`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- 監査 report index / report fixture を追加する。
- 財政援助団体等監査、包括外部監査、措置状況を source type で分ける。
- 指摘本文、対象団体、年度、措置状況を official wording のまま locator 付きで保存する。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成できる。
- `AuditFindingCandidate` 5 件以上を evidence trace 付きで作れる。
- 監査指摘を「無駄遣い」「不正」「違法」と分類しない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-010-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-010-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-010-input-packet.json --json`

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
