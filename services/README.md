# services

OpenPolitics Lens の backend service と batch service を置く。

初期境界:

- `api/`: Web/API client 向け API。
- `ingest/`: 外部 source 取得と RawArtifact 保存。
- `normalize/`: RawArtifact から EvidenceItem と正規化 fact を生成。
- `graph-builder/`: RDB から GraphDB projection を生成。
- `worker/`: schedule / queue / retry orchestration。

各 service は、実装開始時に独立した package metadata と test layout を持つ。
