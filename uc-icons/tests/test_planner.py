from __future__ import annotations
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0,str(SCRIPTS))
import icon_catalog as catalog
from plan_icon import plan_icon
from find_base_object import find_candidates
from find_generation_references import find_references


class RoutingTests(unittest.TestCase):
    def test_every_service_name_exports_its_own_source(self):
        for row in catalog.services():
            with self.subTest(service=row['file']):
                plan=plan_icon(Path(row['file']).stem)
                self.assertEqual(plan['mode'],'export_existing')
                self.assertEqual(plan['base_path'],row['path'])
                self.assertEqual(plan['references'],[])

    def test_unrelated_objects_cannot_be_edit_bases(self):
        for subject in ['black transportation van','blue suitcase','gift box','office chair','table lamp','basin mixer tap','electric car charging station','refrigerator cover']:
            with self.subTest(subject=subject):
                self.assertEqual(plan_icon(subject)['mode'],'new_generation')
                self.assertEqual(find_candidates(subject)['decision'],'no_base_found')

    def test_head_object_controls_orientation(self):
        for subject in ['office chair','table lamp','electric car charging station','refrigerator cover']:
            self.assertEqual(plan_icon(subject)['orientation'],'front-near-orthographic')
        self.assertEqual(plan_icon('black car with wrench',new_design=True)['orientation'],'side-horizontal')
        self.assertEqual(plan_icon('black transportation van')['orientation'],'side-horizontal')

    def test_real_purifier_ambiguity(self):
        self.assertEqual(plan_icon('water purifier')['mode'],'ask_user')
        for subject, filename in [('native RO water purifier','Native RO Water Purifiers (India).png'),('normal water purifier','Water purifier repair.png')]:
            plan=plan_icon(subject)
            self.assertEqual(plan['mode'],'export_existing')
            self.assertEqual(Path(plan['base_path']).name,filename)

    def test_named_service_edit_preserves_base(self):
        plan=plan_icon('Spa for women',change='remove towel; recolor upholstery beige')
        self.assertEqual(plan['mode'],'base_edit')
        self.assertEqual(Path(plan['base_path']).name,'Spa for women.png')
        self.assertEqual(plan['orientation'],'side-horizontal')
        self.assertIn('beige',plan['requested_change'])

    def test_whole_request_compatibility_retains_changes(self):
        for subject, detail in [('pink massage table remove towel','towel'),('sofa without cushions','cushions'),('silicone sofa','silicone'),('spa for women massage bed beige remove towel','beige'),('spa for women massage bed beige','beige'),('pink massage table with blue towel','blue towel')]:
            plan=plan_icon(subject)
            self.assertEqual(plan['mode'],'base_edit',subject)
            self.assertIn(detail,plan['requested_change'])
            self.assertEqual(find_candidates(subject)['mode'],'base_edit')
        self.assertNotEqual(plan_icon('ceiling fan with 5 blades')['mode'],'export_existing')

    def test_all_character_bases(self):
        for gender in ['female','male']:
            for eyes in ['open','closed']:
                plan=plan_icon(f'{gender} technician eyes {eyes}')
                self.assertEqual(plan['mode'],'base_edit')
                self.assertEqual(Path(plan['base_path']).name,f'base-{gender}-eyes-{eyes}.png')

    def test_human_with_object_stays_human(self):
        for subject in ['woman carrying bucket','female salon client with hair dryer','maid with vacuum','female car driver','female AC technician','male washing machine technician']:
            plan=plan_icon(subject,gender='female')
            self.assertEqual(plan['mode'],'base_edit')
            self.assertEqual(plan['subject_kind'],'character')
        self.assertEqual(plan_icon('salon chair')['subject_kind'],'object')

    def test_missing_gender_is_real_question(self):
        self.assertEqual(plan_icon('security guard')['mode'],'ask_user')

    def test_structured_details_reach_render_request(self):
        plan=plan_icon('new office chair',change='make the seat red')
        self.assertIn('seat red',plan['prompt'])
        plan=plan_icon('female chef',change='add a whisk',material='silk')
        for detail in ['female chef','whisk','silk']:
            self.assertIn(detail,plan['requested_change'])

    def test_explicit_new_design_and_composition(self):
        self.assertEqual(plan_icon('Refrigerator',new_design=True)['mode'],'new_generation')
        plan=plan_icon('Carpenter',composition='three-quarter')
        self.assertEqual(plan['mode'],'base_edit')
        self.assertEqual(Path(plan['base_path']).name,'Carpenter.png')
        self.assertEqual(plan['orientation'],'three-quarter')
        self.assertEqual(plan_icon('van',composition='front')['orientation'],'front-near-orthographic')
        self.assertEqual(plan_icon('female chef',new_design=True)['mode'],'base_edit')

    def test_absent_optional_library_is_honest(self):
        with patch.object(catalog,'BASE_MANIFEST',Path('/missing/base.csv')),patch.object(catalog,'SERVICE_MANIFEST',Path('/missing/service.csv')),patch.object(catalog,'MATERIAL_MANIFEST',Path('/missing/material.csv')),patch.object(catalog,'NEW_MANIFEST',Path('/missing/new.csv')):
            self.assertEqual(plan_icon('black van')['mode'],'new_generation')
            self.assertEqual(find_references('granite slab')['mode'],'no_reference')

    def test_missing_character_base_blocks(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(catalog,'SKILL_DIR',Path(folder)),patch.object(catalog,'BASE_MANIFEST',Path(folder)/'missing.csv'):
            self.assertEqual(plan_icon('female chef')['mode'],'blocked')

    def test_cli_outputs_json(self):
        import json
        run=subprocess.run([sys.executable,str(SCRIPTS/'plan_icon.py'),'--subject','black van'],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['mode'],'new_generation')


class ReferenceTests(unittest.TestCase):
    def test_default_budget_and_no_duplicate_sources(self):
        refs=find_references('glass water purifier',material='plastic')['references']
        self.assertLessEqual(len(refs),2)
        self.assertEqual(len({r['asset_id'] for r in refs}),len(refs))

    def test_unknown_material_does_not_get_arbitrary_anchors(self):
        plan=find_references('granite slab')
        self.assertEqual(plan['mode'],'no_reference')
        self.assertEqual(plan['references'],[])
        self.assertTrue(plan['coverage_gaps'])

    def test_material_match_does_not_claim_product_match(self):
        plan=find_references('blue suitcase',material='leather')
        self.assertTrue(plan['references'])
        self.assertEqual(plan['references'][0]['role'],'material_reference')
        self.assertNotEqual(plan['mode'],'closest_product_reference')
        self.assertTrue(all('do not copy object identity' in r['transfer'] for r in plan['references']))

    def test_partial_finish_coverage_is_explicit(self):
        for material, missing in [('frosted glass','frosted'),('iridescent steel','iridescent')]:
            plan=find_references('bowl',material=material)
            self.assertIn(missing,' '.join(plan['coverage_gaps']))

    def test_pending_reference_does_not_teach_identity(self):
        fixture=catalog.services()[0]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'MANIFEST.csv'
            def write(status):
                row={'reference_file':'sample.png','image_path':fixture['image_path'],'approval_status':status,'object_family':'test-orb','identity_aliases':'unusual orb','source_role':'form_reference'}
                with path.open('w',newline='') as handle:
                    writer=csv.DictWriter(handle,fieldnames=row)
                    writer.writeheader();writer.writerow(row)
            write('pending')
            with patch.object(catalog,'NEW_MANIFEST',path):
                self.assertEqual(catalog.family('unusual orb'),'')
                write('approved')
                self.assertEqual(catalog.family('unusual orb'),'test-orb')
                refs=find_references('unusual orb')['references']
                self.assertEqual(refs[0]['role'],'form_reference')

    def test_form_approval_does_not_grant_material_authority(self):
        row={'source':'new-object-references','file':'cup.png','path':'/test/cup.png','asset_id':'test-cup','type':'object','object_family':'cup','source_role':'form_reference','material_tags':'porcelain','finish_tags':'glazed'}
        with patch('find_generation_references.load_references',return_value=[row]),patch.object(catalog,'family',return_value='cup'):
            plan=find_references('cup',material='glazed porcelain')
        self.assertEqual(plan['references'][0]['roles'],['form_reference'])
        self.assertIn('glazed',' '.join(plan['coverage_gaps']))
        self.assertIn('porcelain',' '.join(plan['coverage_gaps']))

    def test_no_reference_budget(self):
        self.assertEqual(find_references('glass bowl',0)['references'],[])
        with self.assertRaises(ValueError):
            find_references('glass bowl',-1)


if __name__=='__main__':
    unittest.main()
