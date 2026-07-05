---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: execution-handoff-draft
input_packet: tokyo-subsidy-ingest-followup-pdf-ocr-input-packet.json
execution_envelope: tokyo-subsidy-ingest-followup-pdf-ocr-execution-envelope.json
---

# 東京都補助金 ingest 後続 PDF/OCR feasibility 実行ハンドオフ

## 結論

`G2PR-005` の normalize evidence contract 完了後の head を土台に、
`G2PR-006` を docs-first の feasibility issue として実行する。

`G2PR-006` は PDF/OCR engine や parser 実装ではなく、source family 別に
OCR 要否、表抽出方針、confidence、parse warning を決めるための synthesis
を作る。

## 実行対象

- `G2PR-006`: PDF/OCR と表抽出の source family 別 feasibility を行う。

## 非対象

- PDF/OCR engine、table extraction、parser 実装。
- live source 取得、外部 network、PDF download、OCR 実行。
- 金額、氏名、団体名、監査指摘、交付先の意味解釈。
- SubsidyProgram、PublicMoneyFlow、SpendingReviewSignal、AuditFinding 生成。
- DB migration、API、Web UI。

## Base

- local base branch: `codex/opl-ingest-subsidy-20260705-followups`
- base commit: `dbac5916023555591c2876b7bb0618c259018198`
- completed predecessor: `G2PR-005`

## Verification

```bash
git diff --check
```
