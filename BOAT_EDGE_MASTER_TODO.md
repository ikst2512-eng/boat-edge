# BOAT EDGE — MASTER TODO / 運用・予想・サイト統合

最終監査：2026-10-12 23時台 JST ／ 所有者が確認した完了条件だけを `[x]` にする。
このファイルは**人間が確認する統合TODO**。自動生成される `BOAT_EDGE_CURRENT_TODO.md`（サイト参考予想）と、完了済みの `BOAT_EDGE_AUTODEV_TASKS.md`（V240 UIタスク）とは別管理。旧TODOを上書き・削除しない。

## 絶対条件・完了判定
- **正式Freshを隔離**：正式の `results_seen=false`, `unlock=false`, `scoring=false`, `RESULT_UNLOCK_TOKEN=null` を維持。正式の結果・払戻・結果ページ・combined API を先に開かない。初回100Rの正式凍結や実験採用を捏造しない。
- **サイト参考研究と正式Freshは別物**。サイトの事後検証データを正式Freshの得点・証明に混ぜない。実コースを展示進入で代用しない。
- **予想後付け禁止**：レースID、締切、実入力、欠場、全買い目、モデルID、発行時刻、GitコミットとSHAを締切前に固定。結果後の書換え・バックフィルを不可とする。
- **予想とオッズの役割分離**：オッズで120通りの順位や予想確率を恣意的に操作しない。欠損値を平均やproxyで埋めない。相対重みを校正済み確率と呼ばない。
- **精度向上の採用条件**：同日・同レース・同点数で、結果未見の事前固定候補 vs 対照を独立照合し、日跨ぎでも改善が再現されるまで本番重みは変更しない。
- 各TODOの終了には **コミット/PR、テスト結果、実データ証拠、GitHub Pages公開、Safari表示（UIの場合）** を個別に記録。Actions `success` だけを完成証明にしない。

## P0 — 最優先：自走・安全・公開
- [x] **T00 統合TODOを保護された別ファイルに作成**：過去トークとGitHub監査を照合し、完了条件と参照先を確立。本項は計画保存だけを指し、各機能の完成は意味しない。
- [ ] **T01 Pages連続キャンセルの根本対策**：データだけの高頻度main更新が公開を巻き込む状況を測定。公開が必要な変更とデータ更新の仕組みを区別し、同一時点の最新UIコミットが公開されたことをSHA・時間で証明。V251の回復実行成功だけでは完了不可。
- [ ] **T02 古いコードの自動復元・重複スケジューラ防止**：V270修正を含む現行コードを確認。旧インストーラや競合する定期処理により予想・UI・証拠が巻き戻らないテストと運用ログを取る。
- [ ] **T03 締切15分前データ取得率を実測で改善**：全6艇、公式beforeinfo、欠場取消、実進入、120通りの公式3連単オッズ、展示/ST、鮮度、各取得証拠をレースごとに監査。0–15分対象の取得成功/公開待ち/エラーを日別に集計。未取得・遅延は未取得表示、当該判断は停止。
- [ ] **T04 オッズ120通りの独立検証**：公式HTMLバイトSHA・公式DOM証明・全120組の正数/重複なし・発行時刻・選択券との一致を本番最新レースで再監査。80〜119通りの不完全値を有効扱いしない。
- [ ] **T05 AIによるUI継続開発の実働証明**：V240のA01–A28はチェック済みでキュー空。API secretの有無は漏洩させず、Codex実行→実際の差分→独立テスト→コミット→Pages→Safari確認の成功事例を監査。次の限定的タスクは明示的に承認されたキューで管理し、UI以外の自動編集を許さない。
- [ ] **T06 正式Freshの親・候補・日付・証拠を照合**：10/01初期案件のブロッカーを維持して監査し、現在の候補V1.21.33と以前の候補とのSHA変更理由を追跡。正式First100 `0/100` を `144`/ `149`件のサイトCORE7候補で代用しない。独立Run1/Run2・SHAバイト一致がない状態では解錠不可。

## P1 — 予想精度とデータ整合性
- [ ] **T07 同一10点の3着抜け改善研究**：V253の不的中原因（頭・2着・3着）を事前固定コホートごとに分類。V254の3着候補とV240の2着候補を現行10点と同一R・同一10点で比較。小標本は「未証明」。
- [ ] **T08 10〜20倍の未見実測評価**：確定配当10〜20倍帯と締切前オッズ帯を混同しない。Top3/5/10、1着、非1頭、3連単、点数、予算、払戻ROIは別計測。オッズを根拠に予想順位を後付けしない。
- [ ] **T09 BOATERS＋競艇日和の独立オリ展照合**：1周、まわり足、直線、展示タイム、展示STを**2サイト別に証拠紐付け**。公式値は第三者2ソースの代用禁止。未取得は取得できていないと表示。
- [ ] **T10 コース・展開の特徴量検証**：実進入、選手の1年/6ヶ月/3ヶ月実コース、1コース逃げ耐性、2コース逃がし/壁、3・4の攻めと5・6受益を、個別未見試験後に採用判断。
- [ ] **T11 水面・モーター・展示を正しく接続**：直近節と今節のモーター/部品交換、風/波/潮/会場季節、当日の**終了済みレースのみ**のLIVE水面、オリ展各項目。欠測補完はしない。
- [ ] **T12 120通りの確率分布と信頼度を区別**：現行サイト参考予想は上位20候補であり全120通りの確率分布は未実装。買い目10点内の正規化相対重みを「的中確率」と表示しない。頭信頼度と3連単TopK信頼度を別扱いする。
- [ ] **T13 未見研究の継続と昇格防止**：V185/V199/V236/V239/V240/V254の検証で、締切前凍結・勝敗の独立取得・一致した母数・SHA・複数日で確認。未証明候補は本番モデルに反映しない。

## P2 — サイト体験・仮想運用
- [ ] **T14 iPhone Safariの画面整理**：「レース選択 → 6艇比較 → 直前情報・欠場・オッズ → 予想Top3/5/10・展開 → 的中結果」を分かりやすく集約。不要な旧パネルと多重JS/CSSの副作用を削減。正確な入力/買い目は保持。Safariで見て初めて完了。
- [ ] **T15 🎯的中・不的中・結果待ちを実機証明**：締切前SHA固定の買い目と確定公式結果だけで表示。対象外・未確認を的中として表示しない。表示コードに文字列があるだけでは完了にしない。
- [ ] **T16 1日5万円の仮想運用**：現状の仮想購入0件を「収益が出た」と呼ばない。校正ゲート・見送り理由・当日残高・実保存した仮想買い目・決済を監査。**実購入は禁止**。
- [ ] **T17 状態表示の鮮度統一**：`data/site_current_state.json` の古い `as_of` や内蔵formal情報より、最新 `data/formal_status.json` を優先。更新時刻・データ元・参考/正式の区分を表示。古い数字は最新値として表示しない。
- [ ] **T18 UI/分析/運用の完了判定を分離**：コードテスト、予想実測、公式証拠、Pages公開、Safari実機の各ゲートを見える化。問題が解消した証拠でのみチェック。

## 2026-10-12 23時台の監査スナップショット（今後の最新値ではない）
- 現行サイト `data/formal_status.json` 23:26 JST：サイトの5ソース候補は利用可、CORE7適格149R。ただし **formalFirst100.races=0**、結果未見/解錠/採点すべて false。親SHA `11e6d19c...a747db`、候補SHA `30c0c7b5...030a41f1`。
- V236 サイト参考研究（28R）：10点9/28（32.14%）、15点12/28（42.86%）。点数が違うので改善証明ではない。
- V255 独立に検証されたサイトの頭予想（2日41R）：20/41（48.78%）。これはV236と同じ母数ではなく、正式Freshでもない。
- V240研究では10点候補の標本が小さく、改善未証明。V254も新しい3着候補の未見標本が不足。
- 仮想予算：5万円／当日仮想購入0件。収益性未証明。
- Pages成功あり、同時にキャンセルが繰返し発生。Safari実画面の完全確認は未実施。
- `data/site_current_state.json` には2026-10-08時点の内蔵正式情報が残るため、現行正式ゲートの一次情報として使わない。

## 検証の参照先
- `data/formal_status.json`, `data/model_status.json`, `data/site_prediction_policy.json`
- `data/site_autopilot/v236_score_current.json`, `data/site_autopilot/v240_score_current.json`, `data/site_autopilot/v254_pre_current.json`, `data/site_autopilot/v255_confidence_current.json`
- `data/site_ops_v220/current.json`, `data/site_paper_sim/current.json`, `data/site_autovalidation/current.json`
- GitHub Actions / Pages, `BOAT_EDGE_CURRENT_TODO.md`, `BOAT_EDGE_AUTODEV_TASKS.md`

> 注：このマスターTODOを追加しただけでは、ここに挙げた運用問題の修正が完了したことにはならない。各チェックは実際の証拠で個別更新する。

## 2026-10-13 01時台の実作業・追加監査（ここは実装証拠。完了チェックとは別）

- **V276 / PR #48 マージ済み**：古い `site_current_state.json` の日付を最新正式状態と混同しない表示に修正。正式 `formal_status.json` の取得時刻と鮮度を独立表示。サイト専用・予測ロジック変更なし。V276 CI PASS。T17はSafari確認未実施なので未完了。
- **V277 / PR #50 マージ済み**：GitHub Pagesキャンセルと最新UIの未公開状態を独立に照合する読取専用監査を導入。8件のオフラインテスト PASS。Pages構成の根本的な変更・連続キャンセル解消は未完了（T01）。
- **V278 / PR #51 マージ済み**：ユーザー明示依頼の安全なUI改善 A29–A33 をV240自走キューに登録。既存安全ゲートは維持。**GitHub Actions SUCCESSでもCodex編集ステップはSKIPPEDだった**ため、完全AI自走ができている証明ではない（T05）。
- **V279 / PR #55 マージ済み**：A29を直接実装。買い目表示を「相対配分%」にし、全120通りの校正済み的中確率ではないことを明示。既存の予想・買い目・公式オッズ・正式結果には変更なし。V279 CI PASS。A30–A33は未完了。
- **V280 / PR #58 マージ済み**：A29完了後にV278の監査が誤って失敗する条件を修正。A29→A33の単調な完了を検査し、正式未見ロックも確認。修正後CI PASS。
- **正式Freshの現況（2026-10-13 01:16 JST確認）**：formalFirst100=0/100、results_seen/unlock/scoring=false、TOKEN=null。10/13はPRE_RESULTで5ソース未揃い。サイト研究と正式Freshを混ぜず継続。
- **Pages現況**：成功デプロイは観測されているが、新たなmainへの細かい更新でキャンセルが継続。PR/Actions SUCCESSと実機Safari公開は別ゲート。
- **次のP0**：T01キャンセル抑制の実装、T03直前0–15分の実測確認、T05自動コード編集の権限/認証条件、T06親/候補の正式 provenance 復旧。いずれも根拠が揃うまで未完了のまま。

## V285–V286 publication and source integrity (2026-10-13 JST)

- **V285 / PR #67 — merged**: main と Pages 最終成功 head の主要UI 6パスの最終更新コミットSHAを直接照合。時刻だけで公開済みとは判定しない。新規6件と既存8件のテストPASS。read-only。Safari実機確認とPagesキャンセル根本解消は**未完**（T01）。
- **V286 / PR #69 — merged**: V216の5分間隔ワークフローの旧V215 gzip/base64埋め込み再インストール工程を削除。既存V265ソースを固定ハッシュで検証する読取専用工程に置換。V214締切前freeze・V211仮想select・後続settleの順序維持。新規3件とV265既存10件のテストPASS。旧経路の削減は確認済みだが、**リポジトリ全体の旧インストーラ廃止は未証明**（T02）。
- 正式Fresh：`formalFirst100.races=0`、`results_seen=false`、`unlock=false`、`scoring=false`、`RESULT_UNLOCK_TOKEN=null`（確認時刻 `2026-10-13 01:39 JST`）。2026-10-13の出走表132R/792艇は取得済み。5ソース未取得はこの時間帯では未確定; 締切15分前の実測が必要（T03）。
- V286 main CI `38280681075`: PASS。Pages `62a04ffb2fe6` の実行 `38280680138` は確認時点でpending。公開完了やSafari表示は未確認と区別する。

## V287 official predeadline six-boat completeness (2026-10-13 JST)

- **V287 / PR #73 (merged, main SHA `3c216a50da50ccbe4bad6e6855d50dfd577a1cce`)**: Previously, one official exhibition-time row or a single start-exhibition item could incorrectly mark the source as complete. Now `beforeinfo.status=ok` requires six unique boat numbers with exhibition times and six unique boat numbers with start-exhibition ST; otherwise `published_wait`. Retains exactly one bounded urgent retry in the final 0–15 minutes and original-source freeze protection. `six_boat_coverage` is saved as explicit evidence, with `beforeinfo_urgent_15m_partial` in health. Does not read results or change rankings.
- **Evidence**: branch V287 regression `38284149581` SUCCESS after repairing a test-detected ST pattern issue; main V287 `38284233417`, V272 `38284233317`, Development CI `38284233274`, and Pages `38284232389` all SUCCESS. Actual iPhone Safari visual QA is separate.
- **2026-10-12 site-only freeze coverage, not a formal Fresh result**: 104 observed matured races; 63 snapshots present, 41 not found after the deadline; 61 source files changed after predeadline evidence, therefore cannot treat present-day SHA mismatch as proof no freeze happened. Early missing later present: 38. The V229 atomic evidence match remains 0 in the observed report. These are diagnostic counts, not model accuracy improvements.
- **As of 2026-10-13 02:15 JST**: 132/132 race cards, 792 racer rows; no 0–15-minute decision windows yet. Beforeinfo `0/0` at that hour is not a missing-data failure. Start of first observed window: 08:20 JST for 鳴門1R (08:35 deadline), based on V220 current status.
- **Formal Fresh**: `formalFirst100.races=0`, `results_seen=false`, `unlock=false`, `scoring=false`, `RESULT_UNLOCK_TOKEN=null`. No formal result or payout access, no model promotion.
- **Open gates**: T03 stays **unchecked** until 0–15-minute actual completion/partial/error counts improve across real decision windows; T01 remains unchecked despite Pages successes until cancellation reduction and Safari review are verified; T07/T13 remain unproven until matched future 10-ticket cohorts.

## V290–V292 — 予想固定漏れの原因分解・実行契機強化（2026-10-13 JST）

- **V290 / PR #83 main `3f8892c1e10db7cd5c5389ef8f3125ca85cd83c9`**: V215の監視対象104Rのうち、10/12時点で締切後もスナップショット未発見41Rを分類。ソース不足の観測あり23R・不足の観測なし18R。最後の監視がV229凍結対象2〜10分前だったのは22R、うち不足の観測なし9R。非存在/未観測は、実行していたこと・ソース適格・予想精度の証明ではない。V220本番JSONでも同一件数を確認。main V220 Actions `38286645912` とV290 `38286646200` SUCCESS。
- **V291 / PR #84 main `dbdfb8827e6cfb7a0497310ed3f62f3e875a109e`**: 上記の分類をiPhone向けAutopilotの前日固定監査に連動。source-only、件数の相互整合を必須、未取得/不整合なら未確認表示。V291 main Actions `38286914526` SUCCESS。Safari目視は未検証。
- **GitHub Actions起動履歴の追加監査**: 2026-10-12 UTC 02–05時（日本時間11–14時）のV235/V229定期実行には約20分の空白が複数存在した。ジョブ所要時間は概ね数分であり、実行遅延を単純に長いジョブ実行だけで説明しない。現行V235にはその後collector成功イベントを契機にした起動変更が加わっているため、過去の状態を現在の稼働断定に使用しない。
- **V292 / PR #88 main `748e5291cc8be9887f4ae190eae928ba5ccbc408`**: 安全なV229 PRE_RESULT凍結監査に、mainの公式出走表collector成功・公式3連単オッズ取得成功後の`workflow_run`起動を追加。cron予定とimmutable write-once保持。failure/cancelled、fork・非mainを拒否。ブランチ・mainテストSUCCESS（`38287493864`, `38287573019`）。main反映直後の`38287590847`に`event=workflow_run`の実際の起動を確認。**起動成功と前締切固定の実際の増加は別証拠**。
- **正式Fresh**: 2026-10-13 02:56 JST時点`formalFirst100.races=0`、`results_seen=false`、`unlock=false`、`scoring=false`、`RESULT_UNLOCK_TOKEN=null`。正式解錠・結果の先読み・未証明モデル本番昇格はしていない。
- T01, T03, T05, T06, T07は依然**未完了**。次の監視で公式beforeinfo 6艇/全120オッズ/取消・欠場・凍結が揃った率、V229`workflow_run`完了、Pages実行成功とSafari実機を独立検証すること。
