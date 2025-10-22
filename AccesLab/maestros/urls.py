# maestros/urls.py

from rest_framework.routers import DefaultRouter
from .views import (
    # Importaciones originales (ya estaban)
    TipoServicioViewSet, ObjetosViewSet, EntregasViewSet, DevolucionesViewSet,
    RolesViewSet, TipoIdentificacionViewSet, TipoSolicitantesViewSet,
    FacultadesViewSet, ProgramasViewSet, CategoriasViewSet, 
    EstadosViewSet, FrecuenciaServicioViewSet, LaboratoriosViewSet, HorariosLaboratorioViewSet
)

maestros_router = DefaultRouter()

# --- Rutas de Usuarios y Estructura Organizacional ---
maestros_router.register(r'roles', RolesViewSet, basename='roles')
maestros_router.register(r'tipos-identificacion', TipoIdentificacionViewSet, basename='tipos_identificacion')
maestros_router.register(r'tipos-solicitantes', TipoSolicitantesViewSet, basename='tipos_solicitantes')
maestros_router.register(r'facultades', FacultadesViewSet, basename='facultades') 
maestros_router.register(r'programas', ProgramasViewSet, basename='programas')   

# --- Rutas de Inventario ---
maestros_router.register(r'categorias', CategoriasViewSet, basename='categorias') 
maestros_router.register(r'objetos', ObjetosViewSet, basename='objetos') 

# --- Rutas de Servicio y Transacciones ---
maestros_router.register(r'tipos-servicio', TipoServicioViewSet, basename='tipos_servicio')
maestros_router.register(r'frecuencias-servicio', FrecuenciaServicioViewSet, basename='frecuencias_servicio') 
maestros_router.register(r'laboratorios', LaboratoriosViewSet, basename='laboratorios') 
maestros_router.register(r'horarios-laboratorio', HorariosLaboratorioViewSet, basename='horarios_laboratorio')  
maestros_router.register(r'estados', EstadosViewSet, basename='estados') 
maestros_router.register(r'entregas', EntregasViewSet, basename='entregas')
maestros_router.register(r'devoluciones', DevolucionesViewSet, basename='devoluciones')

urlpatterns = maestros_router.urls