# BOAT EDGE ゲート1A — 2026-10-15 未保存24R・締切前証拠照合（2026-10-16）

> **状態：1A進行中。** 当日観測140R・スナップショット存在116R・未保存24R。2Rでは公式ソースが締切前に揃っていたのに2–10分の凍結実行機会が欠けたことを確認。6Rで前段の公式展示待ちを確認。残る16Rは保存されたV230診断からは取得/保存の真因が未確定。**全24Rの根本原因を確定したという報告ではない。** 保存率改善・現行モデル改善・正式Fresh採点を主張しない。

## 調査方法と境界

- `BOAT_EDGE_EXECUTION_ORDER.md` ゲート1Aだけの調査。結果・払戻・正式Fresh結果APIは参照しない。後付け予想・保存ファイルの再作成なし。
- 2026-10-15のV215観測履歴 `data/site_paper_sim/readiness_history_v215/20261015.json`（140個のレースID）と、現行mainの`data/site_prediction_snapshots/<race>.json`のパス存在を照合。パスがある116Rは**初回Git原本の整合証明を別途必要**とする。
- GitHub上の`data/site_autopilot/v230_fast_current.json` 2026-10-14 23:00–10-15 14:59 UTCの **46件の変更コミット**の保存状態を調べ、各Rに紐づくV230`targets/outcomes`を照合。保存済みファイルから確認できない実行や対象選択が無かったとは推論しない。
- 公式出走表・直前・オッズ・欠場について**取得後かつ締切前の歴史的Gitコミット**を参照。Source `published_wait` は観測時点の不完全性であり、締切時まで未公開だった証明ではない。
- V215の `source_gaps_seen` は**一度でも観測された不足の集合**。各Rの真因／最終凍結適格性と同一視しない。

## 実測ファネル

| 指標 | 件数 |
|---|---:|
| 2026-10-15 V215観測 | 140 |
| 保存ファイル存在（初回Git原本未認証を含む） | 116 |
| 保存ファイルなし | 24 |
| 未保存のうち不足フラグ履歴あり | 23 |
| 未保存のうち不足フラグ履歴なし | 1（戸田7R） |
| 最終V215観測が締切2–10分前 | 16 |
| 最終V215観測がその外 | 8 |

未保存24Rに見られた**重複する**不足フラグ：`beforeinfo_not_ok=23`、`race_card_stale=14`、`scratch_missing_or_blocked=14`、`scratch_stale=10`、`pre_result_odds_stale=12`、`pre_result_odds_120_incomplete=1`、`official_dom_proof_missing=1`。足して24にはならない。

## ① 具体的な実行窓抜けの証拠：戸田7R・8R

- **20261015-02-07**：13:31 JST時点、6艇・公式beforeinfo六艇展示/展示ST・公式3連単オッズ120通り（DOM確認）・欠場未検知（blocked=false）。参照： [race](https://github.com/ikst2512-eng/boat-edge/blob/15d432139934acdac8453b8d8d8d2e105a36e2e8/data/races/20261015-02-07.json) / [odds](https://github.com/ikst2512-eng/boat-edge/blob/15d432139934acdac8453b8d8d8d2e105a36e2e8/data/site_odds/20261015-02-07.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/15d432139934acdac8453b8d8d8d2e105a36e2e8/data/site_scratches_v182/20261015-02-07.json)。
- **20261015-02-08**：14:03 JST時点、6艇・公式beforeinfo六艇展示/展示ST・公式3連単オッズ120通り（DOM確認）・欠場未検知（blocked=false）。参照： [race](https://github.com/ikst2512-eng/boat-edge/blob/2ad410ffb5ce57be3a9c35292be08b44285692bf/data/races/20261015-02-08.json) / [odds](https://github.com/ikst2512-eng/boat-edge/blob/2ad410ffb5ce57be3a9c35292be08b44285692bf/data/site_odds/20261015-02-08.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/2ad410ffb5ce57be3a9c35292be08b44285692bf/data/site_scratches_v182/20261015-02-08.json)。

- **戸田7R：締切13:44 JST、凍結対象13:34–13:42 JST（04:34–04:42 UTC）。** [Actions created-time区間](https://github.com/ikst2512-eng/boat-edge/actions)の20 run全件を照合しV229/V235 run作成**0件**。直前V229 [38682093193](https://github.com/ikst2512-eng/boat-edge/actions/runs/38682093193)のfirst-freezeは04:33:57–04:33:58 UTC（窓より前、`NO_NEW_ELIGIBLE_SNAPSHOT`）、先行V235 [38681773527](https://github.com/ikst2512-eng/boat-edge/actions/runs/38681773527)の本体は04:30:35–04:31:07 UTC。次のV235実行は04:49台（締切後）。04:34–04:42に先行実行がまたいでいないことは取得したjob時刻で確認。**V230の13:31時点で必要ソースは揃っており、窓内に既存freezeを呼べなかったことは確認できる。** 当時の他の追加ガードまで完全に満たしたことの独立再評価は別途必要。
- **戸田8R：締切14:15 JST、凍結対象14:05–14:13 JST（05:05–05:13 UTC）。** created-time区間の17 runにV229/V235作成**0件**。先行V229 [38684573741](https://github.com/ikst2512-eng/boat-edge/actions/runs/38684573741)は05:02:11 UTC、[38684623642](https://github.com/ikst2512-eng/boat-edge/actions/runs/38684623642)は05:02:47 UTCにfirst-freeze（いずれも窓より前）。次のV235 [38685694550](https://github.com/ikst2512-eng/boat-edge/actions/runs/38685694550)は05:14:44 UTCに初回保存ステップ、締切約16秒前で2分下限より遅い。**14:03の公式ソースは整っていたが、窓内のfreeze実行機会がない。**
- GitHub定期cronの未発火・遅延自体はGitHub Actionsの仕様上発生し得る。修正候補は既存V220の事前証拠を満たす`V229`復旧経路の実行機会を増やすこと。ただし新たな重複writerや緩い締切条件は導入しない。

## ② V230がsource_blockedとした6R（観測時の直接原因は公式展示未確認）

- **20261015-04-05**：12:14 JST時点、beforeinfo.status=`published_wait`、`six_boat_complete=false`、scratch `blocked=true` / `公式直前情報の展示データを検証できない`。公式自体が最終的に未公開だったとは断定しない。 [race](https://github.com/ikst2512-eng/boat-edge/blob/ef367b3310601d0b22b6a0ec3a8151af67388c6f/data/races/20261015-04-05.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/ef367b3310601d0b22b6a0ec3a8151af67388c6f/data/site_scratches_v182/20261015-04-05.json)。
- **20261015-10-06**：10:50 JST時点、beforeinfo.status=`published_wait`、`six_boat_complete=false`、scratch `blocked=true` / `公式直前情報の展示データを検証できない`。公式自体が最終的に未公開だったとは断定しない。 [race](https://github.com/ikst2512-eng/boat-edge/blob/d74f8f8dce765b36f7508882719eebb547b0ecd6/data/races/20261015-10-06.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/d74f8f8dce765b36f7508882719eebb547b0ecd6/data/site_scratches_v182/20261015-10-06.json)。
- **20261015-13-01**：10:22 JST時点、beforeinfo.status=`published_wait`、`six_boat_complete=false`、scratch `blocked=true` / `公式直前情報の展示データを検証できない`。公式自体が最終的に未公開だったとは断定しない。 [race](https://github.com/ikst2512-eng/boat-edge/blob/c8d8ab0c15a970ae47e243bc44d7697699facc45/data/races/20261015-13-01.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/c8d8ab0c15a970ae47e243bc44d7697699facc45/data/site_scratches_v182/20261015-13-01.json)。
- **20261015-13-02**：10:50 JST時点、beforeinfo.status=`published_wait`、`six_boat_complete=false`、scratch `blocked=true` / `公式直前情報の展示データを検証できない`。公式自体が最終的に未公開だったとは断定しない。 [race](https://github.com/ikst2512-eng/boat-edge/blob/d74f8f8dce765b36f7508882719eebb547b0ecd6/data/races/20261015-13-02.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/d74f8f8dce765b36f7508882719eebb547b0ecd6/data/site_scratches_v182/20261015-13-02.json)。
- **20261015-13-06**：12:48 JST時点、beforeinfo.status=`published_wait`、`six_boat_complete=false`、scratch `blocked=true` / `公式直前情報の展示データを検証できない`。公式自体が最終的に未公開だったとは断定しない。 [race](https://github.com/ikst2512-eng/boat-edge/blob/fb25cebb0a77f22a5b2feb41c2c974f73066b16e/data/races/20261015-13-06.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/fb25cebb0a77f22a5b2feb41c2c974f73066b16e/data/site_scratches_v182/20261015-13-06.json)。
- **20261015-14-02**：08:44 JST時点、beforeinfo.status=`published_wait`、`six_boat_complete=false`、scratch `blocked=true` / `公式直前情報の展示データを検証できない`。公式自体が最終的に未公開だったとは断定しない。 [race](https://github.com/ikst2512-eng/boat-edge/blob/c08f4b800de96c3d09144410aab1932ba53dde96/data/races/20261015-14-02.json) / [scratch](https://github.com/ikst2512-eng/boat-edge/blob/c08f4b800de96c3d09144410aab1932ba53dde96/data/site_scratches_v182/20261015-14-02.json)。

この6Rでは、確認した時点で公式出走表は6艇`ok`だった一方、公式`beforeinfo`が`published_wait`かつ六艇未完了。オッズ120通りが揃った例もあるが、展示・欠場の安全ゲートを緩めてはならない。**未公開が締切まで継続したか、後続の取得機会が不足したか**は別途確認が必要。

## ③ 全24R 個別台帳

| レース | 締切 JST | V215最終観測 JST | 観測回数 | 最終観測時の不足フラグ | 現在の分類（仮説含む） |
|---|---|---|---:|---|---|
| 20261015-02-03 戸田 | 11:45 | 11:36:31 (残8.5分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | 根本原因未確定 |
| 20261015-02-05 戸田 | 12:44 | 12:41:51 (残2.1分) | 2 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | 根本原因未確定 |
| 20261015-02-07 戸田 | 13:44 | 13:32:14 (残11.8分) | 2 | なし（適格を意味しない） | 窓内freeze実行なし（有力） |
| 20261015-02-08 戸田 | 14:15 | 14:03:24 (残11.6分) | 2 | なし（適格を意味しない） | 窓内freeze実行なし（有力） |
| 20261015-04-05 平和島 | 12:23 | 12:14:52 (残8.1分) | 2 | beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale, pre_result_odds_120_incomplete, official_dom_proof_missing | 公式展示6艇待ち（時点観測） |
| 20261015-10-06 三国 | 11:08 | 10:58:14 (残9.8分) | 2 | beforeinfo_not_ok, scratch_stale | 公式展示6艇待ち（時点観測） |
| 20261015-10-07 三国 | 11:38 | 11:27:47 (残10.2分) | 2 | beforeinfo_not_ok, scratch_missing_or_blocked | 根本原因未確定 |
| 20261015-10-11 三国 | 13:50 | 13:47:43 (残2.3分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | 根本原因未確定 |
| 20261015-11-04 びわこ | 11:43 | 11:36:31 (残6.5分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | 根本原因未確定 |
| 20261015-11-06 びわこ | 12:47 | 12:41:51 (残5.1分) | 2 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | 根本原因未確定 |
| 20261015-13-01 尼崎 | 10:39 | 10:25:26 (残13.6分) | 1 | beforeinfo_not_ok, scratch_missing_or_blocked | 公式展示6艇待ち（時点観測） |
| 20261015-13-02 尼崎 | 11:06 | 10:58:14 (残7.8分) | 2 | beforeinfo_not_ok, scratch_missing_or_blocked | 公式展示6艇待ち（時点観測） |
| 20261015-13-03 尼崎 | 11:36 | 11:27:47 (残8.2分) | 2 | beforeinfo_not_ok, scratch_missing_or_blocked | 根本原因未確定 |
| 20261015-13-06 尼崎 | 13:01 | 12:48:57 (残12.0分) | 1 | beforeinfo_not_ok, scratch_missing_or_blocked | 公式展示6艇待ち（時点観測） |
| 20261015-13-11 尼崎 | 15:33 | 15:30:20 (残2.7分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | 根本原因未確定 |
| 20261015-14-02 鳴門 | 09:01 | 08:46:36 (残14.4分) | 1 | beforeinfo_not_ok, scratch_missing_or_blocked | 公式展示6艇待ち（時点観測） |
| 20261015-14-06 鳴門 | 10:52 | 10:49:59 (残2.0分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_stale | 根本原因未確定 |
| 20261015-14-08 鳴門 | 11:49 | 11:36:31 (残12.5分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | 根本原因未確定 |
| 20261015-15-05 丸亀 | 17:08 | 17:02:15 (残5.7分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | 根本原因未確定 |
| 20261015-20-10 若松 | 19:48 | 19:42:33 (残5.4分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | 根本原因未確定 |
| 20261015-21-04 芦屋 | 10:03 | 09:50:59 (残12.0分) | 2 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | 根本原因未確定 |
| 20261015-22-10 福岡 | 15:36 | 15:30:20 (残5.7分) | 1 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | 根本原因未確定 |
| 20261015-24-02 大村 | 15:47 | 15:38:41 (残8.3分) | 1 | beforeinfo_not_ok, scratch_missing_or_blocked | 根本原因未確定 |
| 20261015-24-08 大村 | 18:39 | 18:30:56 (残8.1分) | 2 | race_card_stale, beforeinfo_not_ok, scratch_stale | 根本原因未確定 |

**分類の内訳（重複なし）：2R=直前資料が揃ったが2–10分凍結ジョブ実行なし、6R=当時の公式展示不足、16R=残る原因が未確定。** 未分類16Rを「未取得だから正常」「スケジュール故障」と決めつけない。

## 次の同一ゲート内の作業

1. **優先確認対象は戸田7R/8R。** 上記の当時のrace/odds/scratchバイトSHAと、V229/V235の全依存条件がその後のfreeze開始時まで揃っていたかを区別する。source-readyを保存完了と見なさない。
2. 残る16Rは当該レースの締切2–10分におけるV229/V235/V230実行/未実行と、最後のPRE_RESULT原本の状態をrace-key単位で追加照合する。保存されたV230 statusにないことを未実行の証明にしない。
3. source_blocked6Rの公式展示がいつ公開されたか、次の取得/再試行があったかを調べる。未公表をバグとして解除しない。
4. 1Aを完了にするのは、24R全件の直接原因または証拠限界/未確定をレース別に固定し、最大の実装ボトルネックとそれを修正すべき理由を明確化してから。**このPRは原因証拠の前進であり1B修正実装ではない。**


## 追加照合（2026-10-16）— 全24Rを締切2分前のGitソース原本に揃えて分類

**この節が最新の分類。** 前半の6R「観測時」/16R「未確定」は当時の途中段階であり、最新分類と矛盾しない。各Rの`deadline - 2 minutes`以前にGit mainへ記録された最新コミットSHAから、`data/races/`・`data/site_odds/`・`data/site_scratches_v182/`の3ファイルを同一SHAで読取比較した（正式Fresh・結果は不参照）。

**直接確認できた分類（重複なし）**
- **9R：締切2分前にrace card/6艇beforeinfo/全120オッズ＋DOM検証/非blocked scratchが揃うが初回予想保存ファイルなし。** うち4Rは2–10分窓のV229/V235 run作成が0件、3Rは実行後に最終source/scratchが整ったが再実行なし、2Rは後続first-freezeが厳格な2分下限より遅かった。SHA/モデル等の全freeze追加ガードを通ることまで事後的に証明したわけではない。
- **14R：締切2分前Git原本上の`beforeinfo.status=published_wait` / 6艇展示未確認。** 正式な予想生成は拒否されるべき状態。公式サイト自体が最終時点でも未公表だったか、取得ジョブが取り逃したかは未確定であり、実予想を後付け生成しない。
- **1R：大村8R、締切2分前Git原本ではbeforeinfo等はOKだが、公式3連単オッズの取得時刻が約20.2分前で15分鮮度基準超。** 取得ジョブの遅延か公式未更新かの真因は未確定。

| レース | 締切JST | 結果を含まない当時Git原本 | 証拠上の分類 | 保存ジョブ/欠測の時点観測 |
|---|---|---|---|---|
| 20261015-02-03 戸田3R | 11:45 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/4902a21c8a47c8c47b83c25ee26970315dbc1239) | 保存機会/時刻不足 | 初回freeze 11:40:27→最終scratch 11:40:48、後続なし |
| 20261015-02-05 戸田5R | 12:44 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/c624ebd0f3983960c004a535439cb19900549cab) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-02-07 戸田7R | 13:44 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/e41210b584343c8112bfe0b1282504e83a2c0cb8) | 保存機会/時刻不足 | 窓内V229/V235開始なし（20 run確認） |
| 20261015-02-08 戸田8R | 14:15 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/66bb16bdb57b2c006074ddad4dc54502991f5764) | 保存機会/時刻不足 | 窓内V229/V235開始なし（17 run確認） |
| 20261015-04-05 平和島5R | 12:23 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/d0fe9cf6d8bb24cda8f1c1256cdf2b4a5dd316ea) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-10-06 三国6R | 11:08 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/ba4a3ea22ff6faac5cd581499ce3ffc71b4ab9b6) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-10-07 三国7R | 11:38 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/865fb02a67f0242d3781cb2c96fe17d02158fd2a) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-10-11 三国11R | 13:50 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/27bb0cd4d7a990594a5267d7eaa74cd38dc44af7) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-11-04 びわこ4R | 11:43 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/4902a21c8a47c8c47b83c25ee26970315dbc1239) | 保存機会/時刻不足 | 初回freeze 11:40:27→最終scratch 11:40:48、後続なし |
| 20261015-11-06 びわこ6R | 12:47 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/906de63f8ef2ac0440cd90cea5e89a2c14fdf0af) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-13-01 尼崎1R | 10:39 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/229ec84b0c74d64fcf7bc14c022cde7b141a9aab) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-13-02 尼崎2R | 11:06 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/ba4a3ea22ff6faac5cd581499ce3ffc71b4ab9b6) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-13-03 尼崎3R | 11:36 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/865fb02a67f0242d3781cb2c96fe17d02158fd2a) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-13-06 尼崎6R | 13:01 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/da26b76ecb692dd74e7141e257e8952fd25a28d2) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-13-11 尼崎11R | 15:33 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/b1dc3f4814f454631a39d259c07bdbb34993404e) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-14-02 鳴門2R | 09:01 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/d943689016344a87224042b810f55e768d0100bc) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-14-06 鳴門6R | 10:52 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/7ec14b99f25d03e1b8746b804daddf45f12a9860) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-14-08 鳴門8R | 11:49 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/e555906829602194046a327de8a5202f7bf2362b) | 保存機会/時刻不足 | 初回freeze 11:40:27→最終scratch 11:40:48、後続なし |
| 20261015-15-05 丸亀5R | 17:08 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/cbc592307a1bf8aecf824cf68042bdd9bd54f55c) | 保存機会/時刻不足 | 窓内V229/V235開始なし（21 run確認） |
| 20261015-20-10 若松10R | 19:48 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/09e1f41a129aa8803ef20dc67b11768c3a21cb1f) | 保存機会/時刻不足 | 窓内V229/V235開始なし（20 run確認） |
| 20261015-21-04 芦屋4R | 10:03 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/eabcd1caa81d4f51c3d5b0a2f56f17d4cff510e4) | 締切2分前の公式展示未整備 | beforeinfo=published_wait / 6艇未確認 |
| 20261015-22-10 福岡10R | 15:36 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/23bdef302ae60be1bb438b8a7420a73b7007f04c) | 保存機会/時刻不足 | V229 freeze 15:34:10、厳格な締切2分下限より後 |
| 20261015-24-02 大村2R | 15:47 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/21facfc2f8aa16f175cb3f08790c8bee3c8ec434) | 保存機会/時刻不足 | 先行V229は展示未整備、後続V229 15:45:49とV235 15:45:24は2分下限より後 |
| 20261015-24-08 大村8R | 18:39 | [Git時点SHA](https://github.com/ikst2512-eng/boat-edge/tree/19ca14adf0009b68410608fedc5f6cf577d83420) | 公式オッズ鮮度不足 | 締切2分前、オッズ約20.2分前（15分超） |

### ジョブ時刻と信頼境界

- [V229 38672188465](https://github.com/ikst2512-eng/boat-edge/actions/runs/38672188465) は**11:40:27 JST**にfirst-freezeを実行し、`V229_NO_NEW_ELIGIBLE_SNAPSHOT`。戸田3R・びわこ4R・鳴門8Rの履歴Gitに残るscratch更新は**11:40:48 JST**。従ってこのジョブが最終ソースを参照できず、後続窓内実行も観測されない（各2–10分run区間一覧と照合）。診断でも窓内対象3Rとも`beforeinfo_missing_or_stale`等が報告された。
- [V229 38693145083](https://github.com/ikst2512-eng/boat-edge/actions/runs/38693145083) は**15:34:10 JST**にfirst-freezeを実行。福岡10R締切15:36から110秒しかなく、V229の`mins >= 2`を満たさない（同runは別3Rを保存したためCIは成功）。
- [V229 38694278073](https://github.com/ikst2512-eng/boat-edge/actions/runs/38694278073) のfirst-freezeは**15:45:49 JST**、[V235 38694278129](https://github.com/ikst2512-eng/boat-edge/actions/runs/38694278129) はfirst-freeze工程開始15:45:24 JSTで、大村2R締切15:47の2分下限より遅い。先行V229 [38693703998](https://github.com/ikst2512-eng/boat-edge/actions/runs/38693703998) は15:39:42で、診断にソース不足が残る。
- 丸亀5R・若松10Rの各2–10分窓のActions作成履歴は、それぞれ21件/20件を取得しV229/V235作成0件。**対象窓に作成がなかった証拠であり、過去に開始した別ジョブの全実行行為をゼロと断定するものではない。**
- **なぜSourceが未完成かは別問題**。これら14Rを公式サイトの未公開と断定できない。収集ジョブと公式応答原本の追加調査余地を残す。保存不能な入力で凍結条件を緩和することは禁止。

### 1A→1B 引き継ぎ：最大の実証済み欠損経路

source-ready 9R中、少なくともソース完成後のV229/V235起動機会が薄く、あるいは厳格な`2<=mins<=10`内に戻ってこないケースが複数確認された。**V235がV230で公式ソースを更新した後に、既存V229を起こす信頼済みworkflow_run信号を追加する**のが小さい修正候補。既存V229のGit初回保存・レース同一性・ソースSHA・欠場・時点・Formal Freshガードを維持する。元のcron遅延そのものを直せるわけではない。結果的な本番改善を実測した場合だけ1Bを完了とする。
