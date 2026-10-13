"""V367 immutable source-only replay, byte tamper and time-order contract."""
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v366_isolated_source_only_capture import capture_source_only
from boat_edge_v367_source_only_replay import replay_one
from test_boat_edge_v236_v366_isolated_source_only_capture import (
    setup_case, source_pages, fetcher_for,
)
from test_boat_edge_v236_v364_v230_v336_selection_contract import NOW, KEY


def saved(root):
    setup_case(root)
    result = capture_source_only(root, KEY, clock=lambda: NOW,
                                 fetcher=fetcher_for(source_pages()))
    path = root / result["path"]
    return path, result


def mutate_manifest(path, action):
    file = path / "manifest.json"
    data = json.loads(file.read_bytes())
    action(data)
    file.write_bytes(canonical(data) + b"\n")


class V367ExactSourceOnlyReplay(unittest.TestCase):
    def test_exact_replay_survives_deletion_of_mutable_site_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, saved_result = saved(root)
            original_bytes = {p.name: p.read_bytes() for p in folder.iterdir()}
            self.assertEqual((folder / "race_input.json").read_bytes(),
                             (root / "data/races" / (KEY + ".json")).read_bytes())
            for rel in (
                "data/today.json",
                "data/races/" + KEY + ".json",
                "data/site_prediction_snapshots/" + KEY + ".json",
            ):
                (root / rel).unlink()
            run1 = replay_one(root, KEY, saved_result["manifest_sha256"])
            run2 = replay_one(root, KEY, saved_result["manifest_sha256"])
            self.assertEqual(canonical(run1), canonical(run2))
            self.assertTrue(run1["six_registrations_and_exhibition_rows_replayed"])
            self.assertTrue(run1["official_selected_race_deadline_and_course_replayed"])
            self.assertTrue(run1["local_receipt_timeline_consistent"])
            self.assertFalse(run1["independent_source_or_server_timestamp_authenticated"])
            self.assertFalse(run1["live_race_freeze_proven"])
            self.assertFalse(run1["results_read"])
            self.assertFalse(run1["formal_fresh_read"])
            self.assertFalse(run1["writes_performed"])
            self.assertEqual(
                original_bytes,
                {p.name: p.read_bytes() for p in folder.iterdir()})

    def test_both_source_tampering_detected_by_immutable_sha(self):
        for kind in ("racelist", "beforeinfo"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                folder, data = saved(root)
                target = folder / (kind + ".html")
                target.write_bytes(target.read_bytes() + b"tamper")
                with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_SHA_MISMATCH"):
                    replay_one(root, KEY, data["manifest_sha256"])
                self.assertFalse((root / "data/research_local_v332").exists())

    def test_archived_race_tamper_detected_even_when_current_race_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, data = saved(root)
            archive = folder / "race_input.json"
            archive.write_bytes(archive.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "ARCHIVED_INPUT_SHA_MISMATCH"):
                replay_one(root, KEY, data["manifest_sha256"])

    def test_manifest_broken_and_recomputed_changes_rejected_with_expected_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, data = saved(root)
            manifest = folder / "manifest.json"
            manifest.write_bytes(manifest.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "EXPECTED_MANIFEST_SHA_MISMATCH"):
                replay_one(root, KEY, data["manifest_sha256"])
            with self.assertRaisesRegex(ValueError, "MANIFEST_NOT_CANONICAL"):
                replay_one(root, KEY)
            mutate_manifest(folder, lambda m: m.__setitem__("results_read", True))
            with self.assertRaisesRegex(ValueError, "UNTRUSTED_MANIFEST_CLAIMS"):
                replay_one(root, KEY)

    def test_recomputed_source_sha_cannot_mask_rewritten_official_course(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            path = folder / "beforeinfo.html"
            altered = path.read_bytes().replace(b"img_boat2_2.png", b"img_boat2_1.png")
            path.write_bytes(altered)
            mutate_manifest(folder, lambda m: m["sources"]["beforeinfo"].update(
                {"sha256": hashlib.sha256(altered).hexdigest(), "bytes": len(altered)}))
            with self.assertRaisesRegex(ValueError, "ICON_MISMATCH"):
                replay_one(root, KEY)

    def test_wrong_source_url_filename_and_extra_files_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            mutate_manifest(folder, lambda m: m["sources"]["racelist"].__setitem__(
                "url", "https://www.boatrace.jp/owpc/pc/race/racelist?hd=20261013&jcd=22&rno=11"))
            with self.assertRaisesRegex(ValueError, "SOURCE_URL_OR_PATH_INVALID"):
                replay_one(root, KEY)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            (folder / "untrusted.json").write_text("do not open")
            with self.assertRaisesRegex(ValueError, "ARCHIVE_UNEXPECTED_OR_MISSING_FILES"):
                replay_one(root, KEY)

    def test_receipt_timeline_and_result_flags_are_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            mutate_manifest(folder, lambda m: m["sources"]["beforeinfo"].__setitem__(
                "received_at_jst", (NOW + timedelta(minutes=11)).isoformat()))
            with self.assertRaisesRegex(ValueError, "TIMELINE_INVALID|WINDOW_INVALID"):
                replay_one(root, KEY)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            mutate_manifest(folder, lambda m: m.__setitem__("source_proof_at_jst",
                                                            "2026-10-13T16:42:00+09:00"))
            with self.assertRaisesRegex(ValueError, "TIMELINE_INVALID|WINDOW_INVALID"):
                replay_one(root, KEY)

    def test_manifest_parser_field_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            mutate_manifest(folder, lambda m: m["official_start_course_proof"][
                "course_by_boat"].__setitem__("1", 5))
            with self.assertRaisesRegex(ValueError, "PARSER_PROOF_DRIFT"):
                replay_one(root, KEY)

    def test_race_archive_symlink_and_formal_target_never_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = saved(root)
            race_file = folder / "race_input.json"
            data = race_file.read_bytes()
            race_file.unlink()
            external = root / "external_race.txt"
            external.write_bytes(data)
            race_file.symlink_to(external)
            with self.assertRaisesRegex(ValueError, "SYMLINK_FORBIDDEN"):
                replay_one(root, KEY)
            with self.assertRaisesRegex(ValueError, "INVALID_OR_FORMAL"):
                replay_one(root, "20261001-22-12")

    def test_invalid_claims_cannot_be_enabled_by_editing_manifest(self):
        for flag in ("site_first_prediction_changed", "source_publication_performed",
                     "research_freeze_performed", "accuracy_improvement_proven",
                     "formal_fresh_read", "results_read"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                folder, _ = saved(root)
                mutate_manifest(folder, lambda m: m.__setitem__(flag, True))
                with self.assertRaisesRegex(ValueError, "UNTRUSTED_MANIFEST_CLAIMS"):
                    replay_one(root, KEY)


if __name__ == "__main__":
    unittest.main()
