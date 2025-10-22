from rest_framework import viewsets, permissions
from .serializers import (
    SolicitudesWriteSerializer, 
    SolicitudesReadSerializer,
    # Renombramos IntegranteSolicitudSerializer para que coincida con el uso en el ViewSet
    IntegranteSolicitudSerializer as UsuarioSolicitudSerializer 
)
# 🛑 CORRECTO: Usamos Integrante_Solicitud
from .models import Solicitudes, Integrante_Solicitud 
from usuarios.permissions import IsAdminUser 
from rest_framework.decorators import action
from rest_framework.response import Response

# ----------------------------------------------------------------------
# VISTAS DE SOLICITUDES (Principal)
# ----------------------------------------------------------------------

class SolicitudesViewSet(viewsets.ModelViewSet):
    lookup_field = 'Solicitud_Id' 

    # Optimización del queryset principal
    queryset = Solicitudes.objects.all().select_related(
        'Usuario_Id', 'Tipo_Servicio_Id', 'Entrega_Id', 'Devolucion_Id',
        # === NUEVAS RELACIONES ===
        'Estado_Id', 'Laboratorio_Id', 'Horario_Id'
        # =========================
    ).prefetch_related(
        'solicitudes_objetos_set__Objetos_Id', 
        # 'usuarios_asociados' es la related_name para Integrante_Solicitud (definido en models.py)
        'usuarios_asociados' 
    ).order_by('-Fecha_solicitud', '-Solicitud_Id')

    def get_serializer_class(self):
        """Usa el serializer de escritura para POST/PUT/PATCH/DELETE y el de lectura para GET."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return SolicitudesWriteSerializer 
        return SolicitudesReadSerializer
    
    def get_permissions(self):
        """Define permisos: Todas las acciones requieren autenticación. Modificación/Borrado requieren Admin."""
        # LIST, RETRIEVE, CREATE requieren solo autenticación
        if self.action in ['list', 'retrieve', 'create']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            # UPDATE, PARTIAL_UPDATE (PATCH), DESTROY requieren Admin
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return super().get_permissions()

    # 🛑 IMPLEMENTACIÓN DEL FILTRADO POR USUARIO 🛑
    def get_queryset(self):
        """
        Retorna todas las solicitudes si es Admin, o solo las propias si es un usuario regular.
        Filtra usando el ID de Oracle del usuario logueado.
        """
        user = self.request.user
        base_queryset = super().get_queryset()
        
        if not user.is_authenticated:
            return Solicitudes.objects.none()

        # Identificar al usuario como Administrador
        is_admin = user.is_staff or (hasattr(user, 'rol_nombre') and user.rol_nombre == 'ADMIN')
        
        # Si es Admin, devuelve todas las solicitudes
        if is_admin:
            return base_queryset
        
        # Si NO es Admin, filtra por el usuario creador
        try:
            # Filtra por el campo Usuario_Id (FK a Usuarios) usando el ID de Oracle del usuario logueado
            return base_queryset.filter(Usuario_Id__Usuario_Id=user.id)
            
        except AttributeError:
            # Fallback en caso de que el objeto user no tenga el ID de Oracle mapeado
            return Solicitudes.objects.none()


# ----------------------------------------------------------------------
# VISTAS DE RELACIÓN N:M (Añadir Participantes)
# ----------------------------------------------------------------------

class UsuarioSolicitudViewSet(viewsets.ModelViewSet):
    """Permite asociar un usuario a una solicitud (Añadir un Integrante/Participante)."""
    
    # 🛑 CORRECTO: Usamos el modelo Integrante_Solicitud para la relación N:M
    queryset = Integrante_Solicitud.objects.all().select_related('Usuario_Id', 'Solicitud_Id')
    
    # Usamos el serializer de escritura/validación para la relación
    serializer_class = UsuarioSolicitudSerializer
    
    # Permisos: Solo usuarios autenticados y Administradores pueden gestionar participantes
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]