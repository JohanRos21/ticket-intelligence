from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline


# ============================================================
# 1. CONFIGURACIÓN GENERAL DEL EXPERIMENTO
# ============================================================
# Esta sección define valores fijos del experimento.
# Sirve para que el resultado sea rastreable y repetible.

MODEL_VERSION = "tfidf_logreg_v0.1"

RANDOM_STATE = 20260626

EXPECTED_CATEGORIES = [
    "acceso_autenticacion",
    "pagos_facturacion",
    "error_tecnico",
    "rendimiento",
    "solicitud_funcionalidad",
    "consulta_general",
]


# ============================================================
# 2. CARGA Y PREPARACIÓN DEL DATASET
# ============================================================
# Esta función lee un CSV, valida que tenga las columnas mínimas
# y crea una columna text combinando title + description.
#
# Importante:
# - No hacemos limpieza avanzada todavía.
# - No usamos test en este script.
# - El baseline debe ser simple y fácil de entender.

def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")

    required_columns = {"title", "description", "category"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias: {missing_columns}")

    df["title"] = df["title"].fillna("")
    df["description"] = df["description"].fillna("")
    df["text"] = df["title"] + " " + df["description"]

    return df


# ============================================================
# 3. CREACIÓN DEL MODELO BASELINE
# ============================================================
# Pipeline significa encadenar pasos.
#
# Paso 1:
# TF-IDF convierte el texto en números.
#
# Paso 2:
# Logistic Regression aprende a clasificar esos números
# en una de las seis categorías.
#
# Este modelo es nuestro baseline inicial:
# simple, rápido, interpretable y suficiente para v0.1.

def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=5000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                    class_weight=None,
                ),
            ),
        ]
    )


# ============================================================
# 4. CÁLCULO DE MÉTRICAS
# ============================================================
# Aquí calculamos las métricas principales.
#
# Macro F1 es la métrica principal del proyecto porque evalúa
# el rendimiento promedio por clase, no solo el acierto total.
#
# Esto es importante cuando hay varias categorías y queremos
# que el modelo funcione razonablemente bien en todas.

def calculate_metrics(y_true, y_pred) -> dict:
    accuracy = accuracy_score(y_true, y_pred)

    macro_precision = precision_score(
        y_true,
        y_pred,
        labels=EXPECTED_CATEGORIES,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        y_true,
        y_pred,
        labels=EXPECTED_CATEGORIES,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_true,
        y_pred,
        labels=EXPECTED_CATEGORIES,
        average="macro",
        zero_division=0,
    )

    report = classification_report(
        y_true,
        y_pred,
        labels=EXPECTED_CATEGORIES,
        output_dict=True,
        zero_division=0,
    )

    return {
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "classification_report": report,
    }


# ============================================================
# 5. GUARDADO DE REPORTES Y MODELO
# ============================================================
# Guardamos todo lo necesario para auditar el experimento:
#
# - métricas generales;
# - predicciones sobre validation;
# - errores del modelo;
# - matriz de confusión;
# - modelo entrenado en formato joblib.
#
# Esto es importante para GitHub/CV porque demuestra que no solo
# entrenamos un modelo, sino que también lo evaluamos y registramos.

def save_outputs(
    project_root: Path,
    pipeline: Pipeline,
    validation_df: pd.DataFrame,
    y_pred,
    y_proba,
    metrics: dict,
) -> None:
    reports_dir = project_root / "reports"
    models_dir = project_root / "ml-service" / "models"

    reports_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    max_confidence = y_proba.max(axis=1)

    predictions_df = validation_df.copy()
    predictions_df["predicted_category"] = y_pred
    predictions_df["confidence"] = max_confidence.round(6)
    predictions_df["is_correct"] = (
        predictions_df["category"] == predictions_df["predicted_category"]
    )
    predictions_df["model_version"] = MODEL_VERSION

    errors_df = predictions_df[~predictions_df["is_correct"]].copy()

    matrix = confusion_matrix(
        validation_df["category"],
        y_pred,
        labels=EXPECTED_CATEGORIES,
    )

    confusion_df = pd.DataFrame(
        matrix,
        index=[f"true_{category}" for category in EXPECTED_CATEGORIES],
        columns=[f"pred_{category}" for category in EXPECTED_CATEGORIES],
    )

    train_path = project_root / "data" / "processed" / "train_v0.1.csv"
    validation_path = project_root / "data" / "processed" / "validation_v0.1.csv"

    model_report = {
        "model_version": MODEL_VERSION,
        "note": (
            "Baseline entrenado con train_v0.1.csv y evaluado con "
            "validation_v0.1.csv. No se leyó test_v0.1.csv."
        ),
        "input_files": {
            "train": str(train_path.relative_to(project_root)),
            "validation": str(validation_path.relative_to(project_root)),
        },
        "validation_rows": int(len(validation_df)),
        "classes": list(pipeline.named_steps["classifier"].classes_),
        "vectorizer": {
            "type": "TfidfVectorizer",
            "lowercase": True,
            "strip_accents": "unicode",
            "ngram_range": [1, 2],
            "min_df": 2,
            "max_features": 5000,
        },
        "classifier": {
            "type": "LogisticRegression",
            "max_iter": 1000,
            "random_state": RANDOM_STATE,
            "class_weight": None,
        },
        "metrics": {
            "accuracy": round(float(metrics["accuracy"]), 6),
            "macro_precision": round(float(metrics["macro_precision"]), 6),
            "macro_recall": round(float(metrics["macro_recall"]), 6),
            "macro_f1": round(float(metrics["macro_f1"]), 6),
        },
        "classification_report": metrics["classification_report"],
        "validation_errors": int(len(errors_df)),
    }

    metrics_path = reports_dir / "baseline_validation_metrics_v0.1.json"
    predictions_path = reports_dir / "baseline_validation_predictions_v0.1.csv"
    errors_path = reports_dir / "baseline_validation_errors_v0.1.csv"
    confusion_path = reports_dir / "baseline_confusion_matrix_v0.1.csv"
    model_path = models_dir / "ticket_classifier_tfidf_logreg_v0.1.joblib"

    metrics_path.write_text(
        json.dumps(model_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    predictions_df.to_csv(
        predictions_path,
        index=False,
        encoding="utf-8-sig",
    )

    errors_df.to_csv(
        errors_path,
        index=False,
        encoding="utf-8-sig",
    )

    confusion_df.to_csv(
        confusion_path,
        encoding="utf-8-sig",
    )

    joblib.dump(pipeline, model_path)

    print("Archivos generados:")
    print(f"  - Modelo: {model_path}")
    print(f"  - Métricas: {metrics_path}")
    print(f"  - Predicciones: {predictions_path}")
    print(f"  - Errores: {errors_path}")
    print(f"  - Matriz de confusión: {confusion_path}")


# ============================================================
# 6. FLUJO PRINCIPAL DEL ENTRENAMIENTO
# ============================================================
# Esta es la ejecución completa:
#
# 1. Ubicar archivos.
# 2. Cargar train y validation.
# 3. Entrenar el pipeline.
# 4. Predecir validation.
# 5. Calcular métricas.
# 6. Guardar modelo y reportes.
#
# Test queda reservado para después.

def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    train_path = project_root / "data" / "processed" / "train_v0.1.csv"
    validation_path = project_root / "data" / "processed" / "validation_v0.1.csv"

    print("Cargando datasets...")
    train_df = load_dataset(train_path)
    validation_df = load_dataset(validation_path)

    x_train = train_df["text"]
    y_train = train_df["category"]

    x_validation = validation_df["text"]
    y_validation = validation_df["category"]

    print("Entrenando baseline TF-IDF + Logistic Regression...")
    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    print("Evaluando en validation...")
    y_pred = pipeline.predict(x_validation)
    y_proba = pipeline.predict_proba(x_validation)

    metrics = calculate_metrics(y_validation, y_pred)

    save_outputs(
        project_root=project_root,
        pipeline=pipeline,
        validation_df=validation_df,
        y_pred=y_pred,
        y_proba=y_proba,
        metrics=metrics,
    )

    validation_errors = int((y_validation != y_pred).sum())

    print("")
    print("Baseline TF-IDF + Logistic Regression completado")
    print("IMPORTANTE: no se leyó test_v0.1.csv")
    print("")
    print("Resultados validation:")
    print(f"  - accuracy: {metrics['accuracy']:.4f}")
    print(f"  - macro_precision: {metrics['macro_precision']:.4f}")
    print(f"  - macro_recall: {metrics['macro_recall']:.4f}")
    print(f"  - macro_f1: {metrics['macro_f1']:.4f}")
    print(f"  - errores: {validation_errors} / {len(validation_df)}")


if __name__ == "__main__":
    main()