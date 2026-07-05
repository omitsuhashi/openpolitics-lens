# Scoring

## 結論

スコアは人物の善悪や疑惑を示すものではなく、特定の Policy Theme に対する「確認できる関与・接点の強さ」を説明するための補助指標に限定する。すべての score factor は Evidence Item へ戻せる必要がある。

## Score Families

### Policy Involvement Score

政策関与度。

要素:

- 関連発言回数
- 質問回数
- 議案提出・共同提出
- 委員会所属
- 委員長・理事・役職
- 請願・陳情審査への関与

表示例:

> このテーマに関する確認済み発言と委員会所属が多い。

禁止表現:

> この政策を動かした。

### Decision Influence Score

決定影響度。

要素:

- 首長、担当大臣、委員長、議長、会派幹部などの役職
- 採決時の賛否差
- 提出者または説明者としての登場
- 予算・契約議案の所管関係

注意:

- 個人別賛否がない場合は会派単位の情報として扱う。
- 役職は影響可能性を示すだけで、実際の働きかけの証明ではない。

### Funding Proximity Score

資金近接度。

要素:

- 寄附元または支出先と Policy Theme の業界分類
- 政治資金パーティー収入
- 政治団体間移動
- 金額、頻度、時期

注意:

- 寄附や支出は合法的な公開情報であり、違法性を示さない。
- 「近接」は資金資料上の接点であり、見返りや便宜の証明ではない。

### Timeline Alignment Score

時系列一致。

要素:

- FundingContact
- PoliticalStatement
- BillEvent
- VotePosition
- PublicMoneyFlow

例:

```text
寄附/要望 -> 発言 -> 議案/採決 -> 契約/補助金
```

注意:

- 近い時期に並ぶことは因果関係の証明ではない。
- UI では「時系列上近い確認済み接点」と表示する。

### Manifesto Consistency Score

公約整合性。

要素:

- 選挙公報
- 候補者アンケート
- 公式サイト
- 発言
- 採決

注意:

- 公約文の抽象度が高い場合は `low_confidence` とする。
- 反対の根拠が見つからないことを「整合」としない。

### Beneficiary Proximity Score

受益者接近度。

要素:

- PublicMoneyFlow の契約先・補助先
- その主体と政治団体・業界団体・審議会の関係
- Policy Theme との一致

注意:

- 「受益者」は政策・契約・補助金の公開資料上で利益を受ける主体を指す。
- 不正・便宜・癒着を意味しない。

### Spending Review Signal Score

支出検証シグナル。PublicMoneyFlow、SubsidyProgram、AuditFinding、PerformanceIndicator を横断し、追加確認すべき支出を並べるための補助指標。

要素:

- 予算額、決算額、執行率、繰越、不用額の変化
- 同一事業者、同一団体、同一制度への支出集中
- 随意契約、単独応札、低落札率、入札不調などの契約上の注意点
- 補助目的、対象要件、交付先、実績報告、成果指標の接続不全
- 監査報告、包括外部監査、財政援助団体等監査、住民監査請求結果での指摘
- Policy Theme 上の成果指標と支出増減の乖離

注意:

- この score は「無駄遣い」「不正」「便宜供与」を認定しない。
- 監査で公式に指摘された事項と、アプリが計算した注意 signal を分ける。
- 成果指標が悪化していても、政策効果の因果は自動推定しない。
- public UI では「支出検証シグナル」「追加確認が必要な支出」と表示する。

## Confidence

各 score factor は confidence を持つ。

| 値 | 意味 |
|---|---|
| `verified` | 公式 source から直接抽出され、review 済み |
| `parsed` | 公式 source から機械抽出されたが human review 前 |
| `inferred` | 複数 claim から推定された |
| `low_confidence` | OCR、曖昧な名寄せ、会派単位情報など制約がある |

## Score Output Contract

API と DB に保存する score は次を必須にする。

- `score_family`
- `subject_ref`
- `policy_theme_id`
- `score_value`
- `score_band`
- `method_version`
- `computed_at`
- `factor_breakdown[]`
- `supporting_evidence_item_ids[]`
- `counter_evidence_item_ids[]`
- `limitations`

## UI Display Rules

表示する:

- 「確認済み接点」
- 「公開資料上の近接」
- 「この score に寄与した資料」
- 「反証・未確認点」
- 「支出検証シグナル」
- 「追加確認が必要な支出」

表示しない:

- 「黒幕」
- 「癒着」
- 「不正」
- 「無駄遣い」
- 「裏で動かした」
- 「買収」

## Related Pages

- [Domain Model](domain-model.md) — score の input。
- [Spending Review](spending-review.md) — 補助金・契約・予算の検証 signal。
- [Legal And Evidence Risk](legal-risk.md) — 表示文言と risk。
- [Grand Design](architecture.md) — scoring module の位置づけ。

## 出典

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md)
