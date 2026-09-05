#!/usr/bin/env python3
"""Select at most two complementary, role-scoped references by default."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import icon_catalog as catalog


def load_references() -> list[dict]:
    result = []
    for manifest, key, source in [(catalog.NEW_MANIFEST,'reference_file','new-object-references'),(catalog.BASE_MANIFEST,'base_file','base-objects'),(catalog.MATERIAL_MANIFEST,'material_index_file','material-index')]:
        for row in catalog.load_assets(manifest, key):
            if row.get('type') != 'human':
                result.append({**row,'source':source})
    return result


def tokens(value: str) -> set[str]:
    return catalog.words(value)


def classify_orientation(query_tokens: set[str]) -> str:
    # Compatibility only; main code retains word order for compound identities.
    return catalog.default_orientation(' '.join(sorted(query_tokens)))


def orientation_prompt(orientation: str) -> str:
    return catalog.orientation_prompt(orientation)


def find_references(subject: str, max_refs: int = 2, material: str = '', composition: str = '') -> dict:
    if not 0 <= max_refs <= 5:
        raise ValueError('max_refs must be between 0 and 5')
    orientation = catalog.composition_orientation(composition) if composition else catalog.default_orientation(subject)
    identity = catalog.family(subject)
    wanted_materials = (catalog.words(subject) & catalog.MATERIALS) | catalog.words(material)
    if 'wooden' in wanted_materials:
        wanted_materials.add('wood')
    pool = load_references()
    chosen = []
    seen = set()

    def permitted(row: dict, role: str) -> bool:
        if row['source'] != 'new-object-references':
            return True
        return role in row.get('source_role','').split(';')

    def pick(candidates: list[tuple[int,dict]], role: str, transfer: str) -> None:
        for score, row in sorted(candidates, key=lambda item: (-item[0],item[1]['file'])):
            asset = row.get('asset_id') or row['path']
            if asset in seen:
                existing = next(r for r in chosen if (r.get('asset_id') or r['path']) == asset)
                if role not in existing['roles']:
                    existing['roles'].append(role)
                    existing['transfer'] += ' '+transfer
                if role=='material_reference':
                    existing['matched_terms'] = sorted(wanted_materials & (catalog.words(row.get('material_tags') or row.get('materials','')) | catalog.words(row.get('finish_tags',''))))
                break
            if len(chosen) >= max_refs:
                continue
            seen.add(asset)
            chosen.append({'file':row['file'],'path':row['path'],'asset_id':row.get('asset_id',''),'role':role,'roles':[role],'transfer':transfer,'materials':row.get('material_tags',row.get('materials','')),'finish':row.get('finish_tags','unknown'),'orientation':row.get('orientation','unknown'),'matched_terms':[] if role!='material_reference' else sorted(wanted_materials & (catalog.words(row.get('material_tags') or row.get('materials','')) | catalog.words(row.get('finish_tags',''))))})
            break

    forms = []
    mats = []
    comps = []
    for row in pool:
        if row['source'] == 'base-objects':
            ref_family = catalog.base_family(row)
        else:
            ref_family = row.get('object_family','')
        # Match exclusion phrases, not arbitrary words in explanatory notes.
        exclusions = row.get('avoid_for','').split(';')
        if any(p.strip() and catalog.has_phrase(subject,p) for p in exclusions):
            continue
        if identity and ref_family == identity and permitted(row,'form_reference'):
            score = 10 + len(catalog.words(subject) & catalog.words(row['file']))
            forms.append((score,row))
        materials = catalog.words(row.get('material_tags') or row.get('materials',''))
        finishes = catalog.words(row.get('finish_tags',''))
        overlap = wanted_materials & (materials | finishes)
        if overlap and permitted(row,'material_reference'):
            mats.append((len(overlap),row))
        # Only explicitly curated composition evidence can teach framing.
        if composition and row.get('composition_family') == composition and permitted(row,'composition_reference'):
            comps.append((1,row))
    pick(forms,'form_reference','Subject shape and functional parts only; do not copy palette, framing, shadows, or photographic style.')
    pick(mats,'material_reference','Surface, texture density and highlights only; do not copy object identity, camera, palette, or shadows.')
    pick(comps,'composition_reference','Camera, framing and mass balance only; retain requested subject and UC material style.')
    gaps = []
    if not forms:
        gaps.append('No approved matching form reference.')
    covered = set().union(*(set(r['matched_terms']) for r in chosen))
    missing = wanted_materials - covered
    if missing:
        gaps.append('No selected reference establishes material/finish: '+', '.join(sorted(missing)))
    if composition and not comps:
        gaps.append('Composition uses a text recipe; no approved composition exemplar yet.')
    roles = ' '.join(f'Image {i+1}: {r["transfer"]}' for i,r in enumerate(chosen))
    prompt = (f'Create one Waterlemon UC icon of {subject}. '+catalog.orientation_prompt(orientation)+'. '
              '1024x768 PNG, solid #f5f5f5 background, centered premium tactile 3D micro-object, full subject visible with comfortable margins. '
              'Soft studio light, softened edges, simplified believable matte-to-satin materials, compact palette, clear silhouette. '
              'No cast/drop/contact/floor shadow, text, logos, people or scene clutter; maximum two visual masses. '
              +(f'Requested material/finish: {material}. ' if material else '')+roles)
    return {'subject':subject,'mode':'no_reference' if not chosen else 'closest_product_reference' if chosen[0]['role']=='form_reference' and len(chosen)==1 else 'style_reference_set',
            'orientation':orientation,'references':chosen,'reference_count':len(chosen),'coverage_gaps':gaps,'prompt':prompt,
            'instruction':'Use only these explicit referenced_image_paths. Never use recent conversation images or search output folders.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',required=True)
    parser.add_argument('--max',type=int,choices=range(0,6),default=2)
    parser.add_argument('--material',default='')
    parser.add_argument('--composition',choices=catalog.COMPOSITIONS,default='')
    args=parser.parse_args()
    print(json.dumps(find_references(args.subject,args.max,args.material,args.composition),indent=2))
