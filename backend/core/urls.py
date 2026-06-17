from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mediciones.views import (
    MedicionViewSet,
    ArtefactoDetectadoViewSet,
    PrediccionGastoViewSet,
    SesionDemoViewSet
)

router = DefaultRouter()
router.register(r'mediciones', MedicionViewSet)
router.register(r'artefactos', ArtefactoDetectadoViewSet)
router.register(r'predicciones', PrediccionGastoViewSet)
router.register(r'sesiones', SesionDemoViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]