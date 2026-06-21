# Revisión técnica de ramas EcoWatt

Revisión realizada el 21 de junio de 2026. Los cambios de esta entrega se
mantienen únicamente en `feature/nilm-pipeline`; no se modificaron las ramas de
otros integrantes.

## `main` — hardware

Prioridad crítica:

- El Arduino usa `Serial2.print((uint8_t) data)`, lo que convierte la dirección
  del arreglo y no transmite las mediciones completas. Debe serializar un
  paquete delimitado o JSON con checksum.
- El ESP32 publica valores fijos de demostración en lugar de consumir la trama
  del Arduino.
- El payload ESP32 (`voltage`, `current`, `power`, `uptime_ms`) no coincide con
  el contrato del backend (`V`, `I`, `P`, `phi`, `fp`, `kWh`).
- SoftwareSerial a 115200 baudios puede ser inestable. Conviene bajar la
  velocidad o usar UART de hardware.

Recomendación: acordar primero un único esquema versionado, incluir
`timestamp`, `voltage_rms`, `current_rms`, `active_power_w`, `power_factor` y
`energy_kwh`, y probarlo con mensajes grabados antes de conectar sensores.

## `dev` — backend e integración

Prioridad alta:

- NILM repite una sola medición para completar la ventana temporal; eso no
  representa una secuencia real. Debe consultar las últimas 60 mediciones
  ordenadas.
- El servicio carga `sgn_v2`/`sgn_v1`, pero no el artefacto y preprocesador de
  `sgn_v3`.
- El endpoint de costo crea archivos temporales sin limpieza y deriva kWh desde
  el costo usando una tarifa fija.
- La llamada a Gemini es síncrona y no define timeout; puede bloquear una
  petición web.
- `sqrt(abs(S²-P²))` oculta datos físicamente inconsistentes cuando `P > S`.
- Frontend, API y WebSocket fijan `127.0.0.1`; deben configurarse por variables
  de entorno.
- Faltan pruebas de contrato MQTT, WebSocket, NILM y costo.

Recomendación: integrar primero el contrato MQTT, luego un buffer temporal real
para SGN v3 y finalmente el predictor de gasto con respuesta explícita en kWh,
soles, horizonte y nivel de confianza.

## Ramas de hardware antiguas

Estas ramas permanecen en el commit inicial y no contienen el trabajo actual.
El código de hardware está directamente en `main`. Conviene actualizar o cerrar
esas ramas para que el repositorio no sugiera que hay implementaciones
separadas listas para integrar.

## `feature/nilm-pipeline`

Fortalezas:

- SGN v3 ya separa casas/bloques cronológicos y evita ventanas compartidas.
- Reporta macro-F1, balanced accuracy y baseline siempre apagado.
- El benchmark de contingencia separa sesiones completas y declara su origen
  sintético.

Pendiente antes de producción:

- Obtener mediciones EcoWatt etiquetadas.
- Unificar el preprocesador del entrenamiento con el del backend.
- Evaluar inferencia continua y latencia en el dispositivo objetivo.
- Reentrenar el predictor de gasto con varios días y más de un hogar.

## Orden recomendado de integración

1. Contrato único Arduino → ESP32 → MQTT → Django.
2. Persistencia de mediciones con timestamps confiables.
3. Buffer de ventanas e inferencia SGN v3.
4. Proyección de kWh/costo con historial real.
5. Dashboard en vivo y pruebas de extremo a extremo.
