"""V285 must prove identical UI last-touch commits at main and deployed Pages SHA."""
import unittest
from datetime import datetime, timezone, timedelta
from scripts.boat_edge_v277_pages_monitor import report, same_ui_lineage

NOW=datetime(2026,10,13,0,0,tzinfo=timezone.utc)
def when(m): return (NOW+timedelta(minutes=m)).isoformat()
def ui(suffix="a",minutes=-45):
    return [{"sha":suffix*40,"commit":{"committer":{"date":when(minutes)}}}]
def page(minutes=-1,conclusion="success",status="completed"):
    return {"name":"pages build and deployment","head_sha":"f"*40,
            "created_at":when(minutes),"updated_at":when(minutes+1),
            "conclusion":conclusion,"status":status}

class PagesLineageV285(unittest.TestCase):
    def test_timestamp_later_than_ui_without_matching_sha_is_not_published(self):
        out=report([page(-1)],ui("a",-40),NOW,deployed_ui_commits=ui("b",-45))
        self.assertEqual(out["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
        self.assertFalse(out["ui_lineage_verified"])
    def test_data_only_main_commits_do_not_invalidate_deployed_ui(self):
        out=report([page(-8),page(-11,"cancelled")],ui("a",-30),NOW,deployed_ui_commits=ui("a",-30))
        self.assertEqual(out["status"],"LATEST_UI_COVERED_BY_SUCCESSFUL_ACTIONS")
        self.assertTrue(out["ui_lineage_verified"])
        self.assertEqual(out["pages_cancelled_recent"],1)
        self.assertFalse(out["ui_checked_in_safari"])
    def test_missing_api_proof_fails_closed(self):
        out=report([page(-1)],ui("a",-40),NOW)
        self.assertEqual(out["status"],"PAGES_UI_LINEAGE_UNVERIFIED")
        self.assertFalse(out["ui_lineage_verified"])
    def test_new_head_commit_on_one_path_invalidates_claim(self):
        cur=ui("a",-30)+ui("b",-20)
        dep=ui("a",-30)+ui("c",-40)
        out=report([page(-1)],cur,NOW,deployed_ui_commits=dep)
        self.assertEqual(out["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
    def test_empty_or_invalid_lineage_does_not_pass(self):
        self.assertFalse(same_ui_lineage([],[]))
        self.assertFalse(same_ui_lineage(ui("a"),[]))
        self.assertFalse(same_ui_lineage(ui("a"),[{"sha":"broken"}]))
        self.assertFalse(same_ui_lineage(ui("a"),ui("b")))
    def test_active_build_never_claims_published_without_matching_proof(self):
        runs=[page(-40),page(-1,None,"in_progress")]
        out=report(runs,ui("a",-30),NOW,deployed_ui_commits=ui("c",-50))
        self.assertEqual(out["status"],"UI_PUBLISH_PENDING_ACTIVE_BUILD")
if __name__=="__main__":
    unittest.main()
