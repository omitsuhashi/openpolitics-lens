# Local Infrastructure

## 結論

OpenPolitics Lens のローカル datastore は Docker Compose で固定する。

- RDB: PostgreSQL 18 (`postgres:18.4-trixie`)
- Object storage: MinIO S3 compatible storage (`quay.io/minio/minio`)
- GraphDB: Neo4j Community Edition (`neo4j:2026.05.0`)
- Search index: Meilisearch (`getmeili/meilisearch:v1.37`)

この構成は development 用であり、production secret、公開 network、managed service 運用はまだ扱わない。

## Compose Files

- [compose.yaml](../compose.yaml) — datastore service 定義。
- [.env.example](../.env.example) — local development 用の環境変数 sample。実際の `.env` は git 管理しない。

## Services

| 役割 | Compose service | Host endpoint | Internal endpoint | 永続 volume |
|---|---|---:|---|---|
| RDB 正本 | `postgres` | `localhost:5432` | `postgres:5432` | `postgres_data` |
| S3 compatible storage | `minio` | `localhost:9000` | `minio:9000` | `minio_data` |
| MinIO console | `minio` | `localhost:9001` | `minio:9001` | `minio_data` |
| bucket 初期化 | `minio-init` | なし | `minio:9000` | なし |
| Graph projection | `neo4j` | `localhost:7474`, `localhost:7687` | `neo4j:7474`, `neo4j:7687` | `neo4j_data`, `neo4j_logs` |
| Search index | `meilisearch` | `localhost:7700` | `meilisearch:7700` | `meilisearch_data` |

## Data Ownership

PostgreSQL が system of record。主キー、外部キー、review state、correction request、audit log、score run は PostgreSQL に置く。

MinIO は原本 artifact の保存先。`minio-init` は `openpolitics-raw` bucket を作成し、versioning を有効化する。object key は `raw/{source_id}/{yyyy}/{mm}/{content_hash}.{ext}` を基本形にする。

Neo4j は RDB から再生成できる relationship projection。edge の根拠は Neo4j だけに置かず、RDB の Evidence Item に戻せる ID を持たせる。

Meilisearch は検索 index。検索結果は Source Document、Evidence Item、Public Actor などの RDB ID に戻す。

## Local Usage

```bash
cp .env.example .env
docker compose up -d
docker compose ps
```

停止:

```bash
docker compose down
```

volume も消す場合だけ次を使う。

```bash
docker compose down -v
```

## 出典

- [PostgreSQL 18 Released](https://www.postgresql.org/about/news/postgresql-18-released-3142/) — PostgreSQL Global Development Group が 2025-09-25 に PostgreSQL 18 を latest version として発表。
- [postgres Docker Official Image](https://hub.docker.com/_/postgres) — `18.4`, `18`, `latest`, `18.4-trixie` が supported tag として掲載されている。
- [MinIO Docker image](https://hub.docker.com/r/minio/minio) — standalone server は early development / evaluation 向けとして説明されている。
- [Neo4j Docker Compose standalone](https://neo4j.com/docs/operations-manual/current/docker/docker-compose-standalone/) — Docker Compose で standalone server を起動し、`NEO4J_AUTH` による basic authentication を設定する例がある。
- [Meilisearch local installation](https://www.meilisearch.com/docs/resources/self_hosting/getting_started/install_locally) — Docker で latest stable release を起動する例として `getmeili/meilisearch:v1.37` を示している。

## 関連ページ

- [Grand Design](architecture.md)
- [ADR 0001: Evidence-first hybrid store](adr/0001-evidence-first-hybrid-store.md)
