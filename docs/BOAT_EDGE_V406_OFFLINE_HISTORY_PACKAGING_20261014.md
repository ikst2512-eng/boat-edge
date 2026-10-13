# BOAT EDGE V406｜5年履歴のオフライン日次統合（研究専用）

更新：2026-10-14。PR #253のTrack 02限定。V235/01の締切前保存、03のPages、正式Fresh、本番モデルは一切触らない。

## 前提と実装範囲

- **実データは0R、データ利用許諾は未取得・未確認。** この変更で実Kデータをダウンロードしたり、機械学習モデルを訓練したり、的中率の改善を証明したりしていない。
- 公式BOAT RACEのK（結果）とB（番組）を**利用条件確認後に運用者が適法に準備**した場合に限り、ローカルのV401→V402日次照合結果（V400形式CSV＋manifest＋V402監査報告）を複数日まとめられる。
- B/K照合はV402が日別に実施したと主張する**監査ファイルをチェックする処理**。外部ソースの真正性、実際の公開時刻、過去の締切前番組保存や権利取得を独立に認証するものではない。
- V403で未提出日はUNKNOWN扱い。日次資料が1日もなければエラー。日数欠落があっても隠さず `days_without_verified_v402_reports` と範囲を出す。
- 期間：2021-10-01〜2026-09-30。**2026-10-01以降を含めない**。正式Freshのロック解除・結果/払戻API呼び出しは存在しない。
- このツールは手元のファイルを読むだけで、URL・認証情報・データ取得処理は一切受け付けない。

## 許諾後の入力配置（データは公開リポジトリに置かない）

ローカル `/private/boat-history-staging/` に日別の3点を用意する：

```text
2026-09-29/k.csv
2026-09-29/v400_manifest.json
2026-09-29/v402_report.json
2026-09-30/k.csv
2026-09-30/v400_manifest.json
2026-09-30/v402_report.json
index.json
```

`index.json`（例。実データでも学習済みでもない）：

```json
{
  "schema": "BOAT_EDGE_V406_LOCAL_DAY_INDEX_V1",
  "days": [
    {
      "source_day": "2026-09-29",
      "normalized_csv": "2026-09-29/k.csv",
      "v400_manifest": "2026-09-29/v400_manifest.json",
      "v402_report": "2026-09-29/v402_report.json"
    },
    {
      "source_day": "2026-09-30",
      "normalized_csv": "2026-09-30/k.csv",
      "v400_manifest": "2026-09-30/v400_manifest.json",
      "v402_report": "2026-09-30/v402_report.json"
    }
  ]
}
```

```bash
PYTHONPATH=scripts python3 scripts/boat_edge_v406_offline_history_packager.py \
  --staging-dir /private/boat-history-staging \
  --index-json /private/boat-history-staging/index.json \
  --output-dir /private/boat-history-packaged
```

出力は `history.csv`、`history.manifest.json`、`history.audit.json`。入力を最初にすべて検証してから出力する。相対パスの `..`、絶対パス、シンボリックリンクでステージディレクトリ外へ抜けるパスを拒否する。**実データや権利原本はGitHubにcommitしない。**

## 新しいチェック内容

- V400 manifestの厳密なキー／権利レビュー自己申告／入力バイトSHA。
- V402日次報告のB/Kレース数と会場別内訳、除外数、未証明フラグ、同一日判定。
- 実際の6艇の進入コースと着順がそれぞれ1〜6の置換となるV400整合性、日付、艇番号と選手番号の重複、CSV順序。
- 日付重複や同一レースの二重計上を拒否。合成されたCSV SHA、各日K/manifest/V402報告SHAとレース数の明細（lineage）を監査出力に残す。
- V403の全日付・24場カバレッジを同梱。未知の日を「開催なし」と断言しない。
- V404 / V405にそのまま渡せるCSV＋manifestの形式。ただし後追いの結果データだけで**結果未見の予想証拠**にはならない。モデル採用判定には別途締切前Git初回保存時刻・SHA、未見凍結が必要。

## 検証と残るボトルネック

```bash
python3 -m unittest discover -s tests -p 'test_boat_edge_v406_offline_history_packager.py' -v
```

合成データの複数日統合・時刻・source SHA・日付・24場内訳・不正な保護期間・未レビュー権利・パス抜け・V404/V405との一致を回帰検査する。実5年分の処理時間・メモリ、実績的中率は**未検証**。特に出力CSVの全行を一時メモリに持つため、実利用前には権利確認済みの小規模サンプルによる負荷テストが必要。

公式使用範囲の質問原案・未送信の窓口は `docs/BOAT_EDGE_HISTORY_RIGHTS_INQUIRY_20261014.md`。問い合わせの回答・書面で認められた許諾がない間に一括スクレイピングへ進んではいけない。
