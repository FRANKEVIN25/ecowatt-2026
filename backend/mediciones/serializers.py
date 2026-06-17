from rest_framework import serializers
from .models import Medicion, ArtefactoDetectado, PrediccionGasto, SesionDemo


class MedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicion
        fields = '__all__'


class ArtefactoDetectadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtefactoDetectado
        fields = '__all__'


class PrediccionGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrediccionGasto
        fields = '__all__'


class SesionDemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionDemo
        fields = '__all__'