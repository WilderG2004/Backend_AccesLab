# AccesLab/urls.py

from django.contrib import admin
from django.urls import path, include

# Importaciones para Documentación (DRF Spectacular)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # ============================================
    # PANEL DE ADMINISTRACIÓN DE DJANGO
    # ============================================
    path('admin/', admin.site.urls),
    
    # ============================================
    # DOCUMENTACIÓN DE LA API
    # ============================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # ============================================
    # MÓDULOS DE LA APLICACIÓN
    # ============================================
    
    # 1. Autenticación y Gestión de Usuarios
    # Rutas: /api/auth/token/, /api/auth/register/, /api/auth/me/, etc.
    path('api/auth/', include('usuarios.urls')),
    
    # 2. Catálogos y Maestros (Tablas de Referencia)
    # Rutas: /api/maestros/roles/, /api/maestros/objetos/, etc.
    path('api/maestros/', include('maestros.urls')),
    
    # 3. Reservas y Solicitudes (Lógica de Negocio)
    # Rutas: /api/reservas/solicitudes/, /api/reservas/participantes/
    path('api/reservas/', include('reservas.urls')),

    # 4. Reportes y Análisis
    # Rutas: /api/reportes/kpis/, /api/reportes/actividad-mensual/, etc.
    path('api/reportes/', include('reportes.urls')),
]

# ============================================
# SERVIR ARCHIVOS MEDIA EN DESARROLLO
# ============================================
# ⚠️ IMPORTANTE: Solo funciona con DEBUG=True
# Para producción, usa Nginx o un servicio de almacenamiento (S3, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)