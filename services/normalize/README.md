# services/normalize

RawArtifact / SourceDocument から EvidenceItem と正規化 fact を作る service を置く。

現在の初期実装は、`ingest.FetchManifestRecord`、caller が解決した `raw_artifact_id`、raw HTML bytes から次の最小 contract を生成する。

- `SourceDocument`
- HTML `<title>` の `EvidenceItem`
- `grant_program_page_title_observed` の `EvidenceClaim`
- `NormalizeResult`

責務:

- Source Document Candidate を検証し、SourceDocument と EvidenceItem を生成する。
- EvidenceItem の `source_span_start` / `source_span_end` は raw HTML bytes の offset として扱う。
- 日付、金額、議案番号、会議名、会期、発言番号を正規化する。
- PDF/OCR 由来の warning と confidence を保存する。
- entity-resolution の候補を作り、高リスク merge は review に回す。

初期実装では、金額、交付先、監査指摘、entity resolution、PDF/OCR、live PostgreSQL/MinIO、Web UI/API は扱わない。
