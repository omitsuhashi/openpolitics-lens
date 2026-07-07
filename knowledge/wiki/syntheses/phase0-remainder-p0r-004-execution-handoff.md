---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-004-input-packet.json
execution_envelope: phase0-remainder-p0r-004-execution-envelope.json
---

# Phase 0 P0R-004 実行ハンドオフ

## 結論

`P0R-003` が local `PR_READY` になったため、次の worker dispatch として `P0R-004` を実行対象にする。

`P0R-004` は都議会の会議録・速記録 source probe を fixture-only で実装する issue である。目的は、検索 snapshot 条件、meeting / speaker / speech block locator、RawArtifact / SourceDocumentCandidate / EvidenceItem の trace を同じ registry / fixture harness から扱えるようにすること。

## 実行対象

- `P0R-004`: 都議会 会議録・速記録 probe を実装する。

Execution Envelope には dependency validation のため、完了済み prerequisite として `P0R-001`、`P0R-002`、`P0R-003` も含める。新たに実装 dispatch する対象は `P0R-004` のみである。

## 非対象

- `P0R-005` 以降の individual source probe。
- live search、external network、browser automation、PDF download、OCR 実行。
- 政策 stance、意味分類、議員評価、PublicMoneyFlow、SpendingReviewSignal の生成。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-003`
- blocker head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- base policy: `blocker_head(P0R-003)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-004-assembly-records-probe`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-004`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- 会議録検索 snapshot fixture、検索条件 metadata、meeting / speaker / speech block locator が fixture-only で使える。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を生成できる。
- speech text の直接観測 claim は作れるが、政策 stance や意味分類は生成しない。
- browser automation / live search は通常 test に入らない。
- EvidenceItem から raw artifact と search snapshot 条件へ戻れる。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-004-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-004-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-004-input-packet.json --json`

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
