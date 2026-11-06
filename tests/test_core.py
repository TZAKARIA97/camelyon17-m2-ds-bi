"""Exemples fabriqués : test de logique, pas validation sur données médicales."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.data.inventory import inventory
from src.data.annotations import Polygon, read_xml, local_mask
from src.data.audit import audit
from src.data.wilds_manifest import convert
from src.evaluation.metrics import binary_metrics
from src.evaluation.staging import stage_patient


def manifest():
    return pd.DataFrame([
        dict(path='a.png', patient_id='001', slide_id='s1', center_id='0', label='1', split='train'),
        dict(path='b.png', patient_id='002', slide_id='s2', center_id='1', label='0', split='val'),
        dict(path='c.png', patient_id='003', slide_id='s3', center_id='2', label='1', split='test')])


class AuditTests(unittest.TestCase):
    def test_valid(self):
        self.assertIn('train', audit(manifest()))

    def test_patient_leakage(self):
        df = manifest()
        df.loc[1, 'patient_id'] = '001'
        with self.assertRaisesRegex(ValueError, 'Fuite'):
            audit(df)

    def test_duplicate_paths(self):
        df = manifest()
        df.loc[1, 'path'] = 'a.png'
        with self.assertRaisesRegex(ValueError, 'dupliqué'):
            audit(df)

    def test_unknown_label(self):
        df = manifest()
        df.loc[1, 'label'] = '-1'
        with self.assertRaisesRegex(ValueError, 'Labels'):
            audit(df)

    def test_empty_and_unknown_metadata(self):
        with self.assertRaisesRegex(ValueError, 'vide'):
            audit(manifest().iloc[:0])
        df = manifest()
        df.loc[0, 'center_id'] = ''
        with self.assertRaisesRegex(ValueError, 'vides'):
            audit(df)

    def test_center_overlap(self):
        df = manifest()
        df.loc[2, 'center_id'] = '0'
        with self.assertRaisesRegex(ValueError, 'hors centres'):
            audit(df)

    def test_missing_image(self):
        with self.assertRaisesRegex(ValueError, 'introuvable'):
            audit(manifest(), check_files=True)


class AnnotationTests(unittest.TestCase):
    def test_holes_and_coordinate_scale(self):
        p = [Polygon('metastases', [(100, 100), (118, 100), (118, 118), (100, 118)]),
             Polygon('normal', [(104, 104), (108, 104), (108, 108), (104, 108)])]
        mask = local_mask(p, 100, 100, 10, 2)
        self.assertEqual(mask[0, 0], 1)
        self.assertEqual(mask[3, 3], 0)
        self.assertEqual(mask.shape, (10, 10))
        self.assertEqual(local_mask(p, 500, 500, 10).sum(), 0)

    def test_xml_unknown_group_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic.xml'
            path.write_text('<ASAP_Annotations><Annotations><Annotation PartOfGroup="unknown"/></Annotations></ASAP_Annotations>')
            with self.assertRaisesRegex(ValueError, 'Groupe'):
                read_xml(path)

    def test_xml_order_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic.xml'
            path.write_text('<ASAP_Annotations><Annotations><Annotation PartOfGroup="metastases"><Coordinates><Coordinate Order="2" X="1" Y="1"/><Coordinate Order="0" X="0" Y="0"/><Coordinate Order="1" X="1" Y="0"/></Coordinates></Annotation></Annotations></ASAP_Annotations>')
            self.assertEqual(read_xml(path)[0].points[0], (0, 0))
            path.write_text('<ASAP_Annotations/>')
            with self.assertRaisesRegex(ValueError, 'Aucun'):
                read_xml(path)


class InventoryTests(unittest.TestCase):
    def test_no_xml_never_implies_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'centre_3').mkdir()
            (root/'centre_3'/'patient_007_node_0.tif').touch()
            row = inventory(root)[0]
            self.assertEqual(row['patient_id'], '007')
            self.assertEqual(row['center_id'], '3')
            self.assertEqual(row['slide_label'], '')
            self.assertEqual(row['annotation_status'], 'missing')

    def test_duplicate_xml_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'patient_001_node_0.tif').touch()
            for folder in ('a', 'b'):
                (root/folder).mkdir()
                (root/folder/'patient_001_node_0.xml').touch()
            row = inventory(root)[0]
            self.assertEqual(row['xml_path'], '')
            self.assertEqual(row['annotation_status'], 'ambiguous')

    def test_wilds_official_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Métadonnées artificielles ; les centres 1/2 remplacent les codes bruts du CSV.
            pd.DataFrame(dict(patient=['001', '002', '003'], node=[0]*3,
                              x_coord=[0]*3, y_coord=[0]*3, center=[0, 1, 2],
                              tumor=[0, 1, 0], split=[0, 0, 0])).to_csv(Path(tmp)/'metadata.csv', index=False)
            df = convert(tmp)
            self.assertEqual(df.split.tolist(), ['train', 'val', 'test'])
            self.assertEqual(df.patient_id.iloc[0], '001')


class EvaluationTests(unittest.TestCase):
    def test_confusion_and_rates(self):
        m = binary_metrics([0, 0, 1, 1], [0.1, 0.8, 0.2, 0.9])
        self.assertEqual([m[k] for k in ['tn', 'fp', 'fn', 'tp']], [1, 1, 1, 1])
        self.assertEqual(m['sensitivity'], .5)
        self.assertEqual(m['specificity'], .5)

    def test_single_class_undefined(self):
        m = binary_metrics([0, 0], [.1, .2])
        self.assertIsNone(m['sensitivity'])
        self.assertIsNone(m['roc_auc'])
        self.assertIsNone(m['average_precision'])

    def test_invalid_scores(self):
        for scores in ([np.nan], [1.5]):
            with self.assertRaises(ValueError):
                binary_metrics([1], scores)

    def test_all_pn_categories(self):
        cases = [(['negative']*5, 'pN0'), (['itc']+['negative']*4, 'pN0(i+)'),
                 (['micro']*5, 'pN1mi'), (['macro', 'micro', 'itc', 'negative', 'negative'], 'pN1'),
                 (['macro']+['micro']*3+['negative'], 'pN2')]
        for nodes, expected in cases:
            self.assertEqual(stage_patient(nodes), expected)

    def test_incomplete_patient_rejected(self):
        with self.assertRaises(ValueError):
            stage_patient(['negative']*4)
        with self.assertRaises(ValueError):
            stage_patient(['unknown']+['negative']*4)


if __name__ == '__main__':
    unittest.main()
