---
kind: query
created: 2026-07-03
updated: 2026-07-03
source_files: []
---

# 2026-07-03 LLM Wiki Documentation Package

## 結論

OpenPolitics Lens の初期設計文書は、`knowledge/` を single-root knowledge root とする `llm-wiki` として管理する。reader-facing な canonical design docs は、ユーザーが最初に指定した `docs/*.md` 系の repository layout を、この repository の実体である `knowledge/*.md` に集約し、source summary / query note / draft note / 補助 synthesis は `knowledge/wiki/...` に置く。

この query note は「llm-wiki に従ってドキュメント化して欲しい」という依頼に対する運用メモであり、設計の正本は個別の canonical page に分かれている。

## Knowledge Root

- Knowledge root: `knowledge/`
- Topology: single-root
- Root registry: 作らない
- Authority source: [knowledge/AGENTS.md](../../AGENTS.md)
- Discovery surface: [knowledge/index.md](../../index.md)
- Audit trail: [knowledge/log.md](../../log.md)
- Canonical link style: relative Markdown link
- Draft target: `wiki/drafts/`

## Canonical Pages

### Project-facing design docs

- [Grand Design](../../architecture.md) — システム境界、module、data flow、store、MVP。
- [Domain Model](../../domain-model.md) — Evidence を中心にした domain language と relation model。
- [Data Sources](../../data-sources.md) — 取得 source、自治体候補、connector policy。
- [Scoring](../../scoring.md) — score family、confidence、表示制約。
- [Legal And Evidence Risk](../../legal-risk.md) — 出典表示、推定表現、訂正導線、法務 risk。
- [Roadmap](../../roadmap.md) — 東京都 first の導入計画。

### Source summaries

- [Official Data Source Check](../sources/2026-07-03-official-data-source-check.md) — 2026-07-03 時点で確認した公式 source。

### ADR

- [ADR 0001: Evidence-first hybrid store](../../adr/0001-evidence-first-hybrid-store.md) — RDB 正本、object storage、GraphDB projection、全文検索の分担。
- [ADR 0002: Tokyo first MVP](../../adr/0002-tokyo-first-mvp.md) — 最初の自治体として東京都を採用する判断。

## Local Override Rationale

`llm-wiki` の default routing では design doc や roadmap は `wiki/syntheses/` に置ける。ただし、この repo ではユーザーが最初に `docs/domain-model.md`, `docs/scoring.md`, `docs/data-sources.md`, `docs/legal-risk.md` を明示していたため、その構造を `knowledge/*.md` として保持する local override を採用した。

この override の条件:

- `knowledge/AGENTS.md` に local override として明記する。
- すべての active canonical page を `knowledge/index.md` の Active Page Catalog に載せる。
- 変更時は `knowledge/log.md` に entry を追加する。
- source summary、query note、draft note は `knowledge/wiki/...` に置き続ける。

## LLM Wiki Compliance Check

満たしていること:

- `knowledge/AGENTS.md` が knowledge root の local contract になっている。
- repo root `AGENTS.md` は thin router に留めている。
- `raw/` と `wiki/` を分けている。
- `index.md` に目的別入口と Active Page Catalog がある。
- `log.md` に bootstrap と design filing の履歴がある。
- durable query output を `knowledge/wiki/queries/` に保存している。

注意点:

- 現時点では `raw/` に immutable source file は置いていない。Web 上の一次 source は source summary の `## 出典` で参照している。
- `knowledge/*.md` は local override による canonical page であり、`wiki/syntheses/` へ重複 copy しない。
- GraphDB や ingest 実装はまだないため、設計文書は implementation state ではなく design state を表す。

## 次に更新するときの手順

1. [knowledge/index.md](../../index.md) から対象 page を探す。
2. 設計判断を変える場合は、該当 page と必要なら `knowledge/adr/` を更新する。
3. 新しい durable query output は `knowledge/wiki/queries/` に置く。
4. 公式 source の確認結果は `knowledge/wiki/sources/` に source summary として置く。
5. 直接 canonical update した場合は、`knowledge/index.md` と `knowledge/log.md` を更新する。

## 関連ページ

- [knowledge/AGENTS.md](../../AGENTS.md) — knowledge root の local contract。
- [knowledge/index.md](../../index.md) — reader-facing discovery surface。
- [Grand Design](../../architecture.md) — 設計本文の入口。
- [Official Data Source Check](../sources/2026-07-03-official-data-source-check.md) — source 確認の根拠。

## 出典

- [knowledge/AGENTS.md](../../AGENTS.md)
- [knowledge/index.md](../../index.md)
- [knowledge/log.md](../../log.md)
- [Grand Design](../../architecture.md)
