# reservas/urls.py

from rest_framework.routers import DefaultRouter
from .views import SolicitudesViewSet, UsuarioSolicitudViewSet # <-- Se importa el nuevo ViewSet

reservas_router = DefaultRouter()

# 1. Endpoint para crear, listar y administrar solicitudes principales: /reservas/solicitudes/
reservas_router.register(r'solicitudes', SolicitudesViewSet, basename='solicitudes')

# 2. Endpoint para añadir/remover participantes de una solicitud: /reservas/participantes/
reservas_router.register(r'participantes', UsuarioSolicitudViewSet, basename='participantes')

urlpatterns = reservas_router.urls