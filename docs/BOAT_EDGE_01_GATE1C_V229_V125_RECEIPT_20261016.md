# BOAT EDGE 01 / Gate 1C — V229 → V125監査レコードの将来分だけの整合性修正

## 確認した不具合

2026-10-16 JST、`data/site_ops_v220/gate1c_current.json` の限定サンプル監視に `historical_v125_revision_mismatch=1`。既存 `site_v136_historical_proof.check_historical_proof` は V125 `revisions[]` に原本`snapshot_sha256`・`saved_at`のほか、`first_saved_at`、`prediction_kind`、全Trueの`intrinsic_flags`を要求する。

一方、レビュー前の V229 同一実行で生成される `revisions[]` にはその3フィールドが存在せず、後段が厳密に fail-closed する。V229 の `pass=true` と厳格な初回 Git 監査PASSは別の意味であり、これは単なる表示上の誤解ではなく writer/checker 間の契約不一致。

## 修正の限界と非変更条件

- V229 の**これから作る新規**ファイルだけ、実際に検証済みの`first_saved_at`・`prediction_kind`・真偽チェック`intrinsic_flags`を同じレースの監査revisionへ格納する。pre-resultソースSHA・公式120オッズ・6艇・2〜10分・formal locked など既存V229の判定を緩めない。
- `check_historical_proof` 自身の厳格性は**変更しない**。テストでは同一Gitコミットの初回追加時刻/原本バイトを含む既存checkerまでPASSさせる。
- 既存の不完全なV125 `revisions[]`、既存予想、既存Git履歴を**後付けで増補・上書きしない**。古いデータは検証できないまま不明とする。今後別経路（例：V234）が同じ旧フィールド集合を出す場合は、当該経路の変更許可と独立検証がない限り自動的にPASSにしない。
- V229 source pinはworkflow上の**実Git blob SHA**に更新し、PR CIのpremerge pins + V229 fixtureがPASSすることを要件にする。
- 結果・配当・正式Freshを参照しない。サイト予想TopKやモデルのロジックは変更しない。
- この修正だけで①-1Cの取得適格分母も99%達成も証明されない。未保存レースの公式情報不足/実行空白は引き続き別ブロッカー。

## 受入れ

新規V229生成時のimmutable audit revisionに上記の3フィールドがあり、既存`site_v136_historical_proof`でGit-first-add照合PASS、改竄fixtureはfail closedであること。PR+main CI、実レース原本/監査/Pagesの事後実測を分けて判定する。
