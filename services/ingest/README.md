# services/ingest

外部 source から raw artifact と fetch metadata を取得する service を置く。

責務:

- `discover`: candidate URL を集める。
- `fetch`: HTML、PDF、CSV、JSON、XML を RawArtifact として保存する。
- `parse`: source 固有の軽い抽出を行う。
- content hash、HTTP metadata、connector version、rate limit policy を記録する。

人物・団体の高リスクな名寄せや score 計算はここでは行わない。
