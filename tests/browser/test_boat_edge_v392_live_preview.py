#!/usr/bin/env python3
"""V392 browser E2E: real, published future PRE_RESULT card-only Top3/5/10.

No results/payouts/formal files, no reconstructed old picks, no mock race inputs.
Uses only the exact current-day future race, its card and independently persisted
uncalibrated preview. A read-only renderer test; no Git persistence asserted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

JST = timezone(timedelta(hours=9))
SITE = "https://ikst2512-eng.github.io/boat-edge/index.html"
FORBIDDEN = (
    "/site_results/", "/formal_predictions/", "/site_prediction_history/",
    "/site_learning/", "/site_archive/", "/site_payout",
    "/race/result", "/race/pay", "/result/", "/payout", "/api/v1/",
    "combined", "/data/formal/", "settlement",
)
KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")


def full_url(site, suffix):
    return site.rsplit("/", 1)[0] + "/" + suffix


def select_source_bound_candidate(context, site):
    now = datetime.now(JST)
    r = context.request.get(full_url(site, "data/today.json"), timeout=15000,
                            headers={"Cache-Control": "no-store"})
    assert r.status == 200, "V392_PAGES_TODAY_CATALOG_MISSING"
    catalog = r.json()
    assert catalog.get("date") == now.strftime("%Y-%m-%d"), "V392_CATALOG_NOT_TODAY"
    assert all(catalog.get(k) is False for k in ("results_seen", "unlock", "scoring"))
    candidates = []
    for venue in catalog.get("venues", []):
        code = str(venue.get("jcd", "")).zfill(2)
        for rec in venue.get("races", []):
            key = rec.get("race_key")
            if not isinstance(key, str) or not KEY.fullmatch(key):
                continue
            if not key.startswith(now.strftime("%Y%m%d")) or key[9:11] != code:
                continue
            if rec.get("racers_ready") is not True or not re.fullmatch(
                r"data/races/20\d{6}-\d{2}-\d{2}\.json", str(rec.get("file", ""))
            ):
                continue
            try:
                due = datetime.strptime(key[:8]+rec["deadline"], "%Y%m%d%H:%M").replace(tzinfo=JST)
            except (ValueError, KeyError, TypeError):
                continue
            if due <= now+timedelta(minutes=8):
                continue
            candidates.append((due, code, rec))
    candidates.sort(key=lambda x: x[0])
    assert candidates, "V392_NO_FUTURE_SOURCE_BOUND_CANDIDATE"
    checked = []
    for due, code, rec in candidates[:8]:
        key = rec["race_key"]
        preview = context.request.get(full_url(site, f"data/site_early_previews/{key}.json"),
                                      headers={"Cache-Control": "no-store"}, timeout=15000)
        card = context.request.get(full_url(site, rec["file"]),
                                   headers={"Cache-Control": "no-store"}, timeout=15000)
        if preview.status != 200 or card.status != 200:
            checked.append((key, preview.status, card.status))
            continue
        p, d = preview.json(), card.json()
        if (p.get("race_key") != key or d.get("race_key") != key or
            p.get("prediction_kind") != "EARLY_CARD_ONLY_REFERENCE_NOT_FINAL" or
            p.get("source_card_sha256") !=
                ((d.get("source_audit") or {}).get("race_card") or {}).get("sha256")):
            checked.append((key, "source_sha_mismatch"))
            continue
        if p.get("source_card_fetched_at") != ((d.get("source_audit") or {}).get("race_card") or {}).get("fetched_at"):
            checked.append((key, "source_time_mismatch"))
            continue
        if len(p.get("ranked_120") or []) != 120:
            checked.append((key, "ranked_120_missing"))
            continue
        return code, rec, p, d
    raise AssertionError("V392_NO_PUBLISHED_SOURCE_MATCHED_PREVIEW " + repr(checked))


def run(engine, site):
    with sync_playwright() as playwright:
        browser = getattr(playwright, engine).launch(headless=True)
        context = browser.new_context(
            viewport={"width":390, "height":844}, device_scale_factor=2,
            is_mobile=True, has_touch=True, timezone_id="Asia/Tokyo",
            locale="ja-JP", service_workers="block")
        blocked = []
        page_errors = []
        def protect(route):
            target = urlparse(route.request.url)
            path = target.path.lower()
            if any(token in path for token in FORBIDDEN):
                blocked.append(path)
                route.abort()
            elif target.netloc != urlparse(site).netloc:
                route.abort()
            else:
                route.continue_()
        context.route("**/*", protect)
        try:
            code, rec, preview, race = select_source_bound_candidate(context, site)
            key = rec["race_key"]
            page = context.new_page()
            page.on("pageerror", lambda err: page_errors.append(str(err)[:300]))
            response = page.goto(site+"?v392=live", wait_until="domcontentloaded", timeout=50000)
            assert response and response.status == 200, "V392_PAGES_INDEX_NOT_200"
            page.locator(f'#be108Hub [data-be108-venue="{code}"]').wait_for(
                state="visible", timeout=45000)
            page.locator(f'#be108Hub [data-be108-venue="{code}"]').click()
            race_button = page.locator(f'#be108Hub [data-be108-file="{rec["file"]}"]').first
            race_button.wait_for(state="visible", timeout=25000)
            race_button.click()
            page.wait_for_function(
                """key => (typeof state !== 'undefined' && state?.race?.race_key===key)
                    && document.querySelector('#be392EarlyPreview[data-ready="true"]')""",
                arg=key, timeout=35000)
            panel = page.locator('#be392EarlyPreview')
            assert panel.is_visible(), "V392_EARLY_PANEL_HIDDEN"
            assert panel.get_attribute('data-race-key') == key
            assert panel.locator(".be392-tag").inner_text().strip() == "未凍結・参考順位"
            assert "未校正" in panel.locator(".be392-note").inner_text()
            def shown_combos():
                return panel.locator(".be392-lines .combo").all_text_contents()
            assert shown_combos() == preview["top10"], "V392_PAGES_TOP10_SOURCE_ORDER_DRIFT"
            for amount in (3,5,10):
                panel.locator(f'.be392-tabs button[data-count="{amount}"]').click()
                assert shown_combos() == preview[f"top{amount}"], f"V392_TOP{amount}_ORDER_DRIFT"
                assert panel.locator(f'.be392-tabs button[data-count="{amount}"]').get_attribute(
                    "aria-pressed") == "true"
            assert "source" not in blocked, "V392_BLOCKED_SOURCE_REQUEST"
            assert page.evaluate("typeof state!=='undefined' ? state.race.race_key : ''") == key
            assert datetime.now(JST) < datetime.strptime(key[:8]+rec["deadline"],
                              "%Y%m%d%H:%M").replace(tzinfo=JST), "V392_RACE_CLOSED_DURING_TEST"
            assert not page_errors, "V392_LIVE_PAGES_JS_EXCEPTION " + repr(page_errors)
            # Do not interpret this browser panel as an immutable snapshot or a
            # successful V235 first Git commit. It is source-bound reference only.
            print("V392_LIVE_PAGES_PREDEADLINE_TOPK_RENDER_PASS " +
                  json.dumps({"browser":engine,"race":key,"head":preview["head_candidate"],
                              "top3":preview["top3"],"top5":preview["top5"],
                              "top10":preview["top10"],"ranked_120":len(preview["ranked_120"]),
                              "reference_only":True,"final_first_git_proven":False,
                              "formal_results_read":False},ensure_ascii=False,sort_keys=True),flush=True)
            shots = Path("artifacts/boat-edge-v392")
            shots.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(shots/(f"live-pages-{engine}-{key}.png")),full_page=False)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("chromium","webkit"), required=True)
    parser.add_argument("--site-url", default=SITE)
    args=parser.parse_args()
    run(args.engine,args.site_url)
