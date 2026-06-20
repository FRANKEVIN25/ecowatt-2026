# EcoWatt ML / NILM

Base de trabajo para las tareas JA:

- SCRUM-21: descarga, normalizacion y preprocesamiento REFIT/ECO.
- SCRUM-22: modelo SGN con PyTorch.
- SCRUM-23: entrenamiento, validacion y exportacion de artefactos.
- SCRUM-24: regresion lineal para prediccion de gasto.

La carpeta esta preparada para avanzar con datos reales o con datos simulados mientras backend, hardware y WebSocket terminan su integracion.

## Setup

```powershell
cd ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Flujo rapido con datos mock

```powershell
python -m ecowatt_ml.generate_mock_data --output data/sample_measurements.csv --seconds 3600
python -m ecowatt_ml.generate_mock_data --samples 50000 --output data/training_data.csv
python -m ecowatt_ml.convert_refit --input "C:\Users\jessz\Downloads\CLEAN_REFIT_081116\CLEAN_House8.csv" --output data/refit_house8_training.csv --samples 50000 --every-n-rows 120
python -m ecowatt_ml.train_cost_regression --input data/sample_measurements.csv --output models/cost_regression.joblib
python -m ecowatt_ml.train_sgn --input data/sample_measurements.csv --output models/sgn_mock.pt --epochs 5
python -m ecowatt_ml.train_sgn --input data/refit_house8_training.csv --output models/sgn_v2.pt --epochs 50 --window-size 60
python -m ecowatt_ml.predict --input data/sample_measurements.csv --sgn-model models/sgn_mock.pt --cost-model models/cost_regression.joblib
python -m ecowatt_ml.predict --sgn-model models/sgn_mock.pt --features "220,0.46,16.2,101,28,105,0.96"
```

## Columnas esperadas

El pipeline trabaja con CSV tabular. Las columnas minimas son:

| columna | descripcion |
| --- | --- |
| `timestamp` | Fecha/hora ISO 8601. |
| `voltage_rms` | Voltaje RMS. |
| `current_rms` | Corriente RMS. |
| `phase_angle` | Angulo de fase en grados. |
| `active_power_w` | Potencia activa en W. |
| `reactive_power_var` | Potencia reactiva en VAR. |
| `apparent_power_va` | Potencia aparente en VA. |
| `power_factor` | Factor de potencia. |
| `energy_kwh` | Energia acumulada en kWh. |
| `appliance_label` | Etiqueta NILM para entrenamiento. |
| `tariff_soles_kwh` | Tarifa usada para costo estimado. |

## Datasets reales

REFIT/ECO pueden tener licencias, formatos y granularidades distintas. Para hackathon, el primer objetivo es convertir cualquier fuente al contrato anterior. Despues el mismo pipeline podra entrenar sin tocar dashboard ni backend.

El entrenamiento SGN divide primero las filas de forma cronologica, deja una
separacion de `window_size - 1` filas y recien entonces genera las ventanas.
Esto evita que entrenamiento y validacion compartan mediciones. El escalador
tambien se ajusta solamente con el bloque de entrenamiento.
