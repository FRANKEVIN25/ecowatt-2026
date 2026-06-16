#  EcoWatt 2026

> **Sistema inteligente de monitoreo y gestión del consumo eléctrico residencial**  
> Hackathon EcoWatt 2026 — Universidad Nacional de Ingeniería (UNI)  
> Organizado por Affinity Group WIE UNI · Rama Estudiantil IEEE UNI

---

## Equipo

| Nombre | Rol | Universidad |
|--------|-----|-------------|
| Frank Kevin Jauregui Bendezu | Software Lead / Backend | UPCH |
| Jesus Anselmo Morales Alvarado | Backend / ML Engineer | UPCH |
| John Kenneth Karita | Hardware Lead / Electrónica | UNI |
| Oscar Angello Marcelo Romero Pizarro | Hardware / Electrónica | UNI |

---

## ¿Qué es EcoWatt?

EcoWatt es una solución integral para el monitoreo y gestión del consumo eléctrico en viviendas residenciales. Combina hardware de bajo costo con algoritmos de inteligencia artificial para:

- **Medir** en tiempo real: voltaje, corriente, potencia activa/reactiva, factor de potencia y kWh
- **Identificar** automáticamente qué artefacto está conectado mediante **NILM** (Non-Intrusive Load Monitoring)
- **Predecir** el gasto eléctrico mensual en soles
- **Recomendar** acciones para reducir el consumo vía IA conversacional

---

## Arquitectura del sistema

```
[Arduino UNO + CT 5A + ZMPT101B]
            ↓ TTL Serial
[ESP32 WROOM-32] → WiFi → [Broker MQTT]
                                ↓
                    [Backend Django + DRF]
                    [PostgreSQL — Series temporales]
                                ↓
                    [Pipeline NILM]
                    ├── Preprocesamiento (ventanas 1s)
                    ├── SGN — Semantics-Guided Neural Network (PyTorch)
                    ├── Seq2Point (backup)
                    └── Regresión Lineal — predicción de gasto
                                ↓
                    [IA Conversacional — Gemini API / Claude API]
                                ↓
                    [Dashboard — SvelteKit + Tailwind + Recharts]
```

> Base científica: Chatterjee & Heer (2025) — *Non-Intrusive Load Monitoring (NILM) with very low-frequency data from smart meters in Switzerland*. Energy & Buildings 344, 116002. [DOI](https://doi.org/10.1016/j.enbuild.2025.116002)

---

## Stack tecnológico

### Hardware
![Arduino](https://img.shields.io/badge/Arduino-00979D?style=flat&logo=arduino&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=flat&logo=espressif&logoColor=white)

| Componente | Función |
|-----------|---------|
| Arduino UNO | Lectura analógica de sensores |
| ESP32 WROOM-32 | Procesamiento + WiFi + MQTT |
| Sensor CT 5A | Medición de corriente (no invasivo) |
| ZMPT101B | Medición de voltaje AC |
| Relay 5V | Control de cargas |
| Dimmer + focos 25W/100W | Cargas de prueba |

### Software
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white)
![Svelte](https://img.shields.io/badge/SvelteKit-FF3E00?style=flat&logo=svelte&logoColor=white)

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.x · Django · DRF · PostgreSQL · Redis |
| ML / NILM | PyTorch · SGN · Seq2Point · scikit-learn · pandas · numpy |
| IA Conversacional | Gemini API (principal) · Claude API (backup) |
| Frontend | SvelteKit · Tailwind CSS · Recharts |
| Comunicación HW | MQTT · TTL Serial |
| DevOps | Git · GitHub · Docker |

---

## Estructura del proyecto

```
ecowatt-2026/
│
├── hardware/
│   ├── arduino/          # Código C para Arduino UNO
│   └── esp32/            # Código C para ESP32 WROOM-32
│
├── backend/
│   ├── ecowatt/          # Proyecto Django principal
│   ├── requirements.txt
│   └── docker-compose.yml
│
├── ml/
│   ├── data/             # Datasets NILM (REFIT, ECO)
│   ├── models/           # Modelos entrenados (.pt / .pkl)
│   ├── notebooks/        # Exploración y entrenamiento
│   └── nilm_pipeline.py  # Pipeline principal SGN + Seq2Point
│
├── frontend/
│   └── ecowatt-dashboard/ # Proyecto SvelteKit
│
└── docs/
    ├── analisis.md
    └── disenio_excalidraw.md
```

---

## Instalación y setup

### Requisitos previos
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Docker (opcional)

### Backend

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/ecowatt-2026.git
cd ecowatt-2026/backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL y APIs

# Migraciones
python manage.py migrate

# Correr servidor
python manage.py runserver
```

### Frontend

```bash
cd ecowatt-2026/frontend/ecowatt-dashboard
npm install
npm run dev
```

### Variables de entorno necesarias

```env
# .env
DATABASE_URL=postgresql://usuario:password@localhost:5432/ecowatt
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
GEMINI_API_KEY=tu_api_key
CLAUDE_API_KEY=tu_api_key
SECRET_KEY=django_secret_key
DEBUG=True
```

---

## Cronograma de desarrollo

| Fecha | Actividad |
|-------|-----------|
| 13 jun | Jornada de inicio — Salón IEEE UNI |
| 14–19 jun | Desarrollo del proyecto |
| 20 jun | Jornada de seguimiento — Salón IEEE UNI |
| **22 jun** | **Presentación final — Auditorio CCAT UNI** |

---

## Criterios de evaluación

| Criterio | Puntaje |
|----------|---------|
| Innovación y Creatividad | 30 pts |
| Área Electrónica | 20 pts |
| Área Software e IA | 20 pts |
| Fluidez en la Exposición | 10 pts |
| **Total** | **80 pts** |

---

## Referencias científicas

- Chatterjee, A., & Heer, P. (2025). *Non-Intrusive Load Monitoring (NILM) with very low-frequency data from smart meters in Switzerland*. Energy & Buildings, 344, 116002. https://doi.org/10.1016/j.enbuild.2025.116002
- Kelly, J., & Knottenbelt, W. (2015). *Neural NILM: Deep neural networks applied to energy disaggregation*. ACM BuildSys 2015.
- Murray, D., Stankovic, L., & Stankovic, V. (2017). *An electrical load measurements dataset of United Kingdom households*. Scientific Data, 4.

---

## Licencia

MIT License — Frank Kevin Jauregui Bendezu · Jesus Morales · John Karita · Oscar Marcelo · 2026

---

<div align="center">
  <strong> EcoWatt 2026 — Eficiencia Energética Inteligente para el Hogar</strong><br>
  Hackathon EcoWatt · Universidad Nacional de Ingeniería · Junio 2026
</div>
