# BOAT EDGE 02 — S級情報の実データ入力仕様・権利判定（2026-10-16）

**RESEARCH_ONLY / ZERO_REAL_RACES_IMPORTED / ZERO_LICENSE_GRANTS_VERIFIED / ZERO_ACCURACY_UPLIFT_MEASURED**

対象の「S」は資料の有用度であり、スクレイピングやAI学習への利用権を意味しない。既存の [研究INBOX](../BOAT_EDGE_02_RESEARCH_INBOX.md)、[2026-10-16 横断台帳](BOAT_EDGE_02_SOURCE_LANDSCAPE_20261016.md)、PR #192（条件付き120通り）、PR #253（公式B/Kを対象とするV400–V406研究）と重複実装しない。

## S級4ソースの結論（Web確認日 2026-10-16）

| サイト | 公開されている有力情報 | BOAT EDGEが現時点で許可なく取り込んでよいもの | 禁止／保留 |
|---|---|---|---|
| ボートとデータ https://www.boatrace-data.com/guide/ | Elo、ST四分位Q1/Q2/Q3、スロー/ダッシュ別ST分布、レース展開シミュレーション、乗り手補正機力。https://www.boatrace-data.com/policy/ | **定義・着想のみ**を参照し、許諾済み別ソースから独立算出 | サイト独自Elo/機力指数をそのまま保存・転載すること、ボットによる大量取得 |
| 艇国データバンク https://boatrace-db.net/index/rules/ | 選手×実コースの他艇着順、進入・展示関連統計 | 他艇への影響を評価する独自アルゴリズムの着想のみ | サイトはツール取得に3秒以上のアクセス間隔等を規定する一方、私的範囲超の転載・使用を制限。3秒規則は商用データ利用権ではない。公式B/K/期別は公式配布先を使うよう案内 |
| BOATERS https://boaters-boatrace.com/guide/data-how-to-read | 先頭艇条件付き2着確率、前付け変更、枠別場別成績、展示後AI | 確率分解 P(1着)×P(2着｜1着)×P(3着｜1/2着) の考え方のみ | https://boaters-boatrace.com/info/terms 第8条にスクレイピング・クローリング禁止、舟券購入目的以外の利用も制限。AI学習用の個別数値・データ取得は禁止／未許諾 |
| BOAT RACE公式 https://www.boatrace.jp/owpc/pc/extra/data/download.html | 全国24場のB番組表・K競走成績・選手期別履歴、公開直前情報 | **以前に適正取得され、個別に権限確認した手元の事前CSV**を、ローカル研究専用で使う設計 | https://www.boatrace.jp/owsp/sp/extra/policy.html はコンテンツの無断二次利用を包括的に認めず、大量アクセスを制限。配布画面の存在のみでは商用学習・転載権を証明できない |

### 追加で確認した別経路

- https://github.com/BoatraceCSV/boatracecsv.github.io はCSV形式の出走表・直前情報・歴史データの**列定義**を公開し、リポジトリをMITと掲げている。しかし元データの多くは BOAT RACE / BOATCAST 由来であり、**リポジトリのMIT表示を元データ権利者の商用AI学習許諾と見なさない**。CSV本体や独自集計をBOAT EDGEへコピーしない。
- 列形式参考: https://boatracecsv.github.io/docs/data/programs.html および https://boatracecsv.github.io/docs/data/previews.html 。直前STT、TKZ、SUI、オリジナル展示はソース別の公開時刻を持つ。元データを入手できたとしても「その時刻にその値が使えた」ことの独立した証拠は別途必要。
- JMA は公共データ利用規約1.0適用の公開コンテンツあり https://www.jma.go.jp/jma/kishou/info/coment.html 。気象はこのS級4サイトとは別の補助入力候補で、現時点の水面実測値として扱わない。

## 実際に準備した S級一次データ用オフライン入力

実装: `scripts/boat_edge_02_s_offline_input.py` （標準Pythonのみ）
検証: `tests/test_boat_edge_v236_s_offline_input.py` （合成CSVのみ、17テスト）

現在取り込める**入力型**: 個別権限を確認して手元にステージング済みの、1レース1行・6艇の事前正規化CSV（参考列名: `レースコード`, `艇1_登録番号` 等）。BOATERS/競艇日和/ボートとデータ/艇国DB/BoatraceCSVからの自動収集・出力ファイル取り込みは不可。ネットワーク取得は行わない。

1艇あたり13個の「元の事前値」（計最大78セル）：

- 全国勝率、全国2連対率、全国3連対率
- 当地勝率、当地2連対率、当地3連対率
- 全国平均ST
- モーター2連対率、3連対率
- ボート2連対率、3連対率
- F本数、L本数

6艇が完全にそろう場合だけ、全国勝率、全国2連対率、平均ST、モーター2連対率、3連対率の**同レース平均に対する差分**を追加算出（最大5×6=30セル）。これらは「選手能力補正Elo」「純粋な機力指数」「条件付き2着率」とは**別物**であり、その名称で誤表示しない。欠測はNULLのまま、0/平均/proxyで補完しない。

### 最小manifest

以下は**項目例**であり、`source_sha256` は実ファイルの SHA-256 に置き換え、`rights_evidence` には現実の契約条項や内部でレビューした証拠への参照を記載する。書いた文字だけで権利や公開時刻が独立検証できたとはみなさない。

```json
{
  "schema": "BOAT_EDGE_02_OPERATOR_STAGED_PREDEADLINE_RACECARD_V1",
  "source_kind": "BOAT_EDGE_OPERATOR_STAGED_PREDEADLINE_NO_NETWORK",
  "source_sha256": "実際のCSVをハッシュ化した64桁hex",
  "race_key": "202609290103",
  "deadline_jst": "2026-09-29T12:00:00+09:00",
  "first_seen_at_jst": "2026-09-29T09:02:00+09:00",
  "data_available_at_jst": "2026-09-29T09:00:00+09:00",
  "rights_status": "OPERATOR_ATTESTED_LOCAL_RESEARCH_ONLY",
  "rights_evidence": "個別に確認した許諾・提供経路・利用範囲の根拠をここに記入"
}
```

```bash
python3 scripts/boat_edge_02_s_offline_input.py --csv /path/to/operator-reviewed-racelist.csv --manifest /path/to/source-manifest.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_v236_s_offline_input.py' -v
```

**注意:** 2021-10-01〜2026-09-30のみ扱い、2026-10-01+のFormal Fresh対象を拒否。6艇の登録番号重複、対象R違い、CSV SHA不一致、JST以外、deadline以降のタイムスタンプ、不明な権利審査、オッズ・的中・払戻・他社独自指数列を拒否。実装が読んだ時刻が真正な提供元時刻である証明ではない。実データの許諾審査も自動化できない。

## S級4サイトを参考にした未接続の特徴量と必要な実データ

| 研究特徴量 | 必要なソース | 現状 |
|---|---|---|
| 対戦相手補正Elo | 権利を持つ過去K、6艇の相手、場、実コース、結果公開時刻 | **0実データ**。PR #253の安全な歴史ブリッジと連携待ち |
| ST四分位・IQR | 選手×コース×スロー/ダッシュ別の過去**本番**ST（展示STとは区別） | 過去STをまだ取れない。平均STだけ入力可能 |
| モーター純粋効果 | モーターID、使用期間、前節までの乗り手、整備、実結果、相手/コース補正 | モーター2/3連率は入力可能。「純粋な機力」は未実装 |
| 逃がし・先頭艇別2着確率 | 先着・2着・3着と実コースの過去K。1逃げと非1頭で母数を分ける | 独立の権利済み歴史結果が必要。既存PR #192と重複させない |
| 他艇×攻撃/受益の相互作用 | 6艇同時組合せ、実進入、1Mの攻撃/抵抗の一次ラベル | 公開の独自超展開データは無断複製不可。一次ラベルがない限り仮説のみ |

## 結果として言えること

- **コードとして実装・検証したのは13種類×6艇のローカル一次入力と5種類の相対差算出。**
- **実レースCSV投入は0件、許諾取得0件、モデル学習0件、Top3/5/10改善実測0件。**
- 権利確認済みの実ファイルが無い状況では**取得したふりをせず停止**する。新規スクレイパー・新スケジューラー・本番重み調整・Pages変更・正式Fresh結果の先読みをしない。
- 次の実務ボトルネックはモデルやテストの数ではなく、一次データの利用権・時点真正性・過去5年のカバレッジ。既存PR #253に沿って確認する。
