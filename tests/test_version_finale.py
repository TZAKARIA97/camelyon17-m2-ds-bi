import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "version_finale"


def load_parameters():
    path = FINAL / "parametres_decoupage.py"
    spec = importlib.util.spec_from_file_location("parametres_decoupage_finale", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VersionFinaleAlignmentTests(unittest.TestCase):
    def test_retained_variant_uses_fixed_physical_surface(self):
        parameters = load_parameters()
        self.assertEqual(parameters.PARAMETRES["patch_um"], 112)
        self.assertEqual(parameters.PARAMETRES["patch"], 224)
        self.assertEqual(parameters.VARIANTES["retenue"]["patch_level"], [2])
        self.assertEqual(parameters.VARIANTES["retenue"]["labelling"], "centre")

    def test_published_level_selection_matches_retained_variant(self):
        result = json.loads(
            (FINAL / "resultats_publics" / "selection_niveau.json").read_text(encoding="utf-8")
        )
        scores = {row["niveau"]: row["roc_auc_validation"] for row in result["comparaison_validation"]}
        self.assertEqual(result["niveau_retenu"], 2)
        self.assertGreater(scores[2], scores[1])

    def test_heatmap_examples_use_retained_level(self):
        script = (FINAL / "cartes_chaleur.py").read_text(encoding="utf-8")
        self.assertIn("python cartes_chaleur.py --niveau 2", script)


if __name__ == "__main__":
    unittest.main()
