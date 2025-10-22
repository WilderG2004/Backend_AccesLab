# usuarios/views.py (Refactorizado)

from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db import transaction 
import logging

# Importaciones locales
from .serializers import UsuarioAdminSerializer, UsuariosProgramasSerializer # 🟢 ADD UsuariosProgramasSerializer
from .permissions import IsAdminUser, IsSelfOrAdmin 
from .models import Usuarios, Usuarios_Roles, Usuarios_Programas # 🟢 ADD Usuarios_Programas

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 1. VISTA PARA EL REGISTRO (POST /api/auth/register/) - Solo para Admins
# ----------------------------------------------------------------------
class UsuarioAdminCreateView(generics.CreateAPIView):
    """
    Permite a un usuario autenticado y con rol de 'ADMIN' crear nuevos usuarios.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser] 
    serializer_class = UsuarioAdminSerializer
    
    def perform_create(self, serializer):
        serializer.save()


# ----------------------------------------------------------------------
# 2. VISTA PARA LA GESTIÓN CRUD (ModelViewSet) - Acceso a Admin y Self
# ----------------------------------------------------------------------
class UsuarioAdminViewSet(viewsets.ModelViewSet):
    """
    Permite a un administrador gestionar usuarios y permite a los usuarios
    ver/editar su propio perfil (además de la vista /me).
    """
    
    # ... (QUERYSET sin cambios) ...
    queryset = User.objects.all().select_related(
        'perfil_oracle', 
        'perfil_oracle__Tipo_Id',
        'perfil_oracle__Solicitante_Id'
    ).prefetch_related(
        'perfil_oracle__roles_usuario_detalle', 
        'perfil_oracle__roles_usuario_detalle__Rol_Id'
    ).order_by('id') 
    
    serializer_class = UsuarioAdminSerializer
    
    # 🟢 CAMBIO: Usamos una mezcla de permisos en get_permissions
    
    def get_permissions(self):
        """
        Define los permisos basados en la acción:
        - list: Solo Admin puede ver la lista completa.
        - create: Solo Admin puede crear nuevos usuarios.
        - retrieve/update/partial_update: Solo Admin O el propio usuario (IsSelfOrAdmin).
        - destroy: Solo Admin puede eliminar.
        """
        if self.action == 'list' or self.action == 'create' or self.action == 'destroy':
            # Acciones masivas o destructivas: Solo Admin
            self.permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # Acciones sobre un objeto: Admin o el dueño (IsSelfOrAdmin)
            self.permission_classes = [IsAuthenticated, IsSelfOrAdmin]
        else:
            # Default
            self.permission_classes = [IsAuthenticated]
            
        return super().get_permissions()
    
    
    @transaction.atomic 
    def perform_destroy(self, instance):
        # ... (PERFORM_DESTROY sin cambios) ...
        try:
            perfil_oracle = instance.perfil_oracle
            
            # ELIMINAR RELACIONES DEPENDIENTES (USUARIOS_ROLES y USUARIOS_PROGRAMAS)
            Usuarios_Roles.objects.filter(Usuario_Id=perfil_oracle).delete()
            # 🟢 ADD: Eliminar también los programas asociados
            Usuarios_Programas.objects.filter(Usuario_Id=perfil_oracle).delete() 
            
            logger.info(f"Roles y Programas de Oracle eliminados para el usuario {instance.username} (ID: {instance.id}).")
            
            perfil_oracle.delete()
            logger.info(f"Perfil de Oracle eliminado para el usuario {instance.username} (ID: {instance.id}).")
            
        except AttributeError:
            logger.warning(f"Advertencia: No se encontró el perfil de Oracle para el usuario {instance.username} (ID: {instance.id}).")
        except Exception as e:
            logger.error(f"ERROR CRÍTICO AL ELIMINAR ORACLE: {e}. Se intentará un ROLLBACK.")
            raise e
            
        if User.objects.filter(pk=instance.pk).exists():
             instance.delete()
             logger.info(f"Usuario de Django (auth_user) eliminado para {instance.username} (ID: {instance.id}).")


# ----------------------------------------------------------------------
# 3. VISTA PARA PERFIL PERSONAL (/api/auth/me) 
# ----------------------------------------------------------------------
class MeView(APIView):
    # ... (Contenido sin cambios) ...
    permission_classes = [IsAuthenticated] 

    def get(self, request):
        serializer = UsuarioAdminSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        
        # El usuario no debería poder cambiar su rol ni el campo is_admin
        mutable_data = request.data.copy()
        mutable_data.pop('rol_id', None)
        mutable_data.pop('is_admin', None)
        
        serializer = UsuarioAdminSerializer(
            user, 
            data=mutable_data, 
            partial=True 
        )
        
        if serializer.is_valid(raise_exception=True): 
            serializer.save() 
            return Response(serializer.data)

# ----------------------------------------------------------------------
# 🟢 NUEVO VIEWSET: Gestión de Usuarios_Programas
# ----------------------------------------------------------------------

class UsuariosProgramasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la asignación de programas académicos a usuarios.
    Permite crear, listar y eliminar las relaciones Usuarios_Programas.
    Solo accesible por usuarios con rol de Admin.
    """
    queryset = Usuarios_Programas.objects.all().select_related('Usuario_Id', 'Programa_Id')
    serializer_class = UsuariosProgramasSerializer
    permission_classes = [IsAuthenticated, IsAdminUser] # Solo Admin

    def get_queryset(self):
        queryset = super().get_queryset()
        # Permite filtrar por usuario_id en la URL: /api/auth/usuarios-programas/?usuario_id=X
        user_id = self.request.query_params.get('usuario_id', None)
        if user_id is not None:
            return queryset.filter(Usuario_Id__Usuario_Id=user_id)
        return queryset