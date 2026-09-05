#!/usr/bin/env python3
"""Resolve one icon request without rendering or modifying images."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import icon_catalog as catalog

PRESERVE = 'identity, orientation, perspective, crop, proportions, optical size, lighting, existing shadows, materials, and untouched parts'


def compact_candidate(row: dict) -> dict:
    return {k:row.get(k,'') for k in ('file','path','asset_id','type','orientation')}


def with_base(result: dict, row: dict, change: str) -> dict:
    if not row.get('orientation') or row.get('orientation') == 'unknown':
        sibling = next((r for r in catalog.bases() if r['path']==row['path']), None)
        if sibling:
            row = {**row, 'orientation': sibling.get('orientation','unknown')}
    return {**result,'mode':'base_edit' if change else 'export_existing','base_path':row['path'],'asset_id':row.get('asset_id',''),'orientation':row.get('orientation','unknown'),'requested_change':change,'must_preserve':PRESERVE,'prompt_template':'base-image-edit' if change else 'export'}


def plan_icon(subject: str, change: str = '', new_design: bool = False, gender: str = '', eyes: str = '', composition: str = '', material: str = '', max_refs: int = 2) -> dict:
    if not subject.strip():
        raise ValueError('An icon subject is required')
    # Preserve compatibility with older whole-request --subject invocations.
    parts = re.split(r'\b(remove|recolou?r|without|add|swap|replace|make)\b', subject, maxsplit=1, flags=re.I)
    if len(parts) == 3:
        subject = parts[0].strip()
        inline_change = (parts[1]+' '+parts[2]).strip()
        change = inline_change + ('; '+change if change else '')
    result={'subject':subject,'requested_change':change,'mode':'new_generation','base_path':None,'references':[],'must_preserve':'','background':'#f5f5f5','export_policy':'contain-and-composite-only'}
    exact=[r for r in catalog.services()+catalog.bases() if catalog.normalize(Path(r['file']).stem)==catalog.normalize(subject)]
    if exact and not new_design and not any((gender,eyes)):
        unique={r['path']:r for r in exact}
        if len(unique)>1:
            return {**result,'mode':'ask_user','question':'Choose the intended asset.','candidates':[compact_candidate(r) for r in unique.values()]}
        return apply_options(with_base(result,next(iter(unique.values())),change), composition, material)

    if catalog.is_human(subject):
        query=catalog.words(subject)
        gender=gender or ('female' if query & {'female','woman','women','girl','lady'} else 'male' if query & {'male','man','men','boy'} else '')
        if not gender:
            return {**result,'mode':'ask_user','question':'Choose the canonical character base: female or male.','candidates':['female','male']}
        eyes=eyes or ('closed' if 'closed' in query else 'open' if 'open' in query else 'closed' if query & {'spa','salon','massage','pampering','resting'} else 'open')
        path=catalog.SKILL_DIR / f'references/characters/base/base-{gender}-eyes-{eyes}.png'
        if not path.is_file():
            name=f'{"Woman" if gender=="female" else "Man"} face (eyes {eyes}).png'
            fallback=next((r for r in catalog.bases() if r['file']==name),None)
            path=Path(fallback['path']) if fallback else path
        if not path.is_file():
            return {**result,'mode':'blocked','reason':'Required canonical character base unavailable; do not generate a replacement identity.'}
        return apply_options({**result,'mode':'base_edit','subject_kind':'character','base_path':str(path),'orientation':'front-bust','must_preserve':PRESERVE,'requested_change':f'Create the requested {subject} service variant using the same character.'+(' '+change if change else ''),'prompt_template':'base-image-edit'},composition,material)

    if not new_design:
        # A named service followed by a local edit keeps that service's identity.
        contextual = []
        if subject:
            for service in catalog.services():
                name = catalog.normalize(Path(service['file']).stem)
                if catalog.normalize(subject).startswith(name+' '):
                    base = next((r for r in catalog.bases() if r['path']==service['path']), None)
                    if base and catalog.family(subject)==catalog.base_family(base):
                        contextual.append(base)
        candidates=contextual or catalog.choose_bases(subject)
        if len(candidates)>1:
            return {**result,'mode':'ask_user','question':'Choose the intended object variant.','candidates':[compact_candidate(r) for r in candidates]}
        if candidates:
            candidate=candidates[0]
            represented=catalog.words(candidate['file']+' '+candidate.get('objects','')+' '+candidate.get('colors','')+' '+candidate.get('materials','')+' '+candidate.get('material_tags',''))
            qualifiers=catalog.words(subject) & (catalog.COLORS | catalog.MATERIALS)
            if re.search(r'\bwith\b',subject):
                change=f'Match requested accessory details: {subject}.'+(' '+change if change else '')
            if qualifiers-represented or contextual:
                change=f'Match requested subject details: {subject}.'+(' '+change if change else '')
            if ' with ' in catalog.normalize(Path(candidate['file']).stem) and ' with ' not in catalog.normalize(subject):
                change=f'Keep only the requested subject: {subject}; remove unrequested accessory props.'+(' '+change if change else '')
            if material:
                change=(change+'; ' if change else '')+f'Apply requested material/finish: {material}.'
            result=with_base(result,candidate,change)
            if composition:
                desired=catalog.composition_orientation(composition)
                if desired!=result['orientation']:
                    result.update(mode='base_edit',requested_change=(change+'; ' if change else '')+f'Use explicitly requested {composition} composition.',orientation=desired,must_preserve='identity, materials, lighting, and untouched details; composition explicitly overridden',prompt_template='base-image-edit')
            return result
    from find_generation_references import find_references
    refs=find_references(subject,max_refs,material=material,composition=composition)
    return {**result,'subject_kind':'object','orientation':refs['orientation'],'references':refs['references'],'reference_mode':refs['mode'],'coverage_gaps':refs['coverage_gaps'],'prompt':refs['prompt']+(' Additional request: '+change if change else ''),'prompt_template':'new-generation'}


def apply_options(result: dict, composition: str, material: str) -> dict:
    additions = []
    if material:
        additions.append(f'Apply requested material/finish: {material}.')
    if composition:
        desired = 'front-bust' if composition=='front' and result.get('subject_kind')=='character' else catalog.composition_orientation(composition)
        if desired != result['orientation']:
            additions.append(f'Use explicitly requested {composition} composition.')
            result['orientation'] = desired
            result['must_preserve'] = 'identity, materials, lighting and untouched details; composition explicitly overridden'
    if additions:
        result.update(mode='base_edit',prompt_template='base-image-edit',requested_change=' '.join([result['requested_change'],*additions]).strip())
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',required=True,help='Object or exact service name; put edits in --change.')
    parser.add_argument('--change',default='')
    parser.add_argument('--new-design',action='store_true',help='Skip object reuse; characters still preserve a canonical base.')
    parser.add_argument('--gender',choices=('female','male'),default='')
    parser.add_argument('--eyes',choices=('open','closed'),default='')
    parser.add_argument('--composition',choices=catalog.COMPOSITIONS,default='')
    parser.add_argument('--material',default='')
    parser.add_argument('--max-refs',type=int,choices=range(0,6),default=2)
    args=parser.parse_args()
    print(json.dumps(plan_icon(args.subject,args.change,args.new_design,args.gender,args.eyes,args.composition,args.material,args.max_refs),indent=2))


if __name__=='__main__':
    main()
