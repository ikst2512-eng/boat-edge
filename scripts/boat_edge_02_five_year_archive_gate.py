#!/usr/bin/env python3
"""Offline-only historical archive integrity gate. No downloads or result parsing."""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re

SCHEMA = "BOAT_EDGE_02_2021_2025_ARCHIVE_GATE_V1"
MONTHS = {f"{year:04d}-{month:02d}" for year in range(2021, 2026) for month in range(1,13)}
KINDS = {"pre_race_program", "post_race_result"}
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")

def _is_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("BAD_DATE") from None

def _safe_path(root, name):
    if not isinstance(name,str) or not name or "\\" in name or name.startswith("/"):
        raise ValueError("BAD_ARCHIVE_PATH")
    pure=Path(name)
    if any(part in (".","..") for part in pure.parts):
        raise ValueError("BAD_ARCHIVE_PATH")
    path=root/pure
    resolved=path.resolve()
    if not resolved.is_relative_to(root.resolve()) or not path.is_file() or path.is_symlink():
        raise ValueError("UNSAFE_OR_MISSING_ARCHIVE_FILE")
    return path

def _file_digest(path):
    checksum=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            checksum.update(chunk)
    return checksum.hexdigest()

def audit(manifest,archive_root,grant_file,*,repo_root=None):
    """Check operator supplied local bytes only. No independent license verification."""
    if not isinstance(manifest,dict) or manifest.get("schema")!=SCHEMA:
        raise ValueError("ARCHIVE_SCHEMA_REQUIRED")
    rights=manifest.get("rights")
    if not isinstance(rights,dict) or rights.get("review_status")!="HUMAN_REVIEWED_APPROVED":
        raise ValueError("RIGHTS_HUMAN_REVIEW_REQUIRED")
    if rights.get("automated_download") is not False or rights.get("third_party_scraping") is not False:
        raise ValueError("OFFLINE_MANUAL_SUPPLY_ONLY")
    for permission in ("local_archival_storage","offline_statistical_analysis","ml_training"):
        if rights.get(permission) is not True:
            raise ValueError("RIGHTS_SCOPE_MISSING:"+permission)
    for key in ("provider","rightsholder","grant_reference","reviewer","reviewed_at","grant_sha256"):
        if not isinstance(rights.get(key),str) or not rights[key].strip():
            raise ValueError("RIGHTS_PROVENANCE_MISSING")
    if not SHA_RE.fullmatch(rights["grant_sha256"]):
        raise ValueError("BAD_GRANT_SHA256")
    if rights.get("scope_years")!=[2021,2022,2023,2024,2025]:
        raise ValueError("FIVE_YEAR_RIGHTS_SCOPE_REQUIRED")
    if rights.get("data_kinds")!=sorted(KINDS):
        raise ValueError("BOTH_DATA_KINDS_RIGHTS_REQUIRED")
    expires=_is_date(rights.get("expires_on"))
    _is_date(rights.get("reviewed_at"))
    if expires<date.today():
        raise ValueError("GRANT_EXPIRED")
    root=Path(archive_root).resolve()
    grant=Path(grant_file).resolve()
    if not root.is_dir() or not grant.is_file():
        raise ValueError("ARCHIVE_ROOT_AND_GRANT_REQUIRED")
    if repo_root is not None:
        protected=(Path(repo_root).resolve()/"data").resolve()
        if root==protected or root.is_relative_to(protected) or grant.is_relative_to(protected):
            raise ValueError("PROTECTED_REPOSITORY_DATA_FORBIDDEN")
    if _file_digest(grant)!=rights["grant_sha256"]:
        raise ValueError("GRANT_BYTES_MISMATCH")
    partitions=manifest.get("partitions")
    if not isinstance(partitions,list) or len(partitions)!=len(MONTHS)*len(KINDS):
        raise ValueError("MONTHLY_120_PARTITIONS_REQUIRED")
    seen=set()
    names=set()
    total_bytes=0
    for p in partitions:
        if not isinstance(p,dict):
            raise ValueError("PARTITION_INVALID")
        month,kind=p.get("month"),p.get("kind")
        key=(month,kind)
        if month not in MONTHS or kind not in KINDS or key in seen:
            raise ValueError("PARTITION_DUPLICATE_OR_OUTSIDE_PERIOD")
        seen.add(key)
        if (type(p.get("declared_record_count")) is not int or p["declared_record_count"]<=0
                or type(p.get("size_bytes")) is not int or p["size_bytes"]<=0):
            raise ValueError("PARTITION_EMPTY_OR_UNCOUNTED")
        digest=p.get("sha256")
        if not isinstance(digest,str) or not SHA_RE.fullmatch(digest):
            raise ValueError("PARTITION_DIGEST_INVALID")
        name=p.get("file")
        if not isinstance(name,str) or name in names:
            raise ValueError("PARTITION_FILE_REUSED")
        names.add(name)
        path=_safe_path(root,name)
        if path.stat().st_size!=p["size_bytes"] or _file_digest(path)!=digest:
            raise ValueError("PARTITION_BYTE_INTEGRITY_FAILURE")
        total_bytes+=p["size_bytes"]
    if seen!={(m,k) for m in MONTHS for k in KINDS}:
        raise ValueError("ARCHIVE_MONTH_COVERAGE_INCOMPLETE")
    return {
        "schema":SCHEMA,"period":"2021-01-01..2025-12-31",
        "inventory_months":60,"verified_local_file_count":120,
        "verified_total_bytes":total_bytes,"archive_sha256_verified":True,
        "grant_document_sha256_verified":True,
        "permission_independently_verified":False,
        "monthly_coverage_declared_not_race_completeness":True,
        "predeadline_features_proven":False,"unseen_holdout_accuracy_proven":False,
        "model_promotion_authorized":False,"formal_fresh_results_accessed":False,
    }

def main():
    parser=argparse.ArgumentParser(description="Offline only: five-year source inventory")
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--archive-root",type=Path,required=True)
    parser.add_argument("--grant-file",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    result=audit(json.loads(args.manifest.read_text(encoding="utf-8")),args.archive_root,args.grant_file,repo_root=root)
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
