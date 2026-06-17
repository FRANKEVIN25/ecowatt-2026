import uuid
from django.db import models


class Medicion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    cuarto = models.CharField(max_length=100, default='principal')
    voltaje_rms = models.FloatField()
    corriente_rms = models.FloatField()
    angulo_fase = models.FloatField()
    potencia_activa = models.FloatField()
    potencia_reactiva = models.FloatField()
    potencia_aparente = models.FloatField()
    factor_potencia = models.FloatField()
    kwh_acumulado = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Medición'
        verbose_name_plural = 'Mediciones'

    def __str__(self):
        return f"{self.cuarto} - {self.timestamp} - {self.potencia_activa}W"


class ArtefactoDetectado(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    medicion = models.ForeignKey(
        Medicion,
        on_delete=models.CASCADE,
        related_name='artefactos'
    )
    nombre_artefacto = models.CharField(max_length=100)
    confianza = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Artefacto Detectado'
        verbose_name_plural = 'Artefactos Detectados'

    def __str__(self):
        return f"{self.nombre_artefacto} - {self.confianza:.2f}%"


class PrediccionGasto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_calculo = models.DateField(auto_now_add=True)
    kwh_proyectado = models.FloatField()
    costo_proyectado_soles = models.FloatField()
    tarifa_usada = models.FloatField(default=0.60)

    class Meta:
        ordering = ['-fecha_calculo']
        verbose_name = 'Predicción de Gasto'
        verbose_name_plural = 'Predicciones de Gasto'

    def __str__(self):
        return f"{self.fecha_calculo} - S/ {self.costo_proyectado_soles}"


class SesionDemo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    total_kwh = models.FloatField(default=0.0)
    artefactos_detectados = models.JSONField(default=list)

    class Meta:
        ordering = ['-inicio']
        verbose_name = 'Sesión Demo'
        verbose_name_plural = 'Sesiones Demo'

    def __str__(self):
        return f"Sesión {self.inicio} - {self.total_kwh} kWh"