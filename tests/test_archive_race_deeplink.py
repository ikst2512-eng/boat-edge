from pathlib import Path
import unittest


class ArchiveRaceNavigationTest(unittest.TestCase):
    def test_archive_links_to_race_screen_not_raw_json(self):
        page = Path("archive.html").read_text(encoding="utf-8")
        self.assertIn("a.href='./index.html?race='+encodeURIComponent(x.race_key)", page)
        self.assertNotIn("a.href='./data/races/'+encodeURIComponent(x.race_key)+'.json'", page)

    def test_deep_link_uses_existing_identity_guard_and_safe_fetch(self):
        page = Path("index.html").read_text(encoding="utf-8")
        self.assertIn('function openArchivedRaceFromUrl()', page)
        self.assertIn('loadRace("data/races/"+key+".json",jcd)', page)
        self.assertIn('if(!be03RaceSourceIdentity(file,jcd,race))', page)
        self.assertIn('refreshAll().then(openArchivedRaceFromUrl);', page)
        self.assertIn('loadFormalOverlay(race.race_key)', page)


if __name__ == "__main__":
    unittest.main()
