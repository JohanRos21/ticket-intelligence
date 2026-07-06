from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

import app  # noqa: E402


class AppTests(unittest.TestCase):
    def test_health_exposes_model_version(self):
        self.assertEqual(
            app.health_check(),
            {"status": "ok", "model_version": "tfidf_logreg_v0.1"},
        )

    def test_predict_returns_category_confidence_and_version(self):
        fake_model = Mock()
        fake_model.predict.return_value = ["error_tecnico"]
        fake_model.predict_proba.return_value = np.array([[0.05, 0.95]])

        with patch.object(app, "model", fake_model):
            result = app.predict_ticket(
                app.TicketInput(title="La app falla", description="Error 500")
            )

        self.assertEqual(result.category, "error_tecnico")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.model_version, app.MODEL_VERSION)
        fake_model.predict.assert_called_once_with(["La app falla Error 500"])

    def test_predict_rejects_blank_input(self):
        with self.assertRaises(app.HTTPException) as raised:
            app.predict_ticket(app.TicketInput(title="  ", description=""))
        self.assertEqual(raised.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
