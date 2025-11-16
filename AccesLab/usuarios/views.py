# usuarios/views.py (Optimizado con serializers flexibles)

from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db import transaction 
import logging

# Importaciones locales
from .serializers import UsuarioAdminSerializer, UsuariosProgramasSerializer
from .permissions import IsAdminUser, IsSelfOrAdmin 
from .models import Usuarios, Usuarios_Roles, Usuarios_Programas

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 1. VISTA PARA EL REGISTRO - Solo para Admins
# ----------------------------------------------------------------------
class UsuarioAdminCreateView(generics.CreateAPIView):
    """
    Permite a un usuario autenticado y con rol de 'ADMIN' crear nuevos usuarios.
    ✅ El serializer maneja automáticamente la creación flexible (IDs o nombres).
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser] 
    serializer_class = UsuarioAdminSerializer
    
    def perform_create(self, serializer):
        serializer.save()


# ----------------------------------------------------------------------
# 2. VISTA PARA LA GESTIÓN CRUD (ModelViewSet)
# ----------------------------------------------------------------------
class UsuarioAdminViewSet(viewsets.ModelViewSet):
    """
    Permite a un administrador gestionar usuarios y permite a los usuarios
    ver/editar su propio perfil.
    ✅ Sin cambios - el serializer flexible maneja toda la lógica.
    """
    
    queryset = User.objects.all().select_related(
        'perfil_oracle', 
        'perfil_oracle__Tipo_Id',
        'perfil_oracle__Solicitante_Id'
    ).prefetch_related(
        'perfil_oracle__roles_usuario_detalle', 
        'perfil_oracle__roles_usuario_detalle__Rol_Id'
    ).order_by('id') 
    
    serializer_class = UsuarioAdminSerializer
    
    def get_permissions(self):
        """
        Define los permisos basados en la acción:
        - list/create/destroy: Solo Admin
        - retrieve/update/partial_update: Admin o el propio usuario
        """
        if self.action in ['list', 'create', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, IsSelfOrAdmin]
        else:
            self.permission_classes = [IsAuthenticated]
            
        return super().get_permissions()
    
    @transaction.atomic 
    def perform_destroy(self, instance):
        """
        Elimina usuario con cascada en Oracle (roles y programas).
        ✅ Sin cambios necesarios.
        """
        try:
            perfil_oracle = instance.perfil_oracle
            
            # Eliminar relaciones dependientes
            Usuarios_Roles.objects.filter(Usuario_Id=perfil_oracle).delete()
            Usuarios_Programas.objects.filter(Usuario_Id=perfil_oracle).delete() 
            
            logger.info(f"Roles y Programas eliminados para {instance.username}")
            
            perfil_oracle.delete()
            logger.info(f"Perfil Oracle eliminado para {instance.username}")
            
        except AttributeError:
            logger.warning(f"Sin perfil Oracle para {instance.username}")
        except Exception as e:
            logger.error(f"Error eliminando Oracle: {e}")
            raise e
            
        if User.objects.filter(pk=instance.pk).exists():
            instance.delete()
            logger.info(f"Usuario Django eliminado: {instance.username}")


# ----------------------------------------------------------------------
# 3. VISTA /ME - Perfil del Usuario Autenticado (OPTIMIZADA)
# ----------------------------------------------------------------------
class MeView(APIView):
    """
    Vista para que el usuario autenticado vea y edite su propio perfil.
    ✅ OPTIMIZADA: Eliminada lógica duplicada, el serializer maneja todo.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/auth/me/
        Retorna los datos del usuario autenticado.
        ✅ El serializer ya incluye: rol_id, rol_nombre, is_admin
        """
        user = request.user
        serializer = UsuarioAdminSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        """
        PATCH /api/auth/me/
        Permite al usuario editar su propio perfil (excepto rol/admin).
        ⚠️ CAMBIOS: Nombres de campos actualizados para el serializer flexible.
        """
        user = request.user
        
        # Prevenir que el usuario cambie su propio rol o privilegios de admin
        mutable_data = request.data.copy()
        mutable_data.pop('rol_id_input', None)      # ⚠️ Actualizado
        mutable_data.pop('rol_nombre_input', None)  # ⚠️ Nuevo campo
        mutable_data.pop('is_admin_input', None)    # ⚠️ Actualizado
        
        serializer = UsuarioAdminSerializer(
            user, 
            data=mutable_data, 
            partial=True 
        )
        
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)


# ----------------------------------------------------------------------
# 4. VIEWSET: Gestión de Usuarios_Programas
# ----------------------------------------------------------------------
class UsuariosProgramasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la asignación de programas académicos a usuarios.
    ✅ Sin cambios - el serializer flexible maneja la creación.
    
    Endpoints:
    - POST /api/auth/usuarios-programas/
      Body: {"usuario_id": 1, "programa_id": 5}  # Usar programa existente
      Body: {"usuario_id": 1, "programa_nombre": "Ing. Software", "facultad_nombre": "Ingeniería"}  # Crear nuevo
    
    - GET /api/auth/usuarios-programas/?usuario_id=1  # Filtrar por usuario
    - DELETE /api/auth/usuarios-programas/{id}/
    """
    queryset = Usuarios_Programas.objects.all().select_related(
        'Usuario_Id', 
        'Programa_Id',
        'Programa_Id__Facultad_Id'
    )
    serializer_class = UsuariosProgramasSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """
        Permite filtrar por usuario_id en la URL.
        Ejemplo: /api/auth/usuarios-programas/?usuario_id=5
        """
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('usuario_id', None)
        if user_id is not None:
            return queryset.filter(Usuario_Id__Usuario_Id=user_id)
        return queryset