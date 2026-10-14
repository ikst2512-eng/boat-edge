# BOAT EDGE｜過去5年の競走成績・番組表データ利用範囲の照会事項（未送信）

更新: 2026-10-14 JST。研究専用。許諾取得済みとは**絶対に記録しない**。

## 公式一次情報と確実に確認できた窓口

- 公式データページ: https://www.boatrace.jp/owpc/pc/extra/data/download.html （レーサー期別LZH、全国24場の競走成績K・番組表Bの各ダウンロード入口）
- 公式サイトポリシー: https://www.boatrace.jp/owsp/sp/extra/policy.html （本サイトのコンテンツの権利、無断での利用やサーバー運営に支障を与える大量アクセスへの制限。ダウンロード公開は機械学習・予測サイトでの使用許諾の根拠にならない）
- 公式問い合わせ案内: https://www.boatrace.jp/owpc/pc/support/opinion 。**公式WEBについて 03-5539-8696、10:00〜18:00** と案内。ページ内意見フォームは**質問等には返信できない**旨が明記されているため、条件照会は電話で担当窓口・書面照会先を確認するのが合理的。**電話・フォーム送信は行っていない**。

## 電話窓口で確認すべき内容

BOAT EDGEは、競走成績K・番組Bの2021-10-01〜2026-09-30を対象に、(1)研究用ローカル保存、(2)自動一括取得の可否・許容速度、(3)機械学習・統計的特徴量への利用、(4)公開予想サイトの数値・モデル重みとしての利用（広告/収益化の有無が条件に影響するか）、(5)原データ・派生集計・モデルの再配布、(6)著作権以外の契約/データベース利用条件、(7)レース別締切前番組の更新履歴・公表時刻証拠、(8)公式から提供可能な日次B/Kデータの保有年次と欠測、(9)費用と契約窓口について質問する。

**照会用簡潔文面（未送信）**

> BOAT RACE公式の「競走成績ダウンロード」「番組表ダウンロード」の利用範囲について伺います。2021年10月〜2026年9月の約5年分を、民間の統計・機械学習によるボートレース予想研究に利用し、将来はウェブサイト上で予想確率・集計値を表示する予定です。K/Bアーカイブの自動取得・ローカル保存・統計解析・学習・派生集計の公開、商用利用の可否と必要な許諾・契約、アクセス制限・費用、担当窓口をご教示いただけますか。元データ自体の再配布は予定しておらず、回答をいただくまで大量取得は控えます。

## 回答の監査記録テンプレート

記録日時、窓口部署・担当者（公開しない）、確認された対象データ/年月、取得方法、許容レート/日量、ローカル保管許可、機械学習利用許可、サイト公開許可、商用許可、派生集計/学習済み重みの扱い、第三者提供条件、書面許諾の原本ハッシュ、失効/更新条件、未回答事項を分けて記録する。**口頭の曖昧な返答を権利承認としてシステムの `rights_review_status` に反映しない。**

BOAT EDGE正式Freshの結果ロックは引き続き0/100。V400〜V405は合成テストと研究コードだけで、元の実結果0R、許諾0件。


## 2026-10-14 外部データ実在調査（公式B/K以外）

公式B/Kだけに依存せず、**実際にGitHubコネクターから公開CSVの存在・先頭列・行数・Git blob SHAを検証**した。公開結果を本番にコピー・保存・再配布していない。Formal Freshの2026-10-01以降は閲覧していない。

| 候補 | 実在確認 | 仕様・不足 |
| --- | --- | --- |
| BoatraceCSV: `data/programs/race_cards/2026/09/30.csv` | **存在**、145データ行（表示上）、181,134B、blob SHA `2f6e8a87c8b22c65093a5b4443682117eedf91a3` | `レースコード`、`艇N_登録番号`、全国/当地/モーター/節間成績。過去5年全域ではない |
| BoatraceCSV: `data/previews/stt/2026/09/30.csv` | **存在**、145データ行、16,360B、blob SHA `024cb7dbe81138001cf211421a275d47da47a0d1` | `取得日時` がJSTで含まれる。**時刻の列があることと締切前保存の独立認証は別** |
| BoatraceCSV: `data/results/realtime/2026/09/30.csv` | **存在**、145データ行、35,984B、blob SHA `9b60f5a6e7ccf9d02e0dc9ff6e3d08bdc039b623` | 6着までの艇番と実進入コース、取得日時。Formal Freshの10/1以降は見ない |
| BoatraceCSV: `race_cards/2025/05/03.csv` | **存在**、194データ行、297,056B、blob SHA `a118883aab7db5c0468853e2cbab674d409c6c84` | 2025年からの公開ソースで、2021〜24年の同パスは未確認 |
| BoatraceCSV: `race_cards/2024/09/30.csv`、`2023/09/30.csv`、`2022/09/30.csv`、`2021/10/01.csv` | **このパスでは4件ともNOT_FOUND** | 5年履歴の全期間をこの単一ソースで埋められると主張しない |
| BoatraceCSV: `results/realtime/2025/09/30.csv` | **このパスではNOT_FOUND** | 取得開始時期の制約。2026/9/30が存在することは2025全域の存在証明ではない |

公開元: https://github.com/BoatraceCSV/boatracecsv.github.io
仕様: https://boatracecsv.github.io/docs/data/
番組表仕様: https://github.com/BoatraceCSV/boatracecsv.github.io/blob/main/docs/data/programs.md
結果仕様: https://github.com/BoatraceCSV/boatracecsv.github.io/blob/main/docs/data/results.md

その他の代替候補:
- **BR-STAT** https://br-stat.jp/data-source : 2021年1月から約28.8万レース保有と公表。ただし公開バルクCSV/API、再利用ライセンスは未確認。自サイトの内部DBがそのまま外部配布されると推測しない。
- **ryo100794/boat** https://github.com/ryo100794/boat : 10年B/KバックフィルCLIとSQLite構造の公開ソース。これは**コード**であり、許諾済みの10年分データセットではない。既存V407/V408と機能が重なるので丸ごと移植しない。
- **atsuki-3590/boatrace_download** https://github.com/atsuki-3590/boatrace_download : B/K解析とCSV変換コード。V407/V408と重複するため、フォーマット検証時の参考に限定する。

### 02の次の接続先（実装判断）

1. **直近データ**: BoatraceCSVの `race_cards` + `previews/stt` は同じ12桁レースコードでJOIN可能。既存の予想保存V235の結果未見証拠と結合して、取得日時が締切前の特徴量だけを別の研究検証で比較する。ただし01の保存パイプラインを02が変更しない。
2. **5年履歴**: 2021〜24年の不足は公式B/Kの許諾済みオフライン変換か、独立に許諾・実データが確認できた別の提供元で補う。**欠測を水増し・偽装しない**。
3. **結果・精度**: 2026-10-01以降のFormal Fresh結果はロックを守り、解錠前にはアクセス・採点しない。2026-09-30以前の歴史的結果を利用する場合も元の公開時刻・権利・出走表のas-of証拠を明示し、未見的中率の証拠に偽装しない。
4. **許諾**: READMEのMIT表記はコードに関する表記で、競走結果の二次利用許諾を自動で証明しない。BoatraceCSVの管理者と公式の権利者に「非公開学習・派生統計・商用公開予想・生CSV再配布の可否」を別々に照会する。問い合わせはまだ未送信。

この調査により「外部に実CSVがあるか」は**YES**、「5年分すべてがこのソースでそろうか」は**NO/未確認**、「BOAT EDGEへの二次利用許諾」は**未確認**と区別できた。


## 2026-10-14 追加ウェブ調査・優先順位確定

一次ソース再確認:
- BoatraceCSV データ一覧 https://boatracecsv.github.io/docs/data/ : 12桁レースコードでJOIN可能。race_cards / waku10 / recent_national / recent_local / motor_stats / previews(tkz,stt,sui,original_exhibition) / results(realtime,payouts)。
- BoatraceCSV previews https://github.com/BoatraceCSV/boatracecsv.github.io/blob/main/docs/data/previews.md : 締切5分前を狙う5分間隔の収集で、取得日時と締切時刻を別々に記録。保存列だけでは時点の独立証明は完成しない。Git commitや取得ログと照合。
- BoatraceCSV results https://boatracecsv.github.io/docs/data/results.html : 実進入・着順・払戻。締切後のデータであるため、特徴量には絶対に使わず、許諾済みの非Formal Fresh研究結果検証のみ。
- BOAT RACE公式 https://www.boatrace.jp/owpc/pc/extra/data/download.html : 24場番組表・競走成績B/K、選手期別成績の公開配布。公開配布とAI学習・商用二次利用の許諾は別。
- BR-STAT https://br-stat.jp/data-source : 2021年1月以降約288,000レース・全24場と公表。内部PostgreSQL保有の説明であり、一般向け一括CSV/APIや利用許諾は未確認。
- BoatraceCSV fun-site https://github.com/BoatraceCSV/fun-site/blob/main/docs/data-sources.md : 実運用でGitHub PagesのCSVをHTTPフォールバックとして使用している具体例。これもBOAT EDGEへの権利移転・保証ではない。

**研究実装の固定判断**:
1. 2026-09-30以前の実データ候補を最優先。Formal Fresh 2026-10-01以降の結果・払戻・combined endpointにアクセスしない。
2. まずBoatraceCSVのrace_cards, previews/stt, tkz, sui, original_exhibitionの列・取得日時・締切時刻・Git時刻を検証する。単に日付が一致しても予想時点の特徴量として採用しない。
3. 2021〜2024年はBoatraceCSVの同一race_cardsパスが未確認であり、公式B/Kまたは別の明示許諾ソースで補完する。存在しないCSVを推測して埋めない。
4. 本番投入前に、第三者CSVの権利、公式一次データの利用条件、商用予想サイトでの表示、派生モデル学習、再配布をそれぞれ確認する。MIT表記だけで元データの再利用権を断定しない。
5. Top3/5/10改善認定は、既存モデルと同一レース・同一予想時点・同一除外規則で、結果未見の保存予想を比較してから。過去結果の後付け検証は別ラベル。
6. 01の自動予想保存と03の画面には02から介入しない。研究PR #253はドラフトを維持する。

**今回の調査はソース確認と方針の確定であり、5年分の実データ取込完了、利用許諾取得、予測改善の実証を意味しない。**


## 2026-10-14 現物CSV追加検証（BoatraceCSV、研究用・2026-09-30）

GitHubの公開リポジトリの実ファイルを参照して列構成とレコード数を確認。件数は各CSVのヘッダ以外の行数であり、**異種CSV間のJOIN成功件数ではない**。ライセンス未確定のためBOAT EDGE側へ生データの複製・結果の再配布・モデル学習はしていない。

| 種別 | 実ファイル | データ行 | Git blob SHA |
|---|---|---:|---|
| 出走表 | `data/programs/race_cards/2026/09/30.csv` | 145 | `2f6e8a87c8b22c65093a5b4443682117eedf91a3` |
| 展示進入/ST | `data/previews/stt/2026/09/30.csv` | 145 | `024cb7dbe81138001cf211421a275d47da47a0d1` |
| 展示タイム/チルト | `data/previews/tkz/2026/09/30.csv` | 144 | `21cb7f27d5e2312f89315a68d88f3cd9f57a3fbb` |
| 気象 | `data/previews/sui/2026/09/30.csv` | 144 | `186c8a797d8ee43fc4f4a194ab37b13dd7305773` |
| オリジナル展示 | `data/previews/original_exhibition/2026/09/30.csv` | 132 | `7e2eca242dc719d0411935ccc86c771947f86cf5` |
| 開催・レース名 | `data/programs/title/2026/09/30.csv` | 144 | `57db4cca732e8088ff82b697f0f457c08045323f` |
| 競走結果（過去日・研究評価のみ） | `data/results/realtime/2026/09/30.csv` | 145 | `9b60f5a6e7ccf9d02e0dc9ff6e3d08bdc039b623` |

重要な仕様上の注意:
- `previews` の共通6列はレースコード・レース日・場・レース回・締切時刻・**取得日時(JST)**。直前データを採用するには取得日時が締切より前であることに加え、必要に応じて当時のGit初回保存・実行ログの証拠を要求する。
- `original_exhibition` は会場別に項目が違う。江戸川は配信無し、桐生は「半周ラップ」、住之江・尼崎・徳山は2項目。**一周/まわり足/直線の3項目が必ず揃うと仮定しない**。132件という数値だけで障害と断定しない。
- `tkz` と `sui` の144行、`stt` の145行を「全レース一致」とみなさない。実際のレースキー集合の積集合・欠落理由・重複・時間整合を確認するまで予測用の完全な結合と認定しない。
- `results` は後出し情報。予測特徴量に一切混ぜず、Formal Fresh以外の明示許諾済み履歴評価にのみ使用する。
- 直近CSVの存在は5年間の連続カバレッジ、再利用許諾、独立したas-of時刻の証明を意味しない。

出典: https://github.com/BoatraceCSV/boatracecsv.github.io/blob/main/docs/data/previews.md および https://github.com/BoatraceCSV/boatracecsv.github.io/blob/main/docs/data/programs.md 。これらの公開仕様を根拠に、01・03を変更せず02のデータ優先順位を固定する。


## 2026-10-14 CI確定・実装状況

- V409追加の最新テストを含む GitHub Actions #38466913960 は **SUCCESS**（head `beb35c86eee51b50ddfa055ad75bfff07d485fc3`）。
- GitHub比較で研究ブランチは main に対して **ahead 87 / behind 49**、差分31ファイル。大半は研究専用の新規ファイル、既存の変更ファイルは `.github/workflows/boat-edge-development-ci.yml`。このため main 更新の衝突を避け、PR #253 はドラフトのまま。mergeableは照会時点で false だが、変更ファイル一覧だけでは具体的な競合ハンクを特定できない。
- V409は **許諾済みのローカルCSVを受け取って検証する実装**。GitHub上の公開CSVを研究リポジトリへ取り込んだものではない。実CSVでの照合件数、未見Top3/5/10の実測は未達。
- V409で同一レースの stt/tkz/sui/original_exhibition 4ソースの時刻適格な積集合を算出。取得時刻のみで予想時点のGit証跡まで証明できるとは扱わない。


## 実CSVレースキーJOIN実測（2026-09-30、2026-10-14調査）

GitHub公開リポジトリの**実CSV本文**を読み取り、CSVパーサでレコードを数え、`レースコード`をキーに照合。全て2026-09-30のファイルのみを対象。結果・払戻CSVは**取得せず**、Formal Freshの2026-10-01以降にはアクセスしていない。

- 出走表 `race_cards`: **144ユニークR**（過去の145行報告は改行の数え方による誤り。144Rに訂正）
- 開催情報 `title`: **144/144**一致
- 展示進入/ST `stt`: **144/144**一致、全144件でCSV上の取得日時が締切前
- 展示タイム/チルト `tkz`: **144/144**一致、全144件でCSV上の取得日時が締切前
- 風・波 `sui`: **144/144**一致、全144件でCSV上の取得日時が締切前
- オリジナル展示 `original_exhibition`: **132/144**一致、132件のCSV上の取得日時が締切前
- **4プレビュー同一レースの締切前時刻積集合 = 132/144R (91.67%)**、`stt+tkz+sui`の3プレビュー積集合 = **144/144R (100%)**
- オリ展の欠落12Rはすべて**江戸川（場コード03）の1R〜12R**。ソースの会場別配信仕様と整合し、他会場の欠損として扱わない。
- 出走表Git blob `2f6e8a87c8b22c65093a5b4443682117eedf91a3`、stt `024cb7dbe81138001cf211421a275d47da47a0d1`、tkz `21cb7f27d5e2312f89315a68d88f3cd9f57a3fbb`、sui `186c8a797d8ee43fc4f4a194ab37b13dd7305773`、original `7e2eca242dc719d0411935ccc86c771947f86cf5`、title `57db4cca732e8088ff82b697f0f457c08045323f`。
- 取得日時の列を検査したのであって、各ファイルが締切前にGitで公開されていたことや、当時のモデル予想が結果未見で凍結されたことまでは**未検証**。よって的中率向上や正式Fresh PASSを主張しない。
- 調査は公開内容の読み取り・集計のみ。元CSVを研究リポジトリに再配布せず、モデル学習にも利用していない。権利確認が必要。

V409はローカル許諾済みファイルを受け取る別のオフライン監査実装であり、今回の直接読取による集計と混同しない。
