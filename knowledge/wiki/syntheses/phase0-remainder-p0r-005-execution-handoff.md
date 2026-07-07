---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-005-input-packet.json
execution_envelope: phase0-remainder-p0r-005-execution-envelope.json
---

# Phase 0 P0R-005 実行ハンドオフ

## 結論

`P0R-003` が local `PR_READY` になったため、`P0R-005` は実行可能である。`P0R-004` とは独立 source probe として扱い、`P0R-003` head から branch を作る。

`P0R-005` は都議会の提出議案・議決結果 source probe を fixture-only で実装する issue である。目的は、議案番号、件名、議決結果、会期、source URL を locator 付き EvidenceItem / direct claim として扱えるようにすること。

## 実行対象

- `P0R-005`: 都議会 提出議案・議決結果 probe を実装する。

Execution Envelope には dependency validation のため、完了済み prerequisite として `P0R-001`、`P0R-002`、`P0R-003` も含める。新たに実装 dispatch する対象は `P0R-005` のみである。

## 非対象

- `P0R-004`、`P0R-006` 以降の individual source probe。
- live source 取得、external network、browser automation、PDF download、OCR 実行。
- 個人別賛否、`VotePosition`、政策 stance、意味分類、PublicMoneyFlow、SpendingReviewSignal の生成。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-003`
- blocker head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- base policy: `blocker_head(P0R-003)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-005-assembly-bills-decisions-probe`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-005`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- 年度・定例会別の bill / decision fixture から議案番号、件名、議決結果、会期、source URL を locator 付きで保存できる。
- `bill_decision_observed` などの claim type を catalog に追加する。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成できる。
- source に個人別賛否がない場合、`VotePosition` を生成しない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-005-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-005-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-005-input-packet.json --json`

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
