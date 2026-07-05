# Service Layout

## 結論

OpenPolitics Lens は monorepo として、実行単位を `apps/` と `services/` に分け、共有契約を `packages/` に置く。設計・判断履歴は引き続き `knowledge/` を正とする。

初期実装では次の構成を採用する。

```text
openpolitics-lens/
  apps/
    web/
  services/
    api/
    ingest/
    normalize/
    graph-builder/
    worker/
  packages/
    contracts/
    db/
    domain/
  infra/
    local/
    scripts/
  knowledge/
```

この分け方の目的は、外部 source 取得、正規化、API、UI、projection、job 実行を別々に変更・検証できるようにすること。特に `ingest` を `api` や `web` に混ぜない。`ingest` は外部サイト、PDF、検索 UI、rate limit、再取得に依存する batch 系 service であり、request/response を扱う API とは運用特性が異なる。

## Directory Responsibilities

### `apps/web`

ユーザー向け Web UI を置く。人物ページ、政策テーマページ、Evidence viewer、Relationship graph などを提供する。

責務:

- `services/api` が返す Evidence 付き API response を表示する。
- AI 要約、原文、推定 edge、確認済み edge を視覚的に分ける。
- source URL、Evidence Item、取得日時へ戻れる導線を維持する。

禁止すること:

- 外部 source を直接 crawl しない。
- DB や object storage に直接接続しない。
- Evidence のない claim を表示用に作らない。

### `services/api`

Web UI と将来の public/admin client に向けた API service を置く。

責務:

- 人物、政策テーマ、議案、発言、契約、団体、graph query を返す。
- すべての表示用 response に Evidence bundle を含める。
- public API と admin/review API の境界を分ける。
- OpenAPI schema を `packages/contracts` と同期する。

初期実装は Python/FastAPI を第一候補にする。理由は、`ingest` / `normalize` と Pydantic model、DB access、validation code を共有しやすいから。ただし Web 側の型は OpenAPI から TypeScript client を生成して共有する。

### `services/ingest`

外部 source から raw artifact と fetch metadata を取得する batch/CLI service を置く。

責務:

- `discover`: source family ごとの入口 page、年度 page、検索入口から candidate URL を集める。
- `fetch`: HTML、PDF、CSV、JSON、XML を RawArtifact として object storage に不変保存する。
- `parse`: source 固有の軽い抽出を行い、SourceDocument / raw parse output の候補を作る。
- connector version、rate limit policy、terms note、content hash、HTTP header を保存する。

禁止すること:

- 人物・団体・法人の高リスクな自動名寄せをしない。
- 政治的な意味づけや score を作らない。
- source から直接言えない relation を確認済み edge として作らない。

### `services/normalize`

取得済み RawArtifact / SourceDocument から正規化 fact と EvidenceItem を作る service を置く。

責務:

- 日付、金額、議案番号、会議名、会期、発言番号を正規化する。
- PDF/OCR 由来の表記揺れ、confidence、parse warning を保存する。
- Person、Bill、Speech、PoliticalGroup、FundingContact、PublicMoneyFlow などの候補 fact を作る。
- entity-resolution の候補を作るが、高リスク merge は admin review に回す。

### `services/graph-builder`

PostgreSQL の正規化済み fact から GraphDB projection を作る batch service を置く。

責務:

- RelationshipEdge を Neo4j 等に idempotent に projection する。
- GraphDB を空にしても RDB から再生成できるようにする。
- edge ごとに evidence list、valid_from、valid_to、confidence、source priority を持たせる。

### `services/worker`

定期実行、queue 消費、再取得、parser 再実行、projection rebuild などの job runner を置く。

責務:

- connector job、normalize job、graph rebuild job を schedule / queue から実行する。
- 失敗・再試行・差分件数・最終成功日時を記録する。
- service の business logic は各 service package に置き、worker は orchestration に寄せる。

### `packages/contracts`

service 間と Web/API 間で共有する machine-readable contract を置く。

対象:

- OpenAPI
- JSON Schema
- event schema
- generated client の入力 source

この directory を正にし、`apps/web` と `services/api` が個別に response 型を手書きでずらさないようにする。

### `packages/db`

DB schema、migration、seed、local fixture を置く。

対象:

- PostgreSQL migration
- seed data
- local verification fixture
- schema note

RDB は system of record なので、`packages/db` は service 固有の内部実装ではなく shared package として扱う。

### `packages/domain`

複数 runtime で共有する domain vocabulary と軽量 model を置く。

対象:

- domain enum
- Evidence state
- source family id
- review state
- score method id

Python と TypeScript の実装を無理に同一 source へ押し込まず、必要になった段階で `python/` と `typescript/` を分ける。正本は `packages/contracts` と DB schema に寄せる。

### `infra/local`

ローカル開発用の補助設定を置く。Compose の正本は repo root の `compose.yaml` のままにする。

対象:

- local-only config
- smoke test helper
- datastore bootstrap 補助

### `infra/scripts`

repo 横断の操作 script を置く。service 固有 script は各 service の中に置く。

対象:

- local setup helper
- schema generation helper
- verification helper

## Dependency Rules

依存方向は次を基本にする。

```text
apps/web
  -> packages/contracts

services/api
  -> packages/contracts
  -> packages/db
  -> packages/domain

services/ingest
  -> packages/db
  -> packages/domain

services/normalize
  -> packages/db
  -> packages/domain

services/graph-builder
  -> packages/db
  -> packages/domain

services/worker
  -> services/* public CLI/application APIs
  -> packages/db
```

禁止する依存:

- `apps/web` から `services/ingest` や DB へ直接依存しない。
- `services/ingest` から `apps/web` に依存しない。
- `packages/domain` から `services/*` に依存しない。
- `packages/contracts` から runtime implementation に依存しない。

## Initial Implementation Order

1. `packages/db`
   - `raw_artifacts`, `source_documents`, `evidence_items` の migration を用意する。
2. `services/ingest`
   - 東京都議会の static HTML connector から始める。
   - RawArtifact 保存、content hash、fetch metadata を確定する。
3. `services/normalize`
   - SourceDocument と EvidenceItem の最小生成を実装する。
4. `services/api`
   - Evidence bundle 付き read API を作る。
5. `apps/web`
   - source viewer と人物ページの最小表示を作る。
6. `services/worker`
   - 手動 CLI が安定してから schedule / queue 化する。
7. `services/graph-builder`
   - RDB fact が安定してから projection を作る。

## Repository State

この設計に合わせて、repo root には初期 directory と責務 README を置く。実装 package、dependency manager、CI task はまだ固定しない。各 service の runtime を作る時点で、該当 service の `pyproject.toml` / `package.json` / test layout を追加する。

## 関連ページ

- [Grand Design](architecture.md) — module boundary と data flow の正本。
- [Data Sources](data-sources.md) — `discover -> fetch -> parse` と connector 型。
- [Local Infrastructure](local-infrastructure.md) — PostgreSQL、MinIO、Neo4j、Meilisearch の local datastore 構成。
- [Roadmap](roadmap.md) — MVP の導入順序。

## 出典

- [Grand Design](architecture.md)
- [Data Sources](data-sources.md)
- [Local Infrastructure](local-infrastructure.md)
- [Roadmap](roadmap.md)
