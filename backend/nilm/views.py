import sys
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mediciones.models import Medicion, ArtefactoDetectado, PrediccionGasto

# Agregar la carpeta ml/src al path para importar ecowatt_ml
ML_SRC_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "src"
sys.path.insert(0, str(ML_SRC_PATH))

ML_MODELS_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


class NilmLatestView(APIView):
    def get(self, request):
        try:
            from ecowatt_ml.predict import predict_appliance_from_features

            ultima_medicion = Medicion.objects.first()
            if not ultima_medicion:
                return Response(
                    {"mensaje": "Sin mediciones disponibles"},
                    status=status.HTTP_404_NOT_FOUND
                )

            features = [
                ultima_medicion.voltaje_rms,
                ultima_medicion.corriente_rms,
                ultima_medicion.angulo_fase,
                ultima_medicion.potencia_activa,
                ultima_medicion.potencia_reactiva,
                ultima_medicion.potencia_aparente,
                ultima_medicion.factor_potencia,
            ]

            sgn_model_path = ML_MODELS_PATH / "sgn_v2.pt"
            if not sgn_model_path.exists():
                sgn_model_path = ML_MODELS_PATH / "sgn_v1.pt"

            resultado = predict_appliance_from_features(features, sgn_model_path)

            artefacto = ArtefactoDetectado.objects.create(
                medicion=ultima_medicion,
                nombre_artefacto=resultado["detected_appliance"],
                confianza=resultado["confidence"],
            )

            return Response({
                "timestamp": ultima_medicion.timestamp.isoformat(),
                "detected_appliance": resultado["detected_appliance"],
                "confidence": resultado["confidence"],
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CostPredictionView(APIView):
    def get(self, request):
        try:
            from ecowatt_ml.predict import predict_monthly_cost
            import tempfile
            import pandas as pd

            mediciones = Medicion.objects.all().order_by('timestamp')[:200]
            if not mediciones:
                return Response(
                    {"mensaje": "Sin mediciones disponibles"},
                    status=status.HTTP_404_NOT_FOUND
                )

            data = [{
                "timestamp": m.timestamp,
                "voltage_rms": m.voltaje_rms,
                "current_rms": m.corriente_rms,
                "phase_angle": m.angulo_fase,
                "active_power_w": m.potencia_activa,
                "reactive_power_var": m.potencia_reactiva,
                "apparent_power_va": m.potencia_aparente,
                "power_factor": m.factor_potencia,
                "energy_kwh": m.kwh_acumulado,
                "appliance_label": "desconocido",
                "tariff_soles_kwh": 0.60,
            } for m in mediciones]

            df = pd.DataFrame(data)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                df.to_csv(f.name, index=False)
                temp_path = f.name

            cost_model_path = ML_MODELS_PATH / "cost_regression_refit_house8.joblib"
            resultado = predict_monthly_cost(temp_path, cost_model_path)

            PrediccionGasto.objects.create(
                kwh_proyectado=resultado["predicted_monthly_cost_soles"] / 0.60,
                costo_proyectado_soles=resultado["predicted_monthly_cost_soles"],
                tarifa_usada=0.60,
            )

            return Response({
                "projected_cost_soles": resultado["predicted_monthly_cost_soles"],
                "tariff_soles_kwh": 0.60,
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )