# EcoWatt ML Pipeline

## Objetivo

Entregar una ruta reproducible desde datos crudos de medicion electrica hasta:

- deteccion de artefacto conectado con confianza;
- prediccion mensual de gasto en soles;
- artefactos exportables para integracion con Django.

## Fases

1. Ingesta REFIT/ECO o CSV de hardware.
2. Normalizacion al contrato `ml/README.md`.
3. Generacion de ventanas temporales para NILM.
4. Entrenamiento SGN sequence-to-point con compuerta de estado por aparato.
5. Entrenamiento de regresion lineal para gasto.
6. Exportacion de `models/sgn_v3.pt`, sidecar `.joblib`, metricas JSON y `models/cost_regression.joblib`.
7. Integracion backend mediante servicio interno o tarea asincrona.

## Independencias y mocks

| tarea | puede avanzar ahora | mock recomendado |
| --- | --- | --- |
| SCRUM-21 | si | `ml/data/sample_measurements.csv` |
| SCRUM-22 | si | etiquetas sinteticas de artefactos |
| SCRUM-23 | si | entrenamiento corto con dataset mock |
| SCRUM-24 | si | energia acumulada + tarifa fija |
| SCRUM-27 | parcial | payload `/api/nilm/latest/` |
| SCRUM-29 | parcial | payload `/api/cost/prediction/` |

## Criterios minimos de demo

- El pipeline debe correr con un comando documentado.
- Los modelos deben guardarse en `ml/models/`.
- Las metricas deben imprimirse al terminar entrenamiento.
- La prueba SGN debe usar un bloque cronologico futuro o una casa no vista.
- Deben reportarse F1, balanced accuracy, MAE y baseline siempre-apagado.
- La salida debe poder convertirse directamente a los modelos Django:
  `ArtefactoDetectado` y `PrediccionGasto`.

## Niveles de evidencia

Las métricas deben mostrarse separadas para evitar confundir una demostración
con una validación real:

| nivel | uso | métrica disponible |
| --- | --- | --- |
| REFIT House 8 | validación con datos públicos reales | macro-F1 0.347, balanced accuracy 0.762 |
| simulación de contingencia | continuidad de la demo sin hardware | macro-F1 0.818, accuracy 0.845 |
| hardware EcoWatt | aceptación final del sistema | pendiente de mediciones etiquetadas |

El benchmark sintético usa 640 sesiones independientes y deja 141 sesiones
completas para prueba. No tiene solapamiento de sesiones ni se ajustó alterando
las etiquetas de prueba. Sus números no deben atribuirse a REFIT.

## Ruta para mejorar F1 y gasto

1. Corregir el contrato MQTT y almacenar potencia agregada continua.
2. Etiquetar eventos de encendido/apagado de al menos una semana por hogar.
3. Evaluar por días o sesiones no vistas, nunca por ventanas aleatorias.
4. Entrenar NILM por aparato y calibrar umbrales con validación separada.
5. Proyectar kWh y soles con historial diario, tarifa y calendario.
6. Mostrar intervalos de confianza y comparar contra un baseline simple.
