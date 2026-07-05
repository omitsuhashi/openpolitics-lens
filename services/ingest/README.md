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

fixture mode は local file だけで動く。通常の検証と test は外部 network を使わない。

```bash
cd services
uv run python -m ingest tokyo-metro-grants \
  --fixture-html tests/fixtures/tokyo_metro_grants_index.html \
  --output-dir ingest/out \
  --run-id fixture-20260705 \
  --discovered-at 2026-07-05T09:00:00Z \
  --fetched-at 2026-07-05T09:01:00Z
```

`--live` は将来の手動 live fetch 用の明示 opt-in。G2PR-003 の通常 path と test では使わない。現 CLI は `--live` 指定時に network request を行わず終了する。

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
