#!/usr/bin/env python3
"""Compatibility preflight. Prefer plan_icon.py for complete routing."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from plan_icon import plan_icon


def find_candidates(query: str, limit: int = 5) -> dict:
    plan=plan_icon(query)
    mode=plan['mode']
    candidates=plan.get('candidates',[])[:limit]
    if plan.get('base_path'):
        candidates=[{'path':plan['base_path'],'base_file':Path(plan['base_path']).name,'orientation':plan['orientation']}]
    return {'query':query,'status':'single' if plan.get('base_path') else 'ambiguous' if mode=='ask_user' else 'not_found','candidates':candidates,'decision':'use_base_image' if plan.get('base_path') else 'ask_user_to_choose' if mode=='ask_user' else 'no_base_found','mode':mode,'reason':plan.get('reason',''),'question':plan.get('question','')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',required=True)
    parser.add_argument('--limit',type=int,default=5)
    args=parser.parse_args()
    print(json.dumps(find_candidates(args.subject,args.limit),indent=2))
