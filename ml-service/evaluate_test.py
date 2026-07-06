"""Evaluación final y reproducible del modelo v0.1 sobre el conjunto test.

Este script solo carga el modelo ya entrenado: nunca ajusta parámetros ni llama
``fit``. El conjunto test permanece así como una medición final independiente.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from train_baseline import EXPECTED_CATEGORIES, MODEL_VERSION, calculate_metrics, load_dataset


MODEL_FILENAME = "ticket_classifier_tfidf_logreg_v0.1.joblib"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate(project_root: Path) -> dict:
    test_path = project_root / "data" / "processed" / "test_v0.1.csv"
    model_path = project_root / "ml-service" / "models" / MODEL_FILENAME
    reports_dir = project_root / "reports"

    if not model_path.exists():
        raise FileNotFoundError(f"No se encontró el modelo: {model_path}")

    test_df = load_dataset(test_path)
    model = joblib.load(model_path)
    predictions = model.predict(test_df["text"])
    probabilities = model.predict_proba(test_df["text"])
    metrics = calculate_metrics(test_df["category"], predictions)

    output = test_df.drop(columns=["text"]).copy()
    output["predicted_category"] = predictions
    output["confidence"] = probabilities.max(axis=1).round(6)
    output["is_correct"] = output["category"] == output["predicted_category"]
    output["model_version"] = MODEL_VERSION
    errors = output[~output["is_correct"]].copy()

    matrix = confusion_matrix(
        test_df["category"], predictions, labels=EXPECTED_CATEGORIES
    )
    confusion = pd.DataFrame(
        matrix,
        index=[f"true_{category}" for category in EXPECTED_CATEGORIES],
        columns=[f"pred_{category}" for category in EXPECTED_CATEGORIES],
    )

    report = {
        "evaluation": "final_test_v0.1",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_version": MODEL_VERSION,
        "note": "Evaluación final sobre test; el modelo fue cargado sin reentrenamiento.",
        "input_files": {
            "test": str(test_path.relative_to(project_root)),
            "model": str(model_path.relative_to(project_root)),
        },
        "sha256": {"test": sha256(test_path), "model": sha256(model_path)},
        "test_rows": int(len(test_df)),
        "classes": list(model.named_steps["classifier"].classes_),
        "metrics": {
            name: round(float(metrics[name]), 6)
            for name in ("accuracy", "macro_precision", "macro_recall", "macro_f1")
        },
        "classification_report": classification_report(
            test_df["category"],
            predictions,
            labels=EXPECTED_CATEGORIES,
            output_dict=True,
            zero_division=0,
        ),
        "test_errors": int(len(errors)),
    }

    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "final_test_metrics_v0.1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    output.to_csv(
        reports_dir / "final_test_predictions_v0.1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    errors.to_csv(
        reports_dir / "final_test_errors_v0.1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    confusion.to_csv(
        reports_dir / "final_test_confusion_matrix_v0.1.csv", encoding="utf-8-sig"
    )
    return report


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    report = evaluate(project_root)
    print("Evaluación final completada (sin reentrenamiento)")
    print(f"Filas test: {report['test_rows']}")
    for name, value in report["metrics"].items():
        print(f"{name}: {value:.4f}")
    print(f"Errores: {report['test_errors']} / {report['test_rows']}")


if __name__ == "__main__":
    main()
