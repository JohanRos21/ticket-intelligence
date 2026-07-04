from __future__ import annotations

from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# ============================================================
# 1. CONFIGURACIÓN DEL MODELO
# ============================================================

MODEL_VERSION = "tfidf_logreg_v0.1"
MODEL_FILENAME = "ticket_classifier_tfidf_logreg_v0.1.joblib"


# ============================================================
# 2. ESQUEMAS DE ENTRADA Y SALIDA
# ============================================================
# TicketInput define lo que recibirá la API.
# PredictionOutput define lo que devolverá la API.
#
# Esto ayuda a FastAPI a validar datos y generar documentación
# automática en /docs.

class TicketInput(BaseModel):
    title: str
    description: str


class PredictionOutput(BaseModel):
    category: str
    confidence: float
    model_version: str


# ============================================================
# 3. CARGA DEL MODELO
# ============================================================
# Cargamos el pipeline completo:
# TF-IDF + Logistic Regression.
#
# El modelo se carga una vez cuando inicia la API.

def load_model():
    current_dir = Path(__file__).resolve().parent
    model_path = current_dir / "models" / MODEL_FILENAME

    if not model_path.exists():
        raise FileNotFoundError(f"No se encontró el modelo: {model_path}")

    return joblib.load(model_path)


model = load_model()


# ============================================================
# 4. CREACIÓN DE LA API
# ============================================================

app = FastAPI(
    title="Ticket Intelligence ML Service",
    version="0.1.0",
    description="Microservicio ML para clasificar tickets de soporte.",
)


# ============================================================
# 5. ENDPOINT DE SALUD
# ============================================================
# Sirve para comprobar que el servicio está encendido.

@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "model_version": MODEL_VERSION,
    }


# ============================================================
# 6. ENDPOINT DE PREDICCIÓN
# ============================================================
# Recibe title + description.
# Devuelve category + confidence + model_version.

@app.post("/predict", response_model=PredictionOutput)
def predict_ticket(ticket: TicketInput) -> PredictionOutput:
    text = f"{ticket.title or ''} {ticket.description or ''}".strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="El título y la descripción no pueden estar ambos vacíos.",
        )

    predicted_category = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]
    confidence = float(probabilities.max())

    return PredictionOutput(
        category=predicted_category,
        confidence=round(confidence, 6),
        model_version=MODEL_VERSION,
    )