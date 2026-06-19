from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mediciones.views import (
    MedicionViewSet,
    ArtefactoDetectadoViewSet,
    PrediccionGastoViewSet,
    SesionDemoViewSet
)
from nilm.views import NilmLatestView, CostPredictionView

router = DefaultRouter()
router.register(r'mediciones', MedicionViewSet)
router.register(r'artefactos', ArtefactoDetectadoViewSet)
router.register(r'predicciones', PrediccionGastoViewSet)
router.register(r'sesiones', SesionDemoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/nilm/latest/', NilmLatestView.as_view(), name='nilm-latest'),
    path('api/cost/prediction/', CostPredictionView.as_view(), name='cost-prediction'),
]