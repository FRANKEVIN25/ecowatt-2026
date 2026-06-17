from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Medicion, ArtefactoDetectado, PrediccionGasto, SesionDemo
from .serializers import (
    MedicionSerializer,
    ArtefactoDetectadoSerializer,
    PrediccionGastoSerializer,
    SesionDemoSerializer
)


class MedicionViewSet(viewsets.ModelViewSet):
    queryset = Medicion.objects.all()
    serializer_class = MedicionSerializer

    @action(detail=False, methods=['get'])
    def ultima(self, request):
        ultima = Medicion.objects.first()
        if ultima:
            serializer = self.get_serializer(ultima)
            return Response(serializer.data)
        return Response({'mensaje': 'Sin mediciones'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def historial(self, request):
        limite = int(request.query_params.get('limite', 60))
        mediciones = Medicion.objects.all()[:limite]
        serializer = self.get_serializer(mediciones, many=True)
        return Response(serializer.data)


class ArtefactoDetectadoViewSet(viewsets.ModelViewSet):
    queryset = ArtefactoDetectado.objects.all()
    serializer_class = ArtefactoDetectadoSerializer

    @action(detail=False, methods=['get'])
    def ultimo(self, request):
        ultimo = ArtefactoDetectado.objects.first()
        if ultimo:
            serializer = self.get_serializer(ultimo)
            return Response(serializer.data)
        return Response({'mensaje': 'Sin detecciones'}, status=status.HTTP_404_NOT_FOUND)


class PrediccionGastoViewSet(viewsets.ModelViewSet):
    queryset = PrediccionGasto.objects.all()
    serializer_class = PrediccionGastoSerializer

    @action(detail=False, methods=['get'])
    def ultima(self, request):
        ultima = PrediccionGasto.objects.first()
        if ultima:
            serializer = self.get_serializer(ultima)
            return Response(serializer.data)
        return Response({'mensaje': 'Sin predicciones'}, status=status.HTTP_404_NOT_FOUND)


class SesionDemoViewSet(viewsets.ModelViewSet):
    queryset = SesionDemo.objects.all()
    serializer_class = SesionDemoSerializer

    @action(detail=False, methods=['post'])
    def iniciar(self, request):
        sesion = SesionDemo.objects.create()
        serializer = self.get_serializer(sesion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        sesion = self.get_object()
        sesion.fin = timezone.now()
        sesion.save()
        serializer = self.get_serializer(sesion)
        return Response(serializer.data)