from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib


# ============================================================
# 1. CONFIGURACIÓN DEL MODELO
# ============================================================
# Este script usa el modelo baseline ya entrenado.
# No entrena nada nuevo.
# Solo carga el .joblib y hace predicciones.

MODEL_VERSION = "tfidf_logreg_v0.1"

MODEL_FILENAME = "ticket_classifier_tfidf_logreg_v0.1.joblib"


# ============================================================
# 2. CARGA DEL MODELO
# ============================================================
# joblib.load recupera el pipeline completo:
#
# TF-IDF + Logistic Regression
#
# Eso significa que no tenemos que transformar el texto manualmente.
# El pipeline ya sabe cómo convertir texto a números y clasificar.

def load_model():
    project_root = Path(__file__).resolve().parents[1]
    model_path = project_root / "ml-service" / "models" / MODEL_FILENAME

    if not model_path.exists():
        raise FileNotFoundError(f"No se encontró el modelo: {model_path}")

    return joblib.load(model_path)


# ============================================================
# 3. PREDICCIÓN DE UN TICKET
# ============================================================
# Entrada:
# - title
# - description
#
# Salida:
# - category
# - confidence
# - model_version
#
# La confianza se toma como la probabilidad más alta que asigna
# Logistic Regression entre todas las categorías.

def predict_ticket(model, title: str, description: str) -> dict:
    text = f"{title or ''} {description or ''}".strip()

    if not text:
        raise ValueError("El título y la descripción no pueden estar ambos vacíos.")

    predicted_category = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]

    confidence = float(probabilities.max())

    return {
        "category": predicted_category,
        "confidence": round(confidence, 6),
        "model_version": MODEL_VERSION,
    }


# ============================================================
# 4. EJEMPLOS MANUALES
# ============================================================
# Si ejecutas el script sin argumentos, prueba algunos tickets
# de ejemplo para verificar que el modelo responde.

def run_examples(model) -> None:
    examples = [
        {
            "title": "No puedo iniciar sesión",
            "description": "El sistema rechaza mi contraseña aunque estoy usando la clave correcta.",
        },
        {
            "title": "Me cobraron dos veces",
            "description": "Aparecen dos cargos por la misma compra en mi tarjeta.",
        },
        {
            "title": "La página queda en blanco",
            "description": "Al ingresar al módulo de reportes no aparece ningún contenido.",
        },
        {
            "title": "El sistema está muy lento",
            "description": "El dashboard tarda varios minutos en cargar la información.",
        },
        {
            "title": "Agregar exportación a PDF",
            "description": "Necesitamos descargar los reportes en formato PDF.",
        },
        {
            "title": "¿Dónde veo mis facturas?",
            "description": "Quiero saber en qué sección puedo descargar mis comprobantes.",
        },
    ]

    for index, example in enumerate(examples, start=1):
        prediction = predict_ticket(
            model=model,
            title=example["title"],
            description=example["description"],
        )

        print(f"CASO {index}")
        print(f"Título: {example['title']}")
        print(f"Descripción: {example['description']}")
        print(json.dumps(prediction, ensure_ascii=False, indent=2))
        print("-" * 60)


# ============================================================
# 5. ENTRADA POR CONSOLA
# ============================================================
# Permite probar un ticket específico así:
#
# python ml-service/predict_local.py \
#   --title "No puedo pagar" \
#   --description "Mi tarjeta fue rechazada"

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Predicción local de categoría para tickets de soporte."
    )

    parser.add_argument("--title", type=str, help="Título del ticket")
    parser.add_argument("--description", type=str, help="Descripción del ticket")

    args = parser.parse_args()

    model = load_model()

    if args.title is None and args.description is None:
        run_examples(model)
        return

    prediction = predict_ticket(
        model=model,
        title=args.title or "",
        description=args.description or "",
    )

    print(json.dumps(prediction, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()