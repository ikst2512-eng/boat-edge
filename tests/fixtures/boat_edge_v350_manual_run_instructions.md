# V350 manual scheduled Actions evidence export

After merging this PR to main, open Actions > BOAT EDGE V350 Actions Evidence (manual read-only) > Run workflow, select main, and run with max_pages=3. Download the artifact named boat-edge-v350-scheduled-run-evidence from the completed run. It contains V348 run metadata and V349 same-start hints.

This workflow is manually triggered only. It uses read-only actions/contents permissions, does not push commits, and does not stop any production writer. V348's updated_at is NOT a verified completion timestamp, and neither file proves changed paths or concurrent duplicate writes. Review actual run jobs, logs, and commit provenance before retiring any workflow.
