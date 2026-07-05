# services/api

Web UI と将来の external client に向けた API service を置く。

責務:

- 人物、政策テーマ、議案、発言、契約、団体、graph query を返す。
- すべての表示用 response に Evidence bundle を含める。
- OpenAPI schema を `packages/contracts` と同期する。

初期候補は Python / FastAPI。Web 側とは generated TypeScript client で接続する。
