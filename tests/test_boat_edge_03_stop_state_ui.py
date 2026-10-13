"""03 UI contract: paused or unsynced tickets must not look purchasable.

Static source assertions deliberately avoid loading real race/results endpoints.
They protect presentation guards only; no prediction or Fresh mutation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "assets" / "boat_edge_v207_first_prediction.js").read_text(encoding="utf-8")


def test_stopped_tickets_hidden_and_no_stale_race_rows():
    assert "const stop=st.kind==='stop'||pendingScratch||!ticketViewSynced||!rowOK" in JS
    assert "if(stop){const w=document.createElement('div')" in JS
    assert "else rows.slice(0,count).forEach" in JS
    assert "list.replaceChildren()" in JS
    assert "box.dataset.status=st.kind" in JS


def test_stopped_allocation_and_odds_are_not_actionable():
    assert "stop?'配分：買い目を停止・未確認のため非表示'" in JS
    assert "stop?'公式オッズ・想定払戻：買い目停止・未確認のため非表示'" in JS
    assert "前レースの買い目は表示しません" in JS
    assert "fresh=Boolean(sum.fresh&&!settled&&proof?.quality==='verified')" in JS


def test_topk_controls_hidden_when_stopped():
    for threshold in ("rows.length<5", "rows.length<10"):
        assert "stop||" + threshold in JS
    assert "all.hidden=stop" in JS
