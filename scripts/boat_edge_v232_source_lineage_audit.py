#!/usr/bin/env python3
"""Read-only V232 source lineage inventory; not model reproducibility proof."""
import json
from pathlib import Path

INPUTS = {
    "prediction": "data/site_prediction_snapshots",
    "prediction_audit": "data/site_prediction_audit",
    "race_card": "data/races",
    "scratch": "data/site_scratches_v182",
    "odds_receipt": "data/site_prediction_snapshots/odds_v214",
}

def audit(root):
    root=Path(root)
    source=(root/"scripts/boat_edge_v232_pre_result_cohort.py").read_text(encoding="utf-8")
    missing=[name for name,path in INPUTS.items() if path not in source]
    return {
        "schema":"BOAT_EDGE_V232_READ_ONLY_SOURCE_LINEAGE_INVENTORY_V1",
        "scope":"SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH",
        "source_script":"scripts/boat_edge_v232_pre_result_cohort.py",
        "upstream_input_directories":INPUTS,
        "source_reference_missing":missing,
        "prediction_generator_code_independently_identified":False,
        "runtime_data_lineage_independently_verified":False,
        "static_import_coverage_is_not_model_coverage":True,
        "model_completeness_attested":False,
        "accuracy_improvement_proven":False,
    }

if __name__=="__main__":
    print(json.dumps(audit(Path(".")),indent=2,sort_keys=True))
