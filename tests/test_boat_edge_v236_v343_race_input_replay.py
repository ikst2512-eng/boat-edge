"""Exact input replay with synthetic PRE_RESULT fixtures only."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v332_live_local_freeze import live_local_freeze
from boat_edge_v343_race_input_replay import verify
from test_boat_edge_v236_v332_live_local_e2e import KEY, PRE, prepare, mock_page
from test_boat_edge_v236_v339_cross_run_audit import report


def bundle(root, fetcher=mock_page):
    prepare(root)
    frozen = live_local_freeze(root, KEY, capture=True, fetcher=fetcher, clock=lambda: PRE)
    r = report(digest=frozen["sha256"])
    return r, root / frozen["path"], root / f"data/source_captures/{KEY[:8]}/{KEY}/race_input.json"


def rewrite_freeze(path, report_doc, edit):
    obj = json.loads(path.read_bytes())
    edit(obj)
    obj["candidate_sha256"] = hashlib.sha256(canonical(obj["candidate"])).hexdigest()
    raw = canonical(obj) + b"\n"
    path.write_bytes(raw)
    report_doc["completed"][0]["sha256"] = hashlib.sha256(raw).hexdigest()


class V343ExactInputReplay(unittest.TestCase):
    def test_exact_bytes_and_candidate_reproduce_without_live_card_or_formal_reads(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r, freeze, snapshot = bundle(root)
            original = (root / f"data/races/{KEY}.json").read_bytes()
            self.assertEqual(snapshot.read_bytes(), original)
            (root / f"data/races/{KEY}.json").unlink()
            (root / "data/formal_status.json").write_text("MUST_NOT_BE_READ")
            result = verify(root, r)
            self.assertTrue(result["candidate_replay_verified_within_supplied_report"])
            self.assertTrue(result["rows"][0]["exact_candidate_reproduced"])
            self.assertFalse(result["source_html_integrity_verified"])
            self.assertFalse(result["results_read"])
            self.assertFalse(result["eligible_for_formal_fresh_scoring"])

    def test_source_card_changed_during_http_capture_preserves_original_input(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            race_path = root / f"data/races/{KEY}.json"
            original = race_path.read_bytes()
            def changing_page(url):
                race_path.write_text("LIVE_CARD_CHANGED_DURING_CAPTURE")
                return mock_page(url)
            frozen = live_local_freeze(root, KEY, capture=True, fetcher=changing_page, clock=lambda: PRE)
            snapshot = root / f"data/source_captures/{KEY[:8]}/{KEY}/race_input.json"
            self.assertEqual(snapshot.read_bytes(), original)
            self.assertTrue(verify(root, report(digest=frozen["sha256"]))[
                "candidate_replay_verified_within_supplied_report"])

    def test_missing_old_snapshot_cannot_be_reconstructed_from_live_card(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r, frozen, snapshot = bundle(root)
            snapshot.unlink()
            with self.assertRaisesRegex(ValueError, "MISSING_OR_OUTSIDE_ROOT"):
                verify(root, r)
            self.assertFalse(snapshot.exists())

    def test_modified_input_bytes_fail_even_when_parseable(self):
        with tempfile.TemporaryDirectory() as d:
            r, _, snapshot = bundle(Path(d))
            snapshot.write_bytes(snapshot.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "RACE_INPUT_SHA_MISMATCH"):
                verify(Path(d), r)

    def test_modified_candidate_with_all_hashes_recomputed_still_fails_replay(self):
        with tempfile.TemporaryDirectory() as d:
            r, frozen, _ = bundle(Path(d))
            def swap(obj):
                tickets = obj["candidate"]["modes"]["national_only"]["top10_boat_research_only"]
                tickets[0], tickets[1] = tickets[1], tickets[0]
            rewrite_freeze(frozen, r, swap)
            with self.assertRaisesRegex(ValueError, "CANDIDATE_INPUT_REPLAY_MISMATCH"):
                verify(Path(d), r)

    def test_freeze_mutation_without_report_rehash_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r, frozen, _ = bundle(Path(d))
            frozen.write_bytes(frozen.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "REPORTED_FREEZE_SHA_MISMATCH"):
                verify(Path(d), r)

    def test_stale_original_input_at_final_write_time_blocks_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            prepare(root)
            calls = 0
            def slow_page(url):
                nonlocal calls
                calls += 1
                return mock_page(url)
            # Three captures finish at 16:34; source beforeinfo from 16:19
            # is then exactly 15m old. The final snapshot+write reaches 16:35.
            times = iter([PRE] * 7 + [PRE + timedelta(minutes=14), PRE + timedelta(minutes=15)])
            def clock():
                return next(times, PRE + timedelta(minutes=15))
            with self.assertRaisesRegex(ValueError, "SOURCE_TOO_STALE"):
                live_local_freeze(root, KEY, capture=True, fetcher=slow_page, clock=clock)
            self.assertFalse((root / f"data/research_local_v332/{KEY[:8]}/{KEY}.json").exists())

    def test_snapshot_retry_never_overwrites_changed_input(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r, frozen, snapshot = bundle(root)
            saved = snapshot.read_bytes()
            frozen.unlink()  # synthetic interrupted-final-write simulation
            race_path = root / f"data/races/{KEY}.json"
            obj = json.loads(race_path.read_bytes())
            obj["racers"][0]["national"]["win_rate"] = 1.0
            race_path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, "IMMUTABLE_RACE_INPUT_SNAPSHOT_MISMATCH"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertEqual(snapshot.read_bytes(), saved)
            self.assertFalse(frozen.exists())

    def test_identical_snapshot_retry_can_finish_interrupted_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r, frozen, snapshot = bundle(root)
            original = frozen.read_bytes()
            frozen.unlink()
            resumed = live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertEqual(frozen.read_bytes(), original)
            self.assertEqual(resumed["sha256"], r["completed"][0]["sha256"])

    def test_snapshot_file_and_ancestor_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r, frozen, snapshot = bundle(root)
            raw = snapshot.read_bytes()
            frozen_raw = frozen.read_bytes()
            snapshot.unlink()
            elsewhere = root / "elsewhere.json"
            elsewhere.write_bytes(raw)
            snapshot.symlink_to(elsewhere)
            with self.assertRaisesRegex(ValueError, "SYMLINK_FORBIDDEN"):
                verify(root, r)
            frozen.unlink()
            with self.assertRaisesRegex(ValueError, "SNAPSHOT_SYMLINK_FORBIDDEN"):
                live_local_freeze(root, KEY, clock=lambda: PRE)
            self.assertFalse(frozen.exists())
            frozen.write_bytes(frozen_raw)
            snapshot.unlink()
            snapshot.write_bytes(raw)
            relocated = root / "relocated-captures"
            snapshot.parent.rename(relocated)
            snapshot.parent.symlink_to(relocated, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "SYMLINK_FORBIDDEN"):
                verify(root, r)

    def test_result_guard_and_formal_report_rejected_before_artifact_access(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r, frozen, _ = bundle(root)
            rewrite_freeze(frozen, r, lambda o: o.update(results_read=True))
            with self.assertRaisesRegex(ValueError, "RESEARCH_ONLY_GUARDS"):
                verify(root, r)
        with self.assertRaisesRegex(ValueError, "NONFORMAL_DATE_REQUIRED"):
            verify(Path("/missing"), report("20261001-22-12"))

    def test_zero_completed_freezes_are_not_verified(self):
        result = verify(Path("/missing"), report(completed=False))
        self.assertFalse(result["candidate_replay_verified_within_supplied_report"])
        self.assertEqual(result["rows"], [])

    def test_two_independent_synthetic_runs_have_identical_bytes(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, freeze_a, snapshot_a = bundle(Path(a))
            second, freeze_b, snapshot_b = bundle(Path(b))
            self.assertEqual(freeze_a.read_bytes(), freeze_b.read_bytes())
            self.assertEqual(snapshot_a.read_bytes(), snapshot_b.read_bytes())
            self.assertEqual(canonical(verify(Path(a), first)), canonical(verify(Path(b), second)))


if __name__ == "__main__":
    unittest.main()
