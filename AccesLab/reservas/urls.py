# reservas/urls.py

from rest_framework.routers import DefaultRouter
from .views import SolicitudesViewSet, UsuarioSolicitudViewSet

# ============================================
# ROUTER PARA LÓGICA DE NEGOCIO
# ============================================
router = DefaultRouter()

# --- SOLICITUDES PRINCIPALES ---
# Gestión completa de solicitudes de préstamo y reserva
# Rutas generadas:
# - GET    /api/reservas/solicitudes/           -> Listar todas las solicitudes
# - POST   /api/reservas/solicitudes/           -> Crear nueva solicitud
# - GET    /api/reservas/solicitudes/{id}/      -> Obtener solicitud específica
# - PUT    /api/reservas/solicitudes/{id}/      -> Actualizar completamente
# - PATCH  /api/reservas/solicitudes/{id}/      -> Actualizar parcialmente (aprobar/rechazar)
# - DELETE /api/reservas/solicitudes/{id}/      -> Eliminar solicitud
router.register(r'solicitudes', SolicitudesViewSet, basename='solicitudes')

# --- PARTICIPANTES/INTEGRANTES ---
# Gestión de la relación N:M entre Usuarios y Solicitudes
# Rutas generadas:
# - GET    /api/reservas/participantes/          -> Listar participantes
# - POST   /api/reservas/participantes/          -> Añadir participante a solicitud
# - GET    /api/reservas/participantes/{id}/     -> Obtener participante específico
# - DELETE /api/reservas/participantes/{id}/     -> Remover participante de solicitud
router.register(r'participantes', UsuarioSolicitudViewSet, basename='participantes')

# Exportar las URLs del router
urlpatterns = router.urls