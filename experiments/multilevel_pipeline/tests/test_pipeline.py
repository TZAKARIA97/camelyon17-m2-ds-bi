import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

import analyze
import camelyon_data as cd
import extract_patches as ep


class PipelineTests(unittest.TestCase):
    def test_detect_purple(self):
        rgb = np.full((12, 12, 3), 255, dtype=np.uint8)
        rgb[:8, :8] = [128, 0, 128]
        mask = ep.detect_purple(rgb)
        self.assertTrue(bool(mask[3, 3]))
        self.assertFalse(bool(mask[10, 10]))

    def test_xml_mask_respects_tumor_and_exclusion_groups(self):
        xml = """<ASAP_Annotations><Annotations>
        <Annotation PartOfGroup="Tumor"><Coordinates>
          <Coordinate X="0" Y="0"/><Coordinate X="9" Y="0"/>
          <Coordinate X="9" Y="9"/><Coordinate X="0" Y="9"/>
        </Coordinates></Annotation>
        <Annotation PartOfGroup="Exclusion"><Coordinates>
          <Coordinate X="2" Y="2"/><Coordinate X="4" Y="2"/>
          <Coordinate X="4" Y="4"/><Coordinate X="2" Y="4"/>
        </Coordinates></Annotation>
        <Annotation PartOfGroup="Unknown"><Coordinates>
          <Coordinate X="10" Y="10"/><Coordinate X="15" Y="10"/>
          <Coordinate X="15" Y="15"/><Coordinate X="10" Y="15"/>
        </Coordinates></Annotation>
        </Annotations></ASAP_Annotations>"""
        slide = SimpleNamespace(level_dimensions=[(20, 20)], level_downsamples=[1.0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "annotation.xml"
            path.write_text(xml, encoding="utf-8")
            mask = cd.xml_to_mask(path, slide, 0)
        self.assertEqual(mask[1, 1], 1)
        self.assertEqual(mask[3, 3], 0)
        self.assertEqual(mask[12, 12], 0)

    def test_patient_split_has_no_leakage(self):
        rows = []
        for patient in range(15):
            for y in (0, 1):
                rows.append({"patient": f"patient_{patient:03d}", "center": patient // 3,
                             "y": y, "label": "tumor" if y else "normal"})
        split = analyze.separer_par_patiente(pd.DataFrame(rows), graine=42)
        sets = {name: set(group.patient) for name, group in split.groupby("set")}
        self.assertFalse(sets["entrainement"] & sets["validation"])
        self.assertFalse(sets["entrainement"] & sets["test"])
        self.assertFalse(sets["validation"] & sets["test"])
        self.assertEqual(set(split.groupby("set").y.nunique()), {2})

    def test_split_rejects_one_patient(self):
        df = pd.DataFrame({"patient": ["p", "p"], "center": [0, 0], "y": [0, 1]})
        with self.assertRaisesRegex(ValueError, "Au moins 3"):
            analyze.separer_par_patiente(df)

    def test_threshold_is_highest_reaching_target_recall(self):
        y = np.array([0, 0, 1, 1])
        p = np.array([0.1, 0.4, 0.35, 0.8])
        threshold = analyze.seuil_pour_rappel(y, p, rappel_min=0.5)
        self.assertAlmostEqual(threshold, 0.8)

    def test_logistic_models_converge_for_l1_and_l2(self):
        rng = np.random.default_rng(42)
        X = rng.normal(size=(80, 8))
        y = (X[:, 0] + 0.2 * X[:, 1] > 0).astype(int)
        for l1_ratio in (0, 1):
            model = analyze.nouvelle_regression(0.1, l1_ratio).fit(X, y)
            self.assertEqual(model.predict_proba(X).shape, (80, 2))

    def test_comparison_selects_on_validation_not_test(self):
        metrics = {
            (0, "logistique"): pd.DataFrame([
                {"set": "validation", "AUC": 0.90, "rappel": 0.95, "precision": 0.8},
                {"set": "test", "AUC": 0.99, "rappel": 0.99, "precision": 0.9},
            ]),
            (1, "logistique"): pd.DataFrame([
                {"set": "validation", "AUC": 0.92, "rappel": 0.95, "precision": 0.8},
                {"set": "test", "AUC": 0.70, "rappel": 0.70, "precision": 0.7},
            ]),
        }

        def fake_analyze(_, level, *__args, **__kwargs):
            return object(), 0.2, metrics[(level, "logistique")]

        synthetic = pd.DataFrame([
            {"patient": f"p{i}", "center": i // 3, "y": y}
            for i in range(15) for y in (0, 1)
        ])
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(analyze, "charger_patchs", return_value=synthetic), \
                 patch.object(analyze, "analyser_patchs", side_effect=fake_analyze), \
                 patch.object(analyze.shutil, "copy2"):
                result = analyze.comparer_configurations("patches", [0, 1], ["logistique"], tmp)
                self.assertEqual(int(result.iloc[0]["niveau"]), 1)


if __name__ == "__main__":
    unittest.main()
