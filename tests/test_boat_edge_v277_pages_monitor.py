import unittest
from datetime import datetime, timedelta, timezone
from scripts.boat_edge_v277_pages_monitor import report

NOW = datetime(2026, 10, 13, 0, 0, tzinfo=timezone.utc)
def iso(minutes): return (NOW + timedelta(minutes=minutes)).isoformat()
def ui(minutes): return [{"sha": "a" * 40, "commit": {"committer": {"date": iso(minutes)}}}]
def run(minutes, conclusion, status="completed"):
    return {"name":"pages build and deployment", "created_at": iso(minutes),
            "updated_at": iso(minutes+1), "head_sha":"b"*40,
            "conclusion":conclusion,"status":status}

class V277Tests(unittest.TestCase):
    def test_superseded_cancel_is_not_a_failure_when_newer_success_exists(self):
        d=report([run(-5,"success"),run(-6,"cancelled"),run(-7,"cancelled")],ui(-8),NOW)
        self.assertEqual(d["status"],"LATEST_UI_COVERED_BY_SUCCESSFUL_ACTIONS")
        self.assertEqual(d["pages_cancelled_recent"],2)
        self.assertFalse(d["ui_checked_in_safari"])
    def test_unpublished_ui_does_not_claim_latest(self):
        d=report([run(-50,"success"),run(-55,"cancelled")],ui(-30),NOW)
        self.assertEqual(d["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
    def test_pending_build_not_an_outage(self):
        d=report([run(-50,"success"),run(-1,None,"in_progress")],ui(-25),NOW)
        self.assertEqual(d["status"],"UI_PUBLISH_PENDING_ACTIVE_BUILD")
    def test_recent_ui_change_gets_grace_window(self):
        d=report([run(-50,"success")],ui(-5),NOW)
        self.assertEqual(d["status"],"UI_RECENTLY_CHANGED_WAIT_FOR_PUBLISH")
    def test_missing_ui_commit_fails_closed(self):
        self.assertEqual(report([run(-2,"success")],[],NOW)["status"],"UI_COMMIT_SOURCE_UNVERIFIED")
    def test_missing_time_fails_closed(self):
        self.assertEqual(report([run(-2,"success")],[{"sha":"x","commit":{}}],NOW)["status"],"UI_COMMIT_SOURCE_UNVERIFIED")
    def test_future_ui_commit_does_not_claim_outage(self):
        self.assertEqual(report([run(-30,"success")],ui(30),NOW)["status"],"CLOCK_SKEW_UNVERIFIED")
    def test_non_pages_run_ignored(self):
        d=report([{"name":"unrelated","created_at":iso(-1),"status":"completed","conclusion":"success"}],ui(-30),NOW)
        self.assertEqual(d["status"],"UI_PUBLISH_OVERDUE_NEEDS_ATTENTION")
if __name__=="__main__":unittest.main()
