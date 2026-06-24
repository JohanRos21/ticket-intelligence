# Taxonomía de tickets v0.1

**Proyecto:** Ticket Intelligence  
**Versión:** v0.1  
**Objetivo:** establecer reglas consistentes para clasificar tickets de soporte.

## Principio general

La categoría debe representar el problema principal que necesita resolver el usuario.

No se debe clasificar únicamente por una palabra aislada. Se debe considerar el significado completo del título y la descripción.

---

## 1. acceso_autenticacion

### Definición

Tickets relacionados con la imposibilidad, dificultad o necesidad de ayuda para identificarse, iniciar sesión, cerrar sesión, recuperar credenciales o acceder a una cuenta.

### Casos incluidos

- El usuario no puede iniciar sesión.
- La contraseña es rechazada.
- El usuario olvidó su contraseña.
- No llega el correo o código de recuperación.
- La cuenta está bloqueada.
- El código de verificación no funciona.
- Problemas con autenticación de dos factores.
- La sesión se cierra inesperadamente.
- El usuario no puede acceder después de cambiar sus credenciales.
- Problemas para activar una cuenta cuando impiden autenticarse.

### Casos excluidos

- El sistema completo está caído para todos.
- Una pantalla falla después de iniciar sesión correctamente.
- El sistema carga lentamente después de ingresar.
- El usuario solicita un nuevo método de acceso.
- El origen del bloqueo es un pago o suscripción.

### Ejemplos

- “No puedo iniciar sesión porque mi contraseña aparece como incorrecta”.
- “No recibo el código de recuperación”.
- “Mi cuenta quedó bloqueada después de varios intentos”.
- “La sesión se cierra sola”.

### Reglas para casos ambiguos

- Credenciales, códigos, bloqueo de cuenta o sesión: `acceso_autenticacion`.
- Plataforma completa caída: `error_tecnico`.
- Acceso suspendido por cobro o suscripción: `pagos_facturacion`.
- Solicitud de iniciar sesión con Google u otro proveedor: `solicitud_funcionalidad`.

---

## 2. pagos_facturacion

### Definición

Tickets cuyo problema principal está relacionado con pagos, cobros, facturas, comprobantes, suscripciones, reembolsos o métodos de pago.

### Casos incluidos

- Tarjeta o método de pago rechazado.
- Cobro duplicado.
- Cobro no reconocido.
- Pago realizado pero no registrado.
- Problemas para renovar una suscripción.
- Solicitud de reembolso.
- Factura o comprobante incorrecto.
- Factura no recibida.
- Monto cobrado incorrectamente.
- Cobros posteriores a una cancelación.
- Acceso suspendido por un problema de pago.

### Casos excluidos

- Contraseña incorrecta.
- Cuenta bloqueada por intentos fallidos.
- Pantalla de pago que no abre por un fallo técnico.
- Proceso de pago que funciona, pero es lento.
- Solicitud de un método de pago que todavía no existe.
- Preguntas generales sobre precios o planes.

### Ejemplos

- “Mi tarjeta fue rechazada al pagar”.
- “Me cobraron dos veces”.
- “No recibí mi factura”.
- “El pago no aparece registrado”.
- “Quiero solicitar un reembolso”.

### Reglas para casos ambiguos

- Cobro, factura, reembolso o suscripción problemática: `pagos_facturacion`.
- Pantalla de pago en blanco o botón que falla: `error_tecnico`.
- Pago que termina, pero demora demasiado: `rendimiento`.
- Solicitud de un nuevo método de pago: `solicitud_funcionalidad`.
- Pregunta sobre precios o medios aceptados: `consulta_general`.

---

## 3. error_tecnico

### Definición

Tickets relacionados con fallos, errores o comportamientos incorrectos de una función existente del sistema.

### Casos incluidos

- Una página o módulo no abre.
- Aparece una pantalla en blanco.
- El sistema muestra un mensaje de error.
- Un botón no responde.
- La aplicación se cierra inesperadamente.
- Una operación no se completa.
- Los datos no se guardan correctamente.
- Los datos mostrados son incorrectos.
- Un archivo no se puede cargar o descargar.
- Una integración existente deja de funcionar.
- El sistema completo está caído.
- La aplicación se congela y no permite continuar.

### Casos excluidos

- La operación funciona, pero lentamente.
- El fallo está limitado a credenciales o sesión.
- El problema principal es un cobro o factura.
- El usuario solicita una función que no existe.
- El usuario solo pregunta cómo utilizar una opción.

### Ejemplos

- “La página queda en blanco”.
- “No puedo guardar los cambios”.
- “El botón enviar no responde”.
- “El reporte muestra datos incorrectos”.
- “Ningún usuario puede abrir la plataforma”.

### Reglas para casos ambiguos

- Función existente que falla: `error_tecnico`.
- Función que termina, pero con demora excesiva: `rendimiento`.
- Función inexistente solicitada por el usuario: `solicitud_funcionalidad`.
- Problema limitado a credenciales: `acceso_autenticacion`.
- Pregunta de uso sin evidencia de fallo: `consulta_general`.

---

## 4. rendimiento

### Definición

Tickets relacionados con lentitud, tiempos de respuesta elevados, bloqueos temporales o degradación del desempeño.

La función termina funcionando, pero tarda más de lo esperado.

### Casos incluidos

- Una página tarda demasiado en cargar.
- Un reporte demora varios minutos en generarse.
- Las búsquedas responden lentamente.
- El sistema se vuelve lento en ciertas horas.
- Una función opera más lentamente que antes.
- La aplicación consume demasiados recursos.
- La interfaz se congela unos segundos y luego continúa.
- Una API responde con mucha demora.
- La carga o descarga de archivos es anormalmente lenta.

### Casos excluidos

- La operación falla completamente.
- La página nunca carga.
- El sistema devuelve un error.
- El problema está en credenciales.
- El pago fue rechazado.
- El usuario pide una función nueva.
- El usuario solo pregunta cuánto debería tardar una operación.

### Ejemplos

- “El dashboard demora más de un minuto”.
- “El reporte se genera, pero tarda diez minutos”.
- “Cada búsqueda demora varios segundos”.
- “La plataforma se pone lenta por las tardes”.
- “La descarga termina, pero demora demasiado”.

### Reglas para casos ambiguos

- La operación termina correctamente, pero tarda demasiado: `rendimiento`.
- La operación nunca termina o devuelve error: `error_tecnico`.
- La lentitud se debe a una nueva mejora solicitada: `solicitud_funcionalidad`.
- El pago es rechazado o queda mal registrado: `pagos_facturacion`.

---

## 5. solicitud_funcionalidad

### Definición

Tickets en los que el usuario solicita crear, agregar, modificar o ampliar una capacidad que actualmente no existe o no cubre su necesidad.

### Casos incluidos

- Solicitar una nueva opción o módulo.
- Pedir nuevos filtros de búsqueda.
- Solicitar exportación a un formato no disponible.
- Pedir inicio de sesión con Google u otro proveedor.
- Solicitar un nuevo método de pago.
- Pedir personalización de notificaciones.
- Solicitar integración con otra plataforma.
- Pedir nuevos campos en formularios.
- Solicitar nuevos roles o permisos.
- Pedir modo oscuro.
- Solicitar automatización de una tarea manual.

### Casos excluidos

- Una función existente dejó de funcionar.
- Una página tarda demasiado.
- Una contraseña es rechazada.
- Un pago fue duplicado.
- El usuario solo pregunta cómo utilizar una opción existente.
- El usuario pregunta si una función ya existe.

### Ejemplos

- “Quiero exportar a Excel”.
- “Deberían agregar inicio de sesión con Google”.
- “Solicito modo oscuro”.
- “Necesito nuevos filtros para reportes”.
- “Quiero una integración con Slack”.
- “Deberían permitir pagos con billetera digital”.

### Reglas para casos ambiguos

- La capacidad no existe y se pide agregarla: `solicitud_funcionalidad`.
- La opción existe, pero falla: `error_tecnico`.
- La opción existe y el usuario no sabe usarla: `consulta_general`.
- Se reporta lentitud de una función existente: `rendimiento`.

---

## 6. consulta_general

### Definición

Tickets donde el usuario solicita información, orientación o instrucciones sin reportar claramente un error, lentitud, problema de acceso, problema financiero o nueva funcionalidad.

### Casos incluidos

- Preguntas sobre cómo utilizar una función existente.
- Consultas sobre planes, precios o características.
- Preguntas sobre horarios de atención.
- Consultas sobre políticas o procedimientos.
- Preguntas sobre disponibilidad de una función.
- Solicitudes de orientación básica.
- Preguntas sobre requisitos.
- Consultas sobre dónde encontrar una opción.
- Preguntas sobre tiempos estimados normales.
- Solicitudes de información sobre el estado de un proceso sin reportar un fallo.

### Casos excluidos

- La función existe, pero falla.
- La plataforma está lenta.
- La contraseña o el código no funcionan.
- Existe un cobro incorrecto.
- El usuario solicita desarrollar una nueva función.
- La cuenta está bloqueada.
- Una operación nunca termina.

### Ejemplos

- “¿Cómo descargo un reporte?”.
- “¿Qué diferencias hay entre los planes?”.
- “¿Cuánto tarda normalmente la activación?”.
- “¿Dónde cambio mi correo?”.
- “¿Cuál es el horario de atención?”.
- “¿Qué métodos de pago aceptan?”.

### Reglas para casos ambiguos

- Solo solicita información o instrucciones: `consulta_general`.
- Afirma que una función existente falla: `error_tecnico`.
- Solicita agregar una opción inexistente: `solicitud_funcionalidad`.
- Pregunta por precios o métodos disponibles: `consulta_general`.
- Reporta un cobro o transacción problemática: `pagos_facturacion`.
- Pregunta cómo recuperar una contraseña: `consulta_general`.
- Indica que la recuperación no funciona: `acceso_autenticacion`.

---

## Regla general de decisión

1. Credenciales, cuenta, acceso o sesión → `acceso_autenticacion`.
2. Cobros, pagos, facturas, suscripciones o reembolsos → `pagos_facturacion`.
3. Una función existente falla o produce un resultado incorrecto → `error_tecnico`.
4. Una función funciona, pero demasiado lentamente → `rendimiento`.
5. El usuario solicita una capacidad nueva → `solicitud_funcionalidad`.
6. El usuario solo solicita información o instrucciones → `consulta_general`.

Cuando un ticket mencione varios problemas, se debe seleccionar la categoría correspondiente al problema principal que debe resolver el equipo de soporte.
