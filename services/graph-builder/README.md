# services/graph-builder

PostgreSQL の正規化済み fact から GraphDB projection を生成する batch service を置く。

責務:

- RelationshipEdge を idempotent に projection する。
- GraphDB を RDB から再生成可能に保つ。
- edge ごとの evidence list、期間、confidence を保持する。
