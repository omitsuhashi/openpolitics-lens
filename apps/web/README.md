# apps/web

ユーザー向け Web UI を置く。

責務:

- 人物ページ、政策テーマページ、Evidence viewer、Relationship graph を表示する。
- `services/api` の Evidence 付き API response を読む。
- DB、object storage、外部 source へ直接接続しない。

実装 runtime と framework はまだ未作成。初期候補は TypeScript / Next.js。
