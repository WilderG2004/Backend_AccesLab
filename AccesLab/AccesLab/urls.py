# AccesLab/urls.py (FINAL)

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importaciones para Autenticación (Simple JWT)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Importaciones de vistas de MAESTROS (Corregidas y Completas)
from maestros.views import (
    RolesViewSet, TipoIdentificacionViewSet, TipoSolicitantesViewSet, # ✅ Coincide con views.py
    FacultadesViewSet, ProgramasViewSet, CategoriasViewSet, ObjetosViewSet, 
    EstadosViewSet, TipoServicioViewSet, 
    FrecuenciaServicioViewSet, LaboratoriosViewSet, EntregasViewSet, DevolucionesViewSet,HorariosLaboratorioViewSet
)

# 1. Importaciones para DRF Spectacular (manteniendo la documentación)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# --- ROUTERS ---

# Router para la app 'maestros'
router_maestros = DefaultRouter()
router_maestros.register(r'roles', RolesViewSet)
router_maestros.register(r'tipos-identificacion', TipoIdentificacionViewSet)
router_maestros.register(r'tipos-solicitante', TipoSolicitantesViewSet) 
router_maestros.register(r'facultades', FacultadesViewSet) 
router_maestros.register(r'programas', ProgramasViewSet) 
router_maestros.register(r'categorias', CategoriasViewSet) 
router_maestros.register(r'objetos', ObjetosViewSet) 
router_maestros.register(r'estados', EstadosViewSet)

# ✅ Catálogos y Tablas de Soporte Adicionales
router_maestros.register(r'tipos-servicio', TipoServicioViewSet)
router_maestros.register(r'frecuencias-servicio', FrecuenciaServicioViewSet)
router_maestros.register(r'laboratorios', LaboratoriosViewSet)
router_maestros.register(r'horarios-laboratorio', HorariosLaboratorioViewSet)
router_maestros.register(r'entregas', EntregasViewSet)
router_maestros.register(r'devoluciones', DevolucionesViewSet)


urlpatterns = [
    # Rutas de Documentación
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Rutas Principales
    path('admin/', admin.site.urls),

    # 1. Rutas de AUTENTICACIÓN (app 'usuarios')
    path('api/auth/', include('usuarios.urls')), 
    
    # 2. Rutas de CATÁLOGOS/MAESTROS
    path('api/maestros/', include(router_maestros.urls)), 
    
    # 3. Rutas de LÓGICA DE NEGOCIO (RESERVAS) 
    path('api/reservas/', include('reservas.urls')), 
]