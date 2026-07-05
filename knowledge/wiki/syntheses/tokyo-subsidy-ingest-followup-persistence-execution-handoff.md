---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: execution-handoff-draft
input_packet: tokyo-subsidy-ingest-followup-persistence-input-packet.json
execution_envelope: tokyo-subsidy-ingest-followup-persistence-execution-envelope.json
---

# 東京都補助金 ingest 後続永続化 issue 実行ハンドオフ

## 結論

初回 PR [#1](https://github.com/omitsuhashi/openpolitics-lens/pull/1) の `codex/ingestpr`
を土台に、後続 issue の最初として `G2PR-004` を実装する。

`G2PR-004` は PostgreSQL / MinIO への live 接続ではなく、永続化 contract を固定する。
具体的には migration SQL、object storage key contract、fake object storage writer、fetch manifest から DB row payload への変換を追加する。

## 実行対象

- `G2PR-004`: PostgreSQL / MinIO 永続化 contract を設計・実装する。

## 非対象

- live PostgreSQL / MinIO 接続、migration 適用、bucket 作成。
- production credential、secret、外部 service、課金 service。
- EvidenceItem / EvidenceClaim / normalize 実装。
- PDF/OCR、表抽出、他 source family connector。

## Base

- local base branch: `codex/opl-ingest-subsidy-20260705-followups`
- base commit: `129a6c964050be378ea79eaab12991e4b67012e4`
- initial PR: [#1](https://github.com/omitsuhashi/openpolitics-lens/pull/1)

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
