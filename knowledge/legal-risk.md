# Legal And Evidence Risk

## 結論

このサービスの信頼性は、断定しないことではなく「何を断定でき、何を推定に留めるか」を一貫して分けることで守る。すべての画面で一次資料、抽出範囲、取得日時、AI 要約の有無を確認できるようにする。

## Hard Rules

### 一次資料 link を必須にする

すべての表示単位は Evidence Item へ戻す。

必須:

- source title
- source URL
- retrieved_at
- source document type
- source span
- parser/extractor version

### AI 要約と原文を分ける

AI 要約は便利だが、根拠そのものではない。

UI contract:

- 原文 tab
- 抽出 claim tab
- AI 要約 tab
- score factor tab

AI 要約だけを share card や preview に出す場合でも、原文確認 link を同じ面に出す。

### 推定表現を固定する

使ってよい表現:

- 「確認できる接点」
- 「公開資料上、時系列が近い」
- 「この政策テーマに関与した可能性を示す資料がある」
- 「追加確認が必要」

使ってはいけない表現:

- 「裏で糸を引いた」
- 「癒着」
- 「不正」
- 「見返り」
- 「便宜供与」
- 「黒幕」

### 私生活・家族・住所を扱わない

扱うのは公職上の行動、公開資料、政策決定に関係する情報に限定する。

例外:

- 公式資料で法人・政治団体の所在地として公開され、かつ関係確認に必要な場合。ただし UI では住所全文を出す必要がない限り抑制する。

### 訂正・反論導線を必須にする

Correction Request は最初の MVP から入れる。

保持するもの:

- requester type
- target page/entity/evidence
- claim being challenged
- submitted evidence
- review state
- reviewer decision
- published correction note

## Defamation And Misleading Context Controls

高 risk な表示:

- 資金接点と採決を横に並べるだけで因果を示唆する。
- 受益者接近度を「利益供与」と読める形で出す。
- 個人別賛否がない会派単位情報を個人の vote に見せる。
- OCR の誤読をそのまま金額や氏名として表示する。

対策:

- 因果ではなく時系列一致として表示する。
- `confidence` と `limitations` を visible にする。
- low-confidence extraction は public UI へ出す前に review する。
- source excerpt と full source link を同じ画面に置く。

## Copyright And Terms Controls

会議録や PDF は公開資料でも利用条件が異なる。大量複製や本文全文再配布は避ける。

運用:

- 原本は private object storage に保存し、public UI は必要最小限の引用と source link を出す。
- source ごとに `license_note` と `terms_checked_at` を保存する。
- 国会会議録 API は多重リクエストや短時間大量アクセスを避ける。

## Admin Review Queue

human review が必要なもの:

- OCR 由来の氏名・金額・団体名
- fuzzy entity merge
- inferred edge
- negative context を含む表示
- correction request
- source terms が不明な全文転載

## Incident Response

公開後に問題が見つかった場合:

1. 対象 Evidence Claim を `under_review` にする。
2. public UI では該当 claim を一時非表示または warning 表示にする。
3. raw source と extractor log を確認する。
4. correction note を残す。
5. score run を再計算する。

## 関連ページ

- [Scoring](scoring.md) — risk を避けた score 表示。
- [Domain Model](domain-model.md) — Evidence と inferred relationship の境界。
- [Grand Design](architecture.md) — evidence module の責務。

## 出典

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md)
