# maestros/views.py

from rest_framework import viewsets, permissions
# Asume que tienes la clase IsAdminUser en la aplicación usuarios/permissions.py
from usuarios.permissions import IsAdminUser 

from .models import (
    Roles, Frecuencia_Servicio, Entregas, Devoluciones, 
    Tipo_Servicio, Laboratorios, Tipo_Identificacion, 
    Tipo_Solicitantes, Facultades, Programas, 
    Categorias, Objetos, Estados, Horarios_Laboratorio # CORREGIDO: Usar Horarios_Laboratorio
)
from .serializers import (
    RolesSerializer, FrecuenciaServicioSerializer, EntregasSerializer, DevolucionesSerializer,
    TipoServicioSerializer, LaboratoriosSerializer, TipoIdentificacionSerializer, 
    TipoSolicitanteSerializer, FacultadSerializer, ProgramaSerializer, 
    CategoriaSerializer, ObjetoSerializer, EstadoSerializer, HorariosLaboratorioSerializer
)

# Permiso base: Solo usuarios autenticados Y que sean administradores
ADMIN_PERMISSION = [permissions.IsAuthenticated, IsAdminUser]

# ----------------------------------------------------------------------
# VISTAS DE CATÁLOGOS BASE (Maestros)
# ----------------------------------------------------------------------

class RolesViewSet(viewsets.ModelViewSet):
    queryset = Roles.objects.all().order_by('Nombre_Roles')
    serializer_class = RolesSerializer
    permission_classes = ADMIN_PERMISSION

class TipoIdentificacionViewSet(viewsets.ModelViewSet):
    queryset = Tipo_Identificacion.objects.all().order_by('Nombre_Tipo_Identificacion')
    serializer_class = TipoIdentificacionSerializer
    permission_classes = ADMIN_PERMISSION

class TipoSolicitantesViewSet(viewsets.ModelViewSet):
    queryset = Tipo_Solicitantes.objects.all().order_by('Nombre_Solicitante')
    serializer_class = TipoSolicitanteSerializer
    permission_classes = ADMIN_PERMISSION
    
class FacultadesViewSet(viewsets.ModelViewSet):
    queryset = Facultades.objects.all().order_by('Nombre_Facultad')
    serializer_class = FacultadSerializer
    permission_classes = ADMIN_PERMISSION

class CategoriasViewSet(viewsets.ModelViewSet):
    queryset = Categorias.objects.all().order_by('Nombre_Categoria')
    serializer_class = CategoriaSerializer
    permission_classes = ADMIN_PERMISSION

class TipoServicioViewSet(viewsets.ModelViewSet):
    queryset = Tipo_Servicio.objects.all().order_by('Nombre_Tipo_Servicio')
    serializer_class = TipoServicioSerializer
    permission_classes = ADMIN_PERMISSION

class FrecuenciaServicioViewSet(viewsets.ModelViewSet):
    queryset = Frecuencia_Servicio.objects.all().order_by('Nombre_Frecuencia_Servicio')
    serializer_class = FrecuenciaServicioSerializer
    permission_classes = ADMIN_PERMISSION

class LaboratoriosViewSet(viewsets.ModelViewSet):
    queryset = Laboratorios.objects.all().order_by('Nombre_Laboratorio')
    serializer_class = LaboratoriosSerializer
    permission_classes = ADMIN_PERMISSION

class HorariosLaboratorioViewSet(viewsets.ModelViewSet):
    # OPTIMIZACIÓN: Añadir select_related para obtener el nombre del laboratorio
    queryset = Horarios_Laboratorio.objects.all().select_related('Laboratorio_Id').order_by('Horario_Id')
    serializer_class = HorariosLaboratorioSerializer
    permission_classes = ADMIN_PERMISSION
    
class EstadosViewSet(viewsets.ModelViewSet):
    queryset = Estados.objects.all().order_by('Estado_Id')
    serializer_class = EstadoSerializer
    permission_classes = ADMIN_PERMISSION

# ----------------------------------------------------------------------
# VISTAS CON CLAVES FORÁNEAS
# ----------------------------------------------------------------------

class ProgramasViewSet(viewsets.ModelViewSet):
    queryset = Programas.objects.all().select_related('Facultad_Id').order_by('Nombre_Programa')
    serializer_class = ProgramaSerializer
    permission_classes = ADMIN_PERMISSION

class ObjetosViewSet(viewsets.ModelViewSet):
    queryset = Objetos.objects.all().select_related('Categoria_Id').order_by('Nombre_Objetos')
    serializer_class = ObjetoSerializer
    permission_classes = ADMIN_PERMISSION

# ----------------------------------------------------------------------
# VISTAS DE TABLAS TRANSACCIONALES
# ----------------------------------------------------------------------

class EntregasViewSet(viewsets.ModelViewSet):
    queryset = Entregas.objects.all().select_related('Frecuencia_Servicio_Id').order_by('Entrega_Id')
    serializer_class = EntregasSerializer
    permission_classes = ADMIN_PERMISSION

class DevolucionesViewSet(viewsets.ModelViewSet):
    queryset = Devoluciones.objects.all().order_by('Devolucion_Id')
    serializer_class = DevolucionesSerializer
    permission_classes = ADMIN_PERMISSION