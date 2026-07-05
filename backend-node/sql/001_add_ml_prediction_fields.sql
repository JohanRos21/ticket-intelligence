-- ============================================================
-- TICKET INTELLIGENCE
-- Migración 001: campos de predicción Machine Learning
-- ============================================================
-- Añade a la tabla tickets los campos necesarios para guardar:
-- categoría predicha, confianza, versión del modelo y estado
-- del intento de clasificación.

ALTER TABLE tickets
ADD COLUMN predicted_category VARCHAR(50) NULL AFTER priority,
ADD COLUMN prediction_confidence DECIMAL(8,6) NULL AFTER predicted_category,
ADD COLUMN model_version VARCHAR(100) NULL AFTER prediction_confidence,
ADD COLUMN prediction_status VARCHAR(30) NULL AFTER model_version,
ADD COLUMN prediction_created_at TIMESTAMP NULL DEFAULT NULL AFTER prediction_status;