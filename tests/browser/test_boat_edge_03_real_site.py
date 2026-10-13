#!/usr/bin/env python3
"""Read-only E2E: actual BOAT EDGE site and PRE_RESULT race files.

Both the repository preview and publicly deployed Pages can be exercised.
No mocks, outcome endpoints, payouts, formal predictions, or API/v1 calls.
Headless WebKit is NOT physical iPhone Safari certification.
"""
import argparse
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



def probe_verified_live_topk(context, target, catalog, shots, engine):
    """Optional REAL PRE_RESULT proof, never a synthetic TopK certification.

    Only races with a successful race-specific beforeinfo receipt and a future
    JST deadline are eligible. No outcome, payout or archived race is accessed.
    If none qualifies, expose NOT_CERTIFIED rather than silently treating a
    stopped prediction or an offline fixture as a successful live TopK test.
    """
    now = datetime.now(JST)
    choices = []
    readiness = {"not_ready": 0, "beforeinfo_missing": 0,
                 "invalid_race": 0, "deadline_invalid_or_too_close": 0}
    for venue in catalog.get("venues", []):
        for race in venue.get("races", []):
            if race.get("racers_ready") is not True:
                readiness["not_ready"] += 1
                continue
            if race.get("beforeinfo_status") != "ok":
                readiness["beforeinfo_missing"] += 1
                continue
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
    if not choices:
        return {"status": "NOT_CERTIFIED_NO_VERIFIED_PREDEADLINE_RACE",
                "eligible_count": 0, "readiness": readiness}
    stopped_reasons = []
    for _, venue, race in choices[:5]:
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
        audit = (payload.get("source_audit") or {}).get("beforeinfo") or {}
        if audit.get("status") != "ok" or len(payload.get("racers") or []) != 6:
            stopped_reasons.append({"race": key, "reason": "source_audit_not_ready"})
            continue
        live = context.new_page()
        browser_errors = []
        live.on("pageerror", lambda error: browser_errors.append(str(error)[:180]))
        try:
            response = live.goto(target + "?e2e=03&topk=source", wait_until="domcontentloaded", timeout=45000)
            assert response and response.status == 200
            code = str(venue["jcd"]).zfill(2)
            live.locator('#be108Hub [data-be108-venue="%s"]' % code).click(timeout=40000)
            live.locator('#be108Hub [data-be108-file="%s"]' % path).first.click(timeout=20000)
            live.wait_for_function(
                "(key) => document.querySelector('#raceView.active')"
                " && (typeof state !== 'undefined' ? state?.race?.race_key : null) === key"
                " && document.querySelector('#be207Top.ready')",
                arg=key, timeout=35000
            )
            top = live.locator("#be207Top")
            if top.locator(".be207-stop").count():
                stopped_reasons.append({
                    "race": key,
                    "reason": top.locator(".be207-condition strong").inner_text().strip()
                })
                assert top.locator(".be207-ticket").count() == 0
                continue
            # These come from the actual original ranked DOM, not a fixture.
            raw = live.locator(
                "#be108PredictionModes .be108-ticket-list > .be108-ticket b"
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
            assert not browser_errors, "Live TopK JavaScript errors: " + repr(browser_errors)
            assert live.evaluate(
                "(typeof state !== 'undefined' ? state?.race?.race_key : null)"
            ) == key, "Live TopK changed selected race"
            live.screenshot(
                path=str(shots / ("live-topk-%s.png" % engine)), full_page=True
            )
            return {
                "status": "VERIFIED_TOP3_TOP5_TOP10_SOURCE_ORDER",
                "race": key, "venue": venue["venue"], "ticket_count": len(expected),
                "deadline_jst": race["deadline"], "browser_errors": browser_errors
            }
        finally:
            live.close()
    return {
        "status": "NOT_CERTIFIED_ALL_ELIGIBLE_SOURCE_STOPPED",
        "eligible_count": len(choices), "checked": stopped_reasons,
        "readiness": readiness
    }


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
                live_topk = probe_verified_live_topk(context, target, catalog, shots, engine)
                report.update({
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
    exercise(args.engine, args.site_url, Path(args.screenshots))
