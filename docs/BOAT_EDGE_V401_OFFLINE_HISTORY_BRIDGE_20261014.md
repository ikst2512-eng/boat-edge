# BOAT EDGE V401 — 公式履歴の取得元調査とオフライン取込アダプター（2026-10-14）

**研究専用／未収集／未学習／本番未反映。** V400 PR #253への追加。02の管轄。01のActions書込・V235予想保存、03のUI、正式Fresh、V307/V360・PR #192予想器には変更しない。

## 実際に確認した一次資料と利用上の境界

- [BOAT RACE公式 ダウンロード・他](https://www.boatrace.jp/owpc/pc/extra/data/download.html) には **全国24場の競走成績ダウンロード** と **番組表ダウンロード** が掲載されている。レーサー期別成績のLZH案内とも別系統であり、ページの存在だけで個々のアーカイブの保存期間・網羅率・レイアウト・ライセンスを証明しない。
- [BOAT RACE公式 サイトポリシー](https://www.boatrace.jp/owsp/sp/extra/policy.html) は無断複製等への制約、大量アクセスでサイト運営に支障を与える行為の禁止を掲げる。**この調査時点で、5年分の機械的一括取得、公開GitHubへの元データ再配布、学習商用利用の許諾は確認できていない**。収集許可や利用範囲は権利者に確認し、未確認のまま大量取得処理を自動起動しない。
- 参照実装 [miyamamoto/boatrace-lzh](https://github.com/miyamamoto/boatrace-lzh) は、K(成績)・B(番組)のローカルパース、各レースの `boat_number / racer_number / entrance_position / result_position` のモデルを公開している。MITライセンスは**ソフトウェアのコード**についてで、公式成績・番組表の二次利用許諾にはならない。パーサーにも誤解析の可能性があるため、K原文との独立照合は別ゲート。

## V401 実装済み部分（ネットワークアクセスなし）

`scripts/boat_edge_v401_staged_k_bridge.py` は、権限・条件を人手で確認した **ローカルK元バイト** と、外部パーサーなどが作成した **レース単位の抽出済みJSON** を、V400標準CSV・監査マニフェストへ変換する。

- 元アーカイブと抽出済みJSONの **実SHA-256照合**
- 形式固定 `YYYYMMDDjjrr`、同じ日付、全国24場・各12RのレースID検査
- 6艇・登録番号6件・実進入1〜6の完全順列・着順1〜6の完全順列。**展示進入を実進入の代替としない**
- 欠場、事故、失格、非標準結果は値を埋めず明示的な除外理由で記録。元データ全体の網羅率は本モジュールでは検証できないので `race_coverage_complete=false`
- 公開済み時刻は入力された根拠付きの値だけを使う。単に「2021年のレースだから2021年にアーカイブが利用できた」とは断定しない。元ファイルの独立真正性、配布時刻の独立証明、法的利用権は `false` のまま
- V400に渡す前に全レース検証。**2026-10-01以降の形式Fresh保護日をハード拒否**。現在の本番予想の改善証拠とはならない

## 入力例（**実データではない**）

抽出済みJSONは以下の構造。例は1艇のみ省略表示ではなく、実行入力では **必ず6艇全行**が必要。

```json
{
  "schema": "BOAT_EDGE_V401_STAGED_K_EXTRACT_V1",
  "source_day": "2026-09-30",
  "races": [{
    "race_key": "202609300101",
    "published_at": "2026-09-30T21:00:00+09:00",
    "entries": [
      {"boat":1,"racer_id":"4501","actual_course":1,"finish":1},
      {"boat":2,"racer_id":"4502","actual_course":2,"finish":2},
      {"boat":3,"racer_id":"4503","actual_course":3,"finish":3},
      {"boat":4,"racer_id":"4504","actual_course":4,"finish":4},
      {"boat":5,"racer_id":"4505","actual_course":5,"finish":5},
      {"boat":6,"racer_id":"4506","actual_course":6,"finish":6}
    ]
  }],
  "excluded": [{"race_key":"202609300102","reason":"CANCELLED"}]
}
```

元データ用の別JSONマニフェストは以下の **全項目**が必要。

```json
{
  "schema":"BOAT_EDGE_V401_K_SOURCE_PROVENANCE_V1",
  "raw_source_sha256":"<元アーカイブの実SHA256>",
  "staged_sha256":"<抽出済みJSONの実SHA256>",
  "source_name":"<データ提供元>",
  "source_locator":"<元データアーカイブを特定する文字列>",
  "rights_evidence":"<調査済み利用条件/権利確認の証拠>",
  "rights_review_status":"OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
  "normalization_protocol":"<元形式からの変換規則とバージョン>",
  "parser_name":"<パーサー名>",
  "parser_version":"<使用バージョン>",
  "retrieved_at_jst":"<元アーカイブを取得した時刻 +09:00>"
}
```

`rights_review_status` は運用者の**自己申告**であり法的許諾や実際の成果を証明しない。例示の `published_at` はテスト用ダミーであり、実ソースでは第三者が確かめられる証拠がなければ研究採用しない。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v401_staged_k_bridge.py \
  --source-archive /secure/authorized_k_day.lzh \
  --staged-json /secure/operator_parsed_k_day.json \
  --source-manifest /secure/operator_source_manifest.json \
  --as-of-jst '2026-10-01T00:00:00+09:00' \
  --output-dir /secure/new-empty-v401-output

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_boat_edge_v401_staged_k_bridge.py' -v
```

出力は `normalized.csv`, `v400_manifest.json`, `v401_audit.json`。私有ローカル保管を前提とし、公衆GitHubには投入しない。1つのK日付分ずつ、途中で欠測日を勝手に省略して「5年完了」と主張せず、年間／会場／日別coverageを後から別途検証する。

## 未解決のまま残すゲート

1. 正式な利用許可・対象範囲・保存/モデル学習/公開の可否の確認（ここまではプログラムで代替不能）
2. ネイティブK/Bアーカイブのデコード規則・実データ照合・元ファイル日別の利用可能時刻の監査
3. 年別／場別 coverage と出走表Bとの同一レース・選手一致照合、欠場・失格・決着不能理由の証明
4. 現行対照と候補の同一R/同一10点を時系列保持、未見Top3/5/10と頭・2/3着外れの評価。**検証前の精度向上・採用・実購入は禁止**

正式Freshの解錠・採点は禁止。V401の結果は **research_only=true / model_promotion_authorized=false** を必須とする。
