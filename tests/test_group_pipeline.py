import unittest

import pandas as pd

from src.group_pipeline.summarize_results import summarize_predictions


class GroupPipelineSummaryTests(unittest.TestCase):
    def test_summary_counts_and_threshold(self):
        predictions = pd.DataFrame(
            {
                "etiquette": ["sain", "sain", "tumoral", "tumoral"],
                "proba_tumoral": [0.1, 0.4, 0.6, 0.9],
                "lame": ["slide_a"] * 4,
            }
        )
        summary = summarize_predictions(predictions, fixed_threshold=0.5, target_recall=1.0)
        self.assertEqual(summary["fixed_threshold"]["tn"], 2)
        self.assertEqual(summary["fixed_threshold"]["tp"], 2)
        self.assertEqual(summary["validation_selected_threshold"]["threshold"], 0.6)
        self.assertEqual(summary["counts_by_lame"], {"slide_a": 4})

    def test_unknown_label_is_rejected(self):
        predictions = pd.DataFrame(
            {"etiquette": ["sain", "incertain"], "proba_tumoral": [0.1, 0.9]}
        )
        with self.assertRaisesRegex(ValueError, "inconnues"):
            summarize_predictions(predictions)


if __name__ == "__main__":
    unittest.main()
