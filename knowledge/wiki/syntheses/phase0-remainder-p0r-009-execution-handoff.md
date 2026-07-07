---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-009-input-packet.json
execution_envelope: phase0-remainder-p0r-009-execution-envelope.json
---

# Phase 0 P0R-009 実行ハンドオフ

## 結論

`P0R-003` が local `PR_READY` になったため、`P0R-009` は実行可能である。`P0R-004` から `P0R-008` とは独立 source probe として扱い、`P0R-003` head から branch を作る。

`P0R-009` は `tokyo_metro_grants` を Phase 0 sample baseline に引き上げ、教育・子育ての `SubsidyProgramCandidate` を evidence trace 付きで作る issue である。

## 実行対象

- `P0R-009`: 助成・補助金 `SubsidyProgramCandidate` probe を実装する。

Execution Envelope には dependency validation と runtime reconciliation のため、完了済み prerequisite として `P0R-001` から `P0R-003` を、既完了 sibling として `P0R-004` から `P0R-008` も含める。新たに実装 dispatch する対象は `P0R-009` のみである。

## 非対象

- `P0R-004` から `P0R-008`、`P0R-010` 以降の individual source probe。
- live source 取得、external network、browser automation、PDF download、OCR 実行。
- 個別交付先、金額、成果、PublicMoneyFlow、SpendingReviewSignal の生成。
- `SubsidyProgram` の確定 entity 昇格。Phase 0 は candidate-first とする。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-003`
- blocker head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- base policy: `blocker_head(P0R-003)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-009-subsidy-program-candidates-probe`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-009`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- fixture HTML を 10 candidate 以上に拡張する。
- title、h1、所管局、対象者、申請期間など locator が安定する field だけを candidate claim にする。
- `subsidy_program_candidate_observed` を claim catalog に追加する。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成できる。
- `SubsidyProgramCandidate` 10 件以上を evidence trace 付きで作れる。
- 個別交付先、金額、成果、`PublicMoneyFlow` は生成しない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-009-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-009-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-009-input-packet.json --json`

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
