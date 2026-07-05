# services/worker

定期実行、queue 消費、再取得、parser 再実行、projection rebuild を orchestration する worker を置く。

責務:

- service 固有 logic を直接抱えず、各 service の public CLI/application API を呼ぶ。
- job の失敗、再試行、差分件数、最終成功日時を記録する。
- 手動 CLI が安定した job から順に worker 化する。
