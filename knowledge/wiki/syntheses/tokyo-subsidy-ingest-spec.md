---
kind: synthesis
created: 2026-07-05
updated: 2026-07-05
epic_id: OPL-INGEST-SUBSIDY-20260705
status: spec-gate-approved
---

# 東京都補助金・助成金 ingest 初期仕様

## 結論

`OPL-INGEST-SUBSIDY-20260705` では、教育・子育ての支出検証 MVP に向けて、東京都の補助金・助成金 source を最初の `PublicMoneyFlow` 深掘り対象にする。

初回実装は `services/ingest` に閉じ、都庁総合ホームページの助成・補助金横断入口を起点に、教育・子育て関連の制度ページ候補を `discover` し、HTML を `fetch` して filesystem に RawArtifact と manifest を保存する。PostgreSQL と MinIO への永続化、EvidenceItem / EvidenceClaim / 正規化 fact 生成、SpendingReviewSignal 生成は後続 issue に分ける。

東京都は最初の `Jurisdiction Profile` として扱う。国、都道府県、市区町村、海外自治体を横展開する前提で、connector は `jurisdiction_id`、`source_system`、`source_family`、`connector_id` を分けて記録する。

## Epic ID

`OPL-INGEST-SUBSIDY-20260705`

## 問題設定

OpenPolitics Lens は、公開資料から確認できる政治過程と公金の流れを Evidence-first に追う。教育・子育てを最初の Policy Theme にする場合、議会資料だけでは政策実施と支出の説明が薄い。補助金・助成金は、制度目的、担当局、対象者、交付先、監査指摘へ接続しやすく、教育・子育ての支出検証 MVP の最初の `PublicMoneyFlow` 深掘り対象として妥当である。

現状の repository は service layout と Python 環境の skeleton までで、`services/ingest` に実装 contract がない。そのため、まず外部 source の取得、原本保存、content hash、fetch metadata、Source Document Candidate の contract を固める。

## 成功条件

- `services/ingest` の CLI で fixture を使った `discover` と `fetch` が実行できる。
- `discover` は都庁総合ホームページの助成・補助金入口から、教育・子育て関連の候補 URL と discovery metadata を JSON Lines で出力できる。
- `fetch` は HTML を RawArtifact として filesystem に保存し、`content_hash`, `media_type`, `byte_size`, `http_status`, `connector_version`, `terms_note`, `source_document_candidate` を manifest に記録できる。
- 同一 content の再取得は同じ `sha256` と raw artifact path に収束する。
- 自動テストは外部 network に依存しない。live fetch は手動検証だけに限定する。
- EvidenceItem、EvidenceClaim、正規化 fact、SpendingReviewSignal は生成しない。

## 採用した判断

### 1. 補助金・助成金 first

最初に深掘りする `PublicMoneyFlow` は補助金・助成金にする。

理由:

- 都庁総合ホームページに助成・補助金の横断入口がある。
- 教育委員会、子供政策連携室、福祉局の制度ページへ接続しやすい。
- 財政援助団体等監査と接続しやすく、後続で `AuditFinding` と `SpendingReviewSignal` を分けて扱える。
- 契約・入札 first より、電子調達検索 UI、法人名寄せ、随意契約解釈の不確実性が小さい。

### 2. ingest と normalize を分離する

`services/ingest` の責務は `discover`、`fetch`、RawArtifact 保存、取得監査 metadata、Source Document Candidate 作成までに限定する。

`EvidenceItem`、`EvidenceClaim`、正規化 fact、entity-resolution candidate、parser confidence、parse warning は `services/normalize` の責務にする。

理由:

- ingest は外部 source、rate limit、retry、robots、terms note、content hash、HTTP metadata に集中できる。
- Evidence / claim 生成は parser version、confidence、review state、再実行と結びつくため normalize 側が扱う方が保守しやすい。
- RawArtifact と Source Document Candidate が残れば、normalize は parser を何度でも再実行できる。

### 3. 初回 connector は都庁助成・補助金入口にする

初回 connector は `tokyo_metro_grants` とし、起点 URL は `https://www.metro.tokyo.lg.jp/purpose/grant` にする。

対象は、教育・子育てに関係する可能性がある制度ページ候補の discovery/fetch までに留める。候補判定は初期実装では保守的な keyword と domain allowlist に留め、政治的意味づけや制度評価はしない。

初期 allowlist:

- `www.metro.tokyo.lg.jp`
- `www.kyoiku.metro.tokyo.lg.jp`
- `www.kodomoseisaku.metro.tokyo.lg.jp`
- `www.fukushi.metro.tokyo.lg.jp`

初期 keyword:

- `教育`
- `子供`
- `子ども`
- `こども`
- `若者`
- `子育て`
- `学校`
- `保育`
- `助成`
- `補助`

### 4. filesystem first

初回実装の保存先は filesystem にする。PostgreSQL と MinIO は後続 issue で同じ manifest contract に載せ替える。

理由:

- DB migration と object storage client の契約を初回 ingest と同時に固定すると scope が大きくなる。
- filesystem output で `discover` / `fetch` / `content_hash` / metadata manifest を deterministic に検証できる。
- local fixture test と `git diff --check` で小さく品質確認できる。

推奨 output layout:

```text
services/ingest/out/
  raw/
    jp-tokyo/
      tokyo_metro_grants/
        2026/
          07/
            <sha256>.html
  manifests/
    <run_id>/
      discovered.jsonl
      fetched.jsonl
```

`services/ingest/out/` は生成物なので git 管理しない。

### 5. live fetch は手動、テストは fixture/local のみ

自動テストは fixture HTML と fake fetcher を使う。live fetch は `--live` のような明示 option を持つ手動検証に限定する。CI や通常 test で東京都サイトへ外部 request しない。

### 6. jurisdiction と source family を分離する

OpenPolitics Lens は各自治体や国に対して connector を増やすため、初回実装から `Jurisdiction Profile`、`source_system`、`source_family`、`connector_id` を分離する。

初期 profile:

- `jurisdiction_id`: `jp-tokyo`
- `jurisdiction_level`: `prefecture`
- `country_code`: `JP`
- `subdivision_code`: `JP-13`
- `municipality_code`: `null`
- `display_name`: `東京都`

分離ルール:

- `jurisdiction_id` は政治・行政単位を表す。例: `jp`, `jp-tokyo`, `jp-yokohama`, `jp-osaka`。
- `source_system` は公式運営主体を表す。例: `tokyo_metropolitan_government`, `tokyo_metropolitan_assembly`, `national_diet_library`。
- `source_family` は同じ公開構造を持つ source の集合を表す。例: `tokyo_metro_grants`, `tokyo_assembly_bills`, `ndl_diet_minutes`。
- `connector_id` は実装単位を表す。例: `jp_tokyo.metro_grants.v1`。
- raw artifact と manifest は `jurisdiction_id` と `source_family` を path と record に必ず含める。

この分離により、東京都向け keyword / allowlist / terms note が横浜市、大阪市、国会 source へ漏れないようにする。

## データ contract

### Discovery record

`manifests/<run_id>/discovered.jsonl` は 1 行 1 candidate にする。

必須 field:

- `jurisdiction_id`: `jp-tokyo`
- `jurisdiction_level`: `prefecture`
- `source_system`: `tokyo_metropolitan_government`
- `source_family`: `tokyo_metro_grants`
- `connector_id`: `jp_tokyo.metro_grants.v1`
- `connector_version`
- `canonical_url`
- `discovered_at`
- `parent_url`
- `candidate_type`: `grant_program_page_candidate`
- `title`
- `matched_keywords`
- `relevance_reason`

### Fetch manifest record

`manifests/<run_id>/fetched.jsonl` は 1 行 1 fetched artifact にする。

必須 field:

- `jurisdiction_id`
- `jurisdiction_level`
- `source_system`
- `source_family`
- `connector_id`
- `connector_version`
- `canonical_url`
- `fetched_at`
- `http_status`
- `content_hash`
- `media_type`
- `byte_size`
- `raw_artifact_path`
- `rate_limit_policy`
- `terms_note`
- `source_document_candidate`

### Source Document Candidate

`source_document_candidate` は `SourceDocument` 正本化前の候補であり、normalize が検証して `SourceDocument` に昇格させる入力である。

初期 field:

- `canonical_url`
- `title`
- `source_type`: `grant_program_page`
- `jurisdiction_id`: `jp-tokyo`
- `source_family`: `tokyo_metro_grants`
- `language`: `ja`
- `retrieved_at`
- `raw_artifact_path`

### Connector registry

初期実装では、少なくとも code 上で次の registry を表現できるようにする。

```text
jurisdiction_id: jp-tokyo
source_family: tokyo_metro_grants
connector_id: jp_tokyo.metro_grants.v1
start_url: https://www.metro.tokyo.lg.jp/purpose/grant
```

将来の追加例:

```text
jurisdiction_id: jp
source_family: ndl_diet_minutes
connector_id: jp.ndl_diet_minutes.v1

jurisdiction_id: jp-yokohama
source_family: yokohama_city_council_minutes
connector_id: jp_yokohama.city_council_minutes.v1
```

## 非目標

この epic の初回実装では次を行わない。

- PostgreSQL migration と RDB 永続化。
- MinIO / S3 互換 object storage への保存。
- PDF/OCR、表抽出、添付ファイル解析。
- EvidenceItem、EvidenceClaim、正規化 fact の生成。
- 政治家、団体、事業者、交付先の名寄せ。
- 補助金額、交付先、成果指標、監査指摘の意味解釈。
- SpendingReviewSignal 生成。
- Web UI / API 表示。
- GitHub Issue mirror。
- production 運用、schedule、queue、課金を伴う外部 service 利用。

## 後続で深掘りする項目

非目標化した項目は local issue ledger で追跡する。最低限、次を後続 issue として残す。

| 項目 | 深掘り理由 | 初期状態 |
| --- | --- | --- |
| PostgreSQL / MinIO 永続化 | RDB 正本と immutable object storage へ移す必要がある | ブロック中 |
| normalize による EvidenceItem / EvidenceClaim 生成 | UI/API 表示の根拠 contract に必要 | ブロック中 |
| PDF/OCR と表抽出 | 交付実績、政治資金、監査報告で必要 | ブロック中 |
| SpendingReviewSignal と AuditFinding の接続 | 支出検証 MVP の中核だが断定回避が必要 | ブロック中 |
| 契約・入札 source | PublicMoneyFlow の別軸。電子調達検索 UI の安定取得が未検証 | ブロック中 |
| 予算・決算 source | 制度全体の予算規模と実績把握に必要 | ブロック中 |
| 政治資金 source | FundingContact との横断に必要。PDF/OCR と団体名寄せが重い | ブロック中 |
| 会議録・議案 source | 補助金制度と議会過程を結ぶために必要 | ブロック中 |
| 監査 source | 財政援助団体等監査と包括外部監査から `AuditFinding` を作るために必要 | ブロック中 |
| Open Data / 統計 source | 背景値と成果指標に必要。政治的 claim の直接根拠にはしない | ブロック中 |

## Issue 分解方針

Spec Gate 承認後、次の dependency order で local issue ledger を作る。

| ローカルID | タイトル | 状態 | ブロック元 |
| --- | --- | --- | --- |
| G2PR-001 | Jurisdiction Profile と ingest contract / filesystem output の土台を作る | 実行可能 | なし |
| G2PR-002 | 都庁助成・補助金 connector の fixture discovery/fetch を実装する | ブロック中 | G2PR-001 |
| G2PR-003 | CLI と README を整備し、fixture 検証を通す | ブロック中 | G2PR-002 |
| G2PR-004 | PostgreSQL / MinIO 永続化を設計・実装する | ブロック中 | G2PR-001 |
| G2PR-005 | normalize で EvidenceItem / EvidenceClaim 生成を実装する | ブロック中 | G2PR-002 |
| G2PR-006 | PDF/OCR と表抽出の source family 別 feasibility を行う | ブロック中 | G2PR-002 |
| G2PR-007 | 契約・入札、予算・決算、監査、政治資金、会議録 source を後続 connector として設計する | ブロック中 | G2PR-002 |

初回 PR の実装対象は `G2PR-001` から `G2PR-003` までに限定する。`G2PR-004` 以降は後続 scope として ledger に残す。

## 受け入れ条件

- `services/ingest` に import 可能な Python package がある。
- fixture HTML から `tokyo_metro_grants` の discovery record を deterministic に生成できる。
- fixture fetch で raw artifact と fetch manifest を deterministic に生成できる。
- output path に `sha256` content hash が使われ、同じ content は同じ raw artifact path になる。
- manifest と raw artifact path に `jurisdiction_id`、`source_family`、`connector_id` が含まれ、自治体・国ごとの connector 設定が分離される。
- manifest に `source_document_candidate` が含まれる。
- generated output directory は git 管理されない。
- `services/ingest/README.md` は ingest/normalize の責務境界、CLI、fixture/live の違い、output contract を説明する。
- 後続項目は local issue ledger に `ブロック中` issue として残る。

## 検証方針 / コマンド

初回実装の最小 verification:

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

repo root:

```bash
git diff --check
```

live fetch は外部 network を使うため、通常 verification には含めない。実施する場合は、対象 URL、取得件数、保存先、rate limit policy を明示して手動で行う。

## リモート書き込み方針

現時点では `gh` CLI は利用可能だが、`gh auth status` は token invalid で失敗し、GitHub remote も未設定である。GitHub Issue mirror は行わない。

PR 作成は、remote と GitHub 認証が解決し、明示的に許可された場合だけ行う。PR は draft を基本にし、ready-for-review、merge、force push、権限変更、deploy、課金、production 操作は行わない。

## 人間レビューゲート

- Spec Gate: この仕様書の path、Epic ID、採用判断、非目標、受け入れ条件、検証方針、remote policy、停止条件を承認する。
- Issue Gate: local issue ledger の issue 分解、blocker graph、dependency order、後続 issue の残し方を承認する。
- Remote Gate: remote write が必要になった時点で、実行する action set を提示して承認を得る。

## 停止条件 / 既知のリスク

- Epic ID が変更または曖昧になった場合。
- dirty changes が planned write scope と衝突する場合。
- 初回 connector が live source の取得条件、robots、rate limit、利用条件に抵触する可能性がある場合。
- fixture と live HTML の構造差が大きく、connector contract を変える必要が出た場合。
- DB/MinIO 永続化、normalize、Evidence generation へ scope が膨らむ場合。
- remote 作成、push、PR 作成など external write に current approval がない場合。

## 関連ページ

- [Data Sources](../../data-sources.md) — 東京都 source family と取得 pipeline。
- [Service Layout](../../service-layout.md) — `services/ingest` と `services/normalize` の責務境界。
- [Spending Review](../../spending-review.md) — 補助金・契約・予算・監査を横断する支出検証設計。
- [Tokyo Data Source Design Query](../queries/2026-07-05-tokyo-data-source-design.md) — 教育・子育てと補助金 first の検討元。

## 出典

- [Tokyo Data Source Design Query](../queries/2026-07-05-tokyo-data-source-design.md)
- [Tokyo Data Source Inventory](../sources/2026-07-05-tokyo-data-source-inventory.md)
- [Data Sources](../../data-sources.md)
- [Service Layout](../../service-layout.md)
