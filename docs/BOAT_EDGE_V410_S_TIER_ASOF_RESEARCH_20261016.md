# BOAT EDGE 02 — V410 S級・相手補正Eloと他艇コース別着順（2026-10-16）

状態 **RESEARCH_ONLY / 0 real data / 0 licensed import / 0 accuracy improvement**。V400–V409の延長、PR #253のドラフト内に隔離。収集・本番・Formal Fresh・保存済み予想・01/03を変更しない。

## 実装
- `scripts/boat_edge_v410_s_prior_opponent_elo.py`
- `tests/test_boat_edge_v410_s_prior_opponent_elo.py`
- 既存Development CIにV410単独の合成フィクスチャ回帰テストを追加。新しいcron、収集ジョブ、出力ファイル書き込みは追加しない。

権利確認後に**オペレーターが別途ローカルで準備した**V400互換の `race_key,boat,racer_id,actual_course,finish,published_at` CSV・ハッシュmanifest、およびV404の**B-only**ターゲット6人・締切を入力する。V400で6艇・コース・着順・公開日時の整合性を検査し、同じターゲットの結果は仮に不正な早期タイムスタンプであっても除外する。2026-10-01以降のFormal Fresh対象はV404ターゲットバリデーターで拒否する。ユーザー本人が許諾を取得したことを、このmanifestだけで外部的に認証したとは扱わない。

## 算出する研究特徴量
1. 過去の同じレースで6艇全組15組の勝敗関係を一括評価する**相手比較Elo**。初期1500、K=24、1人につき他5人との勝敗誤差を平均する。レース内は更新前の全員の値を使用し、終了後に同時更新する。**コース・番組相手強度・地区などを因果的に補正し切ったレーティングではない**。
2. ターゲット6艇の選手の履歴件数、Elo値と6艇の平均との差。履歴0件の選手は **NULL** とし初期1500を観測値として出さない。比較対象に欠測があるとレース内相対Eloも NULL。
3. 「選手Aが過去に**実コースi**だったレースで、他の実コースjの艇が何着だったか」の観測数、1/2/3着件数。母数20R未満では2/3着率を出さない（観測数は記録）。**他艇の着順はその選手の因果効果とは限らず、独立の予想確率でもない**。

## 図式・使用制限

履歴 `published_at < target.deadline_jst` かつターゲット日の0〜1825暦日前に限定。TARGET B-only に `finish` や `actual_course` が混入したら拒否。第三者の競艇日和、ボートとデータ、BOATERS、艇国データバンクの独自指数・履歴本文を自動取得しない。公式のB/K提供もAI学習・公開サービスへの一般許可は未確認。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_v410_s_prior_opponent_elo.py' -v
python3 scripts/boat_edge_v410_s_prior_opponent_elo.py --history-csv /approved/operator_history.csv --history-manifest /approved/operator_manifest.json --b-only-target-json /approved/target_roster.json
```

**意図した今後の検証**: 許諾済みの実B/Kを時刻監査したら、Eloのみ追加した候補を既存モデルと「同一R・同一時点・同じTop3/5/10」で比較する。未見の事前凍結がなければ `NOT_PROVEN` と記録。V410は本番予測コードではない。STの四分位・モーター補正・本番120確率・実レース保存に自動接続しない。

## 利用権照会の窓口（2026-10-16確認）
- BOAT RACE公式データ: https://www.boatrace.jp/owpc/pc/extra/data/download.html
- BOAT RACE公式「ご意見・ご要望」: https://www.boatrace.jp/owpc/pc/support/opinion は質問への返信を約束せず、**WEBについて03-5539-8696（10:00–18:00）**に問い合わせ案内。権利・商用データ窓口の取り次ぎを依頼する。https://www.boatrace.jp/owsp/sp/extra/policy.html の私的利用範囲超の許諾制限を確認。
- Team-Nave BRDB-API https://www.team-nave.com/system/jp/products/brdbapi/ は、番組表・競走成績・選手期別データを扱い個人月額¥3,300（税込）、**営利・事業は別途ビジネスプラン契約**。問い合わせ先 support@team-nave.com https://www.team-nave.com/system/jp/business/ 。機械学習、加工派生結果、商用予想サイト公開、自動取得、長期保管、再配布、元のデータ権利者の許諾までを確認する。購入・送信は未実施。

未回答・未契約・未確認の権限は空欄のままにし、`OPERATOR_REVIEWED` を偽装しない。問い合わせ文面は既存 `docs/BOAT_EDGE_HISTORY_RIGHTS_INQUIRY_20261014.md` にあり、送信されていない。
