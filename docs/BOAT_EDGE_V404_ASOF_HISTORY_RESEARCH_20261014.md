# BOAT EDGE V404 — 5年履歴の締切時点別特徴量（2026-10-14）

**RESEARCH_ONLY / LICENSE_PENDING / 0 REAL HISTORICAL RACES INGESTED / NO MODEL PROMOTION.**

## なぜV404が必要か

V400の90/365/1095/1826日集計は**2026-10-01時点**の集計なので、これを2025年のレース予想にそのまま入力すると、2025年のレース終了後に得られた結果を混ぜる危険がある。V404はレース単位で`target.deadline_jst`を評価時点とし、**各Kレースの元マニフェスト由来`published_at`が締切より厳密に前のものだけ**からコース別特徴量を作る。自己申告の公開時刻では証明は不十分であり、`historic_publication_timestamps_independently_verified=false`を必ず出す。

- **対象のB番組表由来フィールド**：レースID、締切日時、1〜6艇の登録番号のみ。対象の着順・実進入・オッズ・確定払戻・モーター事後データは入力禁止。
- **元履歴のK由来フィールド**：6艇・実際の進入コース・確定着順・結果公開時刻。過去の他レースの結果だけを教師側の集計に使う。対象と同一`race_key`は、公開時刻を偽っても強制除外。
- **場別**・全国別・各出走選手別の1〜6コースで、過去90日／365日／1095日／1826日（締切当日が含まれる場合は0〜89／0〜364／0〜1094／0〜1825日前の計W暦日）について出走数、1着、2着、3着の実測カウントを返す。サンプルなしは数0、**架空の勝率や縮約確率を発生させない**。複数の期間を加算するのは誤り。
- 出力は参考用の未校正**統計量**。既存のPR #192条件付き3連単、V307/V360 120通り予想器、V343/V344未見予想凍結の実装は重複させない。

## 実行方法

`history.csv`はV401出力仕様の複数日結合・`race_key,boat`順のファイルと、正しい内容SHAを持つV400マニフェストである。**公開リポジトリに実K/Bをコミットしない**。

B-only対象ファイル例（数値は**架空**）：

```json
{
  "schema": "BOAT_EDGE_V404_B_ONLY_TARGET_ROSTER_V1",
  "race_key": "202609300103",
  "deadline_jst": "2026-09-30T08:35:00+09:00",
  "entries": [
    {"boat":1,"racer_id":"4501"},{"boat":2,"racer_id":"4502"},
    {"boat":3,"racer_id":"4503"},{"boat":4,"racer_id":"4504"},
    {"boat":5,"racer_id":"4505"},{"boat":6,"racer_id":"4506"}
  ]
}
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v404_asof_history_features.py \
  --history-csv /secure/history.csv \
  --history-manifest /secure/v400_manifest.json \
  --b-only-target /secure/b_only_target.json > /secure/v404_asof_features.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_boat_edge_v404_asof_history_features.py' -v
```

`source_sha256`を保持し、`historical_races_not_yet_available`と`same_target_outcome_excluded`をカウントする。元K結果の公開時刻とB締切が本当かどうかはV404単独では独立検証できない。B-only対象の過去締切前保存時刻も自己申告であるため、**正式Fresh未見検証にも本番的中率証明にも使用不可**。

## 追加の外部調査と費用

- BOAT RACE公式 https://www.boatrace.jp/owpc/pc/extra/data/download.html にK競走成績・B番組表ダウンロードの案内あり。サイトポリシー https://www.boatrace.jp/owsp/sp/extra/policy.html に著作権や大量アクセス等の制約。5年分の**機械収集・保存・モデル学習・結果再配布が許可されたとは未確認**。権利者確認まで自動バルクダウンロード・公開アップロードなし。
- 代替の商用候補：Team-Naveの`BRDB-API` https://www.team-nave.com/system/jp/products/brdbapi/ は公式DL由来の番組・競走成績・選手期別データを説明。掲載価格は**GAMBLE-OS個人向け税込月3,300円**で、商用・営利は**別途協議・別契約**。ページはβ版表示であり、現在の稼働・契約上の機械学習・公開予想利用は未確認。**契約／課金／APIアクセスなし**。2024年末サポート終了と記載の旧BRDBC Cloudを現行APIと取り違えない。

## 昇格ゲート

1. 実データ取得許諾（収集・蓄積・学習・出力・再配布/商用）を確認する。利用規約・日時・対象範囲を監査保管。
2. 元K/Bアーカイブを私有の許諾済みストレージに保存、SHAを検証。V401→V402→V403を使い、完全実レースと出走表照合・非開催日を区別して実測網羅率を出す。
3. V404の同レース・同締切時点で90/365/1095/1826日特性を個別評価し、PR #192の既存研究器へ読取専用で接続。対象の実進入/結果を予想前に混ぜない。
4. 日付順学習・日跨ぎホールドアウト、さらに結果未見の新規**Git締切前事前固定**を両腕同一R/同一点数で実施。Top3/5/10、頭、2着・3着抜け、信頼区間を別記。実証されるまで**本番モデル不変更**。

正式Fresh対象の2026-10-01以降レースは、V400〜V404の履歴・対象に取り込めないハード境界。サイト表示と01保存処理に変更なし。
