# OpenPolitics Lens

公開資料に基づいて、政治家・団体・議案・採決・資金・契約・行政過程の確認済み接点を表示するための Web application project。

最初に読む文書:

- [knowledge/index.md](knowledge/index.md) — 設計文書と ADR の入口。
- [knowledge/architecture.md](knowledge/architecture.md) — grand design。
- [knowledge/service-layout.md](knowledge/service-layout.md) — monorepo の app/service/package/infra 構成。
- [knowledge/local-infrastructure.md](knowledge/local-infrastructure.md) — ローカル Docker Compose の datastore 構成。
- [knowledge/roadmap.md](knowledge/roadmap.md) — MVP と導入順序。
- [CONTEXT.md](CONTEXT.md) — domain glossary。

## Local Datastore Stack

ローカル開発用 datastore は Docker Compose で起動する。

```bash
cp .env.example .env.local
docker compose --env-file .env.local up -d
docker compose --env-file .env.local ps
```

主要 endpoint:

- PostgreSQL: `localhost:5432`
- MinIO S3 API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`
- Neo4j Browser: `http://localhost:7474`
- Neo4j Bolt: `bolt://localhost:7687`
- Meilisearch: `http://localhost:7700`

Phase 0 RawArtifact storage smoke だけを確認する場合は MinIO と one-shot
initializer だけを起動する。

```bash
docker compose --env-file .env.local up -d minio minio-init
docker compose --env-file .env.local ps minio minio-init
cd services
uv run python -m ingest storage-smoke \
  --bucket openpolitics-raw \
  --endpoint http://localhost:9000
```

`minio-init` は `openpolitics-raw` bucket 作成と versioning 有効化が完了したら
exit してよい。Docker / MinIO が使えない環境では `storage-smoke` は
`status: skipped` を返し、通常 test には含めない。`storage-smoke` の endpoint は
local MinIO 専用であり、`localhost`、loopback IP、または Compose service 名
`minio` 以外は PUT 前に拒否する。

停止:

```bash
docker compose --env-file .env.local down
```
