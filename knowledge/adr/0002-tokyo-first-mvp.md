# Tokyo first MVP

---
status: accepted
---

最初の自治体 MVP は東京都を対象にする。東京都は、都議会の会議録・議案・議決結果、東京都選挙管理委員会の選挙結果・選挙公報・政治資金、東京都財務局と電子調達システムの予算・契約情報の公式入口が揃っており、1 自治体内で Evidence-first の pipeline を検証しやすい。

## Considered Options

- 国会 first: API があり取得は容易だが、自治体の契約・補助金・政治資金まで含む MVP 目的から外れやすい。
- 横浜市 first: 市会情報は整理されているが、政治資金と契約の横断管轄を詰める必要がある。
- 大阪市 first: 会議情報はあるが、初期 source set の横断設計は東京都の方が揃えやすい。
- 東京都 first: 件数は多いが、source family が揃っている。

## Consequences

- MVP は東京都内に閉じる。
- 政策テーマは教育・子育てを第一候補にする。
- 個人別採決が source に存在しない場合、個人 vote を推定生成しない。
- 横浜市・大阪市は connector と schema が安定してから横展開する。
