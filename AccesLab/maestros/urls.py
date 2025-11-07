# maestros/urls.py

from rest_framework.routers import DefaultRouter
from .views import (
    # Catálogos de Usuarios
    RolesViewSet,
    TipoIdentificacionViewSet,
    TipoSolicitantesViewSet,
    
    # Catálogos Académicos
    FacultadesViewSet,
    ProgramasViewSet,
    
    # Catálogos de Inventario
    CategoriasViewSet,
    ObjetosViewSet,
    
    # Catálogos de Servicios
    TipoServicioViewSet,
    FrecuenciaServicioViewSet,
    EstadosViewSet,
    
    # Catálogos de Infraestructura
    LaboratoriosViewSet,
    HorariosLaboratorioViewSet,
    
    # Tablas Transaccionales
    EntregasViewSet,
    DevolucionesViewSet,
)

# ============================================
# ROUTER PARA TODOS LOS CATÁLOGOS
# ============================================
router = DefaultRouter()

# --- CATÁLOGOS DE USUARIOS Y ORGANIZACIÓN ---
# Rutas: /api/maestros/roles/, /api/maestros/tipos-identificacion/, etc.
router.register(r'roles', RolesViewSet, basename='roles')
router.register(r'tipos-identificacion', TipoIdentificacionViewSet, basename='tipos_identificacion')
router.register(r'tipos-solicitantes', TipoSolicitantesViewSet, basename='tipos_solicitantes')

# --- CATÁLOGOS ACADÉMICOS ---
# Rutas: /api/maestros/facultades/, /api/maestros/programas/
router.register(r'facultades', FacultadesViewSet, basename='facultades')
router.register(r'programas', ProgramasViewSet, basename='programas')

# --- CATÁLOGOS DE INVENTARIO ---
# Rutas: /api/maestros/categorias/, /api/maestros/objetos/
router.register(r'categorias', CategoriasViewSet, basename='categorias')
router.register(r'objetos', ObjetosViewSet, basename='objetos')

# --- CATÁLOGOS DE SERVICIOS ---
# Rutas: /api/maestros/tipos-servicio/, /api/maestros/frecuencias-servicio/, etc.
router.register(r'tipos-servicio', TipoServicioViewSet, basename='tipos_servicio')
router.register(r'frecuencias-servicio', FrecuenciaServicioViewSet, basename='frecuencias_servicio')
router.register(r'estados', EstadosViewSet, basename='estados')

# --- CATÁLOGOS DE INFRAESTRUCTURA ---
# Rutas: /api/maestros/laboratorios/, /api/maestros/horarios-laboratorio/
router.register(r'laboratorios', LaboratoriosViewSet, basename='laboratorios')
router.register(r'horarios-laboratorio', HorariosLaboratorioViewSet, basename='horarios_laboratorio')

# --- TABLAS TRANSACCIONALES ---
# Rutas: /api/maestros/entregas/, /api/maestros/devoluciones/
router.register(r'entregas', EntregasViewSet, basename='entregas')
router.register(r'devoluciones', DevolucionesViewSet, basename='devoluciones')

# Exportar las URLs del router
urlpatterns = router.urls