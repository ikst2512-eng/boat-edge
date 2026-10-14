# BOAT EDGE V402 — 過去B番組表×K成績の独立照合（2026-10-14）

**研究専用。実データ未収集・未学習・的中率改善未証明。** 研究PR #253の独立照合層であり、V400集計・V401オフラインK橋渡し・PR #192の予想候補とは役割を分離する。

## 調査した一次情報・権利

- BOAT RACE公式 `https://www.boatrace.jp/owpc/pc/extra/data/download.html`: 全国24場の競走成績(K)と番組表(B)のダウンロード入口。入口は `www1.mbrace.or.jp/od2/K/dindex.html` と `www1.mbrace.or.jp/od2/B/dindex.html`。**2021–2026の全日を取得できること、事前公開時刻の真正性、5年機械収集・再配布・学習のライセンスはいずれも未証明**。
- 公式サイトポリシー `https://www.boatrace.jp/owsp/sp/extra/policy.html`: 権利者の許可・大量アクセスに関する制限がある。公開コードのMITライセンスはレース原データの取得権利を意味しない。
- 公式データの自動一括取得は禁止ではなく**許諾未確認のため未実施**。別途権利者確認が必要。利用範囲が確認できるまで原データや正規化済みレース結果を公開GitHubに追加しない。

## V402の成果と狙い

- `scripts/boat_edge_v402_offline_b_k_reconciliation.py`: **ローカルに安全に持ち込まれた**KのV401正規化CSV、V400マニフェスト、V401レース別除外記録、B番組表の抽出済みJSON、B元バイトおよびBマニフェストを突合。
- K/BのレースID、開催日、艇番、選手登録番号が全6艇一致することを検査。番組表の締切日時より**結果公開の入力時刻が厳密に後**であることを必須にする。展示進入を実進入と混同しない。
- 番組表に載ったがKで完走データを出せない欠場・事故等は、Kの**レースID付き除外理由記録**に無ければ停止。V401にも除外レースのID保存を追加。Kにしか存在しないレース、重複、未説明欠測、マニフェストSHA不一致は停止。
- `tests/test_boat_edge_v402_offline_b_k_reconciliation.py` の21件は**合成データのみ**。コード・テストはGitHubのblob SHAに一致するローカルコピーで21/21 PASS。**この時点ではV402のGitHub Actions専用テストは未実行**。既存CIの成功はV402専用CI PASSという意味ではない。
- 正式Fresh 2026-10-01以降は従来どおりハード拒否。結果・払戻APIアクセスなし、本番重み・保存経路・Pages/サイトUIは変更なし。

## Bローカル抽出形式

```json
{
  "schema": "BOAT_EDGE_V402_STAGED_B_PROGRAM_DAY_V1",
  "source_day": "2026-09-30",
  "races": [
    {
      "race_key": "202609300101",
      "deadline_jst": "2026-09-30T08:35:00+09:00",
      "entries": [
        {"boat": 1, "racer_id": "4501"},
        {"boat": 2, "racer_id": "4502"},
        {"boat": 3, "racer_id": "4503"},
        {"boat": 4, "racer_id": "4504"},
        {"boat": 5, "racer_id": "4505"},
        {"boat": 6, "racer_id": "4506"}
      ]
    }
  ]
}
```

上記値は**合成fixture**で実際の番組表を意味しない。Bマニフェストは `schema=BOAT_EDGE_V402_B_SOURCE_MANIFEST_V1` と、`source_sha256`, `staged_sha256`, `source_locator`, `rights_evidence`, `rights_review_status=OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY`, `parser_name`, `parser_version`, `retrieved_at_jst` の9項目を固定。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v402_offline_b_k_reconciliation.py \
  --k-csv /secure/day/normalized.csv \
  --k-manifest /secure/day/v400_manifest.json \
  --k-audit /secure/day/v401_audit.json \
  --b-original /secure/day/source_B.lzh \
  --b-staged /secure/day/operator_staged_B.json \
  --b-manifest /secure/day/b_manifest.json \
  --as-of-jst '2026-10-01T00:00:00+09:00'
```

**限界**：B/K抽出値、元バイトと実体の対応・元のレース全件網羅・許諾・第三者サーバーの独立受領日時まではコードだけでは証明できない。そのため結果でも `national_daily_coverage_independently_verified=false`, `license_independently_verified=false`, `b_program_historic_capture_independently_authenticated=false`, `trained_model_created=false`, `accuracy_improvement_proven=false` と明示。

## 次の実施条件

1. 公式または正規提供元からの研究/学習許諾、B/K対象年月の網羅率、元ファイルの正しい復号・入力値照合。
2. B/Kの日時証拠を検証。Kの実コースと着順が分かるのは**レース終了後**なので、過去結果は教師ラベルのみ。回顧的なBを独立した「締切前保存証拠」とは絶対に呼ばない。
3. 日別→年別・場別のカバレッジと欠測理由の分布を監査。5年分の全対象の有無を検証。
4. PR #192や既存V307/V360を重複制作せず、90日/365日/1095日/1826日窓の候補に連動し、**未見の同一10点**でTop3/5/10・頭・2/3着外れを複数日評価。改善の実証前に本番採用禁止。
