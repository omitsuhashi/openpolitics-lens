---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-007-input-packet.json
execution_envelope: phase0-remainder-p0r-007-execution-envelope.json
---

# Phase 0 P0R-007 実行ハンドオフ

## 結論

`P0R-003` が local `PR_READY` になったため、`P0R-007` は実行可能である。`P0R-004` から `P0R-006` とは独立 source probe として扱い、`P0R-003` head から branch を作る。

`P0R-007` は政治資金収支報告書 source probe を fixture-only で実装する issue である。目的は、政治資金収支報告書の PDF/OCR risk を Phase 1 前に可視化し、PoliticalGroup / FinanceReport candidate の入口を作ること。

## 実行対象

- `P0R-007`: 政治資金収支報告書 probe を実装する。

Execution Envelope には dependency validation と runtime reconciliation のため、完了済み prerequisite として `P0R-001` から `P0R-003` を、既完了 sibling として `P0R-004` から `P0R-006` も含める。新たに実装 dispatch する対象は `P0R-007` のみである。

## 非対象

- `P0R-004` から `P0R-006`、`P0R-008` 以降の individual source probe。
- live source 取得、external network、browser automation、PDF download、OCR 実行。
- 金額、氏名、団体名の確定 entity / fact 昇格。
- `FundingContact`、PublicMoneyFlow、SpendingReviewSignal、政策 stance、意味分類の生成。
- live database migration apply、remote write、GitHub Issue mirror、PR 作成。

## Base

- blocker issue: `P0R-003`
- blocker head: `7fb7c999aa4f67410379da2fa25a0cf248de2975`
- base policy: `blocker_head(P0R-003)`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-007-political-fund-reports-probe`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-007`

## Write Scope

- `services/ingest`
- `services/normalize`
- `services/tests`

## Acceptance

- report index、政治団体名簿、PDF sample fixture を追加する。
- text layer / OCR 要否、table locator、warning を保存する。
- `political_group_registry_observed` と `political_fund_report_metadata_observed` を direct observation として扱う。
- 10 RawArtifact / SourceDocumentCandidate と 10 EvidenceItem を fixture-only で生成できる。
- 金額、氏名、団体名の抽出には warning / confidence / review required が付く。
- `FundingContact` は生成しない guard がある。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-007-input-packet.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-007-execution-envelope.json`
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-007-input-packet.json --json`

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
