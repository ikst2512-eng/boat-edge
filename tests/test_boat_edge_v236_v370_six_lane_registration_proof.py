"""V370 explicit six-boat registration parity, no implied lane=registration.

Fixture-only + non-predictive smoke parse of a previously saved official
racelist: NEVER retrospective prediction or authenticated source timing.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from boat_edge_v370_official_racelist_lane_proof import proof_six_lane_registrations
from boat_edge_v366_isolated_source_only_capture import capture_source_only
from test_boat_edge_v236_v366_isolated_source_only_capture import (
    source_pages, setup_case, fetcher_for,
)
from test_boat_edge_v236_v364_v230_v336_selection_contract import NOW, KEY


class V370SixBoatRegIdentity(unittest.TestCase):
    def test_matching_profile_photo_number_and_lane_in_mock_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            race = json.loads((root / "data/races" / (KEY + ".json")).read_bytes())
            raw = source_pages()[0]
            p = proof_six_lane_registrations(raw, race["racers"])
            self.assertEqual(p["lane_to_registration"], {
                str(lane): str(4000 + lane) for lane in range(1, 7)
            })
            self.assertTrue(p["six_lane_racer_photo_printed_registration_matched"])
            self.assertFalse(p["source_authenticity_independently_verified"])

    def test_swapped_1_and_2_registration_numbers_fail_despite_set_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            a, b = source_pages()
            # Swapping only expected lane assignments preserves the same six
            # racer numbers, which V366's previous set-only check accepted.
            race_path = root / "data/races" / (KEY + ".json")
            race = json.loads(race_path.read_bytes())
            race["racers"][0]["registration_no"], race["racers"][1]["registration_no"] = (
                race["racers"][1]["registration_no"], race["racers"][0]["registration_no"]
            )
            race_path.write_text(json.dumps(race))
            with self.assertRaisesRegex(ValueError, "LANE_REGISTRATION_MISMATCH"):
                capture_source_only(root, KEY, clock=lambda: NOW,
                                    fetcher=fetcher_for((a, b)))
            self.assertFalse((root / "data/research_source_only_v366").exists())

    def test_photo_profile_mismatch_and_printed_reg_mismatch_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            race = json.loads((root / "data/races" / (KEY + ".json")).read_bytes())
            a, _ = source_pages()
            for changed, reason in (
                (a.replace(b"/racerphoto/4001.jpg", b"/racerphoto/4002.jpg"),
                 "PHOTO_PROFILE_ID_MISMATCH"),
                (a.replace(b"<div>4001 /", b"<div>4444 /"),
                 "PRINTED_REGISTERED_NUMBER_MISMATCH"),
                (a.replace(b"is-boatColor1", b"is-boatColor2"),
                 "DUPLICATE_BOAT_COLOR_LANE"),
            ):
                with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                    proof_six_lane_registrations(changed, race["racers"])

    def test_unlabelled_six_registrations_never_create_lane_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_case(root)
            race = json.loads((root / "data/races" / (KEY + ".json")).read_bytes())
            unlabelled = ("<html><table>" + "".join(
                f"<tr><td>{4000 + lane} / A1</td></tr>" for lane in range(1, 7)
            ) + "</table></html>").encode()
            with self.assertRaisesRegex(ValueError, "OFFICIAL_RACER_TABLE_NOT_UNIQUE"):
                proof_six_lane_registrations(unlabelled, race["racers"])

    def test_already_saved_same_day_official_racelist_structure_as_offline_fixture(self):
        # This is merely a structural regression from stored source files.
        # It is NOT a live/fresh capture, prospective frozen prediction,
        # independent source timestamp proof, or result lookup.
        source = ROOT / "data/raw/20261013/15_02_racelist.html"
        card = ROOT / "data/races/20261013-15-02.json"
        self.assertTrue(source.is_file() and card.is_file())
        raw = source.read_bytes()
        race = json.loads(card.read_bytes())
        mapping = proof_six_lane_registrations(raw, race["racers"])
        self.assertEqual(
            mapping["lane_to_registration"],
            {str(r["lane"]): str(r["registration_no"]) for r in race["racers"]},
        )
        self.assertFalse(mapping["source_authenticity_independently_verified"])


if __name__ == "__main__":
    unittest.main()
