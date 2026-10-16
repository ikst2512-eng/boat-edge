# BOAT EDGE ①-1C — GitHub schedule欠落時の外部補助起動（準備のみ）

## 課題と制約

2026-10-16 JSTのGitHub Actions実行作成記録には、09:00–09:30にリポジトリ全体で0件、11:00–12:16にも0件の空白がある（記録照会時点）。GitHubの`schedule` はbest-effortであり、YAMLの5分cronは5分稼働のSLAではない。初回予想保存率99%・①-1Dは未証明。

既存の`.github/workflows/V235.yml` は `workflow_dispatch` を受け付け、同じV230の公式6艇・120オッズとV229の締切2–10分・原本SHA制約を使う。新たな本番writerやcronは増やさない。

## このPRが行うこと

- `scripts/boat_edge_01_v235_external_gap_watchdog.py` を**無効状態のまま**用意する。実行する外部環境・APIトークン・定期ジョブの設定は **未実施**。
- ユーザーが独立ホスト（GitHub Actionsのschedule以外）を用意した場合のみ、毎2分程度このスクリプトを呼ぶ。GitHubの当日 `data/today.json` に4–19分後締切のレースがあり、V235実行中がなく、直近の**実際に実行された**V235から420秒以上空いた時に限り、既存のV235を `workflow_dispatch` する。
- V235が `skipped` の場合は「処理済み」と認めない。取得履歴・ジョブ状態・開催日・workflowのidentity/activeが不明な場合は**一切起動しない**。
- GitHub APIが100件の履歴を返しても、**mainブランチのV235履歴が0件なら安全停止**する。別ブランチの実行を見てmainが待機中だと推測しない（PR #446で追加した専用回帰）。
- GitHub上の既存スナップショット、モデル、結果、正式Fresh、スケジュール、ワークフローは変更しない。**外部サーバ・secretの用意までは稼働改善ゼロ**。

## 導入前に必要な利用者側の準備（現時点で未実施）

1. 外部の信頼できる実行環境を用意する。GitHub Actions自体でこのwatchdogをcron実行すると、同じ配送欠落の影響を受けるので不可。環境の時刻はNTPで同期し、Asia/Tokyo 08:00–22:00の2分毎程度に単独スケジューラで起動する。料金・API上限・稼働監視は事前確認。
2. GitHubのfine-grained PATまたはGitHub Appトークンを、**`ikst2512-eng/boat-edge` のみに限定**して発行する。少なくとも Actions: write、Contents: read が必要。外部ホストの**secret環境変数** `BOAT_EDGE_GITHUB_ACTIONS_TOKEN` で渡し、コマンド引数・リポジトリ・ログには書かない。
3. `python3 -m unittest tests/test_boat_edge_01_v235_external_gap_watchdog.py -v` と `python3 scripts/boat_edge_01_v235_external_gap_watchdog.py`（書込みなしdry-run）で確認。dry-runに `DRY_RUN_WOULD_DISPATCH_V235` が出ても、**実際には起動していない**。
4. 設定と実行契約をレビュー・承認した後にだけ、外部ホスト上で `python3 scripts/boat_edge_01_v235_external_gap_watchdog.py --live` をスケジュール化する。必ずV235の実際のrun開始、最初のGit SHA、締切前保存件数、API失敗を観測する。
5. 失敗・予期せぬ連打・大幅なコスト増加が起きたら、外部スケジュールとsecretを停止する。既存GitHubのworkflowや正式Freshは触らない。

GitHub公式仕様:
- 予定実行の遅延/欠落: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- workflow_dispatch APIと必要権限: https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event

**受け入れゲート:** 外部設定を実施し、複数日の全対象/公式適格/除外/原因不明/締切2–10分前初回Git保存を独立監査して各日99%以上を3開催日連続で証明するまでは、①-1C/①-1DをPASSとしない。

## 設置可能な独立Cron構成（Render Blueprint、2026-10-16時点は未デプロイ）

リポジトリ直下の `render.yaml` が**独立ホストの設定原本**。自動でRenderへ接続する処理やクレジットカード処理は一切入っていない。Renderへサービスを作成するまでは**費用も外部定期実行も発生しない**。

- 公式Blueprint仕様: https://render.com/docs/blueprint-spec
- Render CronのUTC・単一run保証・課金: https://render.com/docs/cronjobs （最小月額 **1米ドル/サービス**、ほか稼働時間による従量料金）
- 設定: Singapore地域、Python、`0.5c-512mb`、`*/2 23,0-13 * * *`（日本時間08:00–22:59、UTCに夏時間なし）、`autoDeployTrigger: off`。**GitHub Actionsのcronは追加しない**。
- build時はwatchdogの安全なfixtureテスト、run時は同一Python watchdogの `--live` を呼び出す。ただし `BOAT_EDGE_EXTERNAL_V235_ENABLED` の初期値は**文字列 `false`**。発行済みトークンがあっても `true` への**所有者の明示操作まではGitHubにPOSTしない**。
- 初回Blueprint同期にはRenderアカウント・GitHub接続・課金への所有者同意が必要。そこで `BOAT_EDGE_GITHUB_ACTIONS_TOKEN` をSecretとして登録する（リポジトリへコミット禁止）。Renderの画面で `BOAT_EDGE_EXTERNAL_V235_ENABLED=false` の実行ログ `EXTERNAL_V235_NOT_ENABLED` とPOST 0件を確認する。
- 料金、予定Cron実行、単一Run、API権限、監視・アラートを所有者が承認した**後**にRenderのサービス環境変数 `BOAT_EDGE_EXTERNAL_V235_ENABLED=true` へ切替。以降、標準出力に `EXISTING_V235_DISPATCH_SUBMITTED` の証拠があり、GitHubで該当V235 run作成を独立に観測できた時だけ「補助起動成功」。`autoDeployTrigger: off` なので、本番に修正を再反映する場合もレビュー後手動デプロイする。
- 停止は `BOAT_EDGE_EXTERNAL_V235_ENABLED=false` に戻す／Cronを停止し、必要ならトークン失効。安全停止しても既存V230/V229の初回Git保存・正式Freshロックには変更なし。Blueprintの再同期は環境変数を `false` に戻し得るので、再同期後は状態を確認。
- **Renderを接続・課金・デプロイ・Secret保存したという意味ではない。** クラウド側の初回稼働・予想保存改善・2分配送保証は別途実測が必要。

## 2026-10-16 戸田10Rの実Git/Actions欠測再現（設置準備の受入れ証拠）

- 戸田10Rの締切は15:18 JSTで、既存V229が初回予想を凍結できる時間窓は15:08〜15:16（それぞれ締切10〜2分前）。
- [15:05:52 JSTのPRE_RESULT Git原本](https://github.com/ikst2512-eng/boat-edge/commit/eb815975dcd7eaecc04ff89940007ecc41dcf48c)には6艇の公式出走表・展示原本、公式DOM照合済み3連単120件、欠場確認 `blocked=false` が同じレースのSHAとともに保存されていた。これは当時の入力候補を示すが、モデル全ガードや適格分母の独立証明ではない。
- 実GitHub ActionsのV235起動は15:03:41の次が15:16:29、V229は15:06:06の次が15:16:52。**保存可能な15:08〜15:16にどちらも起動しておらず**、このレースの予想snapshotは生成されなかった。CI PASSでは救済不可。
- 既存外部補助起動の `decision()` を合成時刻で再生すると、15:08には直近実行から420秒未満で `V235_RECENT_ACTUAL_RUN`、15:12には残り6分・420秒超・main履歴正常・非activeの場合に `MISSED_V235_RUNTIME_WITH_IMMINENT_RACE` で既存V235起動候補、15:15には残り4分未満で `NO_SAME_DAY_PREWARM_RACE` になる。専用回帰 `test_real_toda10_missed_window_replay_no_early_or_late_dispatch` がこの境界とactive多重起動拒否を固定する。
- **この再生は外部Cronが稼働したという主張ではない。** `render.yaml` は依然OFF。料金同意・秘密鍵設定・独立実行ログがない限りGitHubへの追加dispatchは0。接続後も実V235 run、初回Git SHA、締切2〜10分証拠を別途照合する。
- Gate 1Cの全開催分母は未証明。締切済みV215未観測Rを「公式適格保存失敗」に振り替えず、3開催日99%の承認条件を維持する。
