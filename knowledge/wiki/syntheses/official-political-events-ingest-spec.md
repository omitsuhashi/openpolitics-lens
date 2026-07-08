---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-OFFICIAL-POLITICAL-EVENTS-20260707
status: spec-gate-approved
---

# 公式政治イベント ingest 設計

## 結論

`OPL-OFFICIAL-POLITICAL-EVENTS-20260707` では、国・都道府県・市区町村を横断して、公式サイトから選挙と政治イベントを取得するための source registry と event ingest contract を作る。

単一の全国 API が存在する前提にはしない。正しい設計は、公式 source を jurisdiction ごとに registry 化し、SourceDocument / EvidenceItem へ戻れる RawArtifact を保存し、正規化済みの `OfficialPoliticalEvent` 候補を coverage ledger と一緒に管理する形である。

ここでいう「すべて」は、初期実装から全イベントを完全取得するという意味ではなく、次の状態を実現するという意味にする。

- 公式 source が特定できた jurisdiction / source family は connector 対象として登録する。
- 公式 source が未特定、検索 UI 依存、PDF 依存、利用条件未確認、JS 依存の場合も coverage gap として記録する。
- 取得済みイベントと未取得領域を同じ ledger で説明できる。
- UI/API へ出すイベントは必ず SourceDocument と EvidenceItem に戻せる。

Spec Gate では、選挙と会議を必須 coverage target として扱う方針を承認済みとする。未対応 source、未確認 jurisdiction、検索 UI 依存、PDF 依存、取得失敗は黙って欠落させず、`SourceCoverageRecord` に残して「未取得だが把握済み」の状態にする。

## Epic ID

`OPL-OFFICIAL-POLITICAL-EVENTS-20260707`

## 問題設定

OpenPolitics Lens は、公開資料から確認できる政治過程を根拠付きで追う。現在の設計は東京都 first の source family と ingest/normalize 分離を持っているが、ユーザーが求めているのは、国・地方自治体を問わず、選挙や政治イベントを公式 source から継続取得する仕組みである。

日本の選挙・政治イベント情報は次の理由で分散している。

- 国政選挙、官報、国会日程、国会会議録、パブリックコメントは国側の公式 source に分かれている。
- 地方選挙は各都道府県・市区町村の選挙管理委員会が一次 source になる。
- 地方議会の日程、委員会、議案、会議録は各議会サイトに分かれている。
- 自治体ごとに HTML、PDF、RSS、検索フォーム、JavaScript UI、過去 archive の構造が異なる。

そのため「全国横断の公式イベント API」を一つ作るのではなく、「公式 source registry を正本にした connector 群」を設計単位にする。

## 成功条件

- 国、都道府県、市区町村、議会、選挙管理委員会を表せる `Jurisdiction Profile` と `Source Registry` の contract が定義されている。
- 選挙、国会、地方議会、行政手続、審議会・検討会を同じ `OfficialPoliticalEvent` 候補として扱える。
- source family ごとに acquisition method、fixture strategy、live acquisition gate、coverage status を定義できる。
- イベント日付、開催主体、対象 jurisdiction、source URL、取得日時、原文位置、confidence、review state を Evidence-first に保持できる。
- 「公式 source がない / 未特定 / 検索 UI で自動取得未対応」の状態を coverage gap として明示できる。
- 初期実装 issue は fixture-first に限定でき、通常 test / CI で外部 network に依存しない。

## 採用した判断

### 1. Source registry を正本にする

公式政治イベントの取得可否は、event record ではなく source registry で管理する。

source registry の最小 field:

- `jurisdiction_id`
- `jurisdiction_level`
- `country_code`
- `subdivision_code`
- `municipality_code`
- `source_system`
- `source_family`
- `connector_id`
- `officiality_level`
- `operator_name`
- `entrypoint_url`
- `retrieval_method`
- `coverage_scope`
- `coverage_status`
- `rate_limit_policy`
- `terms_note`
- `last_verified_at`
- `connector_status`

`coverage_status` は最低限、次を持つ。

- `supported`: fixture と connector contract がある。
- `source_identified`: 公式 source は特定済みだが connector 未実装。
- `manual_review_required`: 検索 UI、PDF layout、JS、利用条件などの理由で手動確認が必要。
- `source_missing`: 公式 source が見つかっていない。
- `blocked_by_terms`: 利用条件上、自動取得を止める。
- `retired`: source が廃止・移転した。

### 2. 「公式性」と「網羅性」を分ける

`officiality_level` は次のように分ける。

| level | 意味 | 例 |
| --- | --- | --- |
| `official_primary` | 当該 event の所管機関または議会が直接公開する一次 source | 選挙管理委員会、衆議院、参議院、自治体議会 |
| `official_notice` | 法令上の告示・公示・公告 source | 官報、自治体公報 |
| `official_aggregator` | 公式機関が他機関分を集約する source | 都道府県選管が管内選挙を集約するページ |
| `official_archive` | 過去記録の公式 archive | 国会会議録検索 API、議会会議録 archive |
| `non_official_reference` | 確認補助。正本にはしない | 民間 election calendar、報道、Wikipedia |

OpenPolitics Lens の正本化対象は `official_primary`、`official_notice`、`official_aggregator`、`official_archive` に限る。`non_official_reference` は source discovery の補助に留め、event の根拠にしない。

### 3. Event taxonomy を先に固定する

`OfficialPoliticalEvent` は日程表示だけでなく、政治過程の時系列 anchor として扱う。

初期 event type:

| family | event type | 例 |
| --- | --- | --- |
| Election | `election_announced`, `election_notice_published`, `candidate_filing_opened`, `candidate_filing_closed`, `campaign_started`, `early_voting_started`, `polling_day`, `vote_counting_started`, `result_published`, `term_started`, `term_expires` | 国政選挙、都道府県知事選、市区町村長選、議会議員選 |
| Diet | `diet_session_convened`, `diet_session_ends`, `plenary_meeting_scheduled`, `committee_meeting_scheduled`, `meeting_record_published`, `bill_submitted`, `vote_held` | 衆議院・参議院 |
| LocalAssembly | `assembly_session_scheduled`, `plenary_meeting_scheduled`, `committee_meeting_scheduled`, `bill_submitted`, `petition_received`, `vote_held`, `minutes_published` | 都道府県議会、市区町村議会 |
| PublicConsultation | `public_comment_opened`, `public_comment_closed`, `public_comment_result_published` | e-Gov、自治体意見募集 |
| AdministrativeDeliberation | `council_meeting_scheduled`, `council_minutes_published`, `plan_draft_published`, `plan_adopted` | 審議会、検討会、計画策定 |

初期実装では、候補者個人の街頭演説、政党イベント、政治家公式 SNS の予定、報道イベントは扱わない。公式行政・議会・選管 source で確認できる制度上の event に限定する。

### 4. 予定、告示、結果、会議録を同じ lifecycle に束ねる

選挙や会議は、単一の日付ではなく lifecycle として扱う。

例: 首長選挙

- 任期満了日
- 選挙期日決定
- 告示日
- 立候補届出
- 期日前投票
- 投票日
- 開票
- 結果公表
- 当選告示
- 任期開始

event 同一性の初期 key:

- `jurisdiction_id`
- `event_family`
- `event_type`
- `office_or_body`
- `election_type` または `meeting_type`
- `scheduled_date`
- `source_system`
- `canonical_url`

同一 event に複数 source がある場合、`OfficialPoliticalEvent` は source ごとの `event_source_assertion` を保持し、日付や title の差異を上書きせず review 対象にする。

### 5. Fixture-first / live-gated を全国横断でも維持する

通常 test / CI は外部 network に依存しない。

source family ごとに最低限、次を分ける。

- `fixture`: 保存済み HTML/PDF/JSON/RSS/XML と fake fetcher を使う deterministic path。
- `run`: 将来の scheduled ingest 用 entrypoint。connector 実装前は network request を行わず終了する。
- `live acquisition gate`: 利用条件、robots、rate limit、対象件数、保存先、検索条件、ページング、失敗時挙動を明示してから手動実行する。

### 6. 全国展開は source family 単位で広げる

自治体を 1 つずつ雑に crawler 化しない。source family の形を先に揃える。

初期 source family registry:

| source_family | jurisdiction scope | source_system | retrieval_method | coverage target |
| --- | --- | --- | --- | --- |
| `jp_national_election_notices` | `jp` | 総務省、官報、中央選挙管理関係 source | `static_html_index`, `pdf_batch`, `official_notice_pdf` | 国政選挙の期日、公示、結果、告示 |
| `jp_diet_schedule` | `jp` | 衆議院、参議院 | `static_html_index`, `rss_or_html_index` | 本会議、委員会、会期、審議中継予定 |
| `jp_ndl_diet_minutes` | `jp` | 国立国会図書館 国会会議録検索システム | `official_api` | 会議録、発言、開催日、会議録 URL |
| `jp_public_comment` | `jp` | e-Gov パブリック・コメント | `rss_or_html_index`, API が確認できれば `official_api` | 意見募集開始、締切、結果公示 |
| `jp_prefecture_election_schedules` | `prefecture` | 都道府県選挙管理委員会 | `static_html_index`, `rss_or_html_index`, `pdf_batch` | 都道府県・管内地方選挙の日程、結果、選挙公報 |
| `jp_municipality_election_schedules` | `municipality` | 市区町村選挙管理委員会 | `static_html_index`, `pdf_batch`, `search_ui_snapshot` | 市区町村長・議会議員選挙の日程、結果、選挙公報 |
| `jp_local_assembly_schedule` | `prefecture`, `municipality` | 地方議会 | `static_html_index`, `search_ui_snapshot`, `pdf_batch` | 本会議、委員会、議案、会議録、請願・陳情 |
| `jp_local_public_consultation` | `prefecture`, `municipality` | 自治体意見募集・審議会 page | `static_html_index`, `rss_or_html_index` | 意見募集、審議会、計画案、公表結果 |

### 7. 東京都 connector は横展開の基準実装にする

既存の `tokyo_metro_grants`、`tokyo_assembly_records_bills`、`tokyo_political_funds` の設計を、全国政治イベント connector の基準実装として再利用する。

再利用する既存判断:

- `jurisdiction_id` / `source_family` / `connector_id` 分離。
- RawArtifact と Source Document Candidate の分離。
- fixture-first verification。
- live acquisition を通常 test から分離する。
- 個人別賛否が source にない場合、VotePosition を推定生成しない。

東京都選挙管理委員会は `jp_prefecture_election_schedules` の最初の fixture source として扱う。

### 8. 選挙と会議を必須 coverage target にする

選挙と会議は、OpenPolitics Lens の政治過程 timeline の背骨になるため、他の政治イベントより強い coverage 管理を行う。

対象:

- 国政選挙、都道府県選挙、市区町村選挙。
- 任期満了日、選挙期日、公示・告示、立候補、期日前投票、投票、開票、結果、当選告示。
- 国会の本会議・委員会。
- 都道府県議会、市区町村議会の本会議・委員会。
- 審議会・検討会は P0 ではなく、行政過程 event として P1 以降に扱う。

漏れを防ぐためのルール:

- `SourceCoverageRecord` が存在しない jurisdiction / source family は「未調査」として扱い、UI/API の coverage 表示で完全扱いしない。
- 選挙・会議の source family は `source_missing`、`source_identified`、`manual_review_required`、`supported` のいずれかを必ず記録する。
- 取得失敗、parser failure、date conflict は event を捨てず、coverage / assertion conflict として残す。
- 公式 source が集約ページと一次ページの両方を持つ場合、集約ページだけで完了扱いにせず、一次 source への到達可否を別 record にする。
- event が見つからないことを claim しない。claim できるのは「対象 source を確認したが、この source には event が掲載されていない」までに留める。

## データ contract

### OfficialPoliticalEventCandidate

normalize が生成するイベント候補。

必須 field:

- `event_candidate_id`
- `event_family`
- `event_type`
- `jurisdiction_id`
- `jurisdiction_level`
- `source_system`
- `source_family`
- `connector_id`
- `title`
- `scheduled_date`
- `scheduled_time`
- `timezone`
- `date_precision`
- `office_or_body`
- `event_status`
- `canonical_url`
- `source_document_id`
- `evidence_item_id`
- `extraction_method`
- `confidence`
- `review_state`
- `limitations`

`event_status` の初期値:

- `scheduled`
- `announced`
- `opened`
- `closed`
- `published`
- `completed`
- `cancelled`
- `postponed`
- `unknown`

### EventSourceAssertion

同じ event に複数 source がある場合の根拠単位。

必須 field:

- `event_candidate_id`
- `source_document_id`
- `evidence_item_id`
- `asserted_field`
- `asserted_value`
- `asserted_at`
- `source_priority`
- `conflict_state`

`conflict_state`:

- `none`
- `duplicate`
- `date_mismatch`
- `title_mismatch`
- `status_mismatch`
- `needs_review`

### SourceCoverageRecord

未取得領域を説明する ledger。

必須 field:

- `jurisdiction_id`
- `source_family`
- `coverage_scope`
- `coverage_status`
- `entrypoint_url`
- `last_checked_at`
- `last_successful_fetch_at`
- `last_error`
- `manual_notes`
- `next_action`

## 初期取得対象の優先順位

### P0: 公式 event spine

- 国会会議録検索 API: API があり、fixture と deterministic parser を作りやすい。
- 衆議院・参議院: 会期、本会議・委員会、審議中継予定、会議情報の公式入口。
- e-Gov パブリック・コメント: 意見募集と結果公示を行政手続 event として扱える。
- 官報: 告示・公告 source として保存する。
- 東京都選挙管理委員会: 地方選挙 connector の最初の fixture source。

### P1: 47 都道府県の選管・議会

- 都道府県選挙管理委員会の選挙日程、結果、選挙公報。
- 都道府県議会の本会議・委員会日程、議案、会議録。
- 都道府県単位で市区町村選挙を集約している場合は `official_aggregator` として記録する。

### P2: 市区町村

- 市区町村選挙管理委員会。
- 市区町村議会。
- 自治体の意見募集、審議会、計画策定 page。

市区町村は数が多く、source pattern もばらつくため、最初から全 connector を実装しない。まず source registry と coverage ledger を作り、source identified / manual review required / source missing を明示する。

## 非目標

この epic の初期計画では次を行わない。

- connector 実装。
- local issue ledger 作成。
- GitHub Issue mirror。
- live source 取得。
- browser automation。
- PDF download、OCR、table extraction。
- DB migration。
- API / Web UI。
- 民間サイト、報道、SNS を event 根拠として採用すること。
- 候補者の政治的評価、政策スタンス分類、発言内容の意味解釈。
- 個人別賛否が source にない vote の推定生成。
- 完全網羅を保証する表示。

## Issue 分解方針

Spec Gate 承認後、local issue ledger では次の順に分解する。

1. Source registry / coverage ledger の domain contract。
2. National official event source の fixture connector。
3. `OfficialPoliticalEventCandidate` normalize contract。
4. 国会会議録 API connector。
5. e-Gov public comment connector。
6. 衆議院・参議院 schedule connector。
7. 官報 official notice connector feasibility。
8. 東京都選管 election schedule / result fixture connector。
9. 47 都道府県選管 source inventory generator。
10. 市区町村 source registry bootstrap と coverage gap ledger。

各 issue は fixture-first に限定し、live acquisition は別 gate に分ける。

## 受け入れ条件

Spec Gate では次を承認対象にする。

- `Epic ID`: `OPL-OFFICIAL-POLITICAL-EVENTS-20260707`
- 「全国横断の単一 API」ではなく source registry + connector 群で作る判断。
- 「すべて」を coverage ledger で説明する判断。
- `officiality_level` と `coverage_status` の導入。
- `OfficialPoliticalEventCandidate` と `EventSourceAssertion` の contract。
- P0 / P1 / P2 の導入順序。
- 初期実装は fixture-first、live acquisition は手動 gate。
- 非公式 source を根拠にしない方針。

## 検証方針 / コマンド

Spec Gate artifact の検証:

```bash
git diff --check
```

Issue 化後の実装検証は issue ごとに追加する。想定 baseline:

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

## リモート書き込み方針

現時点の remote policy は `local_only` とする。

- GitHub Issue 作成、push、PR 作成は行わない。
- `gh` CLI が無い状態でも planning は継続可能。
- GitHub mirror が必要になった場合は、Issue Gate 承認後に Remote Gate で別途承認を取る。

## 人間レビューゲート

- Spec Gate: この文書の設計判断、非目標、受け入れ条件、導入順序の承認。
- Issue Gate: local issue ledger、blocker graph、実行順、acceptance criteria の承認。
- Live Acquisition Gate: source family ごとの利用条件、rate limit、対象件数、保存先、検索条件、手動実行可否の承認。
- Remote Gate: GitHub issue / PR / push など外部書き込みの承認。

## 停止条件 / 既知のリスク

停止条件:

- `すべて` の意味が「初期実装で完全取得保証」へ変更される。
- 公式 source と非公式 source の境界が曖昧になる。
- source の利用条件が自動取得を許さない。
- CAPTCHA、ログイン、課金、権限変更、秘密情報が必要になる。
- live acquisition が通常 test / CI に混ざる。
- event source assertion の conflict を上書きして消す設計になる。

既知のリスク:

- 市区町村 source は構造が大きくばらつき、coverage gap が多く出る。
- 選挙情報は告示前、告示後、結果公表後で page 構造や URL が変わることがある。
- PDF と自治体公報は OCR / table extraction が必要になる可能性がある。
- 官報、議会公報、選管 page は日付表記と和暦が混在する。
- 公式 source 自体が過去ページを削除・移転する場合があるため、RawArtifact の immutable 保存が必須。

## 関連ページ

- [Data Sources](../../data-sources.md) — 既存の国会・東京都 source family と取得方針。
- [Domain Model](../../domain-model.md) — SourceDocument、EvidenceItem、DecisionEvent の既存 contract。
- [Tokyo Source Connector Design](tokyo-source-connector-design.md) — 東京都 source family connector の既存設計。
- [Tokyo Subsidy Ingest Spec](tokyo-subsidy-ingest-spec.md) — jurisdiction / source family / connector 分離の基準。

## 初期参照 source

- 官報: https://www.kanpo.go.jp/
- 国会会議録検索 API: https://kokkai.ndl.go.jp/api.html
- 衆議院: https://www.shugiin.go.jp/internet/index.nsf/html/index.htm
- 参議院: https://www.sangiin.go.jp/
- e-Gov パブリック・コメント: https://public-comment.e-gov.go.jp/servlet/Public
- 東京都選挙管理委員会: https://www.senkyo.metro.tokyo.lg.jp/
