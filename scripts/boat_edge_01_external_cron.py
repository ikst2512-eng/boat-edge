#!/usr/bin/env python3
"""One independently hosted Cron, TWO separately authorized existing workflows.

V235 prediction freeze and V216 source-ready observation have different
owners and opt-in flags. Running one never implicitly opts into the other.
No new GitHub schedule, prediction writer, result API or second paid Cron.
"""
from __future__ import annotations
import sys
import boat_edge_01_v235_external_gap_watchdog as prediction
import boat_edge_01_v216_external_source_watchdog as observation


def main(argv=None):
    args=['--live'] if argv is None else list(argv)
    if args not in (['--live'], []):
        raise ValueError('only --live or dry-run permitted')
    # Never let a V235 API error suppress a separately permitted V216 check.
    # Both still fail closed individually on unknown sources/runtime state.
    p=prediction.main(args)
    v=observation.main(args)
    return max(p,v)


if __name__=='__main__':
    sys.exit(main())
