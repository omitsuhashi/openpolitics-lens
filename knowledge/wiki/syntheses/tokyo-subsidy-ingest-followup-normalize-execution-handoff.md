---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: execution-handoff-draft
input_packet: tokyo-subsidy-ingest-followup-normalize-input-packet.json
execution_envelope: tokyo-subsidy-ingest-followup-normalize-execution-envelope.json
---

# 東京都補助金 ingest 後続 normalize issue 実行ハンドオフ

## 結論

`G2PR-004` の永続化 contract 完了後の head を土台に、後続 issue として
`G2PR-005` を実装する。

`G2PR-005` は SourceDocument / EvidenceItem / EvidenceClaim の最小
normalize contract を固定する。初期実装は HTML の grant program page
candidate に限定し、title 由来の観測 claim だけを生成する。

## 実行対象

- `G2PR-005`: normalize で EvidenceItem / EvidenceClaim 生成を実装する。

## 非対象

- SubsidyProgram、PublicMoneyFlow、SpendingReviewSignal、AuditFinding 生成。
- 補助金額、交付先、成果指標、監査指摘の意味解釈。
- 人物・団体・法人の entity resolution。
- PDF/OCR、表抽出、添付ファイル解析。
- live PostgreSQL / MinIO 接続、migration 適用、bucket 作成、secret 操作。
- Web UI / API 表示。

## Base

- local base branch: `codex/opl-ingest-subsidy-20260705-followups`
- base commit: `8e7e1c37a046a89bb3615ad3d8a403cc76c644f8`
- completed predecessor: `G2PR-004`

## Verification

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

```bash
git diff --check
```
