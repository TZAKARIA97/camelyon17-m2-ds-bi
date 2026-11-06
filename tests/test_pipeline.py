"""Garde-fous de configuration, de sélection et de provenance des exemples."""
import json
import unittest
from pathlib import Path
import pandas as pd
from src.models.train import validate_config
from src.data.audit import audit
from src.data.subset import subset
from src.visualization.report import select_examples


class ConfigTests(unittest.TestCase):
    def test_rejects_test_selection_and_invalid_numbers(self):
        original = json.loads(Path('configs/baseline.json').read_text())
        for key, value in [('selection_split', 'test'), ('threshold', float('nan')),
                           ('threshold', 1.5), ('learning_rate', float('inf')),
                           ('num_workers', -1), ('epochs', True), ('fine_tune', 'false'),
                           ('model', 'not_implemented'), ('seed', 2**32)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_config({**original, key: value})


class GroupTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame([
            dict(path=f'{split}_{patient}_{patch}.png', patient_id=f'{split}_{patient}',
                 slide_id=f'{split}_{patient}', center_id=str(center), label=str(patch % 2), split=split)
            for center, split in enumerate(['train', 'val', 'test'])
            for patient in range(3) for patch in range(4)])

    def test_subset_preserves_groups_and_is_repeatable(self):
        a = subset(self.frame, 2, 2, 42)
        b = subset(self.frame.sample(frac=1, random_state=8), 2, 2, 42)
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(len(a), 12)
        self.assertTrue((a.groupby('patient_id').split.nunique() == 1).all())
        self.assertEqual(set(a.path) - set(self.frame.path), set())
        audit(a)

    def test_subset_does_not_use_labels(self):
        a = subset(self.frame, 2, 2, 9)
        flipped = self.frame.copy()
        flipped['label'] = flipped.label.map({'0': '1', '1': '0'})
        b = subset(flipped, 2, 2, 9)
        self.assertEqual(a.path.tolist(), b.path.tolist())

    def test_duplicate_path_alias_is_rejected(self):
        frame = self.frame.copy()
        frame.loc[1, 'path'] = './' + frame.loc[0, 'path']
        with self.assertRaisesRegex(ValueError, 'dupliqué'):
            audit(frame)

    def test_patient_center_inconsistency_is_rejected(self):
        frame = self.frame.copy()
        frame.loc[0, 'slide_id'] = 'another_slide_same_patient'
        frame.loc[0, 'center_id'] = '99'
        with self.assertRaisesRegex(ValueError, 'groupe patient'):
            audit(frame)


class ExampleTests(unittest.TestCase):
    def test_selects_errors_and_successes_without_fabricating_categories(self):
        frame = pd.DataFrame({'path': ['b', 'a', 'c', 'd', 'e'], 'label': [1, 1, 0, 0, 1],
                              'prediction': [1, 1, 1, 0, 0]})
        selected = select_examples(frame, 1)
        self.assertEqual(set(selected.case), {'TP', 'TN', 'FP', 'FN'})
        self.assertEqual(selected.loc[selected.case == 'TP', 'path'].iloc[0], 'a')
        only_true = select_examples(frame.iloc[:2], 3)
        self.assertEqual(set(only_true.case), {'TP'})


if __name__ == '__main__':
    unittest.main()
