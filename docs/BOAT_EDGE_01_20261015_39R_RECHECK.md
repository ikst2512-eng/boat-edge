# 2026-10-15 main / Actions 再監査

基準main: `932f84ee6c7a86308014349e66ca5d1923a27e04`。対象は2026-10-14のSITE PRE_RESULT保存。正式Fresh・結果・払戻・初回保存処理は変更しない。

## 39Rのレース別観測

124R観測、85Rはパスが存在、39Rはスナップショット未保存。85Rのバイトや初回Git証明の再検証は今回の件数に含めない。24Rは最終チェックにも不足、5Rは過去の不足が最終チェックでは解消、10Rは不足の記録なし。これは観測分類であり根本原因の確定ではない。

| レース | 締切JST | 最終確認・締切前分 | 最終チェックの不足 | 過去に観測した不足 |
|---|---|---:|---|---|
| 20261014-04-06 平和島6R | 12:53 | 10.99 | なし（適格証明ではない） | 観測なし |
| 20261014-04-08 平和島8R | 13:57 | 11.16 | なし（適格証明ではない） | 観測なし |
| 20261014-04-11 平和島11R | 15:40 | 3.67 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_missing_or_blocked, scratch_stale |
| 20261014-06-06 浜名湖6R | 13:47 | 7.67 | beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, scratch_stale |
| 20261014-06-07 浜名湖7R | 14:15 | 3.51 | beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, scratch_stale |
| 20261014-06-10 浜名湖10R | 15:37 | 11.02 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale |
| 20261014-11-05 びわこ5R | 12:08 | 7.68 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-11-08 びわこ8R | 13:45 | 5.67 | beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, scratch_stale |
| 20261014-12-06 住之江6R | 17:25 | 12.44 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-12-07 住之江7R | 17:52 | 2.80 | なし（適格証明ではない） | beforeinfo_not_ok, race_card_stale, scratch_missing_or_blocked |
| 20261014-13-02 尼崎2R | 11:08 | 11.34 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-13-08 尼崎8R | 14:05 | 3.45 | scratch_missing_or_blocked | beforeinfo_not_ok, race_card_stale, scratch_missing_or_blocked |
| 20261014-13-11 尼崎11R | 15:33 | 7.02 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale |
| 20261014-13-12 尼崎12R | 16:05 | 12.15 | なし（適格証明ではない） | beforeinfo_not_ok, scratch_stale |
| 20261014-14-10 鳴門10R | 12:58 | 2.75 | beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale, pre_result_odds_120_incomplete, official_dom_proof_missing | beforeinfo_not_ok, official_dom_proof_missing, pre_result_odds_120_incomplete, pre_result_odds_stale, scratch_missing_or_blocked |
| 20261014-14-12 鳴門12R | 14:11 | 9.45 | scratch_stale | beforeinfo_not_ok, race_card_stale, scratch_stale |
| 20261014-15-02 丸亀2R | 15:44 | 7.67 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_unverified | beforeinfo_not_ok, pre_result_odds_unverified, race_card_stale, scratch_missing_or_blocked |
| 20261014-15-07 丸亀7R | 17:58 | 7.96 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-15-11 丸亀11R | 20:08 | 10.84 | なし（適格証明ではない） | 観測なし |
| 20261014-18-04 徳山4R | 10:01 | 12.12 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-19-03 下関3R | 18:34 | 3.63 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-19-04 下関4R | 19:03 | 3.30 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-19-10 下関10R | 21:51 | 5.61 | なし（適格証明ではない） | 観測なし |
| 20261014-19-11 下関11R | 22:20 | 10.53 | pre_result_odds_stale | pre_result_odds_stale |
| 20261014-20-01 若松1R | 15:25 | 13.29 | なし（適格証明ではない） | 観測なし |
| 20261014-20-02 若松2R | 15:54 | 10.65 | なし（適格証明ではない） | 観測なし |
| 20261014-20-05 若松5R | 17:19 | 6.44 | なし（適格証明ではない） | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-20-10 若松10R | 19:49 | 6.10 | なし（適格証明ではない） | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale |
| 20261014-20-11 若松11R | 20:18 | 4.22 | pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_missing_or_blocked |
| 20261014-21-07 芦屋7R | 11:37 | 9.41 | なし（適格証明ではない） | 観測なし |
| 20261014-21-12 芦屋12R | 14:27 | 13.04 | なし（適格証明ではない） | 観測なし |
| 20261014-22-08 福岡8R | 14:24 | 10.04 | なし（適格証明ではない） | beforeinfo_not_ok, scratch_stale |
| 20261014-22-10 福岡10R | 15:30 | 4.02 | なし（適格証明ではない） | 観測なし |
| 20261014-22-12 福岡12R | 16:31 | 5.65 | beforeinfo_not_ok, scratch_missing_or_blocked | beforeinfo_not_ok, scratch_missing_or_blocked |
| 20261014-24-01 大村1R | 15:23 | 11.29 | なし（適格証明ではない） | 観測なし |
| 20261014-24-07 大村7R | 18:03 | 12.96 | race_card_stale, beforeinfo_not_ok, scratch_stale | beforeinfo_not_ok, race_card_stale, scratch_stale |
| 20261014-24-08 大村8R | 18:40 | 9.63 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale |
| 20261014-24-09 大村9R | 19:11 | 6.43 | race_card_stale, beforeinfo_not_ok, scratch_stale, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_stale |
| 20261014-24-10 大村10R | 19:42 | 3.07 | race_card_stale, beforeinfo_not_ok, scratch_missing_or_blocked, pre_result_odds_stale | beforeinfo_not_ok, pre_result_odds_stale, race_card_stale, scratch_missing_or_blocked |

## 優先3RのActions照合

| レース | V229対象時間JST | 取得した実行履歴 | 判定 |
|---|---|---|---|
| 芦屋7R 11:37締切 | 11:27–11:35 | [38500877753](https://github.com/ikst2512-eng/boat-edge/actions/runs/38500877753) は11:24:46–11:25:12、次は38501888932の11:36:09 | 取得窓内で対象時間に実行なし |
| 下関10R 21:51締切 | 21:41–21:49 | [38565622924](https://github.com/ikst2512-eng/boat-edge/actions/runs/38565622924) は21:40:31–21:40:52、次は38567598235の21:55:40 | 同上。21:40:51診断でも対象外・次レースとして掲載 |
| 福岡10R 15:30締切 | 15:20–15:28 | 15:10–15:31作成の全44件にV229なし。V235は15:10:16–15:11:52 | 対象時間のV229作成を確認できず。窓より前に作成された長時間jobは未除外 |

芦屋の取得窓は11:15–11:38（78件）、下関は21:30–21:52（46件）と21:51–22:05（84件）。GitHub cronの設定時刻は実行保証ではない。V235のスコア込みログは読んでいない。全39Rの各worker当時の入力SHA・判定時刻の突合は未完了。後付け予想は生成しない。

## 重複と安全な変更範囲

静的集計は225 YAML、44定期実行、38 contents-write候補。ディレクトリ226項目のうち1項目はZIP。稼働設定をAPIから全件取得した数ではない。

V341が`if: false` / `${{ false }}` のjob内のgit addまで数え、V133/V136旧installerのTODO・index・policy更新を現役の重複と誤認していた。読み取り専用監査から、この明示停止jobだけを除外する。動的条件と手動条件は引き続き候補扱い。予想・本番workflow・UIは変更なし。回帰でcollector/oddsの親子パス候補が残ることと、現役historyが残ることを確認する。

修正後の同一パス候補は16から10。これを6処理の停止と解釈してはならない。V125/V133のTODO重複は停止済みinstaller由来で、追加停止不要。V234/V254はV235の無効化ステップがあり、cronの存在のみでは稼働重複と認定不可。

残る同一パス候補:

- `BOAT_EDGE_V228_SITE_AI_AUTOPILOT.yml` / `BOAT_EDGE_V232_PROSPECTIVE_COHORT.yml` → `autopilot.html`（未確定、停止しない）
- `BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml` / `BOAT_EDGE_V228_SITE_AI_AUTOPILOT.yml` → `data/site_autopilot/v227_current.json`（未確定、停止しない）
- `BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml` / `BOAT_EDGE_V232_PROSPECTIVE_COHORT.yml` → `data/site_paper_sim/readiness_history_v215`（未確定、停止しない）
- `BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml` / `BOAT_EDGE_V232_PROSPECTIVE_COHORT.yml` → `data/site_paper_sim/readiness_v215_current.json`（未確定、停止しない）
- `BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml` / `BOAT_EDGE_V232_PROSPECTIVE_COHORT.yml` → `data/site_paper_sim/shadow_v213_current.json`（未確定、停止しない）
- `BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml` / `BOAT_EDGE_V232_PROSPECTIVE_COHORT.yml` → `data/site_paper_sim/shadow_v213_ledger.json`（未確定、停止しない）
- `BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` / `site-v125.yml` → `data/site_prediction_audit`（未確定、停止しない）
- `BOAT_EDGE_V228_SITE_AI_AUTOPILOT.yml` / `BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` → `data/site_prediction_snapshots`（未確定、停止しない）
- `BOAT_EDGE_V228_SITE_AI_AUTOPILOT.yml` / `site-v133.yml` → `data/site_prediction_snapshots`（未確定、停止しない）
- `BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` / `site-v133.yml` → `data/site_prediction_snapshots`（未確定、停止しない）

V180/V185/V186旧bundle復元防止、V238/V241のV235 event fanout削除、V109のTODO保存除外はmainに反映済みで再変更しない。

## 今回観測した別障害

[collector run 38683399185](https://github.com/ikst2512-eng/boat-edge/actions/runs/38683399185) は収集成功後、保存段階でV277が凍結済み04-08/06-07の原本変更を拒否し、prune側が10-11の締切超過を検出して停止。安全ガードの正常な拒否であり、39Rすべての原因とはしない。初回保存境界に関わるため今回は変更しない。

[controlled Pages 38682140931](https://github.com/ikst2512-eng/boat-edge/actions/runs/38682140931) はverify-sourceのみ成功、build/deployはskip。dynamic Pages 38683615831は成功。Actions公開への安定移行完了とは判定しない。

## 検証・未完

専用回帰・既存V23系fixture・V271 health・source pinsを実行。実測の保存成功率改善、本番連続運用、Top3/5/10一致は未証明。正式Freshは読取時0/100R、results_seen/unlock/scoring=false、token=null。変更対象は監査コード・fixtureテスト・本レポートのみ。
