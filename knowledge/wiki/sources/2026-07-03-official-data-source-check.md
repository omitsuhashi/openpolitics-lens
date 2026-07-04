---
kind: source
created: 2026-07-03
updated: 2026-07-03
source_files: []
---

# 2026-07-03 Official Data Source Check

## この source の位置づけ

OpenPolitics Lens の初期設計で採用候補にする公式 source を、2026-07-03 時点で確認した記録。実装前に各 source の利用条件、取得方式、rate limit、robots、PDF/OCR 品質を再確認する。

## 確認した公式 source

### 国会会議録検索 API

- URL: https://kokkai.ndl.go.jp/api.html
- 会議単位簡易出力、会議単位出力、発言単位出力がある。
- XML または JSON で返す。
- 会議単位簡易出力と発言単位出力は最大 100 件、会議単位出力は最大 10 件。
- 利用条件上、短時間大量アクセス、多重リクエストを避ける必要がある。

### 衆議院 議案情報

- URL: https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm
- 議案件名、審議状況、経過、本文、修正案への link がある。
- HTML table から抽出する想定。

### e-Stat API

- URL: https://www.e-stat.go.jp/api/
- 政府統計データを機械判読可能な形式で取得できる API。
- 利用には e-Stat ユーザー登録が必要。

### 東京都議会

- URL: https://www.gikai.metro.tokyo.lg.jp/
- 会議録・速記録: https://www.gikai.metro.tokyo.lg.jp/record/
- 提出議案と議決結果: https://www.gikai.metro.tokyo.lg.jp/bill/
- 例: https://www.gikai.metro.tokyo.lg.jp/bill/reg2026-2.html
- 会議録、委員会速記録、会議録検索、提出議案、議決結果、請願・陳情などの入口がある。

### 東京都選挙管理委員会

- URL: https://www.senkyo.metro.tokyo.lg.jp/
- 都議会議員選挙・投開票結果: https://www.senkyo.metro.tokyo.lg.jp/election/togikai-all
- 選挙公報: https://www.senkyo.metro.tokyo.lg.jp/election/senkyo-kouhou
- 政治資金収支報告書: https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku-syokan_this_is_branch
- 政治団体名簿、政治資金収支報告書、選挙結果、選挙公報の入口がある。

### 東京都財務局・電子調達

- 財政情報: https://www.zaimu.metro.tokyo.lg.jp/zaisei/
- 財務局: https://www.zaimu.metro.tokyo.lg.jp/
- 電子調達システム: https://www.e-procurement.metro.tokyo.lg.jp/index.jsp
- 予算、決算、契約情報、電子調達システム、入札情報サービスの入口がある。

### 横浜市会

- URL: https://www.city.yokohama.lg.jp/shikai/
- 市会の記録: https://www.city.yokohama.lg.jp/shikai/kiroku/
- 会議録検索、市会中継、会議録、本会議の結果/議案、委員会資料の入口がある。

### 大阪市会

- URL: https://www.city.osaka.lg.jp/shikai/
- 会議結果、会議録検索、議会中継、議員名簿、政務活動費、入札契約情報の入口がある。

## 設計に反映すること

- 東京都は自治体 MVP の第一候補。
- 国会会議録 API は connector 設計の基準実装に使う。
- HTML/PDF source はまず raw artifact と Evidence Item の保存を優先し、推定・score は後段に回す。
- 個人別採決が source にない場合、会派や議決結果から個人 vote を作らない。

## 未解決点

- 東京都電子調達システムの検索結果を安定取得できるか。
- 政治資金収支報告書の PDF/OCR 品質。
- 東京都議会の会議録検索システムの利用条件と機械取得許容範囲。
- 横浜市、大阪市の政治資金・契約 data をどの管轄 source と結合するか。

## 関連ページ

- [Grand Design](../../architecture.md) — この source check を反映した全体設計。
- [Data Sources](../../data-sources.md) — source matrix。
- [Roadmap](../../roadmap.md) — MVP 導入順序。

## 出典

- [国会会議録検索システム 検索用APIの仕様](https://kokkai.ndl.go.jp/api.html)
- [衆議院 議案の一覧](https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm)
- [e-Stat API機能](https://www.e-stat.go.jp/api/)
- [東京都議会](https://www.gikai.metro.tokyo.lg.jp/)
- [東京都議会 会議録・速記録](https://www.gikai.metro.tokyo.lg.jp/record/)
- [東京都議会 提出議案と議決結果](https://www.gikai.metro.tokyo.lg.jp/bill/)
- [東京都選挙管理委員会](https://www.senkyo.metro.tokyo.lg.jp/)
- [東京都財務局 財政情報](https://www.zaimu.metro.tokyo.lg.jp/zaisei/)
- [東京都電子調達システム](https://www.e-procurement.metro.tokyo.lg.jp/index.jsp)
- [横浜市会](https://www.city.yokohama.lg.jp/shikai/)
- [大阪市会](https://www.city.osaka.lg.jp/shikai/)
