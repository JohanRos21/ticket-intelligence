from __future__ import annotations

import csv
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

SEED = 20260624
EXAMPLES_PER_CATEGORY = 150
GENERATOR_VERSION = "v0.1"
OUTPUT_PATH = Path("data/raw/tickets_synthetic_v0.1.csv")

CATEGORIES = (
    "acceso_autenticacion",
    "pagos_facturacion",
    "error_tecnico",
    "rendimiento",
    "solicitud_funcionalidad",
    "consulta_general",
)


@dataclass(frozen=True)
class Family:
    name: str
    titles: Sequence[str]
    descriptions: Sequence[str]
    slots: Mapping[str, Sequence[str]]


COMMON_SLOTS: Dict[str, Sequence[str]] = {
    "device": (
        "desde mi laptop",
        "desde el celular",
        "en la aplicación web",
        "desde una computadora de la oficina",
        "en el navegador",
        "desde la aplicación móvil",
    ),
    "time_context": (
        "desde esta mañana",
        "desde ayer",
        "desde la última actualización",
        "desde hace unos minutos",
        "desde la semana pasada",
        "desde que cambié la configuración",
    ),
    "frequency": (
        "siempre",
        "casi siempre",
        "de forma intermitente",
        "cada vez que lo intento",
        "solo en algunos intentos",
        "varias veces al día",
    ),
    "impact": (
        "y no puedo continuar con mi trabajo",
        "y el proceso queda detenido",
        "y afecta a varios usuarios",
        "y necesito resolverlo hoy",
        "y no encuentro una alternativa",
        "y esto retrasa la atención de clientes",
    ),
}


FAMILIES: Dict[str, Sequence[Family]] = {
    "acceso_autenticacion": (
        Family(
            "credenciales_rechazadas",
            (
                "No puedo iniciar sesión",
                "Mis credenciales son rechazadas",
                "La clave aparece como incorrecta",
                "Acceso denegado con datos correctos",
            ),
            (
                "Intento ingresar con {credential}, pero el sistema indica que los datos no son válidos {time_context}.",
                "La plataforma rechaza {credential} aunque estoy seguro de que es correcto {device}.",
                "Puedo escribir mis datos, pero al confirmar aparece un mensaje de acceso denegado {frequency}.",
            ),
            {
                "credential": (
                    "mi correo y contraseña",
                    "el usuario y la clave",
                    "las credenciales habituales",
                    "la contraseña recién actualizada",
                )
            },
        ),
        Family(
            "recuperacion_no_recibida",
            (
                "No llega el correo de recuperación",
                "No recibo el enlace para restablecer la clave",
                "Recuperación de contraseña sin respuesta",
            ),
            (
                "Solicité recuperar la contraseña {attempts}, pero el mensaje no llega a {destination}.",
                "El sistema confirma el envío del enlace, aunque no aparece en {destination} {time_context}.",
                "Necesito restablecer la clave y no recibo ningún correo ni código {impact}.",
            ),
            {
                "attempts": ("una vez", "varias veces", "desde ayer", "hace más de una hora"),
                "destination": ("mi bandeja de entrada", "el correo registrado", "spam ni correo principal", "mi dirección corporativa"),
            },
        ),
        Family(
            "cuenta_bloqueada",
            (
                "Mi cuenta quedó bloqueada",
                "No puedo entrar por bloqueo de cuenta",
                "La cuenta fue suspendida tras varios intentos",
            ),
            (
                "Después de {attempts} el sistema bloqueó la cuenta y ya no permite iniciar sesión.",
                "La plataforma informa que mi usuario está bloqueado, incluso después de esperar {wait_time}.",
                "Ya tengo la contraseña correcta, pero el bloqueo continúa activo {impact}.",
            ),
            {
                "attempts": ("varios intentos fallidos", "cambiar la contraseña", "ingresar desde otro dispositivo", "probar un código antiguo"),
                "wait_time": ("treinta minutos", "una hora", "todo el día", "hasta el día siguiente"),
            },
        ),
        Family(
            "doble_factor",
            (
                "El código de verificación no funciona",
                "Problema con la autenticación de dos pasos",
                "Código 2FA rechazado",
            ),
            (
                "El código generado por {method} aparece como inválido aunque todavía está vigente.",
                "No puedo completar el segundo paso porque {problem} {frequency}.",
                "La verificación adicional falla {device} y no me deja acceder a la cuenta.",
            ),
            {
                "method": ("la aplicación autenticadora", "el mensaje SMS", "el correo", "el token de seguridad"),
                "problem": ("el código no llega", "el código expira de inmediato", "el código es rechazado", "la pantalla vuelve al inicio"),
            },
        ),
        Family(
            "sesion_expirada",
            (
                "La sesión se cierra sola",
                "La plataforma me desconecta constantemente",
                "Sesión expirada pocos segundos después de entrar",
            ),
            (
                "Inicio sesión correctamente, pero la plataforma me desconecta {delay} {frequency}.",
                "Mientras trabajo, la sesión expira sin aviso {device}.",
                "Puedo entrar, pero al cambiar de sección vuelvo a la pantalla de acceso {impact}.",
            ),
            {
                "delay": ("a los pocos segundos", "después de un minuto", "al abrir otro módulo", "al guardar información"),
            },
        ),
        Family(
            "activacion_cuenta",
            (
                "No puedo activar mi cuenta",
                "El enlace de activación está vencido",
                "Cuenta registrada pero sin activar",
            ),
            (
                "Completé el registro, pero {activation_problem} y no puedo iniciar sesión.",
                "El enlace recibido para activar la cuenta muestra {message} {time_context}.",
                "La cuenta aparece creada, aunque el sistema sigue pidiendo activación {impact}.",
            ),
            {
                "activation_problem": ("nunca llegó el mensaje de activación", "el botón de activar no responde", "el enlace ya expiró", "la confirmación no se guarda"),
                "message": ("enlace inválido", "token vencido", "cuenta no encontrada", "activación pendiente"),
            },
        ),
        Family(
            "cambio_datos_acceso",
            (
                "No puedo entrar después de cambiar mi correo",
                "Acceso rechazado tras actualizar la contraseña",
                "Problema de acceso luego de modificar mis datos",
            ),
            (
                "Actualicé {field} y desde entonces ninguna de las credenciales me permite ingresar.",
                "El cambio de {field} fue confirmado, pero el acceso sigue usando los datos anteriores.",
                "Después de modificar {field}, la cuenta quedó inaccesible {device}.",
            ),
            {
                "field": ("el correo", "la contraseña", "el nombre de usuario", "el número de teléfono"),
            },
        ),
        Family(
            "cierre_sesion",
            (
                "No puedo cerrar la sesión",
                "La cuenta permanece abierta después de salir",
                "El botón cerrar sesión no termina el acceso",
            ),
            (
                "Presiono cerrar sesión, pero la cuenta continúa abierta {device}.",
                "Después de salir, al volver a la página sigo dentro de la cuenta {frequency}.",
                "La opción de cerrar sesión me devuelve al panel sin finalizar la autenticación.",
            ),
            {},
        ),
    ),
    "pagos_facturacion": (
        Family(
            "pago_rechazado",
            ("Mi pago fue rechazado", "La tarjeta no es aceptada", "No puedo completar el cobro"),
            (
                "Intenté pagar con {payment_method}, pero la transacción fue rechazada {frequency}.",
                "El sistema no acepta {payment_method} aunque tiene fondos y está habilitado para compras.",
                "Al confirmar el pago aparece {error_message} y la suscripción no se renueva.",
            ),
            {
                "payment_method": ("mi tarjeta de crédito", "una tarjeta de débito", "la tarjeta corporativa", "el método guardado"),
                "error_message": ("pago denegado", "método no válido", "transacción no autorizada", "error al procesar el cobro"),
            },
        ),
        Family(
            "cobro_duplicado",
            ("Me cobraron dos veces", "Cobro duplicado en mi tarjeta", "Aparecen dos cargos por la misma compra"),
            (
                "En {statement} aparecen dos cargos por una sola operación realizada {time_context}.",
                "Solo confirmé el pago una vez, pero se registraron {count} cobros idénticos.",
                "La misma factura fue cobrada más de una vez {impact}.",
            ),
            {
                "statement": ("el estado de cuenta", "la banca móvil", "el historial de pagos", "mi tarjeta"),
                "count": ("dos", "tres", "varios"),
            },
        ),
        Family(
            "factura_no_recibida",
            ("No recibí la factura", "El comprobante no aparece", "Pago aprobado sin documento tributario"),
            (
                "El pago fue aprobado, pero no encuentro la factura en {location}.",
                "Necesito el comprobante de {purchase}, aunque el sistema todavía no lo genera.",
                "La transacción terminó correctamente y no recibí ningún documento de pago {time_context}.",
            ),
            {
                "location": ("mi correo", "la sección de facturación", "el historial de compras", "ninguna bandeja"),
                "purchase": ("la suscripción", "la renovación", "la compra del plan", "el último cobro"),
            },
        ),
        Family(
            "monto_incorrecto",
            ("El monto cobrado es incorrecto", "Me cobraron un plan diferente", "Importe equivocado en la factura"),
            (
                "Contraté {expected_plan}, pero el cobro corresponde a {charged_plan}.",
                "La factura muestra {difference} respecto del precio informado.",
                "El total cobrado no coincide con el monto mostrado antes de confirmar la compra.",
            ),
            {
                "expected_plan": ("el plan básico", "una licencia mensual", "el paquete promocional", "una sola cuenta"),
                "charged_plan": ("el plan empresarial", "una licencia anual", "el precio sin descuento", "varias cuentas"),
                "difference": ("un importe mayor", "impuestos duplicados", "un descuento faltante", "servicios no contratados"),
            },
        ),
        Family(
            "pago_no_registrado",
            ("El pago no aparece registrado", "Pagué pero la cuenta sigue vencida", "Transacción aprobada sin activación"),
            (
                "Realicé {payment_type}, pero la suscripción todavía figura como pendiente.",
                "El banco confirma el cobro y la plataforma no reconoce la transacción {time_context}.",
                "La operación aparece aprobada, aunque el servicio sigue suspendido por falta de pago.",
            ),
            {
                "payment_type": ("una transferencia", "el pago con tarjeta", "la renovación", "el depósito bancario"),
            },
        ),
        Family(
            "reembolso",
            ("Solicito un reembolso", "La devolución todavía no llega", "Problema con el reintegro"),
            (
                "El reembolso fue aprobado hace {days}, pero el dinero no aparece en mi cuenta.",
                "Necesito devolver {purchase} porque se realizó por error.",
                "La plataforma marca la devolución como completada, aunque el banco no registra el abono.",
            ),
            {
                "days": ("tres días", "una semana", "diez días", "más de dos semanas"),
                "purchase": ("una compra duplicada", "una renovación automática", "un plan incorrecto", "una licencia no utilizada"),
            },
        ),
        Family(
            "suscripcion_cancelada",
            ("Siguen cobrando una suscripción cancelada", "Cobro posterior a la cancelación", "Renovación automática no autorizada"),
            (
                "Cancelé el servicio {time_context}, pero hoy apareció un nuevo cargo.",
                "La suscripción figura cancelada y aun así se procesó la renovación automática.",
                "Solicité detener los cobros, pero el método de pago volvió a ser debitado.",
            ),
            {},
        ),
        Family(
            "factura_incorrecta",
            ("Datos incorrectos en la factura", "El comprobante tiene información equivocada", "Necesito corregir los datos fiscales"),
            (
                "La factura muestra {wrong_field} que no corresponde a mi empresa.",
                "El comprobante fue emitido con datos antiguos y necesito corregir {wrong_field}.",
                "La información tributaria del documento no coincide con la registrada en la cuenta.",
            ),
            {
                "wrong_field": ("la razón social", "el número tributario", "la dirección fiscal", "el nombre del cliente"),
            },
        ),
    ),
    "error_tecnico": (
        Family(
            "pantalla_blanca",
            ("La página queda en blanco", "Pantalla vacía al abrir un módulo", "No aparece contenido en la sección"),
            (
                "Al abrir {module} solo aparece una pantalla blanca y no se muestra ningún dato.",
                "Puedo navegar por el menú, pero {module} no carga su contenido {device}.",
                "La sección queda vacía {frequency} y necesito volver a cargar la página.",
            ),
            {"module": ("el módulo de reportes", "la configuración", "el panel de usuarios", "la sección de documentos")},
        ),
        Family(
            "boton_no_responde",
            ("El botón no responde", "No ocurre nada al guardar", "La acción principal dejó de funcionar"),
            (
                "Hago clic en {button}, pero no ocurre nada y el proceso queda detenido.",
                "El botón {button} dejó de ejecutar la acción {time_context}.",
                "La interfaz permite completar los datos, aunque {button} no responde {frequency}.",
            ),
            {"button": ("guardar", "enviar", "confirmar", "continuar", "descargar")},
        ),
        Family(
            "datos_no_guardados",
            ("Los cambios no quedan guardados", "La información vuelve a su valor anterior", "No se actualizan los datos"),
            (
                "La plataforma confirma la actualización, pero al volver a entrar aparecen {old_values}.",
                "Guardo el formulario y los cambios desaparecen después de recargar la página.",
                "La operación termina sin error, aunque la base sigue mostrando los datos anteriores.",
            ),
            {"old_values": ("los valores anteriores", "los datos antiguos", "los campos vacíos", "la configuración previa")},
        ),
        Family(
            "archivo_falla",
            ("No puedo subir archivos", "Error al descargar el documento", "El archivo generado está dañado"),
            (
                "Al intentar {file_action} aparece {file_error} y la operación se detiene.",
                "El proceso de {file_action} termina, pero el archivo no puede abrirse.",
                "Cualquier documento produce el mismo error cuando intento {file_action}.",
            ),
            {
                "file_action": ("subir un archivo", "descargar el reporte", "abrir el documento", "exportar la información"),
                "file_error": ("un error de servidor", "formato no válido", "archivo corrupto", "operación fallida"),
            },
        ),
        Family(
            "cierre_inesperado",
            ("La aplicación se cierra sola", "El sistema se cierra al editar", "La aplicación falla durante una operación"),
            (
                "Cada vez que intento {action}, la aplicación se cierra inesperadamente.",
                "El sistema deja de responder y se cierra {device} al realizar {action}.",
                "Puedo entrar normalmente, pero la aplicación falla al {action}.",
            ),
            {"action": ("editar un registro", "abrir un reporte", "adjuntar un archivo", "confirmar una operación")},
        ),
        Family(
            "integracion_fallida",
            ("La integración dejó de funcionar", "No se sincronizan los datos externos", "Falló la conexión con otro servicio"),
            (
                "La integración con {service} estaba funcionando, pero dejó de enviar información {time_context}.",
                "Los datos de {service} ya no se sincronizan aunque la conexión sigue habilitada.",
                "La plataforma muestra un error cada vez que intenta comunicarse con {service}.",
            ),
            {"service": ("el correo", "el sistema contable", "el CRM", "el servicio de almacenamiento")},
        ),
        Family(
            "duplicados",
            ("Se crean registros duplicados", "La misma operación se guarda dos veces", "Aparecen elementos repetidos"),
            (
                "Confirmo la operación una sola vez, pero el sistema genera {duplicate_count} registros iguales.",
                "Cada vez que guardo, la lista muestra el mismo elemento repetido.",
                "La plataforma duplica {entity} sin que vuelva a enviar el formulario.",
            ),
            {
                "duplicate_count": ("dos", "tres", "varios"),
                "entity": ("el ticket", "la factura", "el usuario", "la solicitud"),
            },
        ),
        Family(
            "servicio_caido",
            ("El sistema está caído", "Servicio no disponible", "Nadie puede abrir la plataforma"),
            (
                "Todos los usuarios reciben {server_error} al intentar ingresar.",
                "La plataforma completa dejó de responder {time_context}.",
                "Ningún módulo está disponible y el navegador muestra un error del servidor.",
            ),
            {"server_error": ("un error 500", "servicio no disponible", "tiempo de espera agotado", "conexión rechazada")},
        ),
    ),
    "rendimiento": (
        Family(
            "carga_lenta",
            ("La página tarda demasiado", "El dashboard carga muy lento", "El módulo demora en mostrar información"),
            (
                "{module} termina cargando, pero demora {duration} en mostrar la información.",
                "La pantalla responde correctamente después de esperar {duration} {frequency}.",
                "Desde {time_context}, {module} tarda mucho más de lo habitual.",
            ),
            {
                "module": ("El dashboard", "La lista de usuarios", "El panel principal", "La sección de reportes"),
                "duration": ("más de un minuto", "varios segundos", "casi dos minutos", "demasiado tiempo"),
            },
        ),
        Family(
            "reporte_lento",
            ("Los reportes se generan lentamente", "El informe tarda varios minutos", "Demora excesiva al procesar reportes"),
            (
                "El reporte se genera correctamente, aunque tarda {duration} en completarse.",
                "Los datos finales son correctos, pero el procesamiento de {report_type} es demasiado lento.",
                "Cada solicitud de reporte permanece procesando durante {duration} antes de finalizar.",
            ),
            {
                "duration": ("cinco minutos", "casi diez minutos", "más de quince minutos", "mucho más que antes"),
                "report_type": ("ventas", "usuarios", "actividad", "facturación"),
            },
        ),
        Family(
            "busqueda_lenta",
            ("La búsqueda demora mucho", "Los resultados aparecen con retraso", "Buscar registros toma varios segundos"),
            (
                "Cada búsqueda devuelve resultados, pero tarda {duration} en responder.",
                "Al consultar {entity}, la pantalla queda esperando antes de mostrar coincidencias.",
                "Los filtros funcionan correctamente, aunque la respuesta es demasiado lenta.",
            ),
            {
                "duration": ("entre diez y veinte segundos", "más de medio minuto", "varios segundos", "mucho más de lo normal"),
                "entity": ("usuarios", "tickets", "facturas", "documentos"),
            },
        ),
        Family(
            "lentitud_horaria",
            ("El sistema se pone lento por las tardes", "Rendimiento degradado en horas punta", "La plataforma se ralentiza con muchos usuarios"),
            (
                "En {period} todas las pantallas tardan más, aunque fuera de ese horario funcionan bien.",
                "Cuando hay varios usuarios conectados, el sistema responde con mucha demora.",
                "El rendimiento baja notablemente {period} y las operaciones tardan en completarse.",
            ),
            {"period": ("la tarde", "las horas de mayor uso", "el cierre de mes", "la mañana de los lunes")},
        ),
        Family(
            "archivos_lentos",
            ("La carga de archivos es muy lenta", "Descargar documentos demora demasiado", "Procesamiento lento de archivos"),
            (
                "El archivo termina {file_action}, pero incluso uno pequeño demora {duration}.",
                "La operación no falla, aunque {file_action} es mucho más lenta que antes.",
                "Puedo completar {file_action}, pero el tiempo de espera afecta el trabajo diario.",
            ),
            {
                "file_action": ("de subir", "de descargar", "de procesar", "de importar"),
                "duration": ("varios minutos", "más de diez minutos", "casi una hora", "demasiado tiempo"),
            },
        ),
        Family(
            "api_lenta",
            ("La API responde lentamente", "Tiempo de respuesta elevado", "Las solicitudes tardan varios segundos"),
            (
                "Las solicitudes devuelven datos correctos, pero el tiempo de respuesta supera {duration}.",
                "El endpoint funciona, aunque responde con mucha demora {frequency}.",
                "No hay errores HTTP, pero la latencia aumentó {time_context}.",
            ),
            {"duration": ("cinco segundos", "ocho segundos", "diez segundos", "el tiempo esperado")},
        ),
        Family(
            "congelamiento_temporal",
            ("La interfaz se congela unos segundos", "La aplicación queda bloqueada temporalmente", "Pausas frecuentes al cambiar de sección"),
            (
                "Al {action}, la pantalla queda congelada {duration} y luego continúa.",
                "La aplicación no se cierra, pero deja de responder temporalmente {frequency}.",
                "Cada cambio de sección provoca una pausa antes de mostrar el contenido.",
            ),
            {
                "action": ("cambiar de sección", "guardar un formulario", "abrir un menú", "cargar una tabla"),
                "duration": ("unos segundos", "casi medio minuto", "más tiempo de lo normal", "de forma perceptible"),
            },
        ),
        Family(
            "proceso_masivo_lento",
            ("El procesamiento masivo demora demasiado", "Importar registros toma mucho tiempo", "La tarea por lotes es muy lenta"),
            (
                "El proceso de {bulk_action} termina correctamente, pero tarda {duration}.",
                "Procesar {volume} registros toma demasiado tiempo aunque no aparecen errores.",
                "La tarea masiva completa el trabajo, pero bloquea al usuario durante {duration}.",
            ),
            {
                "bulk_action": ("importación", "actualización masiva", "generación de reportes", "sincronización"),
                "volume": ("cien", "quinientos", "mil", "pocos cientos de"),
                "duration": ("casi una hora", "varios minutos", "mucho más que antes", "un tiempo excesivo"),
            },
        ),
    ),
    "solicitud_funcionalidad": (
        Family(
            "nueva_exportacion",
            ("Quiero exportar a Excel", "Agregar un nuevo formato de exportación", "Necesitamos descargar datos en otro formato"),
            (
                "Actualmente solo se puede exportar en {current_format} y necesitamos soporte para {new_format}.",
                "Solicito una opción que permita descargar {entity} en {new_format}.",
                "Sería útil agregar {new_format} a los formatos disponibles de exportación.",
            ),
            {
                "current_format": ("PDF", "CSV", "una vista web", "un formato fijo"),
                "new_format": ("Excel", "JSON", "XML", "Google Sheets"),
                "entity": ("los reportes", "la lista de usuarios", "las facturas", "los tickets"),
            },
        ),
        Family(
            "nuevo_login",
            ("Agregar inicio de sesión con Google", "Necesitamos acceso con Microsoft", "Nuevo método de autenticación"),
            (
                "Solicito que los usuarios puedan ingresar mediante {provider} además del correo y contraseña.",
                "Sería útil incorporar autenticación con {provider} para facilitar el acceso.",
                "Necesitamos un nuevo método de inicio de sesión basado en {provider}.",
            ),
            {"provider": ("Google", "Microsoft", "Apple", "el proveedor corporativo SSO")},
        ),
        Family(
            "nuevo_pago",
            ("Agregar un nuevo método de pago", "Quiero pagar con billetera digital", "Necesitamos otra opción de cobro"),
            (
                "Sería útil permitir pagos mediante {payment_method} además de las tarjetas.",
                "Solicito incorporar {payment_method} como alternativa de pago.",
                "Necesitamos que la plataforma acepte {payment_method} para nuevas suscripciones.",
            ),
            {"payment_method": ("una billetera digital", "transferencia bancaria", "débito automático", "pago por QR")},
        ),
        Family(
            "filtros_avanzados",
            ("Agregar filtros avanzados", "Necesitamos más opciones de búsqueda", "Solicito filtros combinados"),
            (
                "Quisiera filtrar {entity} por {criteria} al mismo tiempo.",
                "La búsqueda actual es básica y necesitamos filtros por {criteria}.",
                "Solicito una opción para combinar varios criterios al consultar {entity}.",
            ),
            {
                "entity": ("reportes", "tickets", "usuarios", "facturas"),
                "criteria": ("fecha, estado y responsable", "sede, prioridad y categoría", "cliente, plan y periodo", "varios campos personalizados"),
            },
        ),
        Family(
            "integracion_nueva",
            ("Integración con Slack", "Conectar la plataforma con otro servicio", "Necesitamos una nueva integración"),
            (
                "Solicito integrar la plataforma con {service} para {purpose}.",
                "Sería útil enviar información automáticamente a {service}.",
                "Necesitamos una conexión con {service}, ya que actualmente no existe.",
            ),
            {
                "service": ("Slack", "Microsoft Teams", "Google Drive", "un CRM externo"),
                "purpose": ("recibir alertas", "sincronizar archivos", "compartir reportes", "actualizar clientes"),
            },
        ),
        Family(
            "automatizacion",
            ("Automatizar una tarea repetitiva", "Envío programado de reportes", "Necesitamos ejecuciones automáticas"),
            (
                "Quisiera programar {task} para que se ejecute {schedule}.",
                "Solicito una automatización que permita {task} sin intervención manual.",
                "Actualmente hacemos el proceso manualmente y necesitamos automatizar {task}.",
            ),
            {
                "task": ("el envío de reportes", "la asignación de tickets", "la creación de respaldos", "la actualización de estados"),
                "schedule": ("cada lunes", "al final del día", "una vez al mes", "cuando ocurra un evento"),
            },
        ),
        Family(
            "roles_permisos",
            ("Crear permisos personalizados", "Necesitamos nuevos roles", "Agregar control detallado de accesos"),
            (
                "Quisiera definir permisos específicos para {role} en lugar de usar perfiles fijos.",
                "Solicito un nuevo rol que pueda {capability}.",
                "Necesitamos configurar permisos por módulo para diferentes tipos de usuario.",
            ),
            {
                "role": ("supervisores", "agentes", "auditores", "usuarios invitados"),
                "capability": ("ver reportes sin editar", "aprobar solicitudes", "administrar usuarios", "consultar solo su sede"),
            },
        ),
        Family(
            "mejora_interfaz",
            ("Agregar modo oscuro", "Necesitamos una vista móvil", "Personalizar la interfaz"),
            (
                "Sería útil incorporar {feature} para mejorar el uso de la plataforma.",
                "Solicito una opción de {feature}, ya que actualmente no está disponible.",
                "Necesitamos adaptar la interfaz con {feature} para nuestros usuarios.",
            ),
            {"feature": ("modo oscuro", "diseño para celulares", "paneles personalizables", "tamaño de texto configurable")},
        ),
    ),
    "consulta_general": (
        Family(
            "como_usar",
            ("¿Cómo uso esta función?", "Necesito instrucciones para completar el proceso", "¿Dónde encuentro esta opción?"),
            (
                "Quisiera saber cómo {action} dentro de la plataforma.",
                "No encuentro dónde se realiza {action}; necesito orientación.",
                "¿Qué pasos debo seguir para {action} correctamente?",
            ),
            {"action": ("descargar un reporte", "actualizar mis datos", "crear un usuario", "cerrar un ticket", "cambiar una configuración")},
        ),
        Family(
            "planes_precios",
            ("Información sobre los planes", "¿Cuánto cuesta el servicio?", "Diferencias entre las suscripciones"),
            (
                "Quiero conocer las diferencias entre {plan_a} y {plan_b}.",
                "¿Qué funciones están incluidas en {plan_a}?",
                "Necesito información sobre precios, límites y condiciones de los planes disponibles.",
            ),
            {
                "plan_a": ("el plan básico", "la suscripción mensual", "el plan profesional", "la opción empresarial"),
                "plan_b": ("el plan profesional", "la suscripción anual", "el plan empresarial", "la opción básica"),
            },
        ),
        Family(
            "horarios_soporte",
            ("Horario de atención", "¿Cuándo está disponible soporte?", "Necesito conocer el horario de ayuda"),
            (
                "¿En qué días y horarios puedo comunicarme con {support_channel}?",
                "Quisiera saber si el soporte atiende {time_period}.",
                "Necesito información sobre el horario y los canales de atención disponibles.",
            ),
            {
                "support_channel": ("el equipo de soporte", "un agente", "la mesa de ayuda", "atención al cliente"),
                "time_period": ("los fines de semana", "por la noche", "durante feriados", "fuera del horario de oficina"),
            },
        ),
        Family(
            "metodos_disponibles",
            ("Métodos de pago disponibles", "¿Qué opciones acepta la plataforma?", "Información sobre formas de pago"),
            (
                "Quiero saber qué {option_type} acepta actualmente la plataforma.",
                "¿Está disponible {specific_option} para nuevas suscripciones?",
                "Necesito conocer las alternativas permitidas antes de realizar la operación.",
            ),
            {
                "option_type": ("tarjetas y medios de pago", "formatos de exportación", "métodos de acceso", "tipos de archivo"),
                "specific_option": ("el pago con tarjeta", "la exportación CSV", "el acceso por correo", "la carga de PDF"),
            },
        ),
        Family(
            "tiempos_estimados",
            ("¿Cuánto demora este proceso?", "Tiempo normal de activación", "Necesito conocer el plazo estimado"),
            (
                "¿Cuánto suele tardar {process} en condiciones normales?",
                "Quisiera conocer el plazo aproximado para completar {process}.",
                "Necesito saber si {duration} es el tiempo habitual de {process}.",
            ),
            {
                "process": ("la activación de una cuenta", "la generación de un reporte", "la revisión de una solicitud", "la emisión de una factura"),
                "duration": ("unas horas", "un día", "varios minutos", "una semana"),
            },
        ),
        Family(
            "politicas_requisitos",
            ("Consulta sobre políticas", "¿Cuáles son los requisitos?", "Necesito información sobre las condiciones"),
            (
                "Quisiera conocer la política de {topic} de la plataforma.",
                "¿Qué requisitos debo cumplir para {action}?",
                "Necesito información sobre las condiciones aplicables a {topic}.",
            ),
            {
                "topic": ("conservación de datos", "cancelación", "privacidad", "reembolsos", "uso de cuentas"),
                "action": ("registrar una empresa", "activar un plan", "invitar usuarios", "solicitar un reembolso"),
            },
        ),
        Family(
            "disponibilidad_funcion",
            ("¿La plataforma incluye esta función?", "Quiero saber si existe esta opción", "Consulta sobre una característica"),
            (
                "¿Está disponible {feature} en mi plan actual?",
                "Quiero confirmar si la plataforma permite {feature}.",
                "Necesito saber dónde se encuentra {feature} o si todavía no está habilitada.",
            ),
            {"feature": ("la exportación de datos", "el acceso para varios usuarios", "la personalización de reportes", "la descarga de facturas")},
        ),
        Family(
            "estado_proceso",
            ("Consulta sobre el estado de una solicitud", "¿Dónde reviso el avance?", "Necesito conocer el estado del trámite"),
            (
                "Quisiera saber dónde puedo consultar el estado de {process}.",
                "¿Cómo verifico si {process} ya fue completado?",
                "Necesito orientación para revisar el avance de {process} sin reportar un error.",
            ),
            {"process": ("mi registro", "una solicitud de soporte", "la activación del plan", "la emisión de un comprobante")},
        ),
    ),
}


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^a-záéíóúüñ0-9 ]", "", value)
    return value


def merge_slots(*slot_groups: Mapping[str, Sequence[str]]) -> Dict[str, Sequence[str]]:
    merged: Dict[str, Sequence[str]] = {}
    for group in slot_groups:
        merged.update(group)
    return merged


def render(template: str, slots: Mapping[str, Sequence[str]], rng: random.Random) -> str:
    values = {name: rng.choice(options) for name, options in slots.items()}
    return template.format(**values)


def maybe_add_context(text: str, rng: random.Random) -> str:
    additions = (
        "",
        "",
        " Esto sucede en más de un dispositivo.",
        " El problema también fue confirmado por otro usuario.",
        " Ya intenté actualizar la página y volver a probar.",
        " Necesito continuar con el proceso cuanto antes.",
        " Antes funcionaba con normalidad.",
    )
    return f"{text}{rng.choice(additions)}".strip()


def generate_for_family(
    category: str,
    family: Family,
    target_count: int,
    rng: random.Random,
    seen_pairs: set[tuple[str, str]],
) -> List[dict[str, str]]:
    rows: List[dict[str, str]] = []
    slots = merge_slots(COMMON_SLOTS, family.slots)
    attempts = 0
    max_attempts = target_count * 300

    while len(rows) < target_count and attempts < max_attempts:
        attempts += 1
        title = render(rng.choice(family.titles), slots, rng)
        description = render(rng.choice(family.descriptions), slots, rng)
        description = maybe_add_context(description, rng)

        key = (normalize_text(title), normalize_text(description))
        if key in seen_pairs:
            continue

        seen_pairs.add(key)
        rows.append(
            {
                "title": title,
                "description": description,
                "category": category,
                "source": "synthetic_generator",
                "synthetic": "true",
                "template_family": family.name,
                "generator_version": GENERATOR_VERSION,
            }
        )

    if len(rows) != target_count:
        raise RuntimeError(
            f"No se pudieron generar {target_count} ejemplos únicos para "
            f"{category}/{family.name}. Generados: {len(rows)}"
        )

    return rows


def balanced_quotas(total: int, groups: int) -> List[int]:
    base, remainder = divmod(total, groups)
    return [base + (1 if index < remainder else 0) for index in range(groups)]


def build_dataset() -> List[dict[str, str]]:
    rng = random.Random(SEED)
    seen_pairs: set[tuple[str, str]] = set()
    rows: List[dict[str, str]] = []

    for category in CATEGORIES:
        families = FAMILIES[category]
        quotas = balanced_quotas(EXAMPLES_PER_CATEGORY, len(families))

        category_rows: List[dict[str, str]] = []
        for family, quota in zip(families, quotas):
            category_rows.extend(
                generate_for_family(
                    category=category,
                    family=family,
                    target_count=quota,
                    rng=rng,
                    seen_pairs=seen_pairs,
                )
            )

        rng.shuffle(category_rows)
        rows.extend(category_rows)

    rng.shuffle(rows)

    for index, row in enumerate(rows, start=1):
        row["id"] = f"S{index:06d}"

    return rows


def validate_dataset(rows: Iterable[Mapping[str, str]]) -> None:
    rows = list(rows)
    expected_total = EXAMPLES_PER_CATEGORY * len(CATEGORIES)

    if len(rows) != expected_total:
        raise AssertionError(f"Se esperaban {expected_total} filas y se generaron {len(rows)}")

    required_fields = {
        "id",
        "title",
        "description",
        "category",
        "source",
        "synthetic",
        "template_family",
        "generator_version",
    }

    empty_rows = [row["id"] for row in rows if any(not str(row[field]).strip() for field in required_fields)]
    if empty_rows:
        raise AssertionError(f"Hay filas con campos vacíos: {empty_rows[:10]}")

    id_counts = Counter(row["id"] for row in rows)
    duplicate_ids = [row_id for row_id, count in id_counts.items() if count > 1]
    if duplicate_ids:
        raise AssertionError(f"IDs duplicados: {duplicate_ids[:10]}")

    pair_counts = Counter(
        (normalize_text(row["title"]), normalize_text(row["description"]))
        for row in rows
    )
    duplicate_pairs = [pair for pair, count in pair_counts.items() if count > 1]
    if duplicate_pairs:
        raise AssertionError(f"Tickets duplicados exactos: {duplicate_pairs[:3]}")

    category_counts = Counter(row["category"] for row in rows)
    expected_distribution = {category: EXAMPLES_PER_CATEGORY for category in CATEGORIES}
    if dict(category_counts) != expected_distribution:
        raise AssertionError(
            f"Distribución inesperada. Esperado={expected_distribution}, real={dict(category_counts)}"
        )

    invalid_categories = sorted(set(category_counts) - set(CATEGORIES))
    if invalid_categories:
        raise AssertionError(f"Categorías no permitidas: {invalid_categories}")

    if any(row["synthetic"] != "true" for row in rows):
        raise AssertionError("Todas las filas generadas deben estar marcadas como sintéticas")


def write_csv(rows: Sequence[Mapping[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "id",
        "title",
        "description",
        "category",
        "source",
        "synthetic",
        "template_family",
        "generator_version",
    )

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: Sequence[Mapping[str, str]], path: Path) -> None:
    category_counts = Counter(row["category"] for row in rows)
    family_counts = Counter((row["category"], row["template_family"]) for row in rows)

    print("\nDataset sintético generado correctamente")
    print(f"Ruta: {path.resolve()}")
    print(f"Semilla: {SEED}")
    print(f"Versión del generador: {GENERATOR_VERSION}")
    print(f"Total: {len(rows)}")

    print("\nDistribución por categoría:")
    for category in CATEGORIES:
        print(f"  - {category}: {category_counts[category]}")

    print("\nFamilias utilizadas:")
    for category in CATEGORIES:
        names = [family.name for family in FAMILIES[category]]
        details = ", ".join(f"{name}={family_counts[(category, name)]}" for name in names)
        print(f"  - {category}: {details}")


if __name__ == "__main__":
    dataset = build_dataset()
    validate_dataset(dataset)
    write_csv(dataset, OUTPUT_PATH)
    print_summary(dataset, OUTPUT_PATH)
