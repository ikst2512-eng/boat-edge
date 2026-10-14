# BOAT EDGE 02｜V405 複数Rの締切時点別履歴を一括処理

**更新:** 2026-10-14 JST  
**状態:** RESEARCH_ONLY、未見の予想結果・本番採用・正式Freshへのアクセス禁止、商用データ利用権未確認、実履歴0件。

## 変更の目的

- V404は1レースのB-only対象に対して、履歴CSV全体を読み直して各90/365/1095/1826日窓の集計を行う。5年分×多数レースの比較をそのまま繰り返すと計算量が大きくなる。
- **V405 `scripts/boat_edge_v405_batch_asof_history_features.py`** は権利確認済みでオペレーター投入したローカル履歴CSVを1度読み、競走成績の`published_at`順に逐次追加する。期限切れの古い記録は窓から消す。対象自身の結果は、その時点に存在したことになっていても一時的に除いてから対象特徴量を返す。
- V400の元CSV/マニフェストによるSHA-256照合は維持。V404と同じ、対象のB番組表由来`race_key`、`deadline_jst`、6艇登録番号だけを入力とし、`finish`、`actual_course`、結果を含む対象フィールドは禁止。
- 1つの研究リクエストで最大20,000個のB-only対象を扱う。履歴出走選手の結果実コースは過去の説明変数・集計としてだけ扱い、対象レースの事後実進入を予想前に混ぜない。
- **互換性:** V404と同じ「履歴の開催日と締切のJST暦日の差が0〜89、0〜364、0〜1094、0〜1825日（両端含む）」という**暦日窓**を維持している。厳密な過去90×24時間ではない。提供元の公開時刻が各締切より**厳密に前**であることは別途必須。
- 窓と選手・会場別の計数はすべて生カウント。まだモデル確率・3連単120点ランキング・的中率改善・校正にはなっていない。PR #192の条件付き予想器を再実装しない。
- ソート済み対象の順番で処理し、出力配列は元入力順へ戻す。対象同一レースIDの重複は拒否する。

## 実装/CLI

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v405_batch_asof_history_features.py \
  --history-csv /secure/private/operator_history.csv \
  --history-manifest /secure/private/operator_history_manifest.json \
  --b-only-targets-json /secure/private/target_b_only_array.json \
  > /secure/private/v405_batch_snapshots.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_boat_edge_v405_batch_asof_history_features.py' -v
```

`--b-only-targets-json`はV404のB-only対象JSONオブジェクトを並べた配列である。**必ず実際の締切前に利用可能だった事前情報かどうかを別途検証**する。V405にその独立証明機能はない。

## 検証

`tests/test_boat_edge_v405_batch_asof_history_features.py` は**実レース0・完全合成**の複数年/場/日付データを使い、単独V404参照結果とV405バッチ結果をJSON意味レベルで一致照合。複数Rの前後、同日締切、K成績公開遅れ、保護日2026-10-01、対象自身、K元SHA不整合、重複対象、6コース不完全、出力順序・決定性等を確認。

CIでのPASSは実レースの真正性・権利・現実の速度改善・予想精度改善を証明しない。計算量は対象ごとに全履歴再スキャンを避ける設計だが、本物の数十万Rの処理時間は**未測定**。

## 未解決ゲート

1. 公式BOAT RACEの成績K/番組Bは公開ダウンロード窓口あり（https://www.boatrace.jp/owpc/pc/extra/data/download.html）。ただし機械的一括収集/学習/公開予想への利用許諾は不明。第三者BRDB-API等も同様に条件確認が必要。許諾前は大量取得しない。元データを公開GitHubに入れない。
2. V401〜V403の全日B/K照合・除外台帳・権利証拠の実データ監査。過去のB-onlyタイムスタンプとK `published_at`の独立証拠。**古いデータが正しいだけでは「当時の締切前予想が存在した」と証明できない**。
3. 既存PR #192やV307/V360候補と同じレース、同じ買い目点数、結果未見に固定された予想を使う。Top3/5/10、頭・2着/3着の外れ方をホールドアウト評価。事前固定済み予想がないときは「評価不能」と記録し、再作成しない。
4. 未見の改善・信頼区間・監査合格までV405の集計を本番予想・サイト表示・01の保存経路に接続しない。

正式Fresh 2026-10-01以降は保護対象。現在0/100、results_seen=false、unlock=false、scoring=falseを維持。
