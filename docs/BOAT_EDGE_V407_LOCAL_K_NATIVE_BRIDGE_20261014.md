# BOAT EDGE V407｜許諾済みローカルK成績テキスト→V401 JSON変換（研究専用）

更新: 2026-10-14。PR #253の研究用。01/03、正式Fresh、本番予想を変更しない。

## 実装範囲

V401の前で必要だった日別の成績Kの手動JSON変換を補助。既に合法的に取得・解凍されたローカルShift-JIS(CP932)の成績K TXTのみを読み、第三者 boatrace-lzh==0.1.0 の PerformanceParser.parse を使ってRaceEntry型へ変換する。URLへのアクセス、元のLZH取得、スクレイピング、サイト結果アクセス、予想学習は実装しない。

参考ライブラリ: https://github.com/miyamamoto/boatrace-lzh 。そのMITライセンスはライブラリのコード向けであり、BOAT RACEの競走成績を機械学習・公開サイトに利用する許諾にはならない。

入力にはV402形式の全予定RのB番組日別JSONが必要。K側で観測されないRはSOURCE_AMBIGUOUS、6艇に足りないRはINCOMPLETE_RESULTS、非標準の順位はNON_STANDARD_FINISH、実進入不明はUNVERIFIED_ACTUAL_COURSEとして明示的に除外する。艇・登録番号がBと違う、6艇コース/着順が重複する場合はエラー。出走表Bの締切前真正性は独立検証していない。

結果公開日時は生Kファイルから勝手に推測できない。別途 operator による結果公開時刻の証拠ファイルをすべての完走Rに要求し、JST締切後でなければ拒否する。ただし日時の信頼性は自己申告であり、実際の締切前入手の証拠にはならない。

公開時刻JSONの形式は source_day=2026-09-30、schema=BOAT_EDGE_V407_OPERATOR_K_PUBLICATION_TIMES_V1、races={"202609300101":"2026-09-30T21:00:00+09:00"}。この時刻は架空の形式例であって歴史的公開日時の証明ではない。

### 実行

1. 別途、合法に取得されたKテキストをローカルで解凍する。
2. V402形式の同日B番組全予定Rを準備する。
3. 完走した各KレースのJST公開時刻を独立に記録し、未証明時刻を捏造しない。
4. V407実行例:

    PYTHONPATH=scripts python3 scripts/boat_edge_v407_local_performance_bridge.py --local-k-txt /private/K_20260930.txt --local-b-stage /private/B_20260930.json --publication-map /private/pub_20260930.json --output-json /private/K_staged_V401.json

5. 出力されたV401形式JSONは、別途K原文・抽出済みJSON双方のSHAと権利情報を厳密照合するV401→B/K照合V402→日次まとめV406に渡す。入力実データは公開GitHubにアップロードしない。

## 未完了

- 公式B/Kの大量取得、研究・機械学習・予想表示への利用権は未確認。問い合わせ原案は docs/BOAT_EDGE_HISTORY_RIGHTS_INQUIRY_20261014.md 。
- V407は外部パーサーの解釈が正しいとは独立に証明しない。実Kを一件以上公式一次資料で照合する必要がある。
- 実データ0R、実公開時刻認証0件、適法な学習成果0件、Top3/Top5/Top10精度改善未実証。
- 2026-10-01以降の正式Fresh結果は厳格に禁止。予想保存や本番モデルへ混入させない。

合成データのみのCIテスト: python3 -m unittest discover -s tests -p 'test_boat_edge_v407_local_performance_bridge.py' -v
