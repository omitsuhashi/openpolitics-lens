---
kind: source
created: 2026-07-05
updated: 2026-07-05
source_files: []
---

# 2026-07-05 Tokyo Data Source Inventory

## この source の位置づけ

東京都 first MVP の data source を、2026-07-05 時点で追加確認した記録。既存の [Official Data Source Check](2026-07-03-official-data-source-check.md) を置き換えるものではなく、東京都に絞った source family の不足確認と設計入力である。

## 確認した公式 source

### 東京都議会

- [議員名簿](https://www.gikai.metro.tokyo.lg.jp/membership/) は、選挙区別、五十音順、会派等別、会派役員、議員 Web サイトへの入口を持つ。
- [委員会名簿](https://www.gikai.metro.tokyo.lg.jp/membership/committees.html) は、常任委員会、議会運営委員会、特別委員会の名簿入口を持つ。
- [会派構成・会派略称一覧](https://www.gikai.metro.tokyo.lg.jp/outline/factional.html) は、会派別議員数、略称、連絡先を持つ。
- [会議録・速記録](https://www.gikai.metro.tokyo.lg.jp/record/) は、本会議の会議録、委員会の速記録、PC/スマートフォン向け会議録検索への入口を持つ。
- [提出議案と議決結果](https://www.gikai.metro.tokyo.lg.jp/bill/) は、年度・定例会別の議案ページを持つ。
- [令和8年第2回定例会 提出議案と議決結果](https://www.gikai.metro.tokyo.lg.jp/bill/reg2026-2.html) では、知事提出議案、議員提出議案、採択された請願・陳情、議決結果が確認できる。
- [請願・陳情の審議状況](https://www.gikai.metro.tokyo.lg.jp/petition/) は、年度・定例会付託分ごとの入口を持つ。

設計入力:

- Person、Faction、CouncilCommittee、Membership は議員名簿・委員会名簿・会派構成を P0 anchor にする。
- Bill と VotePosition は別物として扱う。個人別採決が source にない場合、個人 vote を作らない。
- 請願・陳情は Public Consultation として扱い、議案とは別 entity にする。

### 東京都選挙管理委員会

- [都議会議員選挙・投開票結果](https://www.senkyo.metro.tokyo.lg.jp/election/togikai-all) は、都議会議員選挙と補欠選挙の投開票結果を年度別に掲載している。
- [選挙公報（前回分）](https://www.senkyo.metro.tokyo.lg.jp/election/senkyo-kouhou) は、東京都議会議員選挙、東京都知事選挙、国政選挙の選挙公報入口を持つ。
- [政治資金収支報告書（東京都選挙管理委員会届出）](https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku-syokan_this_is_branch) は、東京都選管に届出された政治団体の収支報告書を掲載している。
- [政治団体名簿](https://www.senkyo.metro.tokyo.lg.jp/organization/seijidantai-meibo) は、政治団体の名寄せ anchor 候補になる。

設計入力:

- ElectionResult は Person と選挙区の anchor として使う。
- 選挙公報は PoliticalStatement の source として扱う。
- 政治資金収支報告書は PDF/OCR と表抽出の品質検査が必要。政治家本人と政治団体を同一 entity にしない。

### 東京都財務局・電子調達

- [財政情報](https://www.zaimu.metro.tokyo.lg.jp/zaisei/) は、予算、決算、財政、財務局主計部所管審議会等、寄附金などの入口を持つ。
- [契約・入札情報（東京都電子調達システム）](https://www.metro.tokyo.lg.jp/tosei/zaise/keiyaku) は、電子調達システムの概要と、入札予定情報、落札結果情報、入札結果、有資格者名簿を閲覧できる旨を説明している。
- [東京都電子調達システム](https://www.e-procurement.metro.tokyo.lg.jp/index.jsp) は、入札情報サービス、電子入札、資格審査の入口を持つ。

設計入力:

- 予算・決算は BudgetDocument と BudgetLine にする。
- 電子調達は ProcurementNotice、BidResult、ContractAward、Company に分ける。
- 検索 UI の安定取得は未検証。P0 は sample extraction と raw artifact 保存を gate にする。

### 東京都教育委員会

- [政策・予算](https://www.kyoiku.metro.tokyo.lg.jp/about/action_and_budget) は、東京都教育施策大綱、東京都教育ビジョン、主要事務事業の概要への入口を持つ。
- [各種計画等](https://www.kyoiku.metro.tokyo.lg.jp/basic/plan) は、教育分野の計画・報告への入口を持つ。
- [審議会等](https://www.kyoiku.metro.tokyo.lg.jp/basic/council) は、東京都総合教育会議、教員育成協議会、専門家会議などの入口を持つ。
- [統計・調査](https://www.kyoiku.metro.tokyo.lg.jp/about/statistics_and_research) は、教育費調査、地方教育費調査、不登校等の調査、体力テスト報告書などの入口を持つ。

設計入力:

- 教育・子育て MVP では、議会発言と議案だけでは政策実施の説明が薄い。教育委員会の計画、事業、審議会、統計を P0.5 として追加する。
- 成果指標は SourceDocument として保持するが、政治家や会派への因果関係は自動 claim にしない。

### 子供政策連携室・都庁総合ホームページ・オープンデータ

- [子供政策連携室](https://www.kodomoseisaku.metro.tokyo.lg.jp/) は、子供政策連携室の取組、各局の子供目線の取組、事業ポータル、出生数・婚姻数などの資料への入口を持つ。
- [東京都福祉局](https://www.fukushi.metro.tokyo.lg.jp/) は、子供家庭、条例・計画・審議会、調査・統計などの入口を持つ。
- [子供・若者・教育](https://www.metro.tokyo.lg.jp/kyoiku/child-education) は、都庁総合ホームページ上のカテゴリ別入口であり、子供政策連携室、福祉局、教育委員会などの組織別入口を持つ。
- [助成・補助金](https://www.metro.tokyo.lg.jp/purpose/grant) は、都庁総合ホームページ上の目的別入口であり、各局の補助金・助成金制度の discovery source になる。
- [意見募集](https://www.metro.tokyo.lg.jp/purpose/opinion)、[審議会・検討会](https://www.metro.tokyo.lg.jp/purpose/meeting)、[計画・財政・予算](https://www.metro.tokyo.lg.jp/purpose/plan) は、行政過程の discovery source になる。
- [東京都オープンデータカタログサイト](https://portal.data.metro.tokyo.lg.jp/) は、データセット、リソース、API 探索、カテゴリ別 dataset の入口を持つ。子供・若者・教育カテゴリも確認できる。

設計入力:

- 都庁総合ホームページは discovery connector として使い、SourceDocument の canonical owner は各局ページに寄せる。
- Open Data は背景統計・施設情報・成果指標に使う。政治的 claim の直接根拠にはしない。
- 子供関連 source では private/sensitive data を扱わず、公式に公開された制度、集計、施設、事業情報に限定する。

### 東京都監査事務局

- [監査事務局](https://www.kansa.metro.tokyo.lg.jp/) は、監査委員監査、監査結果に基づき知事等が講じた措置、住民監査請求、包括外部監査の入口を持つ。
- [財政援助団体等監査](https://www.kansa.metro.tokyo.lg.jp/kansaiin/zaiseienzyo) は、都が補助金の交付等をしている団体に対し、事業が補助等の目的に沿って適切に行われているか等を監査すると説明している。
- 同ページは、補助金、交付金、負担金、貸付金、損失補てん、利子補給その他の財政的援助を受ける団体を対象として扱っている。
- [包括外部監査](https://www.kansa.metro.tokyo.lg.jp/houkatsugaibu) は、特定テーマについて都や関連団体に対して行う監査制度で、年度別の報告書とテーマを掲載している。

設計入力:

- 監査 source は AuditFinding として保持する。
- SpendingReviewSignal はアプリ側の検証 signal であり、公式監査の指摘と混ぜない。
- 教育・子育て MVP では、教育庁、福祉局、子供政策連携室、関連団体に関係する監査テーマを sample 対象にする。

## 未解決点

- 東京都議会の会議録検索システムを機械取得してよい範囲、rate limit、robots、安定 URL。
- 東京都電子調達システムの検索条件固定、ページング、セッション、ダウンロード可否。
- 政治資金収支報告書の PDF layout、OCR 不要範囲、表抽出精度。
- 子供政策・教育関連の source family をどこまで P0 に含めるか。
- 助成・補助金の横断入口から各局制度ページへ辿る discovery 精度。
- 監査報告書 PDF/CSV から AuditFinding と措置状況を安定抽出できるか。
- 東京都オープンデータカタログの API 仕様、license、dataset 更新検知方法。

## 関連ページ

- [Data Sources](../../data-sources.md) — source matrix と取得・構造化設計。
- [Tokyo Data Source Design Query](../queries/2026-07-05-tokyo-data-source-design.md) — 今回の設計検討。
- [Spending Review](../../spending-review.md) — 補助金・契約・予算の検証設計。
- [Official Data Source Check](2026-07-03-official-data-source-check.md) — 2026-07-03 時点の初期確認。

## 出典

- [東京都議会 議員名簿](https://www.gikai.metro.tokyo.lg.jp/membership/)
- [東京都議会 委員会名簿](https://www.gikai.metro.tokyo.lg.jp/membership/committees.html)
- [東京都議会 会派構成・会派略称一覧](https://www.gikai.metro.tokyo.lg.jp/outline/factional.html)
- [東京都議会 会議録・速記録](https://www.gikai.metro.tokyo.lg.jp/record/)
- [東京都議会 提出議案と議決結果](https://www.gikai.metro.tokyo.lg.jp/bill/)
- [東京都議会 令和8年第2回定例会 提出議案と議決結果](https://www.gikai.metro.tokyo.lg.jp/bill/reg2026-2.html)
- [東京都議会 請願・陳情の審議状況](https://www.gikai.metro.tokyo.lg.jp/petition/)
- [東京都選挙管理委員会 都議会議員選挙・投開票結果](https://www.senkyo.metro.tokyo.lg.jp/election/togikai-all)
- [東京都選挙管理委員会 選挙公報](https://www.senkyo.metro.tokyo.lg.jp/election/senkyo-kouhou)
- [東京都選挙管理委員会 政治資金収支報告書](https://www.senkyo.metro.tokyo.lg.jp/organization/shuushihoukoku-syokan_this_is_branch)
- [東京都選挙管理委員会 政治団体名簿](https://www.senkyo.metro.tokyo.lg.jp/organization/seijidantai-meibo)
- [東京都財務局 財政情報](https://www.zaimu.metro.tokyo.lg.jp/zaisei/)
- [東京都 契約・入札情報](https://www.metro.tokyo.lg.jp/tosei/zaise/keiyaku)
- [東京都電子調達システム](https://www.e-procurement.metro.tokyo.lg.jp/index.jsp)
- [東京都教育委員会 政策・予算](https://www.kyoiku.metro.tokyo.lg.jp/about/action_and_budget)
- [東京都教育委員会 各種計画等](https://www.kyoiku.metro.tokyo.lg.jp/basic/plan)
- [東京都教育委員会 審議会等](https://www.kyoiku.metro.tokyo.lg.jp/basic/council)
- [東京都教育委員会 統計・調査](https://www.kyoiku.metro.tokyo.lg.jp/about/statistics_and_research)
- [子供政策連携室](https://www.kodomoseisaku.metro.tokyo.lg.jp/)
- [東京都福祉局](https://www.fukushi.metro.tokyo.lg.jp/)
- [都庁総合ホームページ 子供・若者・教育](https://www.metro.tokyo.lg.jp/kyoiku/child-education)
- [都庁総合ホームページ 助成・補助金](https://www.metro.tokyo.lg.jp/purpose/grant)
- [都庁総合ホームページ 意見募集](https://www.metro.tokyo.lg.jp/purpose/opinion)
- [都庁総合ホームページ 審議会・検討会](https://www.metro.tokyo.lg.jp/purpose/meeting)
- [都庁総合ホームページ 計画・財政・予算](https://www.metro.tokyo.lg.jp/purpose/plan)
- [東京都オープンデータカタログサイト](https://portal.data.metro.tokyo.lg.jp/)
- [東京都監査事務局](https://www.kansa.metro.tokyo.lg.jp/)
- [東京都監査事務局 財政援助団体等監査](https://www.kansa.metro.tokyo.lg.jp/kansaiin/zaiseienzyo)
- [東京都監査事務局 包括外部監査](https://www.kansa.metro.tokyo.lg.jp/houkatsugaibu)
