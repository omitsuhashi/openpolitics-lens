# Data Sources

## 結論

初期取得元は東京都の公式 source を主軸にする。既存の source set は、東京都内で人物、会派、会議、議案、政治資金、選挙、予算、契約を Evidence-first に結ぶには概ね足りている。ただし、教育・子育てを最初の Policy Theme として説明するには、現在の source set だけでは足りない。

追加が必要なものは次の 4 つ。

- 都議、会派、委員会を固定する基礎名簿 source。
- 請願・陳情、意見募集、審議会・検討会など、議会外の Public Consultation source。
- 東京都教育委員会、子供政策連携室、福祉局などの Policy Measure source。
- 東京都オープンデータカタログと統計・調査 source。これは主張の根拠ではなく、背景値と成果指標に使う。
- 補助金・助成金の横断入口、監査事務局の監査報告、包括外部監査、財政援助団体等監査。これは PublicMoneyFlow の検証 source として使う。

国会 API は connector の基準実装や国政との接続に使えるが、東京都 MVP の P0 では脇役にする。全国自治体横断は、東京都 connector と entity-resolution が安定してからにする。

## Coverage Assessment

| 問い | 判断 | 理由 |
|---|---|---|
| 現在のデータソースで情報は足りているか | 部分的に足りている | 議会、議案、選挙、政治資金、予算、契約の入口は揃っている |
| 人物ページ MVP を作れるか | 足りる | 議員名簿、会派、委員会、発言、議案、選挙結果を追加取得すれば成立する |
| 政策テーマページ MVP を作れるか | 追加 source が必要 | 教育・子育ての行政計画、事業、補助、統計、意見募集が必要 |
| 資金と契約の関係 graph を作れるか | P0 では限定的 | 政治資金 PDF/OCR、契約検索 UI、事業者名寄せが重い |
| 個人別採決を作れるか | source がない場合は不可 | 会派や議決結果から個人 VotePosition を推定生成しない |

## Source Priority

| 優先度 | 領域 | 初期 source | 取得方式 | 採用理由 |
|---|---|---|---|---|
| P0 | 人物・所属 | 東京都議会 議員名簿、委員会名簿、会派構成 | HTML | PublicActor、Membership、CouncilCommittee の基礎 anchor になる |
| P0 | 会議・発言 | 東京都議会 会議録・速記録 | HTML / 検索システム | 都議会公式に会議録、速記録、検索入口がある |
| P0 | 議案・議決 | 東京都議会 提出議案と議決結果 | HTML | 年度・定例会別に議案と議決結果が公開される |
| P0 | 請願・陳情 | 東京都議会 請願・陳情の審議状況 | HTML | 市民・団体から議会への入力と審査結果を追える |
| P0 | 政治資金 | 東京都選挙管理委員会 政治資金収支報告書 | HTML/PDF | 東京都届出の政治団体報告書が公表単位で公開される |
| P0 | 政治団体 | 東京都選挙管理委員会 政治団体名簿 | HTML/PDF/CSV 調査 | PoliticalGroup と資金 report の名寄せ anchor になる |
| P0 | 選挙 | 東京都選挙管理委員会 選挙結果・選挙公報 | HTML/PDF | 候補者、選挙区、選挙公報の起点になる |
| P0 | 予算・契約 | 東京都財務局、東京都電子調達システム | HTML/PDF/search | 予算・決算・契約情報の公式入口がある |
| P0.5 | 補助金・助成金 | 都庁総合ホームページ 助成・補助金、各局の制度ページ | HTML/search | 子育て・教育分野の SubsidyProgram discovery に使う |
| P0.5 | 監査 | 東京都監査事務局 財政援助団体等監査、包括外部監査、監査結果に基づく措置 | HTML/PDF/CSV | 公式に指摘された支出・会計・運営上の問題を AuditFinding として保持する |
| P1 | 政策実施 | 東京都教育委員会 政策・予算、各種計画、審議会、統計・調査 | HTML/PDF | 教育 Policy Measure と成果指標の source になる |
| P1 | 政策実施 | 子供政策連携室、福祉局、My TOKYO 子供・若者・教育 | HTML/PDF/RSS 調査 | 子育て施策、補助、相談、事業更新を追う |
| P1 | 行政過程 | 都庁総合ホームページ 意見募集、審議会・検討会、計画・財政・予算 | HTML/search/RSS 調査 | Public Consultation と計画策定過程を補う |
| P1 | 背景統計 | 東京都オープンデータカタログサイト | Catalog/API/CSV | 政策テーマの背景値、施設、統計、地理粒度に使う |
| P1 | 会議・発言 | 国会会議録検索 API | API JSON/XML | API があり、meeting/speech 単位で取得できる。connector 基準実装にも使える |
| P1 | 議案 | 衆議院 議案情報 | HTML | 国政の議案経過・本文・修正案確認に使う |
| P1 | 統計背景 | e-Stat API | API | 人口・産業・地域統計の背景値に使う |
| P2 | 横展開 | 横浜市会 | HTML/search | 会議録、議案、本会議結果の公式入口がある |
| P2 | 横展開 | 大阪市会 | HTML/search | 会議結果、会議録検索、議会中継の公式入口がある |

## National Sources

### 国会会議録検索 API

URL: https://kokkai.ndl.go.jp/api.html

取得できるもの:

- 会議単位簡易出力
- 会議単位出力
- 発言単位出力
- 発言者、会議名、院名、開催日、会議録 ID、発言 ID

設計メモ:

- `meeting_list` は一覧と URL 取得、`meeting` は会議録全体、`speech` は発言単位に使う。
- 利用条件上、短時間の大量アクセスや多重リクエストを避け、取得間隔を設ける。
- 著作権・引用・情報解析の条件確認が必要。

### 衆議院 議案情報

URL: https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm

取得できるもの:

- 議案件名
- 審議状況
- 経過情報
- 本文、修正案へのリンク

設計メモ:

- HTML table から議案番号、議案件名、状態、本文 link を抽出する。
- 参議院側との突合は後続。

### e-Stat API

URL: https://www.e-stat.go.jp/api/

取得できるもの:

- 政府統計データ
- 小地域・地域メッシュを含む統計表

設計メモ:

- 背景統計専用。政治家や団体との関係 edge には直接使わない。
- API 利用には e-Stat ユーザー登録が必要。

## Tokyo Sources

### 東京都議会

URLs:

- https://www.gikai.metro.tokyo.lg.jp/membership/
- https://www.gikai.metro.tokyo.lg.jp/membership/committees.html
- https://www.gikai.metro.tokyo.lg.jp/outline/factional.html
- https://www.gikai.metro.tokyo.lg.jp/record/
- https://www.gikai.metro.tokyo.lg.jp/bill/
- https://www.gikai.metro.tokyo.lg.jp/bill/reg2026-2.html
- https://www.gikai.metro.tokyo.lg.jp/petition/

取得できるもの:

- 議員名簿、会派構成、委員会名簿
- 本会議の会議録
- 委員会の速記録
- 会議録検索
- 提出議案と議決結果
- 契約案、条例案、予算案、人事案、請願・陳情

設計メモ:

- まず `membership`、`factional`、`committees` を取得し、Person、Faction、CouncilCommittee、Membership の期間付き anchor を作る。
- 次に定例会単位で議案一覧、請願・陳情一覧、会議録・速記録を取得する。
- 議案番号、件名、議決結果、種別を正規化する。
- 個人別賛否が公開されていない議案は、個人の VotePosition に変換しない。
- 契約案は Bill と PublicMoneyFlow を直接同一視しない。議案上の契約案、電子調達の落札結果、契約先を別 entity として Evidence で結ぶ。

### 東京都選挙管理委員会

URLs:

- https://www.senkyo.metro.tokyo.lg.jp/election/togikai-all
- https://www.senkyo.metro.tokyo.lg.jp/election/senkyo-kouhou
- https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku-syokan_this_is_branch
- https://www.senkyo.metro.tokyo.lg.jp/organization/seijidantai-meibo

取得できるもの:

- 都議会議員選挙の投開票結果
- 選挙公報
- 政治資金収支報告書
- 政治団体名簿

設計メモ:

- 選挙結果は Person と選挙区の anchor に使う。
- 選挙公報は公約・主張の source とする。
- 政治資金 PDF/HTML は OCR と表抽出の品質検査が必要。
- 政治家本人、後援会、政党支部、資金管理団体は同一 entity にしない。政治団体名簿で PoliticalGroup を立て、人物とは RelationshipEdge で結ぶ。

### 東京都財務局・電子調達

URLs:

- https://www.zaimu.metro.tokyo.lg.jp/zaisei/
- https://www.zaimu.metro.tokyo.lg.jp/
- https://www.metro.tokyo.lg.jp/tosei/zaise/keiyaku
- https://www.e-procurement.metro.tokyo.lg.jp/index.jsp

取得できるもの:

- 予算、決算、財政情報
- 契約情報
- 電子調達システムの入札情報サービス

設計メモ:

- 予算・契約は Public Money Flow として保持する。
- 入札情報サービスは検索 UI の調査が必要。API ではなく HTML/search connector になる可能性が高い。
- P0 では「契約議案」「予算項目」「入札結果」を無理に完全結合しない。まず contract title、organization、amount、vendor、published_at、source_url を保持し、名寄せは review 前提にする。

### 東京都教育委員会・子供政策連携室

URLs:

- https://www.kyoiku.metro.tokyo.lg.jp/about/action_and_budget
- https://www.kyoiku.metro.tokyo.lg.jp/basic/plan
- https://www.kyoiku.metro.tokyo.lg.jp/basic/council
- https://www.kyoiku.metro.tokyo.lg.jp/about/statistics_and_research
- https://www.kodomoseisaku.metro.tokyo.lg.jp/
- https://www.fukushi.metro.tokyo.lg.jp/

取得できるもの:

- 教育施策大綱、教育ビジョン、主要事務事業
- 教育関連の各種計画、審議会、統計・調査
- 子供政策連携室の事業、子供目線の取組、出生数・婚姻数などの資料
- 福祉局の子供家庭、条例・計画・審議会、調査・統計
- 子供・子育て関連の事業ポータル、相談・支援・事故情報 database への入口

設計メモ:

- 教育・子育て MVP では、この family を P1 ではなく P0.5 として扱う。議会・議案 source だけでは、発言と実施施策の接続が弱い。
- `PolicyMeasure`、`BudgetLine`、`PublicConsultation`、`PerformanceIndicator` を分ける。施策紹介記事だけから成果や有効性を claim しない。
- 子供関連の相談、事故、福祉情報は private/sensitive data を扱わず、公式に公開された集計・制度・施設情報に限定する。

### 東京都オープンデータ・都庁総合ホームページ

URLs:

- https://portal.data.metro.tokyo.lg.jp/
- https://www.metro.tokyo.lg.jp/purpose/grant
- https://www.metro.tokyo.lg.jp/purpose/opinion
- https://www.metro.tokyo.lg.jp/purpose/meeting
- https://www.metro.tokyo.lg.jp/purpose/plan
- https://www.metro.tokyo.lg.jp/kyoiku/child-education

取得できるもの:

- dataset/resource/API 入口
- カテゴリ別の子供・若者・教育 dataset
- 助成・補助金の横断 discovery 入口
- 意見募集、審議会・検討会、計画・財政・予算の横断入口
- 報道発表、RSS、My TOKYO 記事への入口

設計メモ:

- Open Data は背景値と補助 source。政治的 claim の一次根拠は、会議録、議案、報告書、予算書、契約結果などに戻す。
- 都庁総合ホームページの横断カテゴリは discovery connector とし、canonical SourceDocument は各局ページに置く。
- 報道発表は速報性が高いが、最終判断の source にはしない。後で予算書、議案、事業ページ、審議会資料へ差し替える。

### 東京都監査事務局

URLs:

- https://www.kansa.metro.tokyo.lg.jp/
- https://www.kansa.metro.tokyo.lg.jp/kansaiin/zaiseienzyo
- https://www.kansa.metro.tokyo.lg.jp/houkatsugaibu

取得できるもの:

- 財政援助団体等監査
- 監査結果に基づき知事等が講じた措置
- 包括外部監査報告書
- 住民監査請求結果
- 一部の監査報告書 open data

設計メモ:

- 監査 source は `AuditFinding` として保持する。アプリ側の SpendingReviewSignal と混ぜない。
- 財政援助団体等監査は、補助金、交付金、負担金、貸付金、損失補てん、利子補給などの財政的援助を受ける団体を検証する source として重要。
- 包括外部監査は特定テーマ・関連団体単位で過去の指摘と措置を追える。教育・子育て分野に直接関係する年度だけを MVP sample にする。

## Acquisition Design

取得は 3 段階に分ける。

1. `discover`
   - Source Family ごとの index page、年度 page、定例会 page、検索入口から candidate URL を集める。
   - 保存するもの: `source_system`, `source_family`, `canonical_url`, `discovered_at`, `parent_url`, `source_period`, `candidate_type`。
2. `fetch`
   - HTML、PDF、CSV、JSON、XML を RawArtifact として不変保存する。
   - 保存するもの: `fetched_at`, `http_status`, `content_hash`, `etag`, `last_modified`, `media_type`, `byte_size`, `connector_version`, `rate_limit_policy`, `terms_note`。
3. `parse`
   - RawArtifact から SourceDocument、EvidenceItem、EvidenceClaim、正規化済み entity/event を作る。
   - 保存するもの: `parser_version`, `location_type`, `location_value`, `quote_text`, `normalized_text`, `confidence`, `parse_warnings`。

Source Family ごとの connector 型:

| connector 型 | 対象 | 初期実装 |
|---|---|---|
| static_html_index | 議員名簿、会派構成、議案一覧、請願・陳情、教育委員会の計画一覧 | `GET` + DOM parser + content hash |
| html_detail | 議案詳細、施策記事、統計記事 | `GET` + main content extraction |
| search_ui_snapshot | 会議録検索、電子調達の入札情報サービス | Playwright 等で検索条件を固定し、検索結果 HTML を RawArtifact 化 |
| pdf_batch | 選挙公報、政治資金収支報告書、予算・決算 PDF | PDF 保存 + text extraction + table extraction + warning |
| api_json_xml | 国会 API、e-Stat、公開 API がある open data | cursor/range fetch + schema validation |
| catalog_api_or_html | 東京都オープンデータ | catalog metadata と resource URL の差分監視 |

## Structuring Design

正規化は「source ごとに直接取れる fact」と「後段で推定する relation」を分ける。

| Source Family | 主な RawArtifact | 正規化 entity/event | EvidenceClaim 例 |
|---|---|---|---|
| 都議会名簿 | HTML | Person, Faction, CouncilCommittee, Membership | A 議員は B 会派に所属している |
| 会議録・速記録 | HTML/search result | Meeting, Speech, PoliticalStatement | A 議員が B 会議で C と発言した |
| 提出議案・議決結果 | HTML | Bill, BillEvent, DecisionEvent | 第 X 号議案は原案可決された |
| 請願・陳情 | HTML | Petition, PetitionEvent, PublicConsultation | 陳情 X は意見付採択された |
| 選挙結果・選挙公報 | HTML/PDF | Election, District, Candidate, ElectionResult, PoliticalStatement | A 候補は B 選挙区で当選した |
| 政治資金 | PDF/HTML | PoliticalGroup, FinanceReport, FundingContact | A 団体は B から C 円の寄附を受けた |
| 予算・決算 | PDF/HTML | BudgetDocument, BudgetLine, PublicMoneyFlow | A 事業に B 円が計上された |
| 電子調達 | HTML/search result | ProcurementNotice, BidResult, ContractAward, Company | A 契約は B 社が C 円で落札した |
| 教育・子供施策 | HTML/PDF | PolicyMeasure, Plan, PerformanceIndicator, PublicConsultation | A 事業は B 年度主要事務事業に記載された |
| Open Data | CSV/API/resource | IndicatorDataset, Facility, RegionStatistic | A 区の B 指標は C である |
| 監査 | HTML/PDF/CSV | AuditFinding, SpendingReviewSignal | A 監査で B 事業に C の指摘があった |

構造化の原則:

- `SourceDocument` と `RawArtifact` を先に作り、後から parser を何度でも再実行できるようにする。
- `EvidenceClaim` は SourceDocument から直接言える最小単位に留める。
- `RelationshipEdge` は EvidenceClaim の組み合わせから projection する。推定 edge は `is_inferred=true` とし、確認済み edge と混ぜない。
- 氏名、団体名、法人名だけで自動 merge しない。公式 ID、stable URL、法人番号、政治団体届出 ID を優先する。
- PDF/OCR 由来の金額・氏名・団体名は confidence と parse warning を必須にする。

## Municipality Candidate Assessment

| 自治体 | 取得しやすさ | 強み | 主なリスク | MVP 優先度 |
|---|---:|---|---|---:|
| 東京都 | 高 | 議会、議案、政治資金、選挙、予算、契約の公式入口が揃う | 件数が多く、PDF/OCR と検索画面 connector が必要 | 1 |
| 横浜市 | 中 | 市会ページに会議録検索、本会議結果/議案、委員会資料がある | 政治資金は県・市の選管範囲確認が必要 | 2 |
| 大阪市 | 中 | 市会ページに会議結果、会議録検索、議員情報、政務活動費がある | 契約・資金との横断 connector が別系統 | 3 |
| 国会 | 高 | 会議録 API と衆議院議案ページが使える | 自治体の契約・補助金・政治資金との結合対象が広がりすぎる | 並行 P1 |

## Connector Policy

各 connector は次の contract を満たす。

- `source_system`
- `source_url`
- `fetched_at`
- `content_hash`
- `connector_version`
- `rate_limit_policy`
- `terms_note`
- `raw_artifact_uri`
- `parser_version`
- `parse_warnings`

追加 contract:

- `source_family`
- `source_period`
- `discovery_url`
- `retrieval_method`
- `normalization_target`
- `evidence_granularity`
- `manual_review_required`

## 関連ページ

- [Grand Design](architecture.md) — module 全体。
- [Roadmap](roadmap.md) — 導入順序。
- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md) — 公式 source の確認結果。
- [Tokyo Data Source Inventory](wiki/sources/2026-07-05-tokyo-data-source-inventory.md) — 東京都 source の追加確認。
- [Tokyo Data Source Design Query](wiki/queries/2026-07-05-tokyo-data-source-design.md) — 今回の設計検討の要約。
- [Spending Review](spending-review.md) — 補助金・契約・予算の検証設計。

## 出典

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md)
- [Tokyo Data Source Inventory](wiki/sources/2026-07-05-tokyo-data-source-inventory.md)
