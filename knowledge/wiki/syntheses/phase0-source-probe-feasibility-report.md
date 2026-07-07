---
kind: synthesis
created: 2026-07-07
updated: 2026-07-07
epic_id: OPL-PHASE0-REMAINDER-20260707
status: phase0-complete
---

# Phase 0 source probe feasibility report

## 結論

Phase 0 判定: `complete`

- 達成 source family: 7/7
- 最低 gate: 5 source family 以上で RawArtifact / SourceDocumentCandidate / EvidenceItem が各 10 件以上
- 必須 source family: tokyo_audit_reports, tokyo_metro_grants は達成済み
- 通常検証では external network / browser automation / PDF download / OCR を実行しない

## Roadmap 対象 source

- 東京都議会 会議録・速記録
- 東京都議会 提出議案と議決結果
- 東京都選挙管理委員会 選挙公報・選挙結果
- 東京都選挙管理委員会 政治資金収支報告書
- 東京都財務局・電子調達 契約/予算
- 都庁総合ホームページ 助成・補助金
- 東京都監査事務局 財政援助団体等監査・包括外部監査

## Source family coverage

| source_family | status | RawArtifact | SourceDocumentCandidate | EvidenceItem | warnings | review_required | blocked_reason |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| tokyo_assembly_records_bills | complete | 20 | 20 | 20 | 20 | 0 |  |
| tokyo_elections | complete | 10 | 10 | 10 | 0 | 0 |  |
| tokyo_political_funds | complete | 10 | 10 | 10 | 36 | 6 |  |
| tokyo_budget_settlement | complete | 10 | 10 | 10 | 20 | 0 |  |
| tokyo_procurement | complete | 10 | 10 | 10 | 30 | 0 |  |
| tokyo_metro_grants | complete | 10 | 10 | 20 | 0 | 0 |  |
| tokyo_audit_reports | complete | 10 | 10 | 40 | 40 | 0 |  |

## Non-goal guard

| source_family | non-goal guard |
| --- | --- |
| tokyo_assembly_records_bills | VotePosition は source にない限り生成しない / 発言の政策 stance や意味分類は行わない |
| tokyo_elections | 人物、政治団体、政党支部、後援会を自動 merge しない / source から直接観測できない Candidate / ElectionResult は確定しない |
| tokyo_political_funds | FundingContact は生成しない / PDF download と OCR 実行は通常検証で行わない |
| tokyo_budget_settlement | BudgetLine は確定 entity として生成しない / PublicMoneyFlow と SpendingReviewSignal は生成しない |
| tokyo_procurement | ContractAward は確定 entity として生成しない / vendor 名寄せと契約案との突合は行わない |
| tokyo_metro_grants | PublicMoneyFlow は生成しない / 個別交付先、金額、成果は生成しない |
| tokyo_audit_reports | AuditFindingCandidate は公式文言を保持し、アプリ側評価語を混ぜない / public SpendingReviewSignal、score、ranking は生成しない |

## 関連ページ

- [Phase 0 残実装設計](phase0-remainder-implementation-design.md) — Phase 0 gate と source family coverage contract の設計。
- [Phase 0 残実装ローカル issue ledger](phase0-remainder-issues.md) — `P0R-001` から `P0R-012` の実装状態と review gate。
- [Roadmap](../../roadmap.md) — Phase 0 gate の上位ロードマップ。
- [Local Infrastructure](../../local-infrastructure.md) — RawArtifact 保存と local MinIO 起動契約。

## 出典

- [Phase 0 残実装設計](phase0-remainder-implementation-design.md)
- [Phase 0 残実装ローカル issue ledger](phase0-remainder-issues.md)
