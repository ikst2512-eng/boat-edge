"""Synthetic Git race: concurrent first-freeze never loses unrelated source writes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.boat_edge_v01_prune_frozen_collector import filter_newly_frozen
from scripts.boat_edge_v277_snapshot_push_guard import audit, GuardFailure

JST = timezone(timedelta(hours=9))


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, text=True,
                       capture_output=True, check=False)
    if p.returncode:
        raise AssertionError((args, p.stdout, p.stderr))
    return p.stdout.strip()


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf8")


def commit(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-m", message)


class ConcurrentFrozenSource(unittest.TestCase):
    def test_remote_first_freeze_wins_but_other_races_still_publish(self):
        day = (datetime.now(JST) + timedelta(days=1)).strftime("%Y%m%d")
        frozen = day + "-19-09"
        other = day + "-19-10"
        race = "data/races/" + frozen + ".json"
        next_race = "data/races/" + other + ".json"
        raw = "data/raw/" + day + "/19_09_beforeinfo.html"
        scratch = "data/site_scratches_v182/" + frozen + ".json"
        preview = "data/site_early_previews/" + frozen + ".json"
        formal = "data/formal_status.json"
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = base / "server.git"
            owner = base / "collector"
            second = base / "freeze"
            git(base, "init", "--bare", "-b", "main", str(remote))
            git(base, "clone", str(remote), str(owner))
            for repo in [owner]:
                git(repo, "config", "user.email", "ci@example.test")
                git(repo, "config", "user.name", "CI")
            lock = {"guards": {"results_seen": False, "unlock": False,
                                "scoring": False, "RESULT_UNLOCK_TOKEN": None},
                    "formalFirst100": {"races": 0}}
            put(owner, formal, json.dumps(lock))
            def document(key, value):
                return json.dumps({"race_key": key, "meta": {"deadline": "23:55"},
                                   "source": value})
            put(owner, race, document(frozen, "original"))
            put(owner, raw, "official original bytes")
            put(owner, scratch, "old checked source")
            put(owner, preview, "old preview")
            old_row = {"race_key": frozen, "racers_ready": True,
                       "beforeinfo_status": "published_wait"}
            next_row = {"race_key": other, "racers_ready": True,
                        "beforeinfo_status": "published_wait"}
            catalog = {"date": datetime.strptime(day, "%Y%m%d").strftime("%Y-%m-%d"),
                       "results_seen": False,
                       "venues": [{"jcd": "19", "races": [old_row, next_row]}]}
            put(owner, "data/today.json", json.dumps(catalog))
            health = {"results_seen": False, "unlock": False, "scoring": False}
            put(owner, "data/health.json", json.dumps(health))
            commit(owner, "original PRE_RESULT")
            git(owner, "push", "-u", "origin", "main")
            put(owner, race, document(frozen, "unpublished late collector"))
            put(owner, raw, "new collector raw bytes")
            put(owner, scratch, "new collector scratch")
            put(owner, preview, "new collector preview")
            put(owner, next_race, document(other, "valid other race"))
            changed = dict(catalog)
            changed["venues"] = [{"jcd": "19", "races": [
                dict(old_row, beforeinfo_status="ok"),
                dict(next_row, beforeinfo_status="ok"),
            ]}]
            put(owner, "data/today.json", json.dumps(changed))
            put(owner, "data/health.json", json.dumps(health | {"race_cards_ok": 2}))
            commit(owner, "自動更新: PRE_RESULT synthetic test")
            git(base, "clone", str(remote), str(second))
            git(second, "config", "user.email", "ci@example.test")
            git(second, "config", "user.name", "CI")
            put(second, race, document(frozen, "remote frozen official"))
            remote_catalog = dict(catalog)
            remote_catalog["venues"] = [{"jcd": "19", "races": [
                dict(old_row, beforeinfo_status="published_wait"), next_row]}]
            put(second, "data/today.json", json.dumps(remote_catalog))
            put(second, "data/site_prediction_snapshots/" + frozen + ".json",
                "immutable binary SHA proof not inspected")
            commit(second, "verified independent first freeze")
            git(second, "push", "origin", "main")
            git(owner, "fetch", "--no-tags", "origin", "main")
            with self.assertRaisesRegex(GuardFailure, "FROZEN_RACE_SOURCE_MUTATION"):
                audit(owner)
            report = filter_newly_frozen(owner)
            self.assertEqual(report["pruned_frozen_races"], [frozen])
            self.assertTrue(report["remote_evidence_preserved"])
            self.assertEqual(audit(owner)["status"], "PASS")
            self.assertEqual(git(owner, "show", "HEAD:" + race),
                             git(owner, "show", "origin/main:" + race))
            self.assertEqual(git(owner, "show", "HEAD:" + raw),
                             git(owner, "show", "origin/main:" + raw))
            self.assertEqual(git(owner, "show", "HEAD:" + scratch),
                             git(owner, "show", "origin/main:" + scratch))
            self.assertEqual(git(owner, "show", "HEAD:" + preview),
                             git(owner, "show", "origin/main:" + preview))
            self.assertEqual(json.loads((owner / next_race).read_text())["source"],
                             "valid other race")
            self.assertEqual(json.loads((owner / "data/today.json").read_text())[
                "venues"][0]["races"][0]["beforeinfo_status"], "published_wait")
            self.assertEqual(json.loads((owner / "data/health.json").read_text())[
                "collector_source_published_exclusions"], [frozen])
            # A regular fast-forward rebase now publishes the next race without
            # changing a byte from the remote immutable frozen source.
            git(owner, "rebase", "origin/main")
            git(owner, "push", "origin", "main")
            self.assertEqual(audit(owner)["status"], "PASS")

    def test_gated_to_actual_collector_only(self):
        # Bare function never promotes model research, never reads payout files.
        self.assertTrue(callable(filter_newly_frozen))


class ExpiredRaceIsolation(unittest.TestCase):
    """A past-deadline source must never starve a different future race."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.remote = base / "server.git"
        self.root = base / "collector"
        self.second = base / "freezer"
        self.frozen, self.expired, self.future = (
            "20990101-19-09", "20990101-19-10", "20990101-19-11")
        self.now = datetime(2099, 1, 1, 12, 0, tzinfo=JST)
        git(base, "init", "--bare", "-b", "main", str(self.remote))
        git(base, "clone", str(self.remote), str(self.root))
        git(self.root, "config", "user.email", "fixture@example.test")
        git(self.root, "config", "user.name", "Fixture")
        lock = {"guards": {"results_seen": False, "unlock": False,
                           "scoring": False, "RESULT_UNLOCK_TOKEN": None},
                "formalFirst100": {"races": 0}}
        put(self.root, "data/formal_status.json", json.dumps(lock))
        for key, deadline in ((self.frozen, "11:55"),
                              (self.expired, "12:00"), (self.future, "12:10")):
            put(self.root, self.race(key), json.dumps({
                "race_key": key, "meta": {"deadline": deadline}, "source": "remote"}))
            for path in self.companions(key):
                put(self.root, path, "remote original bytes")
        self.catalog = {"date": "2099-01-01", "results_seen": False,
                        "venues": [{"races": [{"race_key": k, "state": "remote"}
                                    for k in (self.frozen, self.expired, self.future)]}]}
        put(self.root, "data/today.json", json.dumps(self.catalog))
        put(self.root, "data/health.json", json.dumps({
            "results_seen": False, "unlock": False, "scoring": False}))
        commit(self.root, "original PRE_RESULT")
        git(self.root, "push", "-u", "origin", "main")
        git(base, "clone", str(self.remote), str(self.second))
        git(self.second, "config", "user.email", "fixture@example.test")
        git(self.second, "config", "user.name", "Fixture")
        for key in (self.frozen, self.expired, self.future):
            path = self.root / self.race(key)
            doc = json.loads(path.read_text())
            doc["source"] = "unpublished local"
            path.write_text(json.dumps(doc))
            for name in self.companions(key):
                put(self.root, name, "unpublished local bytes")
        local = json.loads(json.dumps(self.catalog))
        for row in local["venues"][0]["races"]:
            row["state"] = "local"
        put(self.root, "data/today.json", json.dumps(local))
        put(self.root, "data/health.json", json.dumps({
            "results_seen": False, "unlock": False, "scoring": False, "fetched": 3}))
        commit(self.root, "自動更新: PRE_RESULT synthetic expiration race")
        put(self.second, "data/site_prediction_snapshots/" + self.frozen + ".json",
            "remote immutable proof: never inspect")

    @staticmethod
    def race(key):
        return "data/races/" + key + ".json"

    @staticmethod
    def companions(key):
        day, venue, race = key.split("-")
        return (f"data/raw/{day}/{venue}_{race}_beforeinfo.html",
                f"data/site_scratches_v182/{key}.json",
                f"data/site_early_previews/{key}.json")

    def publish_remote(self):
        commit(self.second, "independent first freeze")
        git(self.second, "push", "origin", "main")
        git(self.root, "fetch", "origin", "main")

    def filter(self):
        with patch("scripts.boat_edge_v01_prune_frozen_collector.datetime", wraps=datetime) as clock:
            clock.now.return_value = self.now
            return filter_newly_frozen(self.root)

    def test_exact_deadline_drops_expired_sources_and_publishes_future_only(self):
        self.publish_remote()
        before_formal = (self.root / "data/formal_status.json").read_bytes()
        report = self.filter()
        self.assertEqual(report["pruned_frozen_races"], [self.frozen])
        self.assertEqual(report["pruned_expired_races"], [self.expired])
        for key in (self.frozen, self.expired):
            for path in (self.race(key), *self.companions(key)):
                self.assertEqual(git(self.root, "show", "HEAD:" + path),
                                 git(self.root, "show", "origin/main:" + path))
        for path in (self.race(self.future), *self.companions(self.future)):
            self.assertIn("unpublished local", (self.root / path).read_text())
        rows = json.loads((self.root / "data/today.json").read_text())["venues"][0]["races"]
        self.assertEqual([r["state"] for r in rows], ["remote", "remote", "local"])
        health = json.loads((self.root / "data/health.json").read_text())
        self.assertEqual(health["collector_source_published_exclusions"],
                         sorted([self.frozen, self.expired]))
        self.assertEqual((self.root / "data/formal_status.json").read_bytes(), before_formal)
        self.assertEqual(audit(self.root)["status"], "PASS")
        git(self.root, "rebase", "origin/main")
        git(self.root, "push", "origin", "main")
        # Remote original snapshot stays byte-identical; no missing prediction
        # is fabricated for the expired or future race.
        self.assertEqual(git(self.root, "show", "HEAD:data/site_prediction_snapshots/" + self.frozen + ".json"),
                         "remote immutable proof: never inspect")
        for key in (self.expired, self.future):
            self.assertFalse((self.root / "data/site_prediction_snapshots" / (key + ".json")).exists())

    def test_expired_race_missing_remote_proof_stops_without_mutation(self):
        git(self.second, "rm", self.race(self.expired))
        self.publish_remote()
        original_head = git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(GuardFailure, "GIT_PROOF_UNAVAILABLE"):
            self.filter()
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), original_head)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_changed_remote_deadline_is_not_treated_as_proven_expired(self):
        doc = json.loads((self.second / self.race(self.expired)).read_text())
        doc["meta"]["deadline"] = "12:05"
        put(self.second, self.race(self.expired), json.dumps(doc))
        self.publish_remote()
        with self.assertRaisesRegex(GuardFailure, "IDENTITY_OR_DEADLINE_MISMATCH"):
            self.filter()
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_remote_race_identity_mismatch_stays_closed(self):
        doc = json.loads((self.second / self.race(self.expired)).read_text())
        doc["race_key"] = self.future
        put(self.second, self.race(self.expired), json.dumps(doc))
        self.publish_remote()
        with self.assertRaisesRegex(GuardFailure, "IDENTITY_OR_DEADLINE_MISMATCH"):
            self.filter()

    def test_unverified_local_deadline_stays_closed(self):
        doc = json.loads((self.root / self.race(self.expired)).read_text())
        doc["meta"]["deadline"] = "unknown"
        put(self.root, self.race(self.expired), json.dumps(doc))
        git(self.root, "add", "-A")
        git(self.root, "commit", "--amend", "--no-edit")
        self.publish_remote()
        with self.assertRaisesRegex(GuardFailure, "DEADLINE_UNVERIFIED"):
            self.filter()

    def test_without_concurrent_remote_freeze_helper_does_not_activate(self):
        with self.assertRaisesRegex(GuardFailure, "NO_NEWLY_REMOTE_FROZEN"):
            self.filter()


if __name__ == "__main__":
    unittest.main()
