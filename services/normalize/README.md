# services/normalize

RawArtifact / SourceDocument から EvidenceItem と正規化 fact を作る service を置く。

責務:

- 日付、金額、議案番号、会議名、会期、発言番号を正規化する。
- PDF/OCR 由来の warning と confidence を保存する。
- entity-resolution の候補を作り、高リスク merge は review に回す。
