# ==============================================================================
# MAESTROS/VIEWS.PY - Optimizado y Simplificado
# ==============================================================================

from rest_framework import viewsets, permissions
from usuarios.permissions import IsAdminUser 

from .models import (
    Roles, Frecuencia_Servicio, Entregas, Devoluciones, 
    Tipo_Servicio, Laboratorios, Tipo_Identificacion, 
    Tipo_Solicitantes, Facultades, Programas, 
    Categorias, Objetos, Estados, Horarios_Laboratorio
)
from .serializers import (
    RolesSerializer, FrecuenciaServicioSerializer, EntregasSerializer, DevolucionesSerializer,
    TipoServicioSerializer, LaboratoriosSerializer, TipoIdentificacionSerializer, 
    TipoSolicitanteSerializer, FacultadSerializer, ProgramaSerializer, 
    CategoriaSerializer, ObjetoSerializer, EstadoSerializer, HorariosLaboratorioSerializer
)


# Permiso base para todos los ViewSets de Maestros
ADMIN_PERMISSION = [permissions.IsAuthenticated, IsAdminUser]


# Clase base para reducir código repetitivo
class BaseAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet base con permisos de Admin.
    ✅ Compatible con serializers flexibles (auto-generación de IDs).
    """
    permission_classes = ADMIN_PERMISSION


# ----------------------------------------------------------------------
# CATÁLOGOS SIMPLES
# ----------------------------------------------------------------------

class RolesViewSet(BaseAdminViewSet):
    queryset = Roles.objects.all().order_by('Nombre_Roles')
    serializer_class = RolesSerializer


class TipoIdentificacionViewSet(BaseAdminViewSet):
    queryset = Tipo_Identificacion.objects.all().order_by('Nombre_Tipo_Identificacion')
    serializer_class = TipoIdentificacionSerializer


class TipoSolicitantesViewSet(BaseAdminViewSet):
    queryset = Tipo_Solicitantes.objects.all().order_by('Nombre_Solicitante')
    serializer_class = TipoSolicitanteSerializer


class FacultadesViewSet(BaseAdminViewSet):
    queryset = Facultades.objects.all().order_by('Nombre_Facultad')
    serializer_class = FacultadSerializer


class CategoriasViewSet(BaseAdminViewSet):
    queryset = Categorias.objects.all().order_by('Nombre_Categoria')
    serializer_class = CategoriaSerializer


class TipoServicioViewSet(BaseAdminViewSet):
    queryset = Tipo_Servicio.objects.all().order_by('Nombre_Tipo_Servicio')
    serializer_class = TipoServicioSerializer


class FrecuenciaServicioViewSet(BaseAdminViewSet):
    queryset = Frecuencia_Servicio.objects.all().order_by('Nombre_Frecuencia_Servicio')
    serializer_class = FrecuenciaServicioSerializer


class LaboratoriosViewSet(BaseAdminViewSet):
    queryset = Laboratorios.objects.all().order_by('Nombre_Laboratorio')
    serializer_class = LaboratoriosSerializer


class EstadosViewSet(BaseAdminViewSet):
    queryset = Estados.objects.all().order_by('Estado_Id')
    serializer_class = EstadoSerializer


# ----------------------------------------------------------------------
# CATÁLOGOS CON RELACIONES FK
# ----------------------------------------------------------------------

class ProgramasViewSet(BaseAdminViewSet):
    """
    ✅ Compatible con creación flexible:
    - Puede crear programa con facultad_id existente
    - Puede crear programa + facultad nueva con facultad_nombre
    """
    queryset = Programas.objects.all().select_related('Facultad_Id').order_by('Nombre_Programa')
    serializer_class = ProgramaSerializer


class ObjetosViewSet(BaseAdminViewSet):
    """
    ✅ Compatible con creación flexible:
    - Puede crear objeto con categoria_id existente
    - Puede crear objeto + categoría nueva con categoria_nombre
    """
    queryset = Objetos.objects.all().select_related('Categoria_Id').order_by('Nombre_Objetos')
    serializer_class = ObjetoSerializer


class HorariosLaboratorioViewSet(BaseAdminViewSet):
    """
    ✅ Compatible con creación flexible:
    - Puede crear horario con laboratorio_id existente
    - Puede crear horario + laboratorio nuevo con laboratorio_nombre
    """
    queryset = Horarios_Laboratorio.objects.all().select_related('Laboratorio_Id').order_by('Horario_Id')
    serializer_class = HorariosLaboratorioSerializer


# ----------------------------------------------------------------------
# TABLAS TRANSACCIONALES
# ----------------------------------------------------------------------

class EntregasViewSet(BaseAdminViewSet):
    """
    ✅ Compatible con creación flexible:
    - Puede crear entrega con frecuencia_id existente
    - Puede crear entrega + frecuencia nueva con frecuencia_nombre
    """
    queryset = Entregas.objects.all().select_related('Frecuencia_Servicio_Id').order_by('-Entrega_Id')
    serializer_class = EntregasSerializer


class DevolucionesViewSet(BaseAdminViewSet):
    queryset = Devoluciones.objects.all().order_by('-Devolucion_Id')
    serializer_class = DevolucionesSerializer