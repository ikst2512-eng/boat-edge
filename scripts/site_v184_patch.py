from pathlib import Path
p=Path('scripts/site_v183_audit.py');s=p.read_text(encoding='utf-8')
marker='V184_COMMITTED_BYTES_AND_SOURCE_REPRODUCIBILITY'
if marker not in s:
    needle='''        if not okay:
            invalid.append({'race_key':key,'reason':reason});continue
        # Additional hard stop: first commit before race deadline using *pre-result* source snapshot.
        source=json_file(root/'data/site_prediction_snapshots'/f'{key}.json')'''
    repl='''        if not okay:
            invalid.append({'race_key':key,'reason':reason});continue
        # V184_COMMITTED_BYTES_AND_SOURCE_REPRODUCIBILITY: the first added Git blob
        # and the source file at that same commit MUST match this artifact.
        from site_v184_integrity import verify_shadow_commit_binding
        secure,reason,source=verify_shadow_commit_binding(root,rel,p.read_bytes(),data,added)
        if not secure:
            invalid.append({'race_key':key,'reason':reason});continue
        # Additional hard stop: use the originally COMMITTED source's deadline.
        # Current mutable snapshots must never be provenance for settled scoring.'''
    if s.count(needle)!=1:raise SystemExit('V184_UNEXPECTED_V183_SOURCE_LAYOUT')
    s=s.replace(needle,repl,1)
    p.write_text(s,encoding='utf-8')
print('V184_INDEPENDENT_PREDEADLINE_GIT_BLOB_GUARD_APPLIED')
