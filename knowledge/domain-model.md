# Domain Model

## 結論

このアプリの中核 entity は `PublicActor` ではなく `EvidenceItem` である。人物、団体、議案、採決、資金、契約はすべて Evidence Item によって説明可能な状態で保持する。

## Core Types

### SourceDocument

外部公開資料を表す。

主な属性:

- `id`
- `source_system`
- `source_type`
- `canonical_url`
- `title`
- `published_at`
- `retrieved_at`
- `raw_artifact_id`
- `license_note`
- `source_reliability`

例:

- 東京都議会の提出議案と議決結果ページ
- 東京都選挙管理委員会の政治資金収支報告書ページ
- 国会会議録検索 API の speech response

### RawArtifact

HTML、PDF、CSV、JSON、XML などの原本保存単位。

主な属性:

- `id`
- `storage_uri`
- `content_hash`
- `media_type`
- `byte_size`
- `fetch_status`
- `connector_version`

### EvidenceItem

表示や score の根拠になる SourceDocument 内の具体範囲。

主な属性:

- `id`
- `source_document_id`
- `location_type`: `html_selector`, `page_span`, `text_offset`, `table_cell`, `api_record`
- `location_value`
- `quote_text`
- `normalized_text`
- `extraction_method`
- `confidence`

### EvidenceClaim

EvidenceItem から直接言える最小 claim。

主な属性:

- `id`
- `claim_type`
- `subject_ref`
- `predicate`
- `object_ref`
- `event_date`
- `amount`
- `currency`
- `evidence_item_id`
- `review_state`

claim は「A 議員が B 議案に賛成した」「C 団体から D 政治団体へ寄附があった」のように小さく保つ。

### PublicActor

政策過程に登場する主体。

subtype:

- `Person`
- `Party`
- `Faction`
- `PoliticalGroup`
- `AdministrativeBody`
- `CouncilCommittee`
- `Company`
- `Nonprofit`
- `IndustryAssociation`

人物には任期・所属・役職を期間付きで持たせる。現所属だけを上書きしない。

### DecisionEvent

政策決定上の出来事。

subtype:

- `BillSubmitted`
- `CommitteeReferred`
- `SpeechMade`
- `VoteHeld`
- `BillPassed`
- `BillRejected`
- `BudgetApproved`
- `ContractAwarded`
- `SubsidyGranted`
- `PublicCommentClosed`

### VotePosition

議案や動議への賛否状態。

値:

- `for`
- `against`
- `abstain`
- `absent`
- `left_before_vote`
- `not_recorded`
- `group_position_only`

個人別採決が公開されない場合は `group_position_only` とし、個人賛否へ変換しない。

### FundingContact

政治資金上の接点。

subtype:

- `donation`
- `party_ticket`
- `expense`
- `transfer`
- `loan`

支出と寄附を同じ「資金関係」として雑に統合しない。方向、名目、年度、報告書、金額を保持する。

### PublicMoneyFlow

公金の流れ。

subtype:

- `budget_line`
- `settlement_line`
- `subsidy`
- `procurement_notice`
- `contract_award`
- `designated_manager`

契約の議案、入札結果、契約先、予算項目は別 entity とし、Evidence で結ぶ。

### SubsidyProgram

補助金、助成金、給付金、交付金などの制度または事業。

主な属性:

- `id`
- `program_name`
- `admin_body_ref`
- `policy_theme_id`
- `eligibility`
- `budget_line_ref`
- `application_period`
- `reported_year`
- `source_document_id`

SubsidyProgram は PublicMoneyFlow の発生源になり得るが、制度そのものと個別交付を混ぜない。個別交付先や金額が公開されている場合だけ `PublicMoneyFlow.subsidy` として保持する。

### AuditFinding

監査報告、包括外部監査、財政援助団体等監査、住民監査請求結果などに記録された公式な指摘または措置状況。

主な属性:

- `id`
- `audit_type`
- `target_body_ref`
- `target_program_ref`
- `finding_type`
- `finding_summary`
- `fiscal_year`
- `status`
- `measure_taken_ref`
- `evidence_item_id`

AuditFinding は「公式に指摘された事項」を表す。アプリ側の推定や疑問点を AuditFinding として保存しない。

### SpendingReviewSignal

PublicMoneyFlow、SubsidyProgram、AuditFinding、PerformanceIndicator を横断して、追加確認が必要な支出を示す検証用 signal。

主な属性:

- `id`
- `signal_type`
- `target_ref`
- `policy_theme_id`
- `severity_band`
- `supporting_evidence_item_ids`
- `counter_evidence_item_ids`
- `limitations`
- `review_state`

SpendingReviewSignal は無駄遣い、不正、便宜供与の認定ではない。public UI では「支出検証シグナル」「追加確認が必要な支出」と表示する。

### RelationshipEdge

GraphDB へ projection する edge。

主な属性:

- `from_ref`
- `to_ref`
- `edge_type`
- `valid_from`
- `valid_to`
- `evidence_item_ids`
- `confidence`
- `is_inferred`
- `inference_method`

`is_inferred=true` の edge は UI で確認済み edge と分ける。

## Relationship Types

確認済み edge:

- `SPOKE_IN`
- `MENTIONED_THEME`
- `SUBMITTED_BILL`
- `VOTED_ON`
- `MEMBER_OF`
- `CHAIRS`
- `RECEIVED_DONATION_FROM`
- `PAID_TO`
- `CONTRACT_AWARDED_TO`
- `SUBSIDY_GRANTED_TO`
- `HAS_AUDIT_FINDING`
- `RELATED_TO_SOURCE`

推定 edge:

- `TEMPORALLY_NEAR`
- `POTENTIALLY_RELATED_TO_THEME`
- `POSSIBLE_BENEFICIARY_CONTACT`
- `POSSIBLE_SPENDING_REVIEW_SIGNAL`

推定 edge は根拠と反証可能性を必ず持つ。

## Identity Resolution Rules

自動同一視してよい条件:

- 同一公式 ID がある。
- 同一 source system の stable URL が同じ。
- 法人番号が同じ。
- 同一政治団体届出番号が同じ。

review が必要な条件:

- 氏名だけが同じ。
- 旧字体、新字体、通称、肩書きの一致だけで同一人物に見える。
- 住所や代表者が一部一致する政治団体。
- 法人名が似ているが法人番号がない。

禁止:

- SNS 表記だけで人物を merge する。
- 政治家本人と後援会、政党支部、資金管理団体を同一 entity にする。

## Temporal Model

すべての所属、役職、会派、委員会、資金関係、契約関係は期間付きで扱う。

必要な時点:

- `event_date`: 出来事の日付
- `published_at`: 資料公開日
- `retrieved_at`: 取得日
- `valid_from` / `valid_to`: 関係の有効期間
- `reported_year`: 政治資金や決算の対象年度

## 関連ページ

- [Grand Design](architecture.md) — module と storage の全体像。
- [Scoring](scoring.md) — model を使った score calculation。
- [Spending Review](spending-review.md) — 補助金・契約・予算を検証する設計。
- [Legal And Evidence Risk](legal-risk.md) — 表示上の制約。

## 出典

- [Official Data Source Check](wiki/sources/2026-07-03-official-data-source-check.md)
