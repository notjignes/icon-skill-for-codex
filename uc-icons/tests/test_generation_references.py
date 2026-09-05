from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import icon_catalog as catalog
from find_generation_references import find_references


def reference(name, family, materials, finish, roles='material_reference', **extra):
    return {
        'source': 'new-object-references', 'file': name, 'path': '/test/' + name,
        'asset_id': name, 'type': 'object', 'object_family': family,
        'source_role': roles, 'material_tags': materials, 'finish_tags': finish,
        **extra,
    }


class MaterialReferenceTests(unittest.TestCase):
    def test_plumber_component_scope_reaches_material_prompt_and_merged_base_alias(self):
        row = next(row for row in catalog.read_manifest(catalog.MATERIAL_MANIFEST) if row.get('service_file') == 'Plumber.png')
        scope = row['material_scope'].strip()
        self.assertIn('faucet cylinder', scope)
        self.assertIn('bare wrench head', scope)
        for subject in ('basin mixer tap with adjustable wrench', 'sink'):
            with self.subTest(subject=subject):
                plan = find_references(subject, material='chrome')
                chosen = next(ref for ref in plan['references'] if Path(ref['path']).name == 'Plumber.png')
                self.assertIn('material_reference', chosen['roles'])
                self.assertEqual(chosen['material_scope'], scope)
                self.assertIn(scope, chosen['transfer'])
                self.assertIn(scope, plan['prompt'])
                self.assertIn('reference-matched roughness and controlled highlights', plan['prompt'])
                self.assertNotIn('matte-to-satin materials', plan['prompt'])
                if subject == 'sink':
                    self.assertEqual(chosen['roles'], ['form_reference', 'material_reference'])
                    self.assertEqual(plan['reference_count'], 1)

    def test_material_scope_does_not_transfer_from_form_only_approval(self):
        scope = 'Use the faucet bare metal highlights only; never copy ceramic gloss.'
        rows = [reference('tap.png', 'tap', 'chrome', 'glossy', 'form_reference', material_scope=scope)]
        with patch('find_generation_references.load_references', return_value=rows):
            plan = find_references('basin mixer tap', material='chrome')
        self.assertEqual(plan['references'][0]['roles'], ['form_reference'])
        self.assertNotIn('material_scope', plan['references'][0])
        self.assertNotIn(scope, plan['references'][0]['transfer'])
        self.assertNotIn(scope, plan['prompt'])
        self.assertIn('chrome', ' '.join(plan['coverage_gaps']))

    def test_absent_material_scope_keeps_generic_transfer(self):
        for scope in ('', None):
            with self.subTest(scope=scope):
                rows = [reference('surface.png', 'panel', 'chrome', 'glossy', material_scope=scope)]
                with patch('find_generation_references.load_references', return_value=rows):
                    plan = find_references('basin mixer tap', material='chrome')
                chosen = plan['references'][0]
                self.assertEqual(chosen['roles'], ['material_reference'])
                self.assertNotIn('material_scope', chosen)
                self.assertNotIn('Material scope:', plan['prompt'])
                self.assertIn('matched material/finish terms only', chosen['transfer'])

    def test_hood_uses_its_own_brushed_steel_without_a_dumbbell_attachment(self):
        plan = find_references('chimney hood', material='brushed steel')
        self.assertEqual(plan['reference_count'], 1)
        chosen = plan['references'][0]
        self.assertEqual(chosen['file'], 'Kitchen chimney.png')
        self.assertEqual(set(chosen['roles']), {'form_reference', 'material_reference'})
        self.assertEqual(chosen['matched_terms'], ['brushed', 'steel'])
        self.assertEqual(plan['coverage_gaps'], [])

    def test_tap_chrome_uses_relevant_component_not_generic_truck_metal(self):
        for material in ('chrome', 'chrome metal'):
            with self.subTest(material=material):
                plan = find_references('basin mixer tap with adjustable wrench', material=material)
                self.assertEqual(plan['reference_count'], 1)
                chosen = plan['references'][0]
                self.assertEqual(Path(chosen['path']).name, 'Plumber.png')
                self.assertEqual(chosen['roles'], ['material_reference'])
                self.assertEqual(chosen['matched_terms'], ['chrome'])
                self.assertNotEqual(plan['mode'], 'closest_product_reference')

    def test_unsupported_satin_chrome_does_not_attach_painted_or_glossy_examples(self):
        plan = find_references('basin mixer tap', material='satin chrome metal')
        self.assertEqual(plan['references'], [])
        self.assertIn('chrome, satin', ' '.join(plan['coverage_gaps']))
        self.assertIn('not established by references: chrome, satin', plan['prompt'])

    def test_finish_overlap_without_requested_substance_is_not_material_evidence(self):
        rows = [reference('aluminum.png', 'laptop', 'aluminum', 'brushed')]
        with patch('find_generation_references.load_references', return_value=rows):
            plan = find_references('chimney hood', material='brushed steel')
        self.assertEqual(plan['references'], [])
        self.assertIn('brushed, steel', ' '.join(plan['coverage_gaps']))

    def test_more_complete_material_evidence_can_complement_a_matching_form(self):
        rows = [
            reference('hood.png', 'kitchen-chimney', 'steel', 'matte', 'form_reference;material_reference'),
            reference('panel.png', 'panel', 'steel', 'brushed'),
        ]
        with patch('find_generation_references.load_references', return_value=rows):
            plan = find_references('chimney hood', material='brushed steel')
        self.assertEqual([r['file'] for r in plan['references']], ['hood.png', 'panel.png'])
        self.assertEqual(plan['references'][0]['roles'], ['form_reference'])
        self.assertEqual(plan['references'][1]['matched_terms'], ['brushed', 'steel'])
        self.assertEqual(plan['coverage_gaps'], [])

    def test_matching_form_with_partial_finish_reports_the_remaining_gap(self):
        rows = [
            reference('hood.png', 'kitchen-chimney', 'steel', 'brushed', 'form_reference;material_reference'),
            reference('truck.png', 'truck', 'metal', 'painted'),
        ]
        with patch('find_generation_references.load_references', return_value=rows):
            plan = find_references('chimney hood', material='satin brushed steel metal')
        self.assertEqual(plan['reference_count'], 1)
        self.assertEqual(plan['references'][0]['matched_terms'], ['brushed', 'steel'])
        self.assertIn('satin', ' '.join(plan['coverage_gaps']))
        self.assertIn('unsupported finishes', plan['references'][0]['transfer'])

    def test_finish_in_subject_is_a_selection_constraint(self):
        rows = [reference('truck.png', 'truck', 'chrome;metal', 'painted')]
        with patch('find_generation_references.load_references', return_value=rows):
            plan = find_references('painted chrome tap')
        self.assertEqual(plan['references'][0]['matched_terms'], ['chrome', 'painted'])

    def test_shared_form_and_material_leave_room_for_requested_composition(self):
        rows = [
            reference('hood.png', 'kitchen-chimney', 'steel', 'brushed', 'form_reference;material_reference'),
            reference('view.png', 'cabinet', 'wood', 'matte', 'composition_reference', composition_family='front'),
        ]
        with patch('find_generation_references.load_references', return_value=rows):
            plan = find_references('chimney hood', material='brushed steel', composition='front')
        self.assertEqual(plan['reference_count'], 2)
        self.assertEqual(plan['references'][0]['roles'], ['form_reference', 'material_reference'])
        self.assertEqual(plan['references'][1]['role'], 'composition_reference')
        self.assertEqual(len({r['asset_id'] for r in plan['references']}), 2)

    def test_pending_and_rejected_material_references_are_not_used(self):
        fixture = catalog.services()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'MANIFEST.csv'
            rows = []
            for status in ('pending', 'rejected'):
                rows.append({
                    'reference_file': status + '.png', 'image_path': fixture['image_path'],
                    'approval_status': status, 'type': 'object', 'source_role': 'material_reference',
                    'material_tags': 'chrome', 'finish_tags': 'satin',
                })
            with manifest.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0])
                writer.writeheader()
                writer.writerows(rows)
            with patch.object(catalog, 'NEW_MANIFEST', manifest), patch.object(catalog, 'BASE_MANIFEST', root / 'missing-base.csv'), patch.object(catalog, 'MATERIAL_MANIFEST', root / 'missing-material.csv'):
                plan = find_references('basin mixer tap', material='satin chrome')
        self.assertEqual(plan['references'], [])
        self.assertTrue(plan['coverage_gaps'])


if __name__ == '__main__':
    unittest.main()
