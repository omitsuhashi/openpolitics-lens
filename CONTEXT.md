# OpenPolitics Lens Context

OpenPolitics Lens は、公開資料に基づいて政治過程を追跡し、発言・採決・資金・契約・行政過程の接点を根拠付きで表示するための文脈である。人物の善悪を断定せず、確認可能な事実と推定を分離する。

## Language

**Public Actor**:
公職者、候補者、政党、会派、政治団体、行政機関、審議会、事業者など、公開資料上で政策過程に登場する主体。
_Avoid_: 権力者, 黒幕, 関係者

**Source Document**:
会議録、議案、採決結果、収支報告書、契約結果、予算書、選挙公報など、取得元と取得時点を特定できる公開資料。
_Avoid_: データ, 情報, ネタ

**Evidence Item**:
画面表示、スコア、関係 edge の根拠になる Source Document 内の具体的な位置または引用範囲。
_Avoid_: 根拠っぽいもの, 参考情報

**Evidence Claim**:
Evidence Item から直接言える、検証可能で最小単位の主張。
_Avoid_: 評価, 疑惑, 解釈

**Political Statement**:
会議録、選挙公報、公式サイト、SNS、アンケート回答などに記録された Public Actor の公的な発言。
_Avoid_: 本音, 思想

**Decision Event**:
議案提出、委員会付託、採決、可決、否決、契約締結、補助金交付など、日時を持つ政策決定上の出来事。
_Avoid_: 動き, 結果

**Vote Position**:
議案または動議に対する賛成、反対、棄権、欠席、退席、会派一任などの表明状態。
_Avoid_: 態度, スタンス

**Funding Contact**:
寄附、政治資金パーティー収入、支出先、政治団体間移動など、政治資金資料で確認できる金銭的接点。
_Avoid_: 癒着, 裏金

**Public Money Flow**:
予算、決算、補助金、委託、入札、随意契約、指定管理など、公金が事業者・団体・地域へ流れる公開資料上の流れ。
_Avoid_: 利権, 儲け

**Relationship Edge**:
Public Actor、Source Document、Decision Event、Funding Contact、Public Money Flow の間に確認できる関係。
_Avoid_: つながり, 癒着

**Inferred Relationship**:
複数の Evidence Claim から推定される関係。表示時は推定理由、信頼度、反証可能性を必ず添える。
_Avoid_: 断定関係, 裏の関係

**Policy Theme**:
再エネ、子育て、教育、公共事業、医療など、発言・議案・予算・契約を横断して集約する政策上の主題。
_Avoid_: カテゴリ, ジャンル

**Correction Request**:
本人、事務所、行政機関、第三者からの訂正・反論・補足申請。処理状態と判断根拠を記録する対象。
_Avoid_: クレーム, 火消し
