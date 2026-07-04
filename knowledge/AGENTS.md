# LLM Wiki Router

この directory は OpenPolitics Lens の persistent knowledge root です。

## Canonical Procedure

- wiki の `bootstrap`, `ingest`, `query`, `draft-review`, `canonicalize`, `lint` の汎用手順は `llm-wiki` skill を canonical source として扱う。
- single-root 作業では `llm-wiki` skill の router に従い、skill-local `references/core.md`、`references/single-root.md`、該当する `references/modes/*.md` を読む。
- `references/structure.md`、`references/page-authoring.md`、`references/optional-tooling.md` は task が必要とする時だけ読む。
- この file はスキルの複製ではなく、この knowledge root 固有の前提と差分だけを書く。

## Local Contract

- knowledge root は `knowledge/`。
- Topology: single-root。
- Root Registry: 作らない。
- Canonical Owner: repository owner。current Codex session は owner から明示依頼された範囲で direct canonical update できる。
- Write Boundary: owned。
- Draft Target: `wiki/drafts/`。
- Direct canonical update は canonical owner かつ `Write: owned` かつ local contract が許す場合だけ行う。
- non-owner actor の durable proposal は Draft Target に route する。
- `raw/` は不変の source material として扱い、読んでも編集しない。
- `wiki/` は source summary、entity、concept、query、draft、補助 synthesis を置く maintained knowledge base として扱う。
- `index.md` は目的別入口と Active Page Catalog を持つ reader-facing discovery surface として扱う。
- `log.md` は bootstrap、ingest、query、draft-review decision、canonicalize action、lint の append-only timeline として扱う。
- canonical link style は relative Markdown link とし、Obsidian wikilink `[[...]]` は使わない。
- wiki documentation の本文は日本語を基本にする。

## Local Overrides

- project-facing design docs は `knowledge/*.md` に置く。これは user-supplied repository layout の `docs/domain-model.md`, `docs/scoring.md`, `docs/data-sources.md`, `docs/legal-risk.md` を、この repository の実体である `knowledge/` 配下へ集約するための override。
- ADR は `knowledge/adr/` に置く。これは `domain-modeling` skill の ADR format を優先するための override。
- source summary、query note、draft note、補助 synthesis は `knowledge/wiki/...` に置く。
- durable page を作成または更新したら `index.md` と `log.md` を更新する。

## Conflict Rule

- この file の local rule が `llm-wiki` skill と衝突する場合は、この file をこの knowledge root の優先ルールとして扱う。
