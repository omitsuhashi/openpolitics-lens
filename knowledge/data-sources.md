# Data Sources

## 結論

初期取得元は、API がある国会データと、公式ページの構造が比較的読みやすい東京都データを組み合わせる。自治体 MVP は東京都から始める。全国自治体横断は、議事録・採決・契約の公開形式がばらつくため、connector と entity-resolution が安定してからにする。

## Source Priority

| 優先度 | 領域 | 初期 source | 取得方式 | 採用理由 |
|---|---|---|---|---|
| P0 | 会議・発言 | 国会会議録検索 API | API JSON/XML | API があり、meeting/speech 単位で取得できる |
| P0 | 会議・発言 | 東京都議会 会議録・速記録 | HTML / 検索システム | 都議会公式に会議録、速記録、検索入口がある |
| P0 | 議案・議決 | 東京都議会 提出議案と議決結果 | HTML | 年度・定例会別に議案と議決結果が公開される |
| P0 | 政治資金 | 東京都選挙管理委員会 政治資金収支報告書 | HTML/PDF | 東京都届出の政治団体報告書が公表単位で公開される |
| P0 | 選挙 | 東京都選挙管理委員会 選挙結果・選挙公報 | HTML/PDF | 候補者、選挙区、選挙公報の起点になる |
| P0 | 予算・契約 | 東京都財務局、東京都電子調達システム | HTML/PDF/search | 予算・決算・契約情報の公式入口がある |
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

- https://www.gikai.metro.tokyo.lg.jp/record/
- https://www.gikai.metro.tokyo.lg.jp/bill/
- https://www.gikai.metro.tokyo.lg.jp/bill/reg2026-2.html

取得できるもの:

- 本会議の会議録
- 委員会の速記録
- 会議録検索
- 提出議案と議決結果
- 契約案、条例案、予算案、人事案、請願・陳情

設計メモ:

- まず定例会単位で議案一覧を取得する。
- 議案番号、件名、議決結果、種別を正規化する。
- 個人別賛否が公開されていない議案は、個人の VotePosition に変換しない。

### 東京都選挙管理委員会

URLs:

- https://www.senkyo.metro.tokyo.lg.jp/election/togikai-all
- https://www.senkyo.metro.tokyo.lg.jp/election/senkyo-kouhou
- https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku-syokan_this_is_branch

取得できるもの:

- 都議会議員選挙の投開票結果
- 選挙公報
- 政治資金収支報告書
- 政治団体名簿

設計メモ:

- 選挙結果は Person と選挙区の anchor に使う。
- 選挙公報は公約・主張の source とする。
- 政治資金 PDF/HTML は OCR と表抽出の品質検査が必要。

### 東京都財務局・電子調達

URLs:

- https://www.zaimu.metro.tokyo.lg.jp/zaisei/
- https://www.zaimu.metro.tokyo.lg.jp/
- https://www.e-procurement.metro.tokyo.lg.jp/index.jsp

取得できるもの:

- 予算、決算、財政情報
- 契約情報
- 電子調達システムの入札情報サービス

設計メモ:

- 予算・契約は Public Money Flow として保持する。
- 入札情報サービスは検索 UI の調査が必要。API ではなく HTML/search connector になる可能性が高い。

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

## 関連ページ

- [Grand Design](architecture.md) — module 全体。
- [Roadmap](roadmap.md) — 導入順序。
- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md) — 公式 source の確認結果。

## 出典

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md)
