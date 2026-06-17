from django.contrib import admin
from .models import Medicion, ArtefactoDetectado, PrediccionGasto, SesionDemo


@admin.register(Medicion)
class MedicionAdmin(admin.ModelAdmin):
    list_display = ['cuarto', 'timestamp', 'potencia_activa', 'factor_potencia', 'kwh_acumulado']
    list_filter = ['cuarto', 'timestamp']
    ordering = ['-timestamp']


@admin.register(ArtefactoDetectado)
class ArtefactoDetectadoAdmin(admin.ModelAdmin):
    list_display = ['nombre_artefacto', 'confianza', 'timestamp']
    list_filter = ['nombre_artefacto']
    ordering = ['-timestamp']


@admin.register(PrediccionGasto)
class PrediccionGastoAdmin(admin.ModelAdmin):
    list_display = ['fecha_calculo', 'kwh_proyectado', 'costo_proyectado_soles', 'tarifa_usada']
    ordering = ['-fecha_calculo']


@admin.register(SesionDemo)
class SesionDemoAdmin(admin.ModelAdmin):
    list_display = ['inicio', 'fin', 'total_kwh']
    ordering = ['-inicio']