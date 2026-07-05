// ============================================================
// 1. CONFIGURACIÓN DEL MICROSERVICIO ML
// ============================================================
// La URL puede venir desde .env.
//
// El valor por defecto apunta al FastAPI local que ya probamos.

const ML_SERVICE_URL =
  process.env.ML_SERVICE_URL || "http://127.0.0.1:8001";

const ML_TIMEOUT_MS = Number(process.env.ML_TIMEOUT_MS || 3000);


// ============================================================
// 2. PREDICCIÓN DE CATEGORÍA
// ============================================================
// Esta función envía title + description a FastAPI.
//
// Decisión importante:
// La función NO lanza el error hacia el controlador cuando ML falla.
//
// En Ticket Intelligence, un fallo del microservicio ML no debe impedir
// que el ticket pueda guardarse posteriormente.
//
// Por eso devolvemos:
// success: true  -> predicción disponible
// success: false -> ML falló o no respondió

async function predictTicket({ title, description }) {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title,
        description: description || "",
      }),
      signal: AbortSignal.timeout(ML_TIMEOUT_MS),
    });

    if (!response.ok) {
      const responseBody = await response.text();

      return {
        success: false,
        predictionStatus: "failed",
        error: `ML service respondió ${response.status}: ${responseBody}`,
      };
    }

    const prediction = await response.json();

    return {
      success: true,
      predictionStatus: "predicted",
      category: prediction.category,
      confidence: prediction.confidence,
      modelVersion: prediction.model_version,
    };
  } catch (error) {
    return {
      success: false,
      predictionStatus: "unavailable",
      error: error.message,
    };
  }
}


module.exports = {
  predictTicket,
};