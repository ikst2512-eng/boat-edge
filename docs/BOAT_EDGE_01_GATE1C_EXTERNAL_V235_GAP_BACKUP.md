# BOAT EDGE ①-1C — GitHub schedule欠落時の外部補助起動（準備のみ）

## 課題と制約

2026-10-16 JSTのGitHub Actions実行作成記録には、09:00–09:30にリポジトリ全体で0件、11:00–12:16にも0件の空白がある（記録照会時点）。GitHubの\`schedule\` はbest-effortであり、YAMLの5分cronは5分稼働のSLAではない。初回予想保存率99%・①-1Dは未証明。

既存の\`.github/workflows/V235.yml\` は \`workflow_dispatch\` を受け付け、同じV230の公式6艇・120オッズとV229の締切2–10分・原本SHA制約を使う。新たな本番writerやcronは増やさない。

## このPRが行うこと

- \`scripts/boat_edge_01_v235_external_gap_watchdog.py\` を**無効状態のまま**用意する。実行する外部環境・APIトークン・定期ジョブの設定は **未実施**。
- ユーザーが独立ホスト（GitHub Actionsのschedule以外）を用意した場合のみ、毎2分程度このスクリプトを呼ぶ。GitHubの当日 \`data/today.json\` に4–19分後締切のレースがあり、V235実行中がなく、直近の**実際に実行された**V235から420秒以上空いた時に限り、既存のV235を \`workflow_dispatch\` する。
- V235が \`skipped\` の場合は「処理済み」と認めない。取得履歴・ジョブ状態・開催日・workflowのidentity/activeが不明な場合は**一切起動しない**。
- GitHub上の既存スナップショット、モデル、結果、正式Fresh、スケジュール、ワークフローは変更しない。**外部サーバ・secretの用意までは稼働改善ゼロ**。

## 導入前に必要な利用者側の準備（現時点で未実施）

1. 外部の信頼できる実行環境を用意する。GitHub Actions自体でこのwatchdogをcron実行すると、同じ配送欠落の影響を受けるので不可。環境の時刻はNTPで同期し、Asia/Tokyo 08:00–22:00の2分毎程度に単独スケジューラで起動する。料金・API上限・稼働監視は事前確認。
2. GitHubのfine-grained PATまたはGitHub Appトークンを、**\`ikst2512-eng/boat-edge\` のみに限定**して発行する。少なくとも Actions: write、Contents: read が必要。外部ホストの**secret環境変数** \`BOAT_EDGE_GITHUB_ACTIONS_TOKEN\` で渡し、コマンド引数・リポジトリ・ログには書かない。
3. \`python3 -m unittest tests/test_boat_edge_01_v235_external_gap_watchdog.py -v\` と \`python3 scripts/boat_edge_01_v235_external_gap_watchdog.py\`（書込みなしdry-run）で確認。dry-runに \`DRY_RUN_WOULD_DISPATCH_V235\` が出ても、**実際には起動していない**。
4. 設定と実行契約をレビュー・承認した後にだけ、外部ホスト上で \`python3 scripts/boat_edge_01_v235_external_gap_watchdog.py --live\` をスケジュール化する。必ずV235の実際のrun開始、最初のGit SHA、締切前保存件数、API失敗を観測する。
5. 失敗・予期せぬ連打・大幅なコスト増加が起きたら、外部スケジュールとsecretを停止する。既存GitHubのworkflowや正式Freshは触らない。

GitHub公式仕様:
- 予定実行の遅延/欠落: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- workflow_dispatch APIと必要権限: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event

**受け入れゲート:** 外部設定を実施し、複数日の全対象/公式適格/除外/原因不明/締切2–10分前初回Git保存を独立監査して各日99%以上を3開催日連続で証明するまでは、①-1C/①-1DをPASSとしない。
