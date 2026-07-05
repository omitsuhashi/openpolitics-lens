# Evidence-first hybrid store

---
status: accepted
---

OpenPolitics Lens は、PostgreSQL を正本、object storage を原本保存、GraphDB を関係探索用 projection、全文検索を検索補助として併用する。GraphDB first にすると Evidence Item、訂正申請、抽出 version、review state の完全性を守りにくく、RDB only にすると政治家・団体・資金・契約・議案の traversal が弱くなるため、Evidence-first の hybrid 構成を採用する。

2026-07-05 時点のローカル datastore stack は、PostgreSQL 18、MinIO、Neo4j、Meilisearch で固定する。すべて Docker Compose で起動し、host 公開 port は `127.0.0.1` に限定する。

## Considered Options

- RDB only: 監査性は高いが、関係探索と graph UI が重い。
- GraphDB only: 関係探索は強いが、source span、抽出履歴、訂正申請、score run の整合性管理が弱い。
- Hybrid: 運用対象は増えるが、正本と projection を分けられる。

## Consequences

- GraphDB は再生成可能な projection とし、正本にしない。
- すべての edge と score factor は RDB の Evidence Item に戻す。
- 初期 MVP でも Neo4j と Meilisearch の local service は用意する。ただし production logic の正本は PostgreSQL と object storage に置く。
- ローカル object storage は MinIO bucket `openpolitics-raw` に集約し、raw artifact の bucket/object key は RDB に保持する。
