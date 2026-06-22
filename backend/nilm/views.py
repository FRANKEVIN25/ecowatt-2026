import sys
from pathlib import Path
import google.generativeai as genai
from django.conf import settings
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
            from ecowatt_ml.predict import predict_appliance_from_window

            ultima_medicion = Medicion.objects.first()
            if not ultima_medicion:
                return Response(
                    {"mensaje": "Sin mediciones disponibles"},
                    status=status.HTTP_404_NOT_FOUND
                )

            sgn_model_path = ML_MODELS_PATH / "sgn_v3.pt"
            mediciones = list(Medicion.objects.all()[:127])
            if len(mediciones) < 127:
                return Response(
                    {
                        "mensaje": (
                            "Se requieren 127 mediciones reales para ejecutar "
                            "la ventana SGN v3."
                        ),
                        "mediciones_disponibles": len(mediciones),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            features = [
                [
                    medicion.voltaje_rms,
                    medicion.corriente_rms,
                    medicion.angulo_fase,
                    medicion.potencia_activa,
                    medicion.potencia_reactiva,
                    medicion.potencia_aparente,
                    medicion.factor_potencia,
                ]
                for medicion in reversed(mediciones)
            ]
            resultado = predict_appliance_from_window(features, sgn_model_path)

            artefacto = ArtefactoDetectado.objects.create(
                medicion=ultima_medicion,
                nombre_artefacto=resultado["detected_appliance"],
                confianza=resultado["confidence"],
            )

            return Response({
                "timestamp": ultima_medicion.timestamp.isoformat(),
                "detected_appliance": resultado["detected_appliance"],
                "detected_appliance_key": resultado["detected_appliance_key"],
                "confidence": resultado["confidence"],
                "predicted_power_w": resultado["predicted_power_w"],
                "active_appliances": resultado["active_appliances"],
                "appliance_predictions": resultado["appliance_predictions"],
                "model_version": "sgn_v3",
                "data_source": "mediciones_reales",
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
        
class ChatIAView(APIView):
    def post(self, request):
        try:
            pregunta = request.data.get('pregunta', '').strip()
            if not pregunta:
                return Response(
                    {"error": "Debes enviar una pregunta"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            ultima_medicion = Medicion.objects.first()
            ultimo_artefacto = ArtefactoDetectado.objects.first()
            ultima_prediccion = PrediccionGasto.objects.first()

            contexto_partes = []

            if ultima_medicion:
                contexto_partes.append(
                    f"Consumo actual: {ultima_medicion.potencia_activa:.1f}W, "
                    f"voltaje {ultima_medicion.voltaje_rms:.1f}V, "
                    f"energia acumulada {ultima_medicion.kwh_acumulado:.3f} kWh."
                )

            if ultimo_artefacto:
                contexto_partes.append(
                    f"Artefacto detectado actualmente: {ultimo_artefacto.nombre_artefacto} "
                    f"con {ultimo_artefacto.confianza*100:.0f}% de confianza."
                )

            if ultima_prediccion:
                contexto_partes.append(
                    f"Gasto mensual proyectado: S/ {ultima_prediccion.costo_proyectado_soles:.2f} "
                    f"a una tarifa de S/ {ultima_prediccion.tarifa_usada:.2f} por kWh."
                )

            contexto = " ".join(contexto_partes) if contexto_partes else "Sin datos de consumo disponibles todavia."

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')

            prompt = f"""Eres el asistente de EcoWatt, un sistema de monitoreo de consumo electrico residencial en Peru.

Datos actuales del hogar:
{contexto}

Pregunta del usuario: {pregunta}

Responde en español, de forma breve (maximo 3 oraciones), clara y orientada a dar una recomendacion practica y accionable sobre ahorro de energia. Usa los datos reales proporcionados, no inventes numeros. Si no tienes datos suficientes, dilo honestamente."""

            response = model.generate_content(prompt)

            return Response({
                "pregunta": pregunta,
                "respuesta": response.text,
                "contexto_usado": contexto,
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
