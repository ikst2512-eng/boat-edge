# BOAT EDGE V403 — 5年間の履歴データ充足監査

更新: 2026-10-14 JST。**RESEARCH_ONLY / 0実データ投入 / ACCURACY_UNPROVEN / NO_PRODUCTION_PROMOTION**。

## 目的・既存実装との分担

- V400: 2021-10-01〜2026-09-30の保護境界を守る90/365/1095/1826日計数と180日半減期。
- V401: 許可済みのローカルK成績原ファイル → 抽出JSON → 正規化CSV、レースごとの除外理由を保持。
- V402: 同一開催日のローカルB番組表とK成績を6艇登録番号・艇番・締切/公開時刻で突合。場別 `by_venue`（番組数・完全結果・除外）を付与。
- **V403**: V402監査済み日別サマリー**だけ**を入力し、5年間の「V402報告が存在しない日付区間」を厳密に列挙し、年別／24場別の供給済み件数を合算する。K/B元データや正式Freshを読み込まない。

既存のPR #192（頭→2着→3着条件付き研究）、V307/V360（120通り候補）、V343/V344（未見事前凍結）を再実装・変更しない。01のデータライターと03のサイトUIは変更しない。

## 集計における重要な区別

- 1日の全国最大24場×12Rを**固定母数に使わない**。場ごとに開催・非開催があり、Bに列挙された出走予定レースだけが照合母数となる。
- V403に監査報告がない日付は `UNKNOWN`。非開催日だったか、提供元が欠損しているかは外部の真正なBファイルと日程証拠を調べるまで確定できない。
- V403がカレンダー日をすべて覆っても、全国全R・全場の完全網羅は証明しない。 `historical_race_coverage_independently_verified=false`。
- 発表日時・元K/B内容の真正性、事前の利用可能時刻、ライセンスは**人間の自己申告マニフェストだけでは証明できない**。未確認の値を補わない。
- `2026-10-01`以降の正式Fresh対象レースを研究用履歴として取り込まない。旧現行候補に遡及的に結果を混ぜない。

## 入力と実行

まず許諾済みの歴史B/KファイルからV401とV402が発行した一日単位のJSON監査結果（`schema=BOAT_EDGE_V402_OFFLINE_B_K_RECONCILIATION_RESEARCH_V1`）を配列にした `v402_reports.json` を作る。これは大きな生レース結果の公開アップロードではないが、元データの利用条件に沿って非公開保管する。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v403_five_year_coverage_audit.py \
  --reports-json /secure/history/v402_reports.json > /secure/history/coverage_v403.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_boat_edge_v403_five_year_coverage_audit.py' -v
```

出力の主な項目は `calendar_days`、`days_with_v402_reports`、`days_without_verified_v402_reports`、`unknown_or_unsubmitted_calendar_ranges`、`annual_counts`、`venue_counts`、入力日別SHA系譜。実結果や予想の的中率は**この監査では計算しない**。

## 未実施事項

1. 公式データ権利者への一括収集・保存・学習利用の許諾範囲の照会。公式 https://www.boatrace.jp/owpc/pc/extra/data/download.html はK/B配布を示すが、それだけでは許諾の確証にならない。サイト https://www.boatrace.jp/owsp/sp/extra/policy.html にも利用・アクセス制限がある。
2. 本当のK/Bの全日アーカイブ取得、1日分の抽出形式真正性と利用可能日時の実証、年別・場別の実測母数。
3. 直近3ヶ月/1年/3年/5年の候補モデルを同レース・同点数で時系列未見検証し、Top3・Top5・Top10、頭・2着・3着抜け、校正・統計的不確実性を別々に評価する。改善実証前に本番重み採用は不可。

GitHub CIは**合成データ専用**で、実際の5年間の結果取込成功や学習成績を証明するものではない。
