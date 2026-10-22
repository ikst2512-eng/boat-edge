"""Audit one frozen feature record against its archived raw JSON bytes.

A matching hash proves byte consistency, NOT the original website publication time.
"""
import argparse
import hashlib
import json
from pathlib import Path
from feature_intake import ingest

def verify(record, raw_bytes):
    if not isinstance(record, dict) or record.get("schema") != "pre_race_features_v1":
        raise ValueError("unsupported record")
    if type(record.get("cutoff_minutes")) is not int:
        raise ValueError("missing cutoff")
    if not isinstance(raw_bytes, bytes) or not raw_bytes:
        raise ValueError("missing raw bytes")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != record.get("source_sha256"):
        raise ValueError("raw content does not match source SHA256")
    raw = json.loads(raw_bytes)
    expected = ingest(raw, raw_bytes, record["captured_at_jst"],
                      record["deadline_jst"], record["cutoff_minutes"])
    if record != expected:
        raise ValueError("frozen values differ from original")
    return {"race_code":record["race_code"], "byte_consistent":True,
            "cutoff_claim_consistent":True,
            "external_publication_proven":False}

if __name__=="__main__":
    cli=argparse.ArgumentParser(description="Compare frozen record to archived raw source")
    cli.add_argument("record",type=Path)
    cli.add_argument("original",type=Path)
    args=cli.parse_args()
    print(json.dumps(verify(json.loads(args.record.read_text(encoding="utf-8")),
                            args.original.read_bytes()),ensure_ascii=False,indent=2))
