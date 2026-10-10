# BOAT EDGE CURRENT TODO

Updated: 2026-10-10
V134 repaired: SITE_REFERENCE 2026-10-09+ exact per-race SHA audit; never read formal results.

## CURRENT
- UI: V133 (repository state as recorded)
- Latest model/formal freeze is NOT certified by this TODO.
- Official V185 prospective freeze requires pre-deadline immutable Git evidence.
- Browser display and model accuracy are separate certification gates.
- Site snapshot count: 145; SHA-verified audits: 144; settled reference histories: 140.
- 🎯 indicator strings present in JS: true; Safari confirmation: false.
- Formal state recorded as of: 2026-10-08 (may be stale).
- Formal guards (recorded): results_seen=False, unlock=False, scoring=False.

## ACTIVE TODO — priority order
1. [ ] FINAL_15M予想の個別監査SHAと保存時刻を確認する。
2. [ ] Safariで🎯的中・不的中・判定対象外を実機確認（コード検査だけではPASSにしない）。
4. [ ] V185未見Freshで3着抜け31R/2着抜け20Rの改善候補を検証。Top3・Top5・Top10、A頭・非1頭を別計測。
5. [ ] 進入実コース×1年/6か月/3か月と1×2壁・逃がし率の連動。
6. [ ] 3/4攻め艇と5/6受益艇の展開分離。
7. [ ] 直近節モーター、展示1周・まわり足・直線、展示ST差の個別検証。
8. [ ] 会場×季節/風/潮と当日既走LIVE水面。欠測補完はしない。
9. [ ] BOATERSと競艇日和の両方でオリ展照合。取得できない場合は明記。
10. [ ] 平均信頼度81.53と観測的中40%の意味を分離し表示を校正。
11. [ ] 的中/バランス/波乱の買い目重複を抑える候補を未見比較。

## WAITING / GATES
- Formal Fresh untouched until gate PASS. Site reference study != formal validation.
- Do not open formal result/payout/combined API or backfill prior predictions.
- No odds-based ranking or missing-feature imputation.
- Do not promote V180/V185 or any hypothesis before multi-day independent Fresh improvement.

## RECENT DONE
- [x] 4モード件数、V133固定のブラウザ・サーバーParity検査。

## TODO EVIDENCE
- data/site_todo_evidence.json
- data/site_learning/head_tail_rootcause_v196.json
- data/site_tail_shadow_v185/quality/20261010.json
- Source observations reflect site research only, not verified production accuracy.
- V109 payout repair is separately tracked; no historical stake allocations inferred.

## TODO GUARD
- ACTIVE contains only incomplete tasks. Browser completion is never inferred from JS text.


## PRESERVED HISTORICAL TODO / USER NOTES
Read-only history, not additional current-model certification.
- [x] V133 browser/server parity PASS for all four prediction modes.
- [x] V133 mode policy fixed at 的中重視10 / バランス10 / 波乱12・15・18 / 激絞り3.
- [x] Live V133 FINAL_15M snapshot + audit PASS — `20261008-01-03`.
- V109 replaces the legacy result collector without changing V108 UI.
- V109 treats confirmed + payout null as incomplete and refetches it.
- V109 payout parser supports ¥ / ￥ / 円.
- V109 backfills historical confirmed payout gaps from 2026-10-07.
- V109 keeps result/trifecta data factual; missing payout is never fabricated.
