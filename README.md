# Ticket Intelligence

Sistema de clasificación automática de tickets de soporte mediante Machine Learning.

Ticket Intelligence es un proyecto independiente que reutiliza de forma controlada una API REST anterior desarrollada con Node.js, Express y MySQL.

## Objetivo

Clasificar tickets utilizando su título y descripción.

La versión v0.1 devolverá:

- category
- confidence
- model_version

## Categorías

1. acceso_autenticacion
2. pagos_facturacion
3. error_tecnico
4. rendimiento
5. solicitud_funcionalidad
6. consulta_general

## Arquitectura prevista

Cliente o Postman
→ API Node.js + Express
→ MySQL
→ Microservicio Python + FastAPI
→ TF-IDF + Logistic Regression

## Estructura

- backend-node: API REST y futura integración con el servicio ML.
- ml-service: entrenamiento, modelo y API FastAPI.
- data: datasets versionados.
- notebooks: experimentación y análisis.
- reports: resultados de evaluación.
- docs: documentación y taxonomía.

## Estado actual

- API original auditada.
- CRUD reutilizado en backend-node.
- Taxonomía v0.1 definida.
- Servicio ML todavía no implementado.
- Dataset todavía no construido.

## Modelo inicial

- TF-IDF
- Logistic Regression
- Métrica principal: Macro F1
