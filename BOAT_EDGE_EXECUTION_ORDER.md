# BOAT EDGE — 完成までの固定実行順（優先順位ロック）

## Owner-approved override — 2026-11-01 (site/integration track)

The owner's latest explicit instruction supersedes the older gate-first sequence **for BOAT EDGE CLEAN main integration and site completion**. Current order: (1) safely retire the old website, redundant site code and duplicated PRs, (2) fix historical-race display, (3) consolidate existing navigation and BOATERS-inspired, original single-page prediction views (result above prediction, escape rate, top-three rate, winning methods, scenarios, leader-dependent placing rates), (4) test, CI, merge to main and verify actual Render production, (5) update an evidence-backed work status. Reuse existing fixes and workflows rather than creating a second automation pipeline. This override does not authorize copying third-party materials or unsupported numerical claims. Formal Fresh isolation, no result leakage, data provenance, and safe deploy/rollback remain mandatory. 02 accuracy research and data collection remain with their respective owners; main integration must not overwrite their independent PRs.

The 2026-10-16 gate sequence below remains as historical and specialized data-reliability acceptance criteria, not a blocker on explicitly reprioritized site and integration work. Do not mark its outstanding evidence gates complete without independent real-race evidence.


**Owner directive: 2026-10-16 JST / 現在の唯一の実行順序台帳。**

## 最終成果物（これ以外を目標にしない）
1. 締切前に固定した根拠付き予想の精度を継続して改善する。
2. 全国24場・各レースのTop3/Top5/Top10を一覧で見られる既存BOAT EDGEサイトを完成させる。
3. 取得・予想・保存・公開・検証・報告を自動運転し、安全な改善サイクルを作る。

## 毎回の作業開始ルール（必須）
- **このファイルの最初の未完了ゲート以外を新規開発しない。** 一度に追う問題は1件。01/02/03で同じ処理を重複実装しない。
- 依頼が現在のゲートと無関係なら「優先順位から外れるため一旦停止。現在のゲートは X」と明示し、現在のタスクに戻す。所有者が**優先順位変更を明示**した場合だけ本ファイルを更新して切り替える。一般的な「進めて」は現在のゲートを進める意味。
- 例外は、進行中のデータ破壊/締切後の予想改竄リスク、公開サイトの重大障害、セキュリティ・法令遵守・利用条件に関する緊急問題、または現ゲートの達成に必要な最小限の依存修正。例外時は証拠と理由を記載し、終わったら同じゲートに戻る。
- 既存の正常機能とデータは残す。サイトの全面作り直し、バージョン番号だけ増やす作業、重複監査、新規研究モデルの乱立、無関係な画面追加をしない。
- 「修正コードがある」「CI成功」「Pages成功」を実運用完了と呼ばない。差分、回帰テスト、main統合、締切前の実データ、初回Git blob SHA、公開ブラウザ表示を区別する。
- 利用権限が確認できない外部サイトの自動取得・学習・再配布はしない。正式Freshの保護を解除しない。結果後の予想再構成・上書き禁止。
- 本台帳のチェックは**証拠が確認できた場合だけ**更新。旧TODOは参照用とし、競合したら本台帳の実行順を優先する（正式Fresh等の安全制約は常に優先）。

## ゲート 1 — 【最優先・進行中】締切前データ取得と予想保存の安定化（01が担当）
**現在の作業はここから動かさない。** 02のモデル拡張、03の装飾/UI新機能、追加の5年研究ツール、オート開発機能は保留。

**2026-10-16 ゲート1A原因分類は完了。** [24Rの同一時点Git原本・Actions証拠](docs/BOAT_EDGE_GATE1A_20261015_24R_SOURCE_TIMELINE.md)を参照。観測140R、保存あり116R、欠測24R。9R=保存情報が揃うが凍結未保存、14R=Git記録で6艇展示未確認、1R=オッズ鮮度不足。公式側の未公表継続や9Rの全追加ガード適格は断定しない。1Bの修正コードは実装・統合済みであり、実運用改善は1Cで未検証。

- [x] **1A 原因分類**：2026-10-15の観測140R中、締切後に保存なし24Rを個別に再監査する。各Rについて締切、当時の公式公開状態、beforeinfo六艇、オッズ120通り、レース表/欠場、V230対象選択・実行契機、V229/V235初回Git保存と競合を突合。原因を「公式未公開」「通信失敗」「実行/選択漏れ」「保存/競合」「証拠条件不一致」「未確定」に分け、重複フラグを原因件数として数えない。後付けで予想を作らない。
**2026-10-16 追加診断：1A「分類」のみ完了。** 24R全件について締切2分前に存在した同一Gitコミット上のsource/odds/scratchを確認し、**9R=保存入力揃うのに凍結未保存（起動なし4R・入力確定前の実行3R・2分下限後の実行2R）、14R=6艇展示がrepo上published_wait、1R=公式オッズ鮮度不足**と分類した。証拠は[24R当日原本とActions実行時刻](docs/BOAT_EDGE_GATE1A_20261015_24R_SOURCE_TIMELINE.md#追加照合2026-10-16全24rを締切2分前のgitソース原本に揃えて分類)。**14Rの公式側公開状況／取り逃し原因は未確定**であり、9Rも全追加ガードの適格証明ではない。未解決の原因は1B以降も追跡し、凍結できない入力を後付けしない。ゲート1Bを開始するが**1Bは未完了**。

**2026-10-16 ゲート1B実装・CI完了（運用効果は1Cで未確認）**：PR [#422](https://github.com/ikst2512-eng/boat-edge/pull/422)でV235完了後の既存V229復旧契機を追加、PR [#423](https://github.com/ikst2512-eng/boat-edge/pull/423)で公式出走表/オッズの正常なGit保存直後に厳格なV220適格判定に基づき**既存V229のみ**を起動する予備経路を追加。V229の締切2〜10分・SHA・初回Git保存境界は一切緩めず、活動中/120秒クールダウン/不明状態は起動を拒否。PR #423のDevelopment CIと他3チェックPASS、main統合SHA `65f54fd908718ab5b69a6c8b3da776d46b2ca598`。**99%以上の保存率・実レース改善は未証明。** 次は1Cを同日開催レースの締切前固定原本から測る。もし改善が出なければ1Bへ戻す。

- [x] **1B 最小修正**：1Aの本番証拠で再現できた最大のボトルネックから**一件ずつ**修正。V230/V229/V235の既存修正（PR #402/#408/#411/#412/#413/#414/#416/#418/#419 等）を再実装しない。旧writer停止は唯一の所有者と被覆率を証明した後だけ。ソースの出所・SHA・締切チェックは緩めない。
- [ ] **1C 実レース再測定**：修正後、次の実運用で日別に「観測R/取得準備できた適格R/公式未公開R/安全停止R/通信失敗R/実行漏れR/保存R/初回Git原本SHA一致R」を集計。原因不明は残数として明記。誤った分母除外を防ぐため適格性は予め固定した証拠で定義し、除外Rも全部開示する。
- [ ] **1D 合格ゲート**：**連続3開催日**、独立に取得適格と証明できたRの締切前・初回Git blob SHA一致の保存成功率が**各日99%以上**。適格・除外・不明の件数を毎日開示。欠場・未公表等は正当な停止として扱い、恣意的に適格から除外しない。初回保存の書換えゼロ、未解決競合ゼロ。公開Pagesで同一レースのTop3/5/10をChromium＋WebKitで確認し、実機Safariが必要なUI完了は別判定。失敗があれば1Aに戻す。

**開始時点の事実（2026-10-16 01:36 JSTの読み取り値）**：10/15の観測対象140R中 snapshotあり116R、締切後なし24R、snapshot+監査SHA一致114R、V229同時原子的保存証拠一致108R。未保存24Rのうち23Rに1つ以上のソース不足フラグ、1Rは観測不足。**23Rが同じ単一原因と確定したわけではない。** 10/16の最初の監視対象は鳴門1R 08:20開始予定。これは過去日の診断であり現在の正常稼働・修正効果を示さない。

## ゲート 2 — 同一条件で予想精度を測定・改善（02が担当）
**ゲート1合格後に本格着手**。既存の有効な締切前・初回Git固定予想の読取りと研究設計は補助として許すが、ゲート1を遅らせる実装はしない。

- [ ] 現行モデルの同一コホートTop3/5/10、1着、欠場、見送り、日別対象件数を事前定義して基準値を出す。
- [ ] 既存で権利確認済みの履歴・特徴量のみから訓練用データを整備。5年実データは利用条件確認後、時点情報と結果情報の分離を保証して収集する。実データ0件の研究コードを精度改善扱いしない。
- [ ] 現行モデル対候補を同一レース・同一買い目点数、結果未見・締切前固定で複数日比較。小標本や自己検証で採用せず、未検証の新モデルを本番へ入れない。
- [ ] 02が改善エビデンスを提示、01が安全な本番昇格をレビュー、03には表示契約のみ連携。

**合格条件**：現行モデルの実測基準値が追跡可能で、改善モデルを採用する場合は未見・同条件・複数日の検証で優位性が示されている。改善がなければ現行モデルを維持して次へ進む。

## ゲート 3 — 24場予想一覧サイトの完成（03が担当）
**ゲート2の基準値確認後**、既存サイトを改良する。ゲート1合格判定に必要なレース選択・保存TopK確認だけはゲート1中に行ってよい。

- [ ] 24場の開催レースを日時・場・R・締切・状態と共に一覧表示。
- [ ] 同じ画面導線で締切前保存済みTop3/Top5/Top10、6艇、展示、欠場、情報鮮度を確認可能にする。
- [ ] 結果待ち/的中/不的中/対象外を事前固定券と独立確認済み結果のある場合だけ表示する。
- [ ] Pagesの公開コミットSHAと保存原本一致を確認し、iPhone Safari実機の主要導線を検証。欠測時は誤った買い目を表示しない。

**合格条件**：通常のiPhone操作で「24場一覧→レース→予想→結果」の導線が一通り通り、必要証拠と画面表示が一致する。

## ゲート 4 — 自動運用・安全な改善ループ（01統合、02精度、03表示）
- [ ] データ取得→予想→締切前Git凍結→Pages公開→保存後の結果照合→日次精度レポートを定常運転する。
- [ ] 適格な失敗の再試行、失敗通知、原因分類、古いwriter/不要cron整理。定期Actions実行を「AI自律コード開発」と混同しない。
- [ ] 新モデルは研究環境で同条件未見評価→承認済み昇格だけ本番反映し、悪化時は安全に元へ戻せるようにする。

**合格条件**：人手の定期操作なしで複数日動作し、障害と精度実測を追跡できる。必要以上の自動コード変更は導入しない。

## 次の一手と毎回の報告形式
**次の一手（固定）**：ゲート1C、修正後の10/16実開催で取得適格/保存/初回Git SHAの件数を締切後に実測する。対象・未公開・安全停止・原因不明を全件開示。未達なら1Bへ戻る。精度研究/新UI/自走化には進まない。

毎回、以下の5項目だけを先に報告する：
1. 今のゲート／次の1件
2. 今回実際に変更・検証したこと（PR/SHA/実レース証拠）
3. 取得対象・適格・保存・SHA一致・不明の件数
4. まだ解決できないこと
5. 次に行う同一ゲート内の作業

## 参照
- 既存統括: `BOAT_EDGE_MASTER_TODO.md`（履歴/詳細、実行順は本台帳）
- `AGENTS.md`（安全・01/02/03責務）
- `data/site_ops_v220/current.json`（当日の観測値。ステータスは日時を必ず確認）
- `data/formal_status.json`（正式Freshロックの一次情報）
