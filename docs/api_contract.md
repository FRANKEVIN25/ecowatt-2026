# EcoWatt API and Mock Contract

Este contrato permite avanzar dashboard y ML sin esperar hardware, MQTT o WebSocket.

## Measurement payload

```json
{
  "timestamp": "2026-06-16T20:00:00Z",
  "room": "principal",
  "voltage_rms": 220.4,
  "current_rms": 0.82,
  "phase_angle": 14.2,
  "active_power_w": 180.5,
  "reactive_power_var": 41.2,
  "apparent_power_va": 190.8,
  "power_factor": 0.94,
  "energy_kwh": 1.42
}
```

## NILM prediction payload

```json
{
  "timestamp": "2026-06-16T20:00:00Z",
  "detected_appliance": "foco_100w",
  "confidence": 0.91
}
```

## Cost prediction payload

```json
{
  "calculation_date": "2026-06-16",
  "projected_kwh": 114.2,
  "projected_cost_soles": 68.52,
  "tariff_soles_kwh": 0.6
}
```

## Suggested REST endpoints

| metodo | ruta | uso |
| --- | --- | --- |
| `GET` | `/api/measurements/latest/` | ultima medicion para tarjetas del dashboard |
| `GET` | `/api/measurements/history/?from=&to=` | serie historica para graficas |
| `GET` | `/api/nilm/latest/` | artefacto detectado y confianza |
| `GET` | `/api/cost/prediction/` | prediccion de gasto mensual |

## Suggested WebSocket message

Canal propuesto: `/ws/measurements/`

```json
{
  "type": "measurement.update",
  "measurement": {
    "timestamp": "2026-06-16T20:00:00Z",
    "active_power_w": 180.5,
    "energy_kwh": 1.42
  },
  "nilm": {
    "detected_appliance": "foco_100w",
    "confidence": 0.91
  },
  "cost": {
    "projected_cost_soles": 68.52
  }
}
```
