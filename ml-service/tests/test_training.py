from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

from train_baseline import (  # noqa: E402
    EXPECTED_CATEGORIES,
    build_pipeline,
    calculate_metrics,
    load_dataset,
)


class TrainingTests(unittest.TestCase):
    def test_load_dataset_combines_and_fills_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.csv"
            pd.DataFrame(
                [{"title": "Login", "description": None, "category": "acceso_autenticacion"}]
            ).to_csv(path, index=False)
            loaded = load_dataset(path)
        self.assertEqual(loaded.loc[0, "text"], "Login ")

    def test_load_dataset_requires_expected_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.csv"
            pd.DataFrame([{"title": "Sin categoría"}]).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                load_dataset(path)

    def test_perfect_predictions_have_perfect_metrics(self):
        metrics = calculate_metrics(EXPECTED_CATEGORIES, EXPECTED_CATEGORIES)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["macro_f1"], 1.0)

    def test_pipeline_contains_vectorizer_and_classifier(self):
        pipeline = build_pipeline()
        self.assertEqual(list(pipeline.named_steps), ["tfidf", "classifier"])


if __name__ == "__main__":
    unittest.main()
