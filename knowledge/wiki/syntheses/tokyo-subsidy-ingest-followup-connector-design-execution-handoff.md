---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: execution-handoff-draft
input_packet: tokyo-subsidy-ingest-followup-connector-design-input-packet.json
execution_envelope: tokyo-subsidy-ingest-followup-connector-design-execution-envelope.json
---

# 東京都補助金 ingest 後続 connector 設計実行ハンドオフ

## 結論

`G2PR-006` の PDF/OCR feasibility 完了後の head を土台に、
`G2PR-007` を docs-first の connector design issue として実行する。

`G2PR-007` は、契約・入札、予算・決算、監査、政治資金、
会議録・議案を後続 source family として扱うため、source family ごとに
`jurisdiction_id`、`source_system`、`source_family`、`connector_id` と
fixture / live acquisition の分離方針を固定する。

## 実行対象

- `G2PR-007`: 契約・入札、予算・決算、監査、政治資金、会議録 source を後続 connector として設計する。

## 非対象

- connector 実装、parser 実装、browser automation。
- live source 取得、外部 network、PDF download、OCR 実行。
- 金額、氏名、団体名、監査指摘、交付先、契約先の意味解釈。
- SubsidyProgram、PublicMoneyFlow、SpendingReviewSignal、AuditFinding、BudgetLine、ContractAward、FundingContact、Speech、Bill 生成。
- DB migration、API、Web UI、GitHub Issue mirror。

## Base

- local base branch: `codex/opl-ingest-subsidy-20260705-followups`
- base commit: `d64ad91ea45a7a8648fe46f0e083efd249dd0e36`
- completed predecessor: `G2PR-006`

## Verification

```bash
git diff --check
```
