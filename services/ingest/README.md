# services/ingest

外部 source から raw artifact と fetch metadata を取得する service を置く。

責務:

- `discover`: candidate URL を集める。
- `fetch`: HTML、PDF、CSV、JSON、XML を RawArtifact として保存する。
- `candidate`: source 固有の軽い metadata 抽出を行い、Source Document Candidate を作る。
- content hash、HTTP metadata、connector version、rate limit policy を記録する。
- `jurisdiction_id`、`source_system`、`source_family`、`connector_id` を分離し、国・自治体ごとの connector 設定を混ぜない。

EvidenceItem、EvidenceClaim、正規化済み fact、人物・団体の高リスクな名寄せ、score 計算はここでは行わない。これらは `services/normalize` 以降の責務とする。

初回 ingest 仕様は [東京都補助金・助成金 ingest 初期仕様](../../knowledge/wiki/syntheses/tokyo-subsidy-ingest-spec.md) を参照する。
