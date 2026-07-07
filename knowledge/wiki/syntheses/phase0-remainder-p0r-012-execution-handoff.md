---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-012-input-packet.json
execution_envelope: phase0-remainder-p0r-012-execution-envelope.json
---

# Phase 0 P0R-012 実行ハンドオフ

## 結論

`P0R-011` が local `PR_READY` になったため、`P0R-012` は実行可能である。`P0R-012` は Phase 0 の完了可否を source family 別 coverage と feasibility report で判定する最後の issue である。

## 実行対象

- `P0R-012`: Phase 0 feasibility report / coverage CLI を作る。

Execution Envelope には直接 prerequisite の `P0R-011` と、新規 dispatch 対象の `P0R-012` を含める。`P0R-004` から `P0R-010` は個別 source probe として runtime / ledger 上で local `PR_READY` 済みである。

## 非対象

- live source 取得、external network、browser automation、PDF download、OCR 実行。
- source probe の大規模再実装や sibling branch 統合。
- public UI、score、ranking、public `SpendingReviewSignal` 表示。
- production S3 / managed object storage / secret 操作。
- remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-011`
- blocker head: `e793c9e7f3290c742608d1f77bc144b609d4b65c`
- base policy: `blocker_head(P0R-011)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-012-phase0-coverage-report`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-012`

## Write Scope

- `services/ingest`
- `services/tests`
- `knowledge/wiki/syntheses`

## Acceptance

- coverage CLI を追加する。
- source family 別に RawArtifact / SourceDocumentCandidate 件数、EvidenceItem 件数、warning 件数、review required 件数、non-goal guard、blocked reason を出す。
- `knowledge/wiki/syntheses/phase0-source-probe-feasibility-report.md` を生成または更新する。
- Roadmap 対象 source 7 系統すべてが report に現れる。
- 5 source family 以上で 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を満たすか、未達理由が明示される。
- 助成・補助金と監査 source が達成 source に含まれない場合、Phase 0 は incomplete と判定される。
- coverage report は通常 test と同じく外部 network、browser automation、PDF download、OCR 実行に依存しない。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-012-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-012-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-012-input-packet.json --json`

通常検証:

```bash
cd services
uv run python -m ingest phase0 fixture-report --fixtures tests/fixtures --output-dir ingest/out
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
