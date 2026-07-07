---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-OFFICIAL-POLITICAL-EVENTS-20260707
status: issue-gate-approved
spec: official-political-events-ingest-spec.md
---

# 公式政治イベント ingest ローカル issue ledger

## 結論

`OPL-OFFICIAL-POLITICAL-EVENTS-20260707` では、選挙と会議を漏らさず扱うため、最初に source registry / coverage ledger / event assertion の土台を作る。その後、国会、e-Gov、官報、東京都選管、東京都議会、47 都道府県、市区町村へ source family 単位で広げる。

初回 PR 実装範囲案は `G2PR-008` から `G2PR-010` までに限定する。ここでは live source 取得を行わず、公式 source の取得可否と未取得 gap を表現できる contract を固定する。

## Ledger

| Epic ID | ローカルID | タイトル | レビュー状態 | 実行状態 | ブロック元 | ブロック先 | GitHub Issue | 実装レビュー | PR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-008 | Source Registry と Coverage Ledger の contract を作る | 承認済み | 実行可能 | なし | G2PR-009, G2PR-010, G2PR-016, G2PR-017, G2PR-018 | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-009 | OfficialPoliticalEventCandidate と EventSourceAssertion の normalize contract を作る | 承認済み | ブロック中 | G2PR-008 | G2PR-010, G2PR-011, G2PR-012, G2PR-013, G2PR-014, G2PR-015, G2PR-016 | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-010 | 選挙・会議の coverage guard と欠落可視化を実装する | 承認済み | ブロック中 | G2PR-008, G2PR-009 | G2PR-015, G2PR-016, G2PR-017, G2PR-018 | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-011 | 国会会議録 API connector の fixture ingest を実装する | 承認済み | ブロック中 | G2PR-008, G2PR-009 | なし | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-012 | 衆議院・参議院 schedule connector の fixture ingest を設計・実装する | 承認済み | ブロック中 | G2PR-008, G2PR-009 | なし | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-013 | e-Gov public comment connector の fixture ingest を実装する | 承認済み | ブロック中 | G2PR-008, G2PR-009 | なし | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-014 | 官報 official notice connector の feasibility を行う | 承認済み | ブロック中 | G2PR-008, G2PR-009 | なし | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-015 | 東京都選管 election schedule / result fixture connector を実装する | 承認済み | ブロック中 | G2PR-008, G2PR-009, G2PR-010 | なし | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-016 | 東京都議会 meeting schedule / bill event fixture connector を実装する | 承認済み | ブロック中 | G2PR-008, G2PR-009, G2PR-010 | なし | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-017 | 47 都道府県の選管・議会 source inventory generator を作る | 承認済み | ブロック中 | G2PR-008, G2PR-010 | G2PR-018 | 未作成 | 未実施 | 未作成 |
| OPL-OFFICIAL-POLITICAL-EVENTS-20260707 | G2PR-018 | 市区町村の選管・議会 source registry bootstrap を作る | 承認済み | ブロック中 | G2PR-008, G2PR-010, G2PR-017 | なし | 未作成 | 未実施 | 未作成 |

## Blocker graph

```text
G2PR-008
  -> G2PR-009
       -> G2PR-010
            -> G2PR-015
            -> G2PR-016
            -> G2PR-017
                 -> G2PR-018
       -> G2PR-011
       -> G2PR-012
       -> G2PR-013
       -> G2PR-014
  -> G2PR-010
  -> G2PR-017
  -> G2PR-018
```

cycle はない。Issue Gate 承認後、`G2PR-008` だけが直ちに実行可能で、`G2PR-009` 以降は依存 issue の完了後に実行可能になる。

## 初回 PR 実装範囲案

- `G2PR-008`
- `G2PR-009`
- `G2PR-010`

初回 PR では、公式 source の取得可否、未取得 gap、event assertion conflict を表現できる最小 contract を作る。国会 API、e-Gov、官報、東京都選管、東京都議会、47 都道府県、市区町村の connector 実装は後続 issue に分ける。

## G2PR-008: Source Registry と Coverage Ledger の contract を作る

### 目的

選挙と会議を漏らさず管理するため、取得済み event だけでなく、未調査、公式 source 未特定、手動確認必要、利用条件 block、取得失敗を表現できる土台を作る。

### 実装範囲

- `services/ingest` または共有 contract 層に `SourceRegistryRecord` と `SourceCoverageRecord` 相当の型を追加する。
- `officiality_level` を `official_primary`, `official_notice`, `official_aggregator`, `official_archive`, `non_official_reference` で表現する。
- `coverage_status` を `supported`, `source_identified`, `manual_review_required`, `source_missing`, `blocked_by_terms`, `retired` で表現する。
- `jurisdiction_id`, `jurisdiction_level`, `source_system`, `source_family`, `connector_id`, `entrypoint_url`, `retrieval_method`, `coverage_scope`, `last_verified_at`, `terms_note` を必須 contract にする。
- fixture JSON / JSONL で registry と coverage ledger を serialize / deserialize できるようにする。

### 受け入れ条件

- 選挙・会議 source family が coverage record なしで `complete` 扱いにならない。
- `official_primary` と `non_official_reference` を混同できない validation がある。
- `blocked_by_terms` の source は connector 実行対象から外れる。
- `git diff --check` が通る。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-009: OfficialPoliticalEventCandidate と EventSourceAssertion の normalize contract を作る

### 目的

公式 source から抽出した選挙・会議 event を、SourceDocument / EvidenceItem に戻れる候補として保持する。

### ブロック元

- `G2PR-008`

### 実装範囲

- `OfficialPoliticalEventCandidate` 相当の normalize contract を追加する。
- `EventSourceAssertion` 相当の根拠単位を追加する。
- `event_family`, `event_type`, `event_status`, `date_precision`, `timezone`, `scheduled_date`, `source_document_id`, `evidence_item_id`, `confidence`, `review_state`, `limitations` を表現する。
- `date_mismatch`, `title_mismatch`, `status_mismatch` を conflict として保持する。
- event 同一性を上書き merge せず、source assertion を追加する形にする。

### 受け入れ条件

- 同じ event に複数 source assertion を付けられる。
- 日付差異を silent overwrite しない。
- EvidenceItem なしの UI/API event 候補を作れない。
- 個人別賛否が source にない場合、VotePosition を生成しない既存方針を崩さない。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-010: 選挙・会議の coverage guard と欠落可視化を実装する

### 目的

「漏れていないように見えるが実際は未取得」という状態を防ぐ。選挙・会議は coverage ledger がない限り完全扱いにしない。

### ブロック元

- `G2PR-008`
- `G2PR-009`

### 実装範囲

- election / meeting source family に coverage record 必須 guard を追加する。
- `source_missing`, `source_identified`, `manual_review_required`, `supported`, `blocked_by_terms` を集計できる coverage summary helper を追加する。
- parser failure、fetch failure、date conflict を coverage / assertion conflict として残す helper を追加する。
- fixture で「未取得だが把握済み」「公式 source 未特定」「取得失敗」を再現する。

### 受け入れ条件

- coverage record がない jurisdiction / source family は complete 表示にならない。
- event が 0 件でも「event が存在しない」と断定しない。
- 取得失敗や parser failure が silent drop されない。
- coverage summary が UI/API 実装前でも unit test で検証できる。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-011: 国会会議録 API connector の fixture ingest を実装する

### 目的

API がある公式 source を最初の event connector として実装し、会議録・発言・開催日を Evidence-first に取り込む基準にする。

### ブロック元

- `G2PR-008`
- `G2PR-009`

### 実装範囲

- `source_family`: `jp_ndl_diet_minutes`
- `connector_id`: `jp.ndl_diet_minutes.v1`
- fixture JSON / XML から meeting record と speech record の SourceDocument Candidate を作る。
- `meeting_record_published` または `meeting_record` 系 event candidate を作る。
- API pagination、request parameter、rate limit は metadata に残す。
- live API request は行わない。

### 受け入れ条件

- fixture だけで deterministic な discovered / fetched / normalized output が得られる。
- API record location を EvidenceItem の location として保持できる。
- meeting date と record publication の区別を曖昧にしない。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-012: 衆議院・参議院 schedule connector の fixture ingest を設計・実装する

### 目的

国会の本会議・委員会予定を会議 event の P0 source として取得する。

### ブロック元

- `G2PR-008`
- `G2PR-009`

### 実装範囲

- `source_family`: `jp_diet_schedule`
- 衆議院と参議院の schedule / calendar / committee page fixture を分ける。
- `plenary_meeting_scheduled`, `committee_meeting_scheduled`, `diet_session_convened`, `diet_session_ends` の候補を作る。
- HTML structure が不安定な場合は `manual_review_required` として coverage ledger に残す。
- live fetch、browser automation は行わない。

### 受け入れ条件

- fixture から会議予定 event candidate を生成できる。
- 日付、院、会議種別、source URL、EvidenceItem が保存される。
- schedule page に event がない場合も coverage record として説明できる。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-013: e-Gov public comment connector の fixture ingest を実装する

### 目的

行政手続 event として、意見募集開始、締切、結果公示を取得する。

### ブロック元

- `G2PR-008`
- `G2PR-009`

### 実装範囲

- `source_family`: `jp_public_comment`
- e-Gov public comment の fixture HTML / RSS / JSON を調査し、安定取得できる形式を採用する。
- `public_comment_opened`, `public_comment_closed`, `public_comment_result_published` の event candidate を作る。
- 案件 ID、所管府省、意見募集期間、結果公示 URL を SourceDocument Candidate に残す。
- live fetch は行わない。

### 受け入れ条件

- fixture から開始日・締切日・結果公示 event を区別できる。
- 締切が未記載または曖昧な場合は `date_precision` と warning を残す。
- non-official mirror を根拠にしない。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-014: 官報 official notice connector の feasibility を行う

### 目的

選挙の公示・告示・公告 source として官報を使うため、取得単位、保存形式、検索方法、利用条件、PDF/OCR 要否を整理する。

### ブロック元

- `G2PR-008`
- `G2PR-009`

### 実装範囲

- 官報の official notice source としての位置づけを整理する。
- 無料公開範囲、保存形式、PDF text layer、検索可否、過去分取得の制約を feasibility に記録する。
- `jp_national_election_notices` への接続条件を整理する。
- connector 実装、PDF download、OCR 実行は行わない。

### 受け入れ条件

- 官報を `official_notice` として扱う条件が明文化される。
- 自動取得を止めるべき利用条件があれば `blocked_by_terms` として表現できる。
- PDF/OCR が必要な場合、後続 issue と warning policy が残る。

### 検証

```bash
git diff --check
```

## G2PR-015: 東京都選管 election schedule / result fixture connector を実装する

### 目的

地方選挙 connector の最初の実装として、東京都選挙管理委員会の選挙日程・結果 source を fixture-first で取り込む。

### ブロック元

- `G2PR-008`
- `G2PR-009`
- `G2PR-010`

### 実装範囲

- `source_family`: `jp_prefecture_election_schedules`
- `jurisdiction_id`: `jp-tokyo`
- `connector_id`: `jp_tokyo.election_schedules.v1`
- 選挙日程、選挙結果、選挙公報の source を fixture で分ける。
- `polling_day`, `result_published`, `election_notice_published`, `term_expires` の候補を作る。
- 都道府県選管が市区町村分を集約している場合は `official_aggregator` として記録し、一次 source への到達可否を別 coverage record にする。
- live fetch は行わない。

### 受け入れ条件

- fixture から election event candidate と coverage record が生成できる。
- 東京都集約 source と市区町村一次 source を混同しない。
- 選挙公報 PDF は RawArtifact 候補に留め、OCR は後続 issue に分ける。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-016: 東京都議会 meeting schedule / bill event fixture connector を実装する

### 目的

地方議会 meeting connector の最初の実装として、東京都議会の本会議、委員会、議案、会議録 source を fixture-first で取り込む。

### ブロック元

- `G2PR-008`
- `G2PR-009`
- `G2PR-010`

### 実装範囲

- `source_family`: `jp_local_assembly_schedule`
- `jurisdiction_id`: `jp-tokyo`
- `connector_id`: `jp_tokyo.assembly_schedule.v1`
- 既存 `tokyo_assembly_records_bills` 設計を参照し、schedule / bill / minutes fixture を分ける。
- `assembly_session_scheduled`, `plenary_meeting_scheduled`, `committee_meeting_scheduled`, `bill_submitted`, `minutes_published` の候補を作る。
- 個人別賛否が source にない場合、VotePosition を生成しない。
- live fetch、検索 UI automation は行わない。

### 受け入れ条件

- fixture から meeting event candidate と coverage record が生成できる。
- 本会議、委員会、議案、会議録を同一 event に雑に merge しない。
- schedule が未掲載でも coverage gap として残る。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-017: 47 都道府県の選管・議会 source inventory generator を作る

### 目的

都道府県レベルで、選挙と会議の公式 source がどこにあるかを漏れなく把握するための inventory を作る。

### ブロック元

- `G2PR-008`
- `G2PR-010`

### 実装範囲

- 47 都道府県の `jurisdiction_id` と選管・議会 source family placeholder を生成する。
- URL が既知の source は `source_identified` とする。
- URL が未確認の source は `source_missing` または `manual_review_required` として coverage ledger に残す。
- 自動 Web search や live fetch は行わず、repo 内 seed / fixture / 手動確認済み source だけを使う。
- 東京都の実装済み connector は `supported` へ昇格できる形にする。

### 受け入れ条件

- 47 都道府県すべてに選管 source coverage record がある。
- 47 都道府県すべてに議会 source coverage record がある。
- URL 未確認の jurisdiction が silent omission にならない。
- inventory output は deterministic で test 可能。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## G2PR-018: 市区町村の選管・議会 source registry bootstrap を作る

### 目的

市区町村レベルの選挙・会議 source を、最初から全 connector 実装するのではなく、coverage gap を明示できる registry として立ち上げる。

### ブロック元

- `G2PR-008`
- `G2PR-010`
- `G2PR-017`

### 実装範囲

- 市区町村 `jurisdiction_id` の seed 方針を決める。
- 選管 source と議会 source の coverage placeholder を生成する。
- 政令指定都市や東京都特別区など、優先自治体の initial source record を作る。
- URL 未確認、検索 UI 依存、PDF 依存、manual review required を coverage ledger に残す。
- live fetch や全自治体 connector 実装は行わない。

### 受け入れ条件

- 市区町村 source を未調査のまま完全扱いしない。
- 優先自治体の選管・議会 source record が生成できる。
- `source_missing` と `manual_review_required` の違いが test で確認できる。
- 47 都道府県 inventory と矛盾しない。

### 検証

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## リモート方針

GitHub Issue mirror は未作成。現時点では local issue ledger を canonical とし、GitHub issue 作成は行わない。

push、PR 作成、GitHub Issue 作成は Remote Gate 承認後にのみ行う。現時点の remote policy は `local_only`。

## Issue Gate で確認すること

- `G2PR-008` から `G2PR-010` を初回 PR 実装範囲にしてよいか。
- `G2PR-011` から `G2PR-018` を後続 issue として残してよいか。
- blocker graph に cycle がないこと。
- 選挙と会議を必須 coverage target とし、未取得 source を silent omission しないこと。
- GitHub Issue mirror を行わず local ledger を canonical とすること。

## 関連ページ

- [Official Political Events Ingest Spec](official-political-events-ingest-spec.md) — 承認済み Spec Gate。
- [Tokyo Source Connector Design](tokyo-source-connector-design.md) — 東京都 source family connector の既存設計。
- [Tokyo Subsidy Ingest Spec](tokyo-subsidy-ingest-spec.md) — jurisdiction / source family / connector 分離の基準。
- [Data Sources](../../data-sources.md) — source family と connector contract。
- [Domain Model](../../domain-model.md) — SourceDocument、EvidenceItem、DecisionEvent の既存 contract。

## 出典

- [Official Political Events Ingest Spec](official-political-events-ingest-spec.md)
