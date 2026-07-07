---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-002-input-packet.json
execution_envelope: phase0-remainder-p0r-002-execution-envelope.json
---

# Phase 0 P0R-002 実行ハンドオフ

## 結論

`P0R-001` が local `PR_READY` になったため、次の runnable issue として `P0R-002` を実行対象にする。

`P0R-002` は EvidenceItem / EvidenceClaim の横断 contract を拡張する issue である。目的は、HTML title だけに閉じた初期 normalize contract を、PDF、table、search snapshot、OCR 由来の EvidenceItem を表現できる schema / warning / locator / claim catalog へ広げること。

## 実行対象

- `P0R-002`: Evidence schema / warning / claim catalog を拡張する。

Execution Envelope には dependency validation のため、完了済み prerequisite として `P0R-001` も含める。新たに実装 dispatch する対象は `P0R-002` のみである。

## 非対象

- `P0R-003` の source registry / fixture harness。
- `P0R-004` 以降の source probe、PDF download、browser automation、OCR 実行。
- `SubsidyProgramCandidate`、`AuditFindingCandidate`、`PublicMoneyFlow`、`SpendingReviewSignal` の生成。
- live PostgreSQL migration apply、live source 取得、外部 network access。
- GitHub Issue mirror、push、PR 作成。

## Base

- blocker issue: `P0R-001`
- blocker head: `9045c8fd6aef5b41d29386e5514310c77f12f100`
- base policy: `blocker_head(P0R-001)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-002-evidence-schema-warning-catalog`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-002`

## Write Scope

- `services/normalize`
- `services/tests`
- `packages/db`

## Acceptance

- `parse_warnings` と locator metadata が Python contract、DB migration、serialized contract、tests に反映される。
- `grant_program_page_title_observed` だけに閉じた claim type 制限を外し、catalog 管理になる。
- 既存 `grant_program_page` normalize test は後方互換で通る。
- PDF / table / search snapshot 用の warning と locator の最小 fixture test がある。
- locator 不足または low confidence の場合、EvidenceClaim へ昇格しない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-002-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-002-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-002-input-packet.json --json`

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
