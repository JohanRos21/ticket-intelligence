# Ticket Intelligence

Sistema de clasificación automática de tickets de soporte en español. Combina
una API REST en Node.js, persistencia MySQL y un microservicio FastAPI que sirve
un modelo TF-IDF + Logistic Regression.

## Resultado final v0.1

El modelo fue entrenado con `train_v0.1.csv`, seleccionado con
`validation_v0.1.csv` y evaluado una sola vez sobre las 113 filas reservadas de
`test_v0.1.csv`, sin reentrenamiento.

| Métrica | Test v0.1 |
|---|---:|
| Accuracy | 0.7522 |
| Macro precision | 0.8241 |
| Macro recall | 0.7466 |
| **Macro F1** | **0.7103** |
| Errores | 28 / 113 |

Los resultados completos, hashes de los insumos, predicciones, errores y matriz
de confusión están en `reports/final_test_*_v0.1.*`. La clase con mayor margen de
mejora es `rendimiento` (recall 0.1111); no se oculta esta limitación del baseline.

## Arquitectura

```text
Cliente
  │ HTTP :3000
  ▼
API Node.js + Express ───────► MySQL :3306
  │ POST /predict
  ▼
FastAPI :8001 ───────► TF-IDF + Logistic Regression v0.1
```

Al crear un ticket, la API solicita una predicción y guarda categoría, confianza
y versión del modelo. La integración es tolerante a fallos: si ML no responde,
el ticket se persiste con `prediction_status=unavailable`.

Categorías soportadas:

- `acceso_autenticacion`
- `pagos_facturacion`
- `error_tecnico`
- `rendimiento`
- `solicitud_funcionalidad`
- `consulta_general`

## Inicio rápido con Docker

Requisito: Docker Engine con Docker Compose v2.

```bash
docker compose up --build -d
docker compose ps
```

Servicios publicados:

- API Node: <http://localhost:3000>
- Health API Node: <http://localhost:3000/health>
- ML API: <http://localhost:8001/docs>
- Health ML: <http://localhost:8001/health>
- MySQL: `localhost:3306`

Prueba end-to-end:

```bash
curl -X POST http://localhost:3000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"title":"No puedo iniciar sesión","description":"Mi contraseña no funciona","priority":"alta"}'
```

Para detener los contenedores:

```bash
docker compose down
```

Los datos de MySQL permanecen en el volumen `mysql_data`. Para un reinicio
destructivo del entorno local: `docker compose down -v`.

> Las credenciales de `docker-compose.yml` son exclusivamente de desarrollo.

## Ejecución local sin Docker

### Microservicio ML

Requiere Python 3.12.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r ml-service/requirements.txt
uvicorn app:app --app-dir ml-service --host 0.0.0.0 --port 8001
```

### API Node

Requiere Node.js 24 y una base MySQL. Cree la tabla con
`backend-node/sql/000_create_tickets.sql`, copie `.env.example` como `.env` y
ajuste las credenciales.

```bash
cd backend-node
npm ci
npm start
```

Endpoints principales:

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/tickets` | Lista y filtra tickets |
| GET | `/api/tickets/:id` | Obtiene un ticket |
| POST | `/api/tickets` | Crea y clasifica un ticket |
| PUT | `/api/tickets/:id` | Actualiza un ticket |
| PATCH | `/api/tickets/:id/status` | Cambia su estado |
| DELETE | `/api/tickets/:id` | Elimina un ticket |

Filtros disponibles en el listado: `status`, `priority` y `search`.

## Pruebas automatizadas

La suite Python usa `unittest` y cubre validación/carga de datos, métricas,
construcción del pipeline y contratos de salud y predicción de FastAPI. La suite
Node usa el runner nativo y cubre la integración ML exitosa y su degradación ante
errores HTTP o de red.

```bash
python -m unittest discover -s ml-service/tests -v
cd backend-node
npm test
```

Estado verificado: **10 pruebas aprobadas** (7 Python + 3 Node).

## Reproducir entrenamiento y evaluación

Entrenamiento y selección sobre train/validation:

```bash
python ml-service/train_baseline.py
```

Evaluación final sobre test (carga el artefacto existente y nunca ejecuta `fit`):

```bash
python ml-service/evaluate_test.py
```

Este último comando genera:

- `reports/final_test_metrics_v0.1.json`
- `reports/final_test_predictions_v0.1.csv`
- `reports/final_test_errors_v0.1.csv`
- `reports/final_test_confusion_matrix_v0.1.csv`

El JSON registra SHA-256 del modelo y del dataset para verificar exactamente qué
artefactos fueron evaluados.

## Estructura del repositorio

```text
backend-node/     API REST, cliente ML, SQL, tests y Dockerfile
data/             dataset fuente y splits versionados
docs/             taxonomía de categorías
ml-service/       entrenamiento, evaluación, FastAPI, modelo y tests
reports/          EDA, validación y evaluación final
scripts/          generación, validación y partición del dataset
docker-compose.yml orquestación local completa
```

## Decisiones y limitaciones

- El baseline prioriza simplicidad y reproducibilidad sobre complejidad.
- Macro F1 es la métrica principal porque pondera por igual las seis clases.
- El dataset v0.1 es sintético; los resultados no sustituyen validación con datos
  reales de producción.
- El bajo recall de `rendimiento` indica confusión con categorías cercanas y debe
  guiar la siguiente iteración de datos/modelo.
- `test_v0.1.csv` no se utiliza para entrenar ni seleccionar hiperparámetros.
