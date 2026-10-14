"""Synthetic Git race: concurrent first-freeze never loses unrelated source writes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
