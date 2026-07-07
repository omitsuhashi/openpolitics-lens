---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-003-input-packet.json
execution_envelope: phase0-remainder-p0r-003-execution-envelope.json
---

# Phase 0 P0R-003 実行ハンドオフ

## 結論

`P0R-001` と `P0R-002` が local `PR_READY` になったため、次の runnable issue として `P0R-003` を実行対象にする。

`P0R-003` は Phase 0 source registry / fixture harness を固定する issue である。目的は、Roadmap 対象 source 7 系統を source family registry、fixture metadata、coverage target から一貫して参照できるようにすること。

## 実行対象

- `P0R-003`: Phase 0 source registry / fixture harness を作る。

Execution Envelope には dependency validation のため、完了済み prerequisite として `P0R-001` と `P0R-002` も含める。新たに実装 dispatch する対象は `P0R-003` のみである。

## 非対象

- `P0R-004` 以降の individual source probe。
- live source 取得、PDF download、browser automation、OCR 実行。
- `SubsidyProgramCandidate`、`AuditFindingCandidate`、`PublicMoneyFlow`、`SpendingReviewSignal` の生成。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-002`
- blocker head: `a66fca34b24a965fae35d2611abf023a1b69c941`
- base policy: `blocker_head(P0R-002)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-003-source-registry-fixture-harness`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-003`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- Roadmap 対象 source 7 系統すべてが registry に現れる。
- fixture harness が source family ごとの RawArtifact / SourceDocumentCandidate / EvidenceItem 件数を集計できる。
- `P0R-004` から `P0R-010` が同じ registry / fixture harness を使える。
- 通常 test が外部 network、browser automation、PDF download、OCR 実行を行わない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-003-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-003-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-003-input-packet.json --json`

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
