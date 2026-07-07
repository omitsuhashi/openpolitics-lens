---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: spec-gate-approved
---

# Phase 0 残実装設計

## 結論

`OPL-PHASE0-REMAINDER-20260707` では、既存の補助金 first 実装を土台に、Phase 0 の未達 gate を「source family 横断の sample artifact と EvidenceItem を fixture-first で作れる状態」まで進める。

既存の `OPL-INGEST-SUBSIDY-20260705` / `G2PR-001` から `G2PR-007` は、ingest contract、`tokyo_metro_grants` fixture connector、永続化 contract、最小 normalize、PDF/OCR feasibility、後続 connector registry の完了記録である。一方、Roadmap の Phase 0 はまだ次を満たしていない。

- 5 種類以上の source から各 10 件の sample artifact を作る。
- 各 source で raw artifact を保存する。
- source URL、取得日時、content hash を記録する。
- 1 source 10 件以上の EvidenceItem を作る。
- parser warning taxonomy を実装 contract と DB に反映する。
- 教育・子育ての `SubsidyProgram` sample と監査 source sample を evidence trace 付きで保持する。
- SpendingReviewSignal を public UI に出す前に、公式監査指摘とアプリ計算 signal を分ける土台を作る。

この epic では public UI、score、GraphDB projection、本番 live ingest、GitHub mirror は扱わない。目的は Phase 1 に入る前に、S3 互換 object storage に載る RawArtifact 保存、RDB の `raw_artifacts` row、locator、warning、review guard、sample coverage を検証可能にすることである。

## Epic ID

`OPL-PHASE0-REMAINDER-20260707`

## 現状

完了済み:

- `services/ingest` は `JurisdictionProfile`、`SourceFamily`、`ConnectorDefinition`、`DiscoveryRecord`、`FetchManifestRecord`、`SourceDocumentCandidate` を持つ。
- `tokyo_metro_grants` は fixture HTML discovery と fake fetch で RawArtifact / manifest を生成できる。
- `packages/db` には `raw_artifacts`、`source_document_candidates`、`source_documents`、`evidence_items`、`evidence_claims` の初期 migration がある。
- `services/ingest` には S3 / MinIO 互換の `ObjectStorageOutputWriter`、fake object storage test、`FetchManifestRecord` から DB row payload を作る helper がある。
- `services/normalize` は `grant_program_page` の HTML title から `SourceDocument`、`EvidenceItem`、`EvidenceClaim` を生成できる。
- [東京都 PDF/OCR・表抽出 feasibility](tokyo-subsidy-pdf-ocr-feasibility.md) は warning taxonomy の候補を整理済み。
- [東京都 source connector 設計](tokyo-source-connector-design.md) は `tokyo_procurement`、`tokyo_budget_settlement`、`tokyo_audit_reports`、`tokyo_political_funds`、`tokyo_assembly_records_bills` の registry 候補を整理済み。

未完了:

- `EvidenceItem` dataclass / migration に `parse_warnings` と locator metadata がない。
- `evidence_claims` migration は `grant_program_page_title_observed` だけを許可しており、Phase 0 の複数 source family に拡張できない。
- `search_ui_snapshot` の検索条件、ページング、sort order、取得日時を manifest / locator として保存する contract がない。
- PDF / table extraction の出力 artifact、page / bbox / table cell locator、warning 保存先が未実装。
- `tokyo_metro_grants` は 10 件 sample baseline ではなく、現在の fixture は 3 件 discovery に留まる。
- Phase 0 の各 source family が S3 互換 object storage の `object_bucket` / `object_key`、RDB `raw_artifacts` row、`canonical_url`、`fetched_at`、`content_hash` を必ず通る、という acceptance が弱い。
- local MinIO bucket `openpolitics-raw` への smoke verification は、この draft で P0R-001 の手動 integration gate として固定する。現行実装は fake object storage と SQL inspection に留まる。
- 一部 docs は古い shorthand の `raw/{source_id}/{yyyy}/{mm}/{content_hash}.{ext}` を使っており、実装済み migration / object writer の `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}` と表記が揺れている。
- 議会、選挙、政治資金、予算・契約、監査の connector / parser / fixture evaluator は未実装。
- `SubsidyProgram`、`AuditFinding`、`SpendingReviewSignal` は domain 設計のみで、実装 contract は未確定。

## Roadmap 対照表

### 成果 / Gate

| Roadmap 項目 | 現状 | 不足 | 実装設計 | 対応 issue |
| --- | --- | --- | --- | --- |
| 東京都 source connector の feasibility report | `tokyo-source-connector-design.md` と `tokyo-subsidy-pdf-ocr-feasibility.md` は docs-first synthesis として存在する | 実 fixture / sample artifact / parser warning / coverage 結果に基づく Phase 0 report ではない | coverage CLI が source family 別に RawArtifact、EvidenceItem、warning、blocked reason を集計し、`knowledge/wiki/syntheses/phase0-source-probe-feasibility-report.md` を生成する | P0R-012 |
| 5 種類の source から各 10 件の sample artifact | `tokyo_metro_grants` fixture は 3 discovery に留まる。他 source family は設計のみ | Roadmap 対象 source 7 系統のうち、10 sample artifact を作れる実装がない | Roadmap の対象 source 7 系統をすべて registry 化し、最低 5 系統、可能なら 7 系統すべてで 10 RawArtifact / SourceDocumentCandidate を fixture-only で作る | P0R-003 から P0R-010 |
| parser warning taxonomy | docs 上の taxonomy 候補はある | `EvidenceItem` / DB / serialized contract / parser result に warning 保存先がない | warning catalog、`parse_warnings`、`location_metadata`、`extraction_artifact_path` を normalize contract と migration に追加する | P0R-002 |
| Evidence Item schema の確定 | HTML title 用の最小 `EvidenceItem` dataclass と migration はある | PDF/table/search snapshot/locator/warning を表現できない。serialized contract がない | HTML/PDF/table/search snapshot 共通の locator schema、warning、confidence、extraction artifact path を確定し、DB と JSON serialization test を揃える | P0R-002 |
| 教育・子育ての `SubsidyProgram` sample artifact | grant page title claim のみ | `SubsidyProgramCandidate` として制度名、所管、対象、申請期間などを evidence trace 付きで保存できない | `tokyo_metro_grants` を 10 sample に拡張し、制度 candidate claim を作る。個別交付 / `PublicMoneyFlow` は作らない | P0R-009 |
| 監査 source の sample artifact | 監査 source は docs 設計のみ | 監査 report RawArtifact、指摘本文 locator、`AuditFindingCandidate` がない | 監査 index/report fixture から 10 sample artifact と `AuditFindingCandidate` 5 件以上を作る | P0R-010 |
| 各 source で raw artifact を保存できる | object storage writer と migration contract はある | source family 横断の storage gate と local MinIO smoke がない | S3 互換 object storage + RDB `raw_artifacts` payload を Phase 0 共通 gate にし、fake test と手動 local MinIO smoke を持つ | P0R-001 |
| source URL、取得日時、content hash を記録できる | `FetchManifestRecord` は `canonical_url`、`fetched_at`、`content_hash` を持つ | 全 source family に適用する acceptance になっていない | source family registry と fixture catalog の必須 field に `canonical_url`、`fetched_at`、`content_hash`、`media_type`、`byte_size`、`connector_version`、`terms_note` を入れる | P0R-001, P0R-003 |
| Evidence Item を 1 source 10 件以上作れる | grant title 1 item / fetched page 程度 | Roadmap source ごとの parser evaluator がない | 各 source parser は 10 EvidenceItem を fixture から生成し、coverage CLI で source family 別に数える | P0R-004 から P0R-010, P0R-012 |
| 監査指摘とアプリ計算 signal を分けて保存できる | `SpendingReviewSignal` は domain docs のみ | 監査指摘 storage と app-calculated signal storage の分離 contract がない。単に「signal を作らない」だけでは Roadmap Gate を満たさない | `AuditFindingCandidate` と `SpendingReviewSignalCandidate` / `app_calculated_review_signal_candidate` を別 contract / table / claim type に分ける。public UI と scoring は非対象 | P0R-011 |

### 対象 source

| Roadmap 対象 source | 現状 | Phase 0 実装設計 | 対応 issue |
| --- | --- | --- | --- |
| 東京都議会 会議録・速記録 | `tokyo_assembly_records_bills` の設計のみ | 会議録検索 snapshot fixture、検索条件 metadata、meeting/speaker/speech block locator、10 RawArtifact、10 EvidenceItem を作る | P0R-004 |
| 東京都議会 提出議案と議決結果 | `tokyo_assembly_records_bills` の設計のみ | 年度・定例会別 bill / decision fixture、議案番号・件名・議決結果の observed claim、VotePosition 非生成 guard を作る | P0R-005 |
| 東京都選挙管理委員会 選挙公報・選挙結果 | `data-sources.md` の source 記録のみ | election result HTML/PDF fixture と public bulletin metadata fixture を分け、Candidate / ElectionResult candidate claim を作る | P0R-006 |
| 東京都選挙管理委員会 政治資金収支報告書 | `tokyo_political_funds` の設計と PDF/OCR feasibility のみ | report index、政治団体名簿、PDF sample evaluator、text layer / OCR 判定、PoliticalGroup / FinanceReport candidate を作る。FundingContact は確定しない | P0R-007 |
| 東京都財務局・電子調達 契約/予算 | `tokyo_budget_settlement` / `tokyo_procurement` の設計のみ | budget/settlement index fixture、電子調達 search snapshot fixture、amount unit warning、BudgetLine / ContractAward candidate guard を作る | P0R-008 |
| 都庁総合ホームページ 助成・補助金 | `tokyo_metro_grants` 3 件 fixture と title claim のみ | 10 sample baseline、`SubsidyProgramCandidate` claim、教育・子育て filter、個別交付 / PublicMoneyFlow 非生成 guard を作る | P0R-009 |
| 東京都監査事務局 財政援助団体等監査・包括外部監査 | docs 設計のみ | audit report index / report fixture、official wording preservation、`AuditFindingCandidate`、app signal 分離 guard を作る | P0R-010, P0R-011 |

## 採用した判断

1. Phase 0 残りは、新しい epic として扱う。
   既存 `G2PR-001` から `G2PR-007` は補助金 first の完了済み ledger なので、残りの source probe を同じ ledger に追記しない。

2. 実装順は common contract first にする。
   source family を増やす前に、`parse_warnings`、locator metadata、claim type catalog、source family registry、sample coverage report を先に固定する。これを後回しにすると source ごとの parser が独自形式になり、Phase 1 の API / UI で回収不能になる。

3. RawArtifact の正規保存先は S3 互換 object storage と RDB `raw_artifacts` row の組にする。
   filesystem writer は fixture / local deterministic verification 用 adapter として残すが、Phase 0 完了判定は `openpolitics-raw` bucket、`object_key`、`raw_artifact_path`、`canonical_url`、`fetched_at`、`content_hash`、`media_type`、`connector_version`、`terms_note` を含む object storage / DB payload contract を基準にする。canonical object key は `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}` とする。

4. 通常 test / CI は fixture-only にする。
   live source 取得、PDF download、browser automation、OCR 実行は通常 test から分離する。live acquisition は source family ごとの checklist と手動 gate が揃うまで実行しない。

5. local MinIO smoke は通常 test ではなく、手動 integration verification として切る。
   Docker Compose の `minio` / `minio-init` と bucket `openpolitics-raw` は Phase 1 技術前提である。起動入口は `.env.local` と `docker compose --env-file .env.local up -d minio minio-init` に固定する。Phase 0 残実装では fake object storage test を必須にし、MinIO への 1 artifact put / metadata / RDB payload 照合は P0R-001 の手動 smoke command として固定する。

6. Roadmap の対象 source 7 系統はすべて Phase 0 の probe 対象にする。
   Roadmap の成果は「5 種類の source」と書いているが、対象 source は 7 系統列挙されている。したがって implementation design では 7 系統すべてを issue 化し、最低 5 系統で 10 sample artifact / 10 EvidenceItem を満たすだけでなく、残り 2 系統も feasibility report と blocked reason を残す。fixture で無理なく扱える場合は 7 系統すべてを完了対象にする。

7. `EvidenceClaim` の claim type は DB check 直書きではなく catalog 化する。
   Phase 0 では claim type が source family ごとに増える。migration の `check (claim_type in (...))` を増やし続けるのではなく、code-side catalog と SQL inspection / fixture tests で許可範囲を検証する。

8. `SubsidyProgram` と `AuditFinding` は candidate-first にする。
   Phase 0 では official source に戻れる `SubsidyProgramCandidate` / `AuditFindingCandidate` 相当を作る。human review policy と cross-source linkage が揃うまで、public-facing `SpendingReviewSignal` は作らない。

9. `SpendingReviewSignal` の public 表示と score は非目標だが、保存分離 contract は Phase 0 scope に含める。
   Roadmap Gate は「監査指摘とアプリ計算 signal を分けて保存できる」であり、「signal を作らない」だけでは不足である。Phase 0 では `AuditFindingCandidate` と app-calculated review signal candidate を別 contract / table / claim type に分け、public UI へ出ない状態で保存分離を検証する。

10. 政治資金、契約・入札、予算・決算は extraction と entity resolution を分ける。
   金額、氏名、団体名、会社名を抽出できても、`FundingContact`、`Company`、`PublicMoneyFlow`、`RelationshipEdge` へ自動確定しない。

## 非目標

- production / live source 取得の定期実行。
- production S3、managed object storage、secret / credential 操作。
- GitHub issue mirror、push、PR 作成。
- public Web UI、API endpoint、GraphDB projection。
- score / ranking / SpendingReviewSignal の public 表示。
- OCR engine 選定と大量 OCR 実行。
- 人物、政治団体、法人、事業者の自動名寄せ。
- 個人別賛否が source にない議案からの `VotePosition` 推定生成。
- 監査指摘を「無駄遣い」「不正」「違法」と断定する分類。

## 実装単位案

正式な local issue ledger は Spec Gate 承認後に作る。この一覧は Issue Gate 前の分解案として扱う。

| Local ID 案 | タイトル | ブロック元 | 完了条件 |
| --- | --- | --- | --- |
| P0R-001 | RawArtifact storage gate を確定する | なし | `openpolitics-raw` bucket / `object_key` / RDB `raw_artifacts` payload / source URL / `fetched_at` / `content_hash` を source family 共通の acceptance にし、fake object storage test と `.env.local` + `docker compose --env-file .env.local up -d minio minio-init` の local MinIO smoke command を持つ |
| P0R-002 | Evidence schema / warning / claim catalog を拡張する | P0R-001 | `EvidenceItem` に `parse_warnings`、`location_metadata`、`extraction_artifact_path` が入り、claim type / predicate catalog が複数 source family を扱える |
| P0R-003 | Phase 0 source registry / fixture harness を作る | P0R-001, P0R-002 | Roadmap 対象 source 7 系統の connector definition、fixture metadata、coverage target、required metadata が code から参照できる |
| P0R-004 | 都議会 会議録・速記録 probe を実装する | P0R-003 | 会議録検索 snapshot fixture、検索条件 metadata、meeting/speaker/speech block locator、10 RawArtifact、10 EvidenceItem を作れる |
| P0R-005 | 都議会 提出議案・議決結果 probe を実装する | P0R-003 | bill / decision fixture から議案番号、件名、議決結果の observed claim を作り、VotePosition 非生成 guard がある |
| P0R-006 | 選挙公報・選挙結果 probe を実装する | P0R-003 | election result / bulletin metadata fixture から Candidate / ElectionResult candidate claim と 10 EvidenceItem を作れる |
| P0R-007 | 政治資金収支報告書 probe を実装する | P0R-003 | report index、政治団体名簿、PDF sample evaluator、text layer / OCR 判定を作り、FundingContact 非生成 guard がある |
| P0R-008 | 財務局・電子調達 契約/予算 probe を実装する | P0R-003 | budget/settlement index と procurement search snapshot から 10 sample artifact、amount unit warning、BudgetLine / ContractAward 非確定 guard を作れる |
| P0R-009 | 助成・補助金 `SubsidyProgramCandidate` probe を実装する | P0R-003 | `tokyo_metro_grants` を 10 sample baseline に拡張し、教育・子育て `SubsidyProgramCandidate` を evidence trace 付きで作れる |
| P0R-010 | 監査 source / `AuditFindingCandidate` probe を実装する | P0R-003 | 監査 report index / report fixture から 10 sample artifact と `AuditFindingCandidate` 5 件以上を作り、公式文言を保持できる |
| P0R-011 | 監査指摘とアプリ計算 signal の保存分離 contract を作る | P0R-010 | `AuditFindingCandidate` と app-calculated review signal candidate を別 contract / table / claim type に分け、public UI へ出ない保存分離 guard を test できる |
| P0R-012 | Phase 0 feasibility report / coverage CLI を作る | P0R-004, P0R-005, P0R-006, P0R-007, P0R-008, P0R-009, P0R-010, P0R-011 | source family 別の sample artifact 件数、EvidenceItem 件数、warning 件数、blocked reason、non-goal guard を report できる |

## 依存順

```text
P0R-001
  -> P0R-002
       -> P0R-003
            -> P0R-004
            -> P0R-005
            -> P0R-006
            -> P0R-007
            -> P0R-008
            -> P0R-009
            -> P0R-010
                 -> P0R-011
                      -> P0R-012
```

`P0R-004` から `P0R-010` は Roadmap の対象 source 7 系統に対応する。Roadmap の「5 種類の source」は最低 gate として扱うが、この spec では対象 source 7 系統すべてを probe 対象にする。5 系統未満しか 10 sample artifact / 10 EvidenceItem を満たせない場合は Phase 0 incomplete とする。残り 2 系統も少なくとも feasibility report と blocked reason を持たなければ Phase 0 を閉じない。

## Contract 変更方針

### RawArtifact storage

Phase 0 の raw artifact 保存は、単に fixture file を作ることではなく、次の不変条件を満たすことと定義する。

- 原本 bytes は S3 互換 object storage に保存できる。local development の bucket は `openpolitics-raw`。
- object key は `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}`。
- `raw_artifact_path` は object storage-backed ingest では `object_key` と一致する。
- RDB `raw_artifacts` row は `object_bucket`、`object_key`、`raw_artifact_path`、`canonical_url`、`fetched_at`、`content_hash`、`hash_algorithm=sha256`、`media_type`、`byte_size`、`connector_id`、`connector_version`、`rate_limit_policy`、`terms_note` を持つ。
- `SourceDocumentCandidate` は同じ `raw_artifact_id`、`raw_artifact_path`、`jurisdiction_id`、`source_family` に戻れる。
- filesystem writer は fixture adapter として許容するが、同じ manifest / DB payload / object key contract を通ることを test する。
- fake object storage test は必須。local MinIO smoke は通常 test から分け、P0R-001 で command と skip 条件を固定する。

既存 docs のうち `raw/{source_id}/{yyyy}/{mm}/{content_hash}.{ext}` と書かれている箇所は shorthand として扱わず、上記 canonical key へ更新する。

### Local MinIO runtime

Phase 0 の local MinIO は、repo root の `compose.yaml` と `.env.local` だけで起動する。

```bash
cp .env.example .env.local
docker compose --env-file .env.local up -d minio minio-init
docker compose --env-file .env.local ps minio minio-init
```

固定値:

- long-running service: `minio`
- one-shot initializer: `minio-init`
- bucket: `openpolitics-raw`
- S3 API host endpoint: `http://localhost:9000`
- MinIO console host endpoint: `http://localhost:9001`
- Compose-network endpoint: `http://minio:9000`
- path-style access: enabled
- bucket versioning: enabled by `minio-init`

`.env.local` は git 管理しない local runtime file とする。Compose の暗黙 `.env` 読み込みには依存しない。direnv を使う場合は `.envrc` が `.env.local` を読み込むが、手順と smoke command は常に `--env-file .env.local` を明示する。

P0R-001 の MinIO smoke は次を確認する。

- `minio-init` が `openpolitics-raw` bucket を作る。
- writer が `raw/{jurisdiction_id}/{source_family}/{yyyy}/{mm}/{sha256}.{ext}` に 1 artifact を put する。
- object metadata に `content_hash`、`hash_algorithm=sha256`、`jurisdiction_id`、`source_family` が入る。
- RDB payload の `object_bucket`、`object_key`、`raw_artifact_path` が object storage 側と一致する。
- Docker / MinIO が使えない環境では通常 test を失敗させず、manual integration skipped として扱う。

### `EvidenceItem`

追加する field:

- `location_metadata`: source family 固有の locator 補助情報。DB は `jsonb`、Python は `dict[str, object]` 相当。
- `parse_warnings`: warning code の tuple / array。DB は `text[]`。
- `extraction_artifact_path`: PDF text extraction、OCR output、table extraction など、RawArtifact から生成した中間 artifact がある場合の path。HTML 直抽出では `None`。

既存 field は維持する。

- `raw_artifact_path` は必須。
- `source_span_start` / `source_span_end` は HTML では raw HTML bytes offset、PDF / table では extraction artifact の text offset とする。
- page / bbox / table cell に戻れない PDF / OCR 抽出は EvidenceClaim に昇格しない。

### Warning catalog

初期 catalog:

- `pdf_text_layer_missing`
- `ocr_required`
- `ocr_low_confidence`
- `table_structure_inferred`
- `merged_cell_or_header_inferred`
- `multi_page_table`
- `amount_unit_ambiguous`
- `name_or_org_ocr_ambiguous`
- `entity_resolution_required`
- `search_ui_snapshot`
- `meaning_not_interpreted`
- `source_layout_unverified`

warning は「抽出できたが弱い」ことを保存するものであり、claim の正当化には使わない。low confidence または locator 不足の場合は EvidenceItem までで止める。

### Claim type catalog

Phase 0 の初期 claim type は、直接観測できる最小単位に限定する。

| source family | claim type 例 | guard |
| --- | --- | --- |
| `tokyo_metro_grants` | `subsidy_program_candidate_observed`, `grant_program_page_title_observed` | 個別交付先・金額・効果は生成しない |
| `tokyo_assembly_records_bills` | `assembly_member_name_observed`, `bill_decision_observed`, `petition_status_observed`, `speech_text_observed` | 個人別賛否を推定しない |
| `tokyo_elections` / `tokyo_political_funds` | `election_result_observed`, `political_group_registry_observed`, `political_fund_report_metadata_observed` | 人物・後援会・政党支部を自動 merge しない |
| `tokyo_budget_settlement` | `budget_document_metadata_observed`, `budget_table_cell_observed` | `BudgetLine` 確定はしない |
| `tokyo_procurement` | `procurement_search_row_observed` | `ContractAward` と会社名寄せはしない |
| `tokyo_audit_reports` | `audit_report_finding_text_observed`, `audit_measure_status_observed` | 公式監査指摘と app-calculated signal candidate を混ぜない |

### Audit / signal separation

Roadmap の「監査指摘とアプリ計算 signal を分けて保存できる」は、Phase 0 で次の contract として扱う。

| contract | origin | 主な field | Phase 0 guard |
| --- | --- | --- | --- |
| `AuditFindingCandidate` | 公式監査 source から直接観測した指摘 / 措置状況 | `audit_type`, `source_document_id`, `evidence_item_id`, `official_text`, `target_body_text`, `fiscal_year`, `measure_status`, `review_state` | 公式文言を保持し、アプリ側の評価語を混ぜない |
| `SpendingReviewSignalCandidate` | アプリが複数 evidence から計算した内部候補 | `signal_type`, `target_ref`, `supporting_evidence_item_ids`, `counter_evidence_item_ids`, `limitations`, `computed_at`, `method_version`, `review_state` | public UI に出さず、`AuditFindingCandidate` と同じ table / claim type に入れない |

Phase 0 では `SpendingReviewSignalCandidate` を public 表示・score には使わない。目的は、監査 report の公式指摘と、アプリが後段で計算する検証 signal が storage 上も contract 上も混ざらないことを test することである。

### Ingest manifest

`DiscoveryRecord` / `FetchManifestRecord` に source family 共通で追加する候補:

- `retrieval_method`
- `source_period`
- `discovery_url`
- `normalization_target`
- `evidence_granularity`
- `manual_review_required`

`search_ui_snapshot` の場合は `location_metadata` または manifest metadata に次を保持する。

- search form URL
- query parameters / fixed search conditions
- target period
- page number
- sort order
- snapshot timestamp
- result row locator

## Source family 実装方針

### 補助金・助成金

目的:

- `tokyo_metro_grants` を Phase 0 sample baseline に引き上げる。
- 教育・子育ての `SubsidyProgramCandidate` を 10 件保持する。

実装方針:

- fixture HTML を 10 candidate 以上に拡張する。
- title、h1、所管局、申請期間、対象者など、locator が安定する field だけを candidate claim にする。
- 個別交付先、金額、成果、PublicMoneyFlow は生成しない。

### 都議会 static HTML

目的:

- PublicActor / Committee / Bill / Petition の anchor になる EvidenceItem を作る。

実装方針:

- membership、factional、committees、bill、petition の fixture を分ける。
- `Person` や `Bill` entity を確定する前に、observed claim と review guard を作る。
- 議決結果は議案単位まで。個人 VotePosition は source にない限り作らない。

### 会議録 search snapshot

目的:

- speech 単位 EvidenceItem を作る前に、検索条件と snapshot 再現性を固定する。

実装方針:

- browser automation は通常 test に入れず、保存済み snapshot fixture を使う。
- meeting、speaker、speech block locator に戻れる fixture だけを parser evaluator に使う。
- 発言の意味分類、政策 stance 判定は行わない。

### 選挙・政治団体

目的:

- Candidate / PoliticalGroup の anchor source を作り、政治資金 PDF と分離する。

実装方針:

- 選挙結果、選挙公報 metadata、政治団体名簿を先に扱う。
- 政治資金収支報告書 PDF は metadata と text-layer/OCR 判定から始める。
- 政治家本人、後援会、政党支部、資金管理団体を自動 merge しない。

### 政治資金 PDF

目的:

- PDF/OCR risk を Phase 1 前に見える化する。

実装方針:

- PDF sample ごとに text layer の有無、table locator、warning を記録する。
- 金額、氏名、団体名は confidence と warning 必須。
- `FundingContact` は生成せず、candidate claim と review required に留める。

### 予算・契約

目的:

- PublicMoneyFlow の前段として、予算 document と電子調達 search snapshot を保持する。

実装方針:

- 財務局 index / PDF metadata と電子調達 search snapshot を分ける。
- amount unit、税込・税抜、vendor 名寄せ、契約案との突合は guard で止める。
- `ContractAward` / `BudgetLine` は Phase 0 では candidate まで。

### 監査

目的:

- 公式監査指摘をアプリ計算 signal と分けて保持する。

実装方針:

- 監査 report index、財政援助団体等監査、包括外部監査、措置状況を source_type で分ける。
- 指摘本文と措置状況は原文 span / table locator に戻れる場合だけ candidate claim にする。
- 10 sample artifact と `AuditFindingCandidate` 5 件以上は作り、app-calculated signal candidate とは別 contract に保存する。public 表示用 `SpendingReviewSignal` と score は作らない。

## 受け入れ条件

- `OPL-PHASE0-REMAINDER-20260707` の local issue ledger が Spec Gate 承認後に作成され、blocker graph に cycle がない。
- Roadmap 対象 source 7 系統すべてが source registry と coverage report に現れ、各系統の status が `complete` / `blocked` / `deferred_by_gate` のいずれかで説明される。
- 各 source family の RawArtifact は S3 互換 object storage contract で保存でき、`object_bucket=openpolitics-raw`、`object_key`、`raw_artifact_path`、`raw_artifact_id` を RDB payload と照合できる。
- 各 source family の sample record は `canonical_url`、`fetched_at` / `retrieved_at`、`content_hash`、`media_type`、`byte_size`、`connector_version`、`terms_note` を保持する。
- 5 source family 以上で、fixture-only 実行から各 10 件以上の RawArtifact / SourceDocumentCandidate sample を作れる。
- 5 source family 以上で、各 10 件以上の EvidenceItem を作れる。
- Roadmap で明示された助成・補助金と監査 source は、5 source family の達成数に含める。どちらかが未達の場合は Phase 0 を閉じない。
- `EvidenceItem` から `raw_artifact_path` と locator metadata に戻れる。
- Evidence Item schema は Python contract、DB migration、JSON Schema または同等の serialized contract、tests に反映される。
- `parse_warnings` が Python contract、DB migration、serialized contract、tests に反映される。
- claim type / predicate は catalog で管理され、DB check 直書きの単一 claim type 制限を外す。
- `SubsidyProgramCandidate` 10 件以上、`AuditFindingCandidate` 5 件以上を evidence trace 付きで作れる。
- `AuditFindingCandidate` と `SpendingReviewSignalCandidate` は別 contract / table / claim type で保存される。
- public 表示用 `SpendingReviewSignal`、score、`PublicMoneyFlow`、`FundingContact`、`ContractAward`、`BudgetLine`、`VotePosition` の非対象 guard が test される。
- 通常 test は外部 network、browser automation、PDF download、OCR 実行を行わない。
- local MinIO smoke は通常 test と分け、利用可能な場合に 1 artifact の put / metadata / DB payload 照合を実行できる。
- coverage report が source family 別に sample artifact 件数、EvidenceItem 件数、warning 件数、review required 件数を出せる。

## 検証方針

通常検証:

```bash
cd services
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

repository root:

```bash
git diff --check
```

local MinIO smoke は P0R-001 で command を固定する。想定形:

```bash
docker compose --env-file .env.local up -d minio minio-init
docker compose --env-file .env.local ps minio minio-init
cd services
uv run python -m ingest storage-smoke \
  --bucket openpolitics-raw \
  --endpoint http://localhost:9000
```

この command 名は draft であり、Issue Gate で実装単位に合わせて確定する。通常 test / CI には含めない。

Phase 0 coverage report は `P0R-012` で command を固定する。想定形:

```bash
cd services
uv run python -m ingest phase0 fixture-report --fixtures tests/fixtures --output-dir ingest/out
```

この command 名は draft であり、Issue Gate で実装単位に合わせて確定する。

## リモート書き込み方針

- `local_only`。
- GitHub issue mirror、push、PR 作成はこの Spec Gate では承認しない。
- PR delivery が必要になった場合は、Issue Gate と Execution Plan Gate の後に Remote Gate を別途開く。
- live source 取得、外部 network、PDF download、browser automation、OCR 実行は、この spec の通常実装 scope では承認しない。
- production S3 / managed object storage / secret 操作は承認しない。local MinIO smoke は local development verification として別扱いにする。

## 人間レビューゲート

- Spec Gate: この文書の scope、Epic ID、非目標、Issue 分解方針、受け入れ条件、リモート方針を承認する。
- Issue Gate: `P0R-001` から `P0R-012` の local issue ledger、依存順、各 issue の acceptance criteria を承認する。
- Execution Plan Gate: schema version 3 execution packet、write scope、worker worktree、local-only policy、fallback policy を preflight する。
- Implementation Review Gate: `issue-implementation-loop` 側で issue ごとに review する。
- Remote Gate: external write が必要になった時だけ開く。

## 停止条件

- `Epic ID` または Phase 0 の完了条件が変更される。
- source family を増やすことで accepted scope が Phase 1 / UI / scoring へ広がる。
- external network、browser automation、PDF download、OCR 実行が必要になる。
- warning / locator contract を満たせないまま EvidenceClaim を生成する必要が出る。
- object storage key、RDB `raw_artifacts` row、manifest `raw_artifact_path` の contract が source family ごとに分岐する。
- `canonical_url`、`fetched_at`、`content_hash` のいずれかを記録できない source を Phase 0 completion に含める必要が出る。
- public 表示用 `SpendingReviewSignal`、score、`PublicMoneyFlow` を Phase 0 内で生成しないと受け入れ条件を満たせない。
- dirty changes が planned write scope と重なる。
- blocker graph に cycle が出る。

## Spec Gate 承認内容

2026-07-07 に承認済み。

- `Epic ID` を `OPL-PHASE0-REMAINDER-20260707` としてよいか。
- Phase 0 残りを、common contract first、fixture-only verification、source family 横断 sample coverage として扱ってよいか。
- S3 互換 object storage + RDB `raw_artifacts` payload を Phase 0 の RawArtifact 保存 gate として明示し、P0R-001 に local MinIO smoke 設計を含めてよいか。
- `P0R-001` から `P0R-012` の分解方針で Issue Gate draft を作ってよいか。
- `SubsidyProgram` / `AuditFinding` は candidate-first とし、監査指摘と app-calculated signal candidate の保存分離を Phase 0 scope に含めてよいか。
- リモート方針を `local_only` とし、GitHub mirror / PR / live acquisition を別 gate に残してよいか。

## 関連ページ

- [Roadmap](../../roadmap.md) — Phase 0 gate。
- [Local Infrastructure](../../local-infrastructure.md) — local MinIO / PostgreSQL / datastore 構成。
- [ADR 0001: Evidence-first hybrid store](../../adr/0001-evidence-first-hybrid-store.md) — PostgreSQL 正本、object storage 原本保存の判断。
- [Data Sources](../../data-sources.md) — source family と acquisition design。
- [Domain Model](../../domain-model.md) — EvidenceItem、EvidenceClaim、SubsidyProgram、AuditFinding、SpendingReviewSignal。
- [Spending Review](../../spending-review.md) — 補助金、監査、支出検証 signal の境界。
- [東京都補助金・助成金 ingest 初期仕様](tokyo-subsidy-ingest-spec.md) — 既存補助金 first epic。
- [東京都 PDF/OCR・表抽出 feasibility](tokyo-subsidy-pdf-ocr-feasibility.md) — warning / confidence 方針。
- [東京都 source connector 設計](tokyo-source-connector-design.md) — 後続 source family registry。

## 出典

- [Roadmap](../../roadmap.md)
- [Local Infrastructure](../../local-infrastructure.md)
- [ADR 0001: Evidence-first hybrid store](../../adr/0001-evidence-first-hybrid-store.md)
- [Data Sources](../../data-sources.md)
- [Domain Model](../../domain-model.md)
- [Spending Review](../../spending-review.md)
- [Tokyo Source Connector Design](tokyo-source-connector-design.md)
