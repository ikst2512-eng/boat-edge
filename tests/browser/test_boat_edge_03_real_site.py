#!/usr/bin/env python3
"""Read-only E2E: actual BOAT EDGE site and PRE_RESULT race files.

Both the repository preview and publicly deployed Pages can be exercised.
Live E2E has no mocks; separate HISTORICAL fixture simulates source readiness
using only saved result-unseen SITE snapshots, never a live prediction proof.
No outcome endpoints, payout data, formal predictions, or API/v1 calls.
Headless WebKit is NOT physical iPhone Safari certification.
"""
import argparse
import hashlib
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGES = "https://ikst2512-eng.github.io/boat-edge/index.html"
JST = timezone(timedelta(hours=9))

# Block before any network access to an outcome endpoint. UI tests may only
# exercise current, result-unseen PRE_RESULT inputs.
FORBIDDEN = (
    "/data/site_results/", "/data/formal_predictions/", "/data/formal/",
    "/data/site_prediction_history/", "/data/site_learning/",
    "/data/site_archive/", "/data/site_payout", "/results/", "/payout",
    "/api/v1/", "/result/", "combined", "settlement",
)




def probe_site_snapshot_evidence(context, target, key, deadline):
    """Read current SITE PRE_RESULT snapshot/audit receipts, never outcome data.

    This proves byte-SHA and V229 audit consistency, NOT the first Git commit,
    and it never equates predeadline live reference rankings with frozen picks.
    Only invoke for an eligible same-day race still before its JST deadline.
    """
    base = target.rsplit("/", 1)[0] + "/"
    snap_url = base + "data/site_prediction_snapshots/" + key + ".json"
    snap_res = context.request.get(snap_url, timeout=12000,
                                   headers={"Cache-Control": "no-store"})
    if snap_res.status == 404:
        return {"status": "NO_SITE_PREDEADLINE_SNAPSHOT", "first_git_commit_verified": False}
    if snap_res.status != 200:
        return {"status": "SNAPSHOT_FETCH_UNAVAILABLE",
                "http_status": snap_res.status, "first_git_commit_verified": False}
    raw = snap_res.body()
    sha = hashlib.sha256(raw).hexdigest()
    try:
        snap = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return {"status": "SNAPSHOT_INVALID_JSON", "first_git_commit_verified": False}
    if snap.get("race_key") != key or snap.get("snapshot_window") != "FINAL_15M" or any(
        (snap.get("guards") or {}).get(k) is not False
        for k in ("results_seen", "unlock", "scoring")
    ):
        return {"status": "SNAPSHOT_RACE_OR_GUARD_INVALID", "first_git_commit_verified": False}
    try:
        due = datetime.strptime(key[:8] + str(deadline), "%Y%m%d%H:%M").replace(tzinfo=JST)
        first = datetime.fromisoformat(str(snap["first_saved_at"]).replace("Z", "+00:00"))
        saved = datetime.fromisoformat(str(snap["saved_at"]).replace("Z", "+00:00"))
        if first.utcoffset() is None or saved.utcoffset() is None:
            raise ValueError("timezone required")
    except (KeyError, TypeError, ValueError, OverflowError):
        return {"status": "SNAPSHOT_TIME_INVALID", "first_git_commit_verified": False}
    if not (first <= saved < due and
            2 <= (due - first).total_seconds() / 60 <= 10):
        return {"status": "SNAPSHOT_OUTSIDE_PREDEADLINE_WINDOW",
                "first_git_commit_verified": False}
    top10 = [(x.get("combo") if isinstance(x, dict) else None) for x in
             (((snap.get("modes") or {}).get("hit") or {}).get("tickets") or [])[:10]]
    if len(top10) != 10 or len(set(top10)) != 10 or any(
        not re.fullmatch(r"[1-6]-[1-6]-[1-6]", x or "") or len(set(x.split("-"))) != 3
        for x in top10
    ):
        return {"status": "SNAPSHOT_TOP10_INVALID", "first_git_commit_verified": False}
    audit_res = context.request.get(
        base + "data/site_prediction_audit/" + key + ".json", timeout=12000,
        headers={"Cache-Control": "no-store"})
    evidence_res = context.request.get(
        base + "data/site_autopilot/v229_evidence/" + key + ".json", timeout=12000,
        headers={"Cache-Control": "no-store"})
    if audit_res.status != 200 or evidence_res.status != 200:
        return {"status": "SNAPSHOT_AUDIT_OR_V229_NOT_PUBLISHED",
                "snapshot_sha256": sha, "first_git_commit_verified": False}
    try:
        audit, proof = audit_res.json(), evidence_res.json()
    except (ValueError, TypeError):
        return {"status": "SNAPSHOT_AUDIT_INVALID_JSON", "first_git_commit_verified": False}
    # V125 normally includes an explicit UNSETTLED sentinel even before a
    # race starts. An empty-result sentinel is not an observed outcome.
    # Reject any other shape/content fail-closed: this probe must never treat
    # a post-result or noncanonical audit as PRE_RESULT freeze evidence.
    if "settlement" in audit:
        settlement = audit["settlement"]
        allowed = {"available", "winning_combo", "hit_any", "mode_hits", "payout"}
        valid_unsettled = (
            isinstance(settlement, dict)
            and set(settlement) == allowed
            and settlement.get("available") is False
            and settlement.get("winning_combo") is None
            and settlement.get("hit_any") is None
            and settlement.get("mode_hits") == {}
            and settlement.get("payout") is None
        )
        if not valid_unsettled:
            return {"status": "AUDIT_CONTAINS_OUTCOME_NOT_PRE_RESULT",
                    "first_git_commit_verified": False}
    if (audit.get("pass") is not True or audit.get("race_key") != key or
        audit.get("latest_snapshot_sha256") != sha or
        proof.get("race_key") != key or proof.get("snapshot_sha256") != sha or
        proof.get("schema") != "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1" or
        proof.get("scope") != "SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS" or
        proof.get("new_snapshot_created_this_run") is not True or
        proof.get("results_seen") is not False or
        proof.get("formal_fresh_unlock") is not False or proof.get("scoring") is not False or
        proof.get("snapshot_saved_at") != snap.get("saved_at")):
        return {"status": "SNAPSHOT_SHA_OR_V229_AUDIT_MISMATCH",
                "snapshot_sha256": sha, "first_git_commit_verified": False}
    return {"status": "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED",
            "snapshot_sha256": sha, "first_saved_at": snap["first_saved_at"],
            "saved_at": snap["saved_at"], "saved_top3": top10[:3],
            "saved_top5": top10[:5], "saved_top10": top10,
            "saved_top10_by_mode": {
                name: [item.get("combo") for item in (mode.get("tickets") or [])[:10]]
                for name, mode in (snap.get("modes") or {}).items()
                if isinstance(mode, dict)
            },
            "first_git_commit_verified": False}



def test_snapshot_evidence_contract_without_network():
    """Synthetic verifier regression: no real results or frozen claims."""
    key = "20261014-14-01"
    combos = ["1-2-3", "1-2-4", "1-2-5", "1-2-6", "1-3-2",
              "1-3-4", "1-3-5", "1-3-6", "1-4-2", "1-4-3"]
    snap = {
        "race_key": key, "snapshot_window": "FINAL_15M",
        "guards": {"results_seen": False, "unlock": False, "scoring": False},
        "first_saved_at": "2026-10-13T23:30:00+00:00",
        "saved_at": "2026-10-13T23:31:00+00:00",
        "modes": {"hit": {"tickets": [{"combo": x} for x in combos]}}
    }
    raw = json.dumps(snap, sort_keys=True).encode()
    sha = hashlib.sha256(raw).hexdigest()
    audit = {"race_key": key, "pass": True, "latest_snapshot_sha256": sha}
    proof = {
        "race_key": key, "snapshot_sha256": sha,
        "schema": "BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1",
        "scope": "SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS",
        "new_snapshot_created_this_run": True, "results_seen": False,
        "formal_fresh_unlock": False, "scoring": False,
        "snapshot_saved_at": snap["saved_at"]
    }
    class Response:
        def __init__(self, value):
            self.status = 404 if value is None else 200
            self.value = value
        def body(self):
            return self.value if isinstance(self.value, bytes) else json.dumps(self.value).encode()
        def json(self):
            return json.loads(self.body())
    class Request:
        def __init__(self, data):
            self.data = data
        def get(self, url, **_):
            return Response(self.data.get(url.split("/data/")[-1]))
    class Context:
        def __init__(self, data):
            self.request = Request(data)
    data = {
        "site_prediction_snapshots/" + key + ".json": raw,
        "site_prediction_audit/" + key + ".json": audit,
        "site_autopilot/v229_evidence/" + key + ".json": proof
    }
    check = lambda d: probe_site_snapshot_evidence(
        Context(d), "https://pages.example/index.html", key, "08:35")
    accepted = check(data)
    assert accepted["status"] == "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED"
    assert accepted["saved_top3"] == combos[:3]
    assert accepted["saved_top10"] == combos
    assert accepted["first_git_commit_verified"] is False
    assert check({})["status"] == "NO_SITE_PREDEADLINE_SNAPSHOT"
    assert check({**data, "site_prediction_audit/" + key + ".json":
                  {**audit, "latest_snapshot_sha256": "0" * 64}}
                 )["status"] == "SNAPSHOT_SHA_OR_V229_AUDIT_MISMATCH"
    assert check({**data, "site_prediction_audit/" + key + ".json":
                  {**audit, "settlement": {}}}
                 )["status"] == "AUDIT_CONTAINS_OUTCOME_NOT_PRE_RESULT"
    # V125 writes this unset sentinel before a race settles; it is not an outcome.
    sentinel = {"available": False, "winning_combo": None, "hit_any": None,
                "mode_hits": {}, "payout": None}
    fresh_audit = {**audit, "settlement": sentinel}
    still_pre = check({**data, "site_prediction_audit/" + key + ".json": fresh_audit})
    assert still_pre["status"] == "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED"
    assert still_pre["first_git_commit_verified"] is False
    # Reject any observed payout, result, unsupported field or unknown shape.
    for contaminated in (
        {**sentinel, "available": True},
        {**sentinel, "winning_combo": "1-2-3"},
        {**sentinel, "hit_any": False},
        {**sentinel, "mode_hits": {"hit": False}},
        {**sentinel, "payout": 0},
        {**sentinel, "unexpected": None},
        {"available": False},
        None,
        {},
    ):
        blocked = check({**data, "site_prediction_audit/" + key + ".json":
                         {**audit, "settlement": contaminated}})
        assert blocked["status"] == "AUDIT_CONTAINS_OUTCOME_NOT_PRE_RESULT", contaminated
    # A summary hint may be stale; invalid race paths and elapsed deadlines
    # are still excluded without touching result or payout sources.
    fixed_now = datetime(2026, 10, 14, 10, 55, tzinfo=JST)
    live_key = "20261014-14-05"
    stale = {
        "date": "2026-10-14",
        "venues": [{"jcd": "14", "venue": "鳴門", "races": [
            {"race_key": live_key, "file": "data/races/" + live_key + ".json",
             "racers_ready": True, "beforeinfo_status": "published_wait",
             "deadline": "11:20"},
            {"race_key": "20261014-14-01",
             "file": "data/races/20261014-14-01.json",
             "racers_ready": True, "beforeinfo_status": "ok",
             "deadline": "08:35"},
            {"race_key": "20261014-14-06", "file": "../data/site_results/bad.json",
             "racers_ready": True, "beforeinfo_status": "ok",
             "deadline": "11:45"}
        ]}]
    }
    candidates, reasons = choose_live_receipt_candidates(stale, fixed_now)
    assert [r["race_key"] for _, _, r in candidates] == [live_key]
    assert reasons["beforeinfo_missing"] == 1
    assert reasons["deadline_invalid_or_too_close"] == 1
    assert reasons["invalid_race"] == 1
    # When a source-verified frozen SITE final is available, it must be
    # preferred over a dynamic reference race during a live browser check.
    order = [
        (fixed_now + timedelta(minutes=4), None, {"race_key": "near-reference"}),
        (fixed_now + timedelta(minutes=8), None, {"race_key": "saved-final"}),
        (fixed_now + timedelta(minutes=10), None, {"race_key": "other-reference"}),
    ]
    ranked = prioritize_saved_final_candidates(order, {"saved-final": {}})
    assert [x[2]["race_key"] for x in ranked] == [
        "saved-final", "near-reference", "other-reference"
    ]
    assert [x[2]["race_key"] for x in prioritize_saved_final_candidates(order, {})] == [
        "near-reference", "saved-final", "other-reference"
    ]
    print("BOAT_EDGE_03_SYNTHETIC_SNAPSHOT_DIAGNOSTIC_REGRESSION_PASS", flush=True)


def choose_live_receipt_candidates(catalog, now):
    """Use same-day race keys and future deadlines; catalog source status is only a hint."""
    choices = []
    readiness = {"not_ready": 0, "beforeinfo_missing": 0,
                 "invalid_race": 0, "deadline_invalid_or_too_close": 0}
    for venue in catalog.get("venues", []):
        for race in venue.get("races", []):
            if race.get("racers_ready") is not True:
                readiness["not_ready"] += 1
                continue
            # Catalog status can lag the race-specific V235 PRE_RESULT refresh.
            # Count it as diagnostic only; the live race receipt decides safety.
            if race.get("beforeinfo_status") != "ok":
                readiness["beforeinfo_missing"] += 1
            path = str(race.get("file") or "")
            key = str(race.get("race_key") or "")
            if (not re.fullmatch(r"data/races/\d{8}-\d{2}-\d{2}\.json", path)
                    or not re.fullmatch(r"20\d{6}-\d{2}-\d{2}", key)
                    or not key.startswith(now.strftime("%Y%m%d"))):
                readiness["invalid_race"] += 1
                continue
            try:
                due = datetime.strptime(
                    str(catalog["date"]) + " " + str(race["deadline"]),
                    "%Y-%m-%d %H:%M"
                ).replace(tzinfo=JST)
            except (KeyError, TypeError, ValueError):
                readiness["deadline_invalid_or_too_close"] += 1
                continue
            # Never certify a past-deadline race or a race already closing.
            if due <= now + timedelta(minutes=3):
                readiness["deadline_invalid_or_too_close"] += 1
                continue
            choices.append((due, venue, race))
    choices.sort(key=lambda item: item[0])

    return choices, readiness


def prioritize_saved_final_candidates(choices, verified_keys):
    """Inspect SHA-proven, still-future SITE FINALs first; keep stable due order.

    This changes only read-only browser coverage, never prediction ranking.
    """
    known = set(verified_keys)
    return sorted(choices, key=lambda item: (
        item[2]["race_key"] not in known, item[0]
    ))


def probe_verified_live_topk(context, target, catalog, shots, engine):
    """Optional REAL PRE_RESULT proof, never a synthetic TopK certification.

    Only races with a successful race-specific beforeinfo receipt and a future
    JST deadline are eligible. No outcome, payout or archived race is accessed.
    If none qualifies, expose NOT_CERTIFIED rather than silently treating a
    stopped prediction or an offline fixture as a successful live TopK test.
    """
    now = datetime.now(JST)
    choices, readiness = choose_live_receipt_candidates(catalog, now)
    if not choices:
        return {"status": "NOT_CERTIFIED_NO_VERIFIED_PREDEADLINE_RACE",
                "eligible_count": 0, "readiness": readiness}
    # A verified snapshot has higher diagnostic value than a moving live
    # reference: look for it first, but only inside the real FINAL_15M window.
    # This reads at most 36 site-only candidates, never result or payout data.
    near = choices[:36]
    verified_saved = {}
    for due, _, race in near:
        if now < due <= now + timedelta(minutes=15):
            evidence = probe_site_snapshot_evidence(
                context, target, race["race_key"], race["deadline"]
            )
            if evidence["status"] == "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED":
                verified_saved[race["race_key"]] = evidence
    near = prioritize_saved_final_candidates(near, verified_saved)
    stopped_reasons = []
    source_ready_checked = 0
    # Source requests are bounded; live mobile browser navigations are capped
    # at five source-ready races to avoid timing out a closing window.
    for _, venue, race in near:
        if source_ready_checked >= 5:
            break
        path = race["file"]
        key = race["race_key"]
        # Additional source audit: only this explicitly allowlisted PRE_RESULT
        # data/races file is fetched; no result or settlement endpoints.
        receipt = context.request.get(
            target.rsplit("/", 1)[0] + "/" + path,
            headers={"Cache-Control": "no-store"}, timeout=15000
        )
        assert receipt.status == 200, "Selected live PRE_RESULT receipt missing: " + key
        payload = receipt.json()
        assert payload.get("race_key") == key, "Cross-race live receipt mismatch"
        meta = payload.get("meta") or {}
        audit = (payload.get("source_audit") or {}).get("beforeinfo") or {}
        if (meta.get("phase") != "PRE_RESULT" or
                any(meta.get(k) is not False for k in
                    ("results_seen", "unlock", "scoring")) or
                str(meta.get("deadline")) != str(race["deadline"])):
            stopped_reasons.append({"race": key, "reason": "race_phase_or_deadline_unsafe"})
            continue
        if audit.get("status") != "ok" or len(payload.get("racers") or []) != 6:
            stopped_reasons.append({"race": key, "reason": "source_audit_not_ready"})
            continue
        source_ready_checked += 1
        saved_evidence = verified_saved.get(key) or probe_site_snapshot_evidence(
            context, target, key, race["deadline"]
        )
        live = context.new_page()
        browser_errors = []
        live.on("pageerror", lambda error: browser_errors.append(str(error)[:180]))
        try:
            response = live.goto(target + "?e2e=03&topk=source", wait_until="domcontentloaded", timeout=45000)
            assert response and response.status == 200
            code = str(venue["jcd"]).zfill(2)
            live.locator('#be108Hub [data-be108-venue="%s"]' % code).click(timeout=40000)
            live.locator('#be108Hub [data-be108-file="%s"]' % path).first.click(timeout=20000)
            try:
                live.wait_for_function(
                    "(key) => document.querySelector('#raceView.active')"
                    " && (typeof state !== 'undefined' ? state?.race?.race_key : null) === key"
                    " && document.querySelector('#be207Top.ready')",
                    arg=key, timeout=(35000 if saved_evidence.get("status") ==
                        "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED" else 18000)
                )
            except Exception:
                # Leave an actionable, read-only trace; a saved FINAL that
                # cannot load is a failure, not a fictitious browser PASS.
                try:
                    dom = live.evaluate("""() => ({
                        location:location.pathname,
                        selected:typeof state==='undefined'?null:state?.race?.race_key,
                        race_view:!!document.querySelector('#raceView.active'),
                        top_present:!!document.querySelector('#be207Top'),
                        top_ready:!!document.querySelector('#be207Top.ready'),
                        top_stop:!!document.querySelector('#be207Top .be207-stop'),
                        title:document.querySelector('#raceTitle')?.textContent,
                        wait:document.querySelector('#be391PredictionWait')?.textContent?.slice(0,200),
                        race_loading:document.documentElement.className
                    })""")
                    live.screenshot(
                        path=str(shots / ("live-select-timeout-%s.png" % engine)),
                        full_page=True, timeout=4000
                    )
                except Exception as diagnostics_error:
                    dom = {"diagnostics_error": str(diagnostics_error)[:180]}
                print("BOAT_EDGE_03_LIVE_SELECTION_TIMEOUT " +
                      json.dumps({"key": key, "saved_evidence": saved_evidence["status"],
                                  "dom": dom, "browser_errors": browser_errors},
                                 ensure_ascii=False), flush=True)
                # A race with NO immutable site-final receipt may safely stay
                # at explicit source-wait. It is NOT a TopK UI PASS. Only
                # classify that visible fail-closed state; unexpected blank
                # screens, JS errors and missing verified FINAL remain failures.
                waiting = str(dom.get("wait") or "")
                if (saved_evidence.get("status") !=
                        "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED"
                        and dom.get("selected") == key
                        and dom.get("race_view") is True
                        and not dom.get("top_ready")
                        and not browser_errors
                        and ("予想表示待ち" in waiting or "買い目停止" in waiting)):
                    stopped_reasons.append({
                        "race": key,
                        "reason": "SOURCE_WAIT_NO_VERIFIED_SAVED_FINAL",
                        "saved_evidence": saved_evidence["status"],
                        "wait": waiting[:120]
                    })
                    continue
                raise
            # A race switch can paint the source list asynchronously after
            # V207 becomes ready. Wait for either an explicit stop or ten
            # uniquely formatted source tickets; do not parse a transient list.
            live.wait_for_function(
                """() => {
                  const t=document.querySelector('#be207Top.ready');
                  if(!t)return false;
                  if(t.querySelector('.be207-stop'))return true;
                  const b=[...document.querySelectorAll(
                    '#be108PredictionModes .be108-ticket-list > .be108-ticket b.be257-ticket-combo')];
                  return b.length>=10 && b.every(node => {
                    const m=/([1-6]-[1-6]-[1-6])/.exec(node.textContent||'');
                    return m && new Set(m[1].split('-')).size===3;
                  });
                }""", timeout=10000
            )
            top = live.locator("#be207Top")
            if top.locator(".be207-stop").count():
                stopped_reasons.append({
                    "race": key,
                    "reason": top.locator(".be207-condition strong").inner_text().strip(),
                    "saved_prediction": saved_evidence
                })
                assert top.locator(".be207-ticket").count() == 0
                continue
            # These come from the actual original ranked DOM, not a fixture.
            raw = live.locator(
                "#be108PredictionModes .be108-ticket-list > .be108-ticket b.be257-ticket-combo"
            ).all_text_contents()
            expected = []
            for value in raw:
                match = re.search(r"(?<!\d)([1-6]-[1-6]-[1-6])(?!\d)", value)
                assert match, "Malformed live source ticket for " + key
                combo = match.group(1)
                assert len(set(combo.split("-"))) == 3, "Repeated lane in live ticket"
                expected.append(combo)
            assert len(expected) >= 10, "Live unblocked prediction has fewer than ten ranked tickets"
            assert len(set(expected)) == len(expected), "Duplicate live prediction tickets"
            for button_name, size in ((None, 3), ("five", 5), ("ten", 10)):
                if button_name:
                    button = top.locator('[data-be207="%s"]' % button_name)
                    assert button.is_visible(), "Live TopK control hidden: " + button_name
                    button.click()
                displayed = live.locator("#be207Top .be207-bets > .be207-ticket")
                assert displayed.count() == size, "Incorrect live TopK count"
                rendered = []
                for row in displayed.all():
                    combo = "-".join(row.locator(".be207-lane").all_text_contents())
                    rendered.append(combo)
                assert rendered == expected[:size], (
                    "Live TopK order diverges from source list for " + key
                )
            # The browser navigation itself can take time. Re-check the actual
            # JST deadline before granting a live PRE_RESULT certification.
            # The original candidate cutoff alone is insufficient if a race
            # closes while a slow WebKit/Pages run is loading.
            verified_at = datetime.now(JST)
            due = datetime.strptime(
                str(catalog["date"]) + " " + str(race["deadline"]),
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=JST)
            if verified_at >= due:
                stopped_reasons.append({
                    "race": key, "reason": "deadline_passed_during_browser_probe"
                })
                continue
            assert not browser_errors, "Live TopK JavaScript errors: " + repr(browser_errors)
            assert live.evaluate(
                "(typeof state !== 'undefined' ? state?.race?.race_key : null)"
            ) == key, "Live TopK changed selected race"
            live.screenshot(
                path=str(shots / ("live-topk-%s.png" % engine)), full_page=True
            )
            selected_mode = live.locator(
                "#be108PredictionModes .be108-mode-tabs .on"
            ).first.get_attribute("data-be108-mode")
            saved_mode_rows = saved_evidence.get(
                "saved_top10_by_mode", {}
            ).get(selected_mode)
            verified_site_final = live.locator(
                '.be181-freeze-banner[data-be181-source="final"]'
                '[data-be181-verification="site-sha-audit"]'
            ).count() > 0
            same_mode_parity = (
                expected[:10] == saved_mode_rows if saved_mode_rows is not None else None
            )
            source_has_saved_final = (
                saved_evidence.get("status") ==
                "SITE_SNAPSHOT_SHA_V229_AUDIT_VERIFIED_GIT_UNCHECKED"
            )
            if source_has_saved_final:
                # The complete SHA/audit/V229 receipt existed BEFORE this
                # prospective browser navigation. A generic dynamic TopK does
                # not establish that the frozen picks reached the public UI.
                assert verified_site_final, (
                    "Saved FINAL exists but public UI did not show its SHA-verified "
                    "frozen picks: " + key + " mode=" + str(selected_mode)
                )
                assert saved_mode_rows is not None and same_mode_parity, (
                    "Published frozen FINAL Top3/5/10 differs from original "
                    "immutable mode-ranked picks: " + key + " mode=" +
                    str(selected_mode)
                )
            return {
                "status": ("VERIFIED_SAVED_FINAL_TOP3_TOP5_TOP10_SHA_PARITY"
                           if source_has_saved_final else
                           "VERIFIED_TOP3_TOP5_TOP10_SOURCE_ORDER"),
                "race": key, "venue": venue["venue"], "ticket_count": len(expected),
                "deadline_jst": race["deadline"], "browser_errors": browser_errors,
                "saved_prediction": saved_evidence,
                "displayed_mode": selected_mode,
                "verified_site_final": verified_site_final,
                "displayed_matches_saved_selected_mode": same_mode_parity
            }
        finally:
            live.close()
    return {
        "status": "NOT_CERTIFIED_ALL_ELIGIBLE_SOURCE_STOPPED",
        "eligible_count": len(choices),
        "source_ready_browser_checked": source_ready_checked,
        "checked": stopped_reasons, "readiness": readiness
    }



def probe_historical_snapshot_render_fixture(context, target, engine):
    """Real production V207 renderer, historical PRE_RESULT inputs; NOT a live proof.

    The archived SITE reference snapshots supply actual preserved ticket order.
    The tiny standalone DOM fakes only V108 readiness/source widgets so the
    presentation module can be tested before fresh data arrives. All saved
    snapshots are opened from the checkout, never outcome or payout resources.
    """
    from html import escape as html_escape

    sources = []
    for key in ("20261013-14-01", "20261013-14-02"):
        file = ROOT / "data" / "site_prediction_snapshots" / (key + ".json")
        saved = json.loads(file.read_text(encoding="utf-8"))
        assert saved["race_key"] == key
        assert saved["snapshot_window"] == "FINAL_15M"
        assert saved["prediction_kind"].startswith("SITE_REFERENCE")
        assert all(saved["guards"].get(k) is False
                   for k in ("results_seen", "unlock", "scoring"))
        rows = saved["modes"]["hit"]["tickets"]
        combos = [v["combo"] for v in rows]
        assert len(combos) >= 10 and len(set(combos)) == len(combos)
        assert all(re.fullmatch(r"[1-6]-[1-6]-[1-6]", x) and
                   len(set(x.split("-"))) == 3 for x in combos)
        sources.append({"key": key, "rows": rows, "combos": combos})

    def source_html(rows):
        return "".join(
            '<div class="be108-ticket" data-be257-view="reference">'
            '<b>' + html_escape(item["combo"]) + '</b>'
            '<em>' + html_escape(str(round(item.get("p", 0), 3))) + '%</em>'
            '<small>倍率未確認</small>'
            '<span class="be140-ticket-money">現在の参考配分 '
            + html_escape(str(item.get("stake_yen", 0))) + '円</span></div>'
            for item in rows
        )

    fixture = context.new_page()
    failures = []
    fixture.on("pageerror", lambda e: failures.append(str(e)))
    try:
        fixture.set_content(
            '<div id="raceView" class="active"><div class="race-summary"></div></div>'
            '<div id="tab-pred"><div id="be108PredictionModes">'
            '<div class="be108-mode-tabs"><button class="on" data-be108-mode="hit">的中重視</button></div>'
            '<div class="be181-freeze-banner" data-be181-source="latest"></div>'
            '<div class="be108-ticket-list">' + source_html(sources[0]["rows"]) + '</div>'
            '</div></div><div id="tab-scenario"></div>'
            '<div id="scenarioHero"><div class="scenario-main">保存された展開参照</div></div>',
            wait_until="domcontentloaded",
        )
        fixture.evaluate(
            """key => {
               window.state = {race: {race_key:key, deadline:"08:35"}};
               window.BoatEdgeV204 = {
                 summarize(){return {settled:false, fresh:false}},
                 sourceLabel(){return "過去PRE_RESULT表示試験（非本番）"},
                 oddsProof(){return {quality:"unknown",label:"未確認"}}
               };
               window.BoatEdgeV205 = {
                 sourceStatus(){return {kind:"partial",title:"履歴fixture：出走状態は模擬",
                                       detail:"本番の予想許可を意味しません"}}
               };
            }""", sources[0]["key"]
        )
        # Fetch the real renderer from checkout/Pages, not a copied test impl.
        fixture.add_script_tag(url=target.rsplit("/", 1)[0] +
                               "/assets/boat_edge_v207_first_prediction.js")
        fixture.wait_for_function(
            "() => !!document.querySelector('#be207Top.ready')", timeout=15000
        )

        def combos_in_dom():
            return fixture.locator("#be207Top .be207-bets > .be207-ticket").evaluate_all(
                "(nodes) => nodes.map(n => [...n.querySelectorAll('.be207-lane')].map("
                "x => x.textContent.trim()).join('-'))"
            )

        def assert_prefix(count, source):
            actual = combos_in_dom()
            assert actual == source[:count], (
                "Historical SITE ticket-order mismatch: %s vs %s" %
                (actual, source[:count]))
            assert fixture.locator("#be207Top .be207-stop").count() == 0
            assert fixture.locator("#be207Top .be207-ticket").count() == count

        assert_prefix(3, sources[0]["combos"])
        fixture.locator('#be207Top [data-be207="five"]').click()
        assert_prefix(5, sources[0]["combos"])
        fixture.locator('#be207Top [data-be207="ten"]').click()
        assert_prefix(10, sources[0]["combos"])
        fixture.locator('#be207Top [data-be207="ten"]').click()
        assert_prefix(3, sources[0]["combos"])

        # Race changes while previous V108 list is still mounted must STOP,
        # not show the old race's saved historical tickets under the new key.
        fixture.evaluate("(key) => {window.state.race.race_key=key;"
                         "window.BoatEdgeV207.render()}", sources[1]["key"])
        assert fixture.locator("#be207Top .be207-stop").count() == 1
        assert fixture.locator("#be207Top .be207-ticket").count() == 0
        fixture.locator("#be391PredictionWait").wait_for(state="visible")
        assert fixture.locator("#be391PredictionWait").get_attribute(
            "data-race-key") == sources[1]["key"]

        # Simulate the V108 source DOM REPLACEMENT (not a prediction calculation).
        fixture.evaluate(
            """markup => {
              const previous=document.querySelector(
                '#be108PredictionModes .be108-ticket-list');
              const next=document.createElement('div');
              next.className='be108-ticket-list';
              next.innerHTML=markup;
              previous.replaceWith(next);
              window.BoatEdgeV207.render();
            }""", source_html(sources[1]["rows"])
        )
        assert_prefix(3, sources[1]["combos"])
        fixture.locator('#be207Top [data-be207="five"]').click()
        assert_prefix(5, sources[1]["combos"])
        fixture.locator('#be207Top [data-be207="ten"]').click()
        assert_prefix(10, sources[1]["combos"])
        assert fixture.locator("#be391PredictionWait").count() == 0
        assert not failures, "Historical V207 browser error: " + repr(failures)
        return {
            "status": "HISTORICAL_PRE_RESULT_RENDER_FIXTURE_PASS_NOT_LIVE",
            "historical_races": [item["key"] for item in sources],
            "mode": "hit",
            "rank_prefixes_checked": [3, 5, 10],
            "old_race_not_leaked": True,
            "production_renderer": "assets/boat_edge_v207_first_prediction.js",
            "result_or_payout_read": False,
            "live_prediction_certified": False,
        }
    finally:
        fixture.close()



def exercise(engine: str, url: str, shots: Path):
    import functools
    import http.server
    import threading
    server = None
    thread = None
    if url == "local":
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *_):
                pass

        handler = functools.partial(Quiet, directory=str(ROOT))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        target = "http://127.0.0.1:%d/index.html" % server.server_port
    else:
        target = url

    shots.mkdir(parents=True, exist_ok=True)
    report = {
        "browser": engine,
        "target": target,
        "result_requests_allowed": 0,
        "formal_fresh_modified": False,
        "physical_iphone_safari_verified": False,
    }
    try:
        with sync_playwright() as pw:
            browser = getattr(pw, engine).launch(headless=True)
            context = browser.new_context(
                viewport={"width": 390, "height": 844}, device_scale_factor=2,
                is_mobile=True, has_touch=True, locale="ja-JP",
                timezone_id="Asia/Tokyo", service_workers="block",
            )
            errors = []
            blocked = []
            page = context.new_page()
            page.set_default_timeout(16000)
            page.on("pageerror", lambda err: errors.append(str(err)[:180]))

            def protect(route):
                u = route.request.url
                path = urlparse(u).path.lower()
                if any(token in path for token in FORBIDDEN):
                    blocked.append(path)
                    route.abort()
                elif urlparse(u).netloc != urlparse(target).netloc:
                    # No external APIs, including official race/result endpoints.
                    blocked.append("external:" + urlparse(u).netloc)
                    route.abort()
                else:
                    route.continue_()

            context.route("**/*", protect)
            try:
                response = page.goto(target + "?e2e=03", wait_until="domcontentloaded", timeout=45000)
                assert response and response.status == 200, "index not served"

                # Read ONLY the current PRE_RESULT race catalog (no result files).
                catalog_response = context.request.get(
                    target.rsplit("/", 1)[0] + "/data/today.json",
                    headers={"Cache-Control": "no-store"}, timeout=15000
                )
                assert catalog_response.status == 200, "today.json not served"
                catalog = catalog_response.json()
                assert catalog.get("results_seen") is False, "result-unseen catalog required"
                assert catalog.get("unlock") is False and catalog.get("scoring") is False
                date = str(catalog.get("date") or "")
                assert date == datetime.now(JST).date().isoformat(), (
                    "Published catalog is stale: %s" % date
                )
                venues = [v for v in catalog.get("venues", []) if len(v.get("races", [])) >= 2]
                assert venues, "No venue with two selectable races"
                chosen = venues[0]
                code = str(chosen["jcd"]).zfill(2)
                first, second = chosen["races"][:2]
                for race in (first, second):
                    assert re.fullmatch(r"data/races/\d{8}-\d{2}-\d{2}\.json", race["file"])
                    assert race["race_key"].startswith(date.replace("-", ""))
                    assert race.get("racers_ready") is True

                venue_button = page.locator('#be108Hub [data-be108-venue="%s"]' % code)
                venue_button.wait_for(state="visible", timeout=40000)
                venue_button.click()
                first_button = page.locator(
                    '#be108Hub [data-be108-file="%s"]' % first["file"]
                ).first
                first_button.wait_for(state="visible", timeout=20000)
                first_button.click()
                page.wait_for_function(
                    "(key) => document.querySelector('#raceView.active')"
                    " && document.querySelector('#raceTitle')?.textContent"
                    "?.includes('1R') && (typeof state !== 'undefined' ? state?.race?.race_key : null) === key",
                    arg=first["race_key"], timeout=35000
                )
                page.locator("#be207Top.ready").wait_for(state="attached", timeout=35000)
                original_key = page.evaluate("(typeof state !== 'undefined' ? state?.race?.race_key : null)")
                assert original_key == first["race_key"]
                assert page.locator("#raceView #raceTitle").is_visible()
                first_panel = page.locator("#be207Top")
                assert first_panel.locator(".be207-condition").inner_text().strip()
                assert first_panel.locator(".be207-explain").inner_text().strip()
                assert first_panel.locator(".be207-budget").inner_text().strip()
                assert page.locator("#be108PredictionModes").count() == 1
                first_stopped = first_panel.locator(".be207-stop").count() > 0
                if first_stopped:
                    assert first_panel.locator(".be207-ticket").count() == 0
                    assert "非表示" in first_panel.locator(".be207-budget").inner_text()
                    # The waiting notice is part of the public mobile UX, not
                    # a generic PASS merely because prediction rows are hidden.
                    page.wait_for_function(
                        "(key) => { const n=document.querySelector('#be391PredictionWait');"
                        " return n && n.dataset.raceKey===key &&"
                        " n.textContent.includes('予想表示待ち'); }",
                        arg=first["race_key"], timeout=15000
                    )
                    assert page.locator("#be391PredictionWait").is_visible(), (
                        "Source-wait message is hidden on mobile"
                    )
                else:
                    assert first_panel.locator(".be207-ticket").count() >= 3
                    for label, expected in (("five", 5), ("ten", 10)):
                        button = first_panel.locator('[data-be207="%s"]' % label)
                        assert button.is_visible(), "Top%s toggle missing" % expected
                        button.click()
                        assert first_panel.locator(".be207-ticket").count() == expected

                # The actual public Pages runtime must also pass the V207 mode
                # click regression; checkout-only proof misses stale deployed JS.
                # This only changes a visible mode and never fetches results.
                modes = page.locator("#be207Top .be207-modes [data-be207-mode]")
                assert modes.count() >= 2, "Prediction mode buttons missing"
                desired = modes.nth(1).get_attribute("data-be207-mode")
                assert desired, "Second prediction mode has no mode key"
                page.locator('#be207Top [data-be207-mode="%s"]' % desired).click()
                page.wait_for_function(
                    "(mode) => document.querySelector('#be108PredictionModes .be108-mode-tabs .on')?.dataset.be108Mode === mode",
                    arg=desired, timeout=25000
                )
                assert page.evaluate("(typeof state !== 'undefined' ? state?.race?.race_key : null)") == first["race_key"], (
                    "Changing prediction mode altered selected race"
                )
                assert not errors, "Uncaught browser JavaScript errors: " + repr(errors)

                # Switch via the actual race navigator, without reloading the page.
                switcher = page.locator(
                    '#be108RaceNav [data-be108-file="%s"]' % second["file"]
                ).first
                try:
                    switcher.wait_for(state="visible", timeout=14000)
                except Exception:
                    switcher = page.locator(
                        '#raceNav [data-file="%s"]' % second["file"]
                    ).first
                    switcher.wait_for(state="visible", timeout=10000)
                switcher.click()
                page.wait_for_function(
                    "(key) => document.querySelector('#raceView.active')"
                    " && (typeof state !== 'undefined' ? state?.race?.race_key : null) === key",
                    arg=second["race_key"], timeout=35000
                )
                page.wait_for_function(
                    "(key) => document.querySelector('#be207Top.ready')"
                    " && document.querySelector('#raceTitle')?.textContent"
                    "?.includes('2R')",
                    arg=second["race_key"], timeout=35000
                )
                assert page.locator("#raceView #raceTitle").is_visible()
                second_panel = page.locator("#be207Top")
                assert second_panel.locator(".be207-condition").inner_text().strip()
                assert second_panel.locator(".be207-budget").inner_text().strip()
                assert page.evaluate("(typeof state !== 'undefined' ? state?.race?.race_key : null)") == second["race_key"]
                # Even during asynchronous redraw, never leave previous-race tickets
                # displayed as if they belonged to the newly selected race.
                race_waiting = page.locator("html.be306-race-await").count() > 0
                if race_waiting:
                    assert second_panel.locator(".be207-ticket").count() == 0
                second_stopped = second_panel.locator(".be207-stop").count() > 0
                if second_stopped:
                    # A 1R source-wait banner must never remain attached to 2R.
                    # This verifies the live Pages race-specific UI status.
                    page.wait_for_function(
                        "(key) => { const n=document.querySelector('#be391PredictionWait');"
                        " return n && n.dataset.raceKey===key &&"
                        " n.textContent.includes('予想表示待ち'); }",
                        arg=second["race_key"], timeout=15000
                    )
                    assert page.locator("#be391PredictionWait").is_visible()
                    assert second_panel.locator(".be207-ticket").count() == 0
                # 03: production CSS must never reveal an old race's six-boat
                # comparison, head picks, result panel or sticky ticket strip
                # while a new race card is still loading. Exercise real
                # deployed index styles in the running browser without mocks
                # of any forecast, outcome, or race data.
                loading_visual = page.evaluate("""() => {
                    const rv=document.querySelector('#raceView');
                    if(!rv)throw Error('NO_RACE_VIEW');
                    const targets=['#be207Top','#be206Quick','#be108PredictionModes',
                        '#be251Outcome','#be48Action','#be48Racers',
                        '#be48Before','#be204Overview','#scenarioHero',
                        '.race-summary .summary-top'];
                    const created=[];
                    for(const selector of targets) {
                        if(rv.querySelector(selector))continue;
                        const el=document.createElement('div');
                        if(selector.startsWith('#'))el.id=selector.slice(1);
                        else el.className='summary-top';
                        rv.appendChild(el);created.push(el);
                    }
                    let n=rv.querySelector('#be03RaceLoadNotice');
                    if(!n) {
                        n=document.createElement('div');
                        n.id='be03RaceLoadNotice';
                        n.className='be03-load-notice';
                        n.textContent='新しいレースを読み込み中';
                        rv.querySelector('.race-summary')?.appendChild(n);
                        created.push(n);
                    }
                    rv.classList.add('be03-race-loading');
                    const hidden=Object.fromEntries(targets.map(s=>{
                      const node=rv.querySelector(s);
                      return [s,node?getComputedStyle(node).display==='none':false];
                    }));
                    const noticeVisible=getComputedStyle(n).display!=='none';
                    const nav=rv.querySelector('#be108RaceNav');
                    const navVisible=!nav||getComputedStyle(nav).display!=='none';
                    rv.classList.remove('be03-race-loading');
                    const restored=getComputedStyle(rv.querySelector('.race-summary .summary-top')).display!=='none';
                    created.forEach(el=>el.remove());
                    return {hidden,noticeVisible,navVisible,restored};
                }""")
                # A PR's Pages URL serves the *old* main until this PR is merged.
                # Only the checked-out local build is the PR candidate; the
                # published build is re-tested strictly after main deployment.
                old_pages_on_pr = (url != "local" and
                                   os.getenv("GITHUB_EVENT_NAME") == "pull_request")
                if old_pages_on_pr and not all(loading_visual["hidden"].values()):
                    report["previous_race_panels_during_load"] = (
                        "PR_PAGES_OLDER_BUILD_NOT_CERTIFIED")
                else:
                    assert all(loading_visual["hidden"].values()), (
                        "Old race content remains visible while new card loads: %r" % loading_visual)
                    assert loading_visual["noticeVisible"] and loading_visual["navVisible"]
                    assert loading_visual["restored"], "Race title must be restored after loading"
                    report["previous_race_panels_during_load"] = "HIDDEN_AND_RESTORED_PASS"
                historical_display = probe_historical_snapshot_render_fixture(
                    context, target, engine
                )
                live_topk = probe_verified_live_topk(context, target, catalog, shots, engine)
                report.update({
                    "historical_display": historical_display,
                    "live_topk": live_topk,
                    "date": date, "venue": chosen["venue"], "venue_code": code,
                    "race_1": first["race_key"], "race_2": second["race_key"],
                    "race_switch": "PASS", "mode_switch": "PASS", "actual_dom": True,
                    "initial_prediction": "STOPPED_WITH_REASON" if first_stopped else "TOPK_VISIBLE",
                    "topk_evidence": "NOT_CERTIFIED_STOPPED" if first_stopped else "TOP3_TOP5_TOP10_PASS",
                    "second_prediction_condition": second_panel.locator(".be207-condition strong").inner_text(),
                    "guard_blocked_requests": len(blocked),
                    "page_errors": errors[:10],
                })
                print("BOAT_EDGE_03_REAL_BROWSER_PASS " + json.dumps(report, ensure_ascii=False), flush=True)
            finally:
                path = shots / ("%s-%s.png" % (
                    "local" if url == "local" else "pages", engine
                ))
                try:
                    page.screenshot(path=str(path), full_page=True, timeout=12000)
                except Exception:
                    pass
                if "date" not in report:
                    print("BOAT_EDGE_03_REAL_BROWSER_FAIL_DEBUG " + json.dumps({
                        "url": page.url, "errors": errors[-12:],
                        "blocked_paths": blocked[:8],
                        "race_title": page.locator("#raceTitle").all_text_contents()[:2],
                        "race_key": page.evaluate("(typeof state !== 'undefined' ? state?.race?.race_key : null) ?? null"),
                    }, ensure_ascii=False), flush=True)
                context.close()
                browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
        if thread:
            thread.join(timeout=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("chromium", "webkit"), required=True)
    parser.add_argument("--site-url", default="local", help="local or published Pages index.html")
    parser.add_argument("--screenshots", default="artifacts/boat-edge-03-browser")
    args = parser.parse_args()
    test_snapshot_evidence_contract_without_network()
    exercise(args.engine, args.site_url, Path(args.screenshots))
