---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: execution-plan-approved
input_packet: phase0-remainder-p0r-001-input-packet.json
execution_envelope: phase0-remainder-p0r-001-execution-envelope.json
---

# Phase 0 P0R-001 実行ハンドオフ

## 結論

承認済み Issue Gate のうち、最初の runnable issue である `P0R-001` を実行対象にする。

`P0R-001` は Phase 0 の RawArtifact storage gate を固定する issue である。目的は、S3 互換 object storage と RDB `raw_artifacts` payload の共通 contract、`.env.local` + local MinIO 起動、fake object storage test、手動 MinIO smoke command を検証可能にすること。

## 実行対象

- `P0R-001`: RawArtifact storage gate を確定する。

## 非対象

- `P0R-002` 以降の Evidence schema、source registry、source family probe。
- live source 取得、PDF download、browser automation、OCR 実行。
- production S3、managed object storage、secret / credential 操作。
- GitHub Issue mirror、push、PR 作成。
- public UI、score、GraphDB projection。

## Base

- epic base ref: `codex/opl-phase0-remainder-20260707/epic-base`
- epic base sha: `f63f6afefadc4da323cc2a11d5eea53a3f472f81`
- issue branch: `codex/opl-phase0-remainder-20260707/P0R-001-rawartifact-storage-gate`
- issue worktree: `/private/tmp/openpolitics-lens-worktrees/opl-phase0-remainder-20260707/P0R-001`

## Write Scope

- `services/ingest`
- `services/tests`
- `services/pyproject.toml`
- `packages/db`
- `README.md`
- `knowledge/local-infrastructure.md`
- `compose.yaml`
- `.env.example`
- `.envrc`

`.env.local` は local ignored file のまま扱い、tracked artifact にしない。

## Verification

Execution Plan Gate preflight:

- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/grill-to-pr-loop/scripts/check_prereqs.py --phase execution` passed。
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_input_packet.py knowledge/wiki/syntheses/phase0-remainder-p0r-001-input-packet.json` passed。
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/validate_execution_envelope.py knowledge/wiki/syntheses/phase0-remainder-p0r-001-execution-envelope.json` passed。
- `python3 /Users/omitsuhashi/repos/omitsuhashi/skills/skills/issue-implementation-loop/scripts/check_capabilities.py --input knowledge/wiki/syntheses/phase0-remainder-p0r-001-input-packet.json --json` passed。

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

手動 integration:

```bash
docker compose --env-file .env.local up -d minio minio-init
docker compose --env-file .env.local ps minio minio-init
cd services
uv run python -m ingest storage-smoke \
  --bucket openpolitics-raw \
  --endpoint http://localhost:9000
```

Docker / MinIO が使えない環境では、通常 test を失敗させず、manual integration skipped として記録する。

## リモート方針

- `local_only`。
- GitHub Issue mirror、push、PR 作成は行わない。
- remote delivery が必要になった場合は別途 Remote Gate を開く。
