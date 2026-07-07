# services/ingest

外部 source から RawArtifact と取得 metadata を作る service。

## 境界

`services/ingest` の責務:

- `discover`: source の入口 HTML から Source Document Candidate 候補 URL を集める。
- `fetch`: HTML、PDF、CSV、JSON、XML を RawArtifact として保存する。
- `candidate`: source 固有の軽い metadata を取り、Source Document Candidate を manifest に残す。
- content hash、HTTP metadata、connector version、rate limit policy、terms note を記録する。
- `jurisdiction_id`、`source_system`、`source_family`、`connector_id` を分離し、国・自治体ごとの connector 設定を混ぜない。

`services/ingest` では行わないこと:

- EvidenceItem / EvidenceClaim の生成
- 正規化済み fact の生成
- 人物・団体・交付先の名寄せ
- SpendingReviewSignal や score の計算

これらは `services/normalize` 以降の責務。

## Jurisdiction Profile

初回 connector は東京都の補助金・助成金入口を対象にする。

```text
jurisdiction_id: jp-tokyo
jurisdiction_level: prefecture
country_code: JP
subdivision_code: JP-13
municipality_code: null
display_name: 東京都
source_system: tokyo_metropolitan_government
source_family: tokyo_metro_grants
connector_id: jp_tokyo.metro_grants.v1
start_url: https://www.metro.tokyo.lg.jp/purpose/grant
```

`jurisdiction_id` は行政単位、`source_system` は公開主体、`source_family` は公開構造、`connector_id` は実装単位を表す。

## CLI

CLI は cron / daily ingest 用の `run` と、外部 network を使わない再現検証用の
`fixture` を分ける。`--live` option は使わない。

現時点では live fetch は未実装であり、`run` は network request を行わず終了する。
live fetch 実装後は `run` を通常実行 path にし、手動 rehearsal は `--dry-run` で行う。

fixture command は local file だけで動く。通常の検証と test は外部 network を使わない。

```bash
cd services
uv run python -m ingest tokyo-metro-grants fixture \
  --fixture-html tests/fixtures/tokyo_metro_grants_index.html \
  --output-dir ingest/out \
  --run-id fixture-20260705 \
  --discovered-at 2026-07-05T09:00:00Z \
  --fetched-at 2026-07-05T09:01:00Z
```

将来の daily ingest は次の形に寄せる。

```bash
cd services
uv run python -m ingest tokyo-metro-grants run \
  --output-dir ingest/out \
  --run-id tokyo-grants-20260705
```

live fetch 実装前の `run` は status 2 で終了し、network request を行わない。

RawArtifact storage smoke は local MinIO が使える環境だけで手動実行する。通常
test / CI には含めない。

```bash
cd ..
docker compose --env-file .env.local up -d minio minio-init
cd services
uv run python -m ingest storage-smoke \
  --bucket openpolitics-raw \
  --endpoint http://localhost:9000
```

この command は 1 artifact の put、object metadata、RDB `raw_artifacts` payload
を照合する。Docker / MinIO が未起動の場合は `status: skipped` を返す。
endpoint は local MinIO 専用で、`localhost`、loopback IP、Compose service 名
`minio` 以外は PUT 前に拒否する。`--require-available` を付けると未起動も失敗として扱う。

## Output Layout

上の command は `services/ingest/out/` に生成物を書く。

```text
services/ingest/out/
  manifests/
    <run_id>/
      discovered.jsonl
      fetched.jsonl
  raw/
    jp-tokyo/
      tokyo_metro_grants/
        <yyyy>/
          <mm>/
            <sha256>.html
```

`discovered.jsonl` は 1 行 1 candidate、`fetched.jsonl` は 1 行 1 RawArtifact manifest。`raw_artifact_path` は同じ output root からの相対 path。

`services/ingest/out/` は生成物なので git 管理しない。

## 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

repository root では whitespace 検証も行う。

```bash
git diff --check HEAD^..HEAD
```

初回 ingest 仕様は [東京都補助金・助成金 ingest 初期仕様](../../knowledge/wiki/syntheses/tokyo-subsidy-ingest-spec.md) を参照する。
