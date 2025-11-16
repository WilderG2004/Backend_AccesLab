# usuarios/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework import permissions
from .models import Usuarios_Roles 
import logging
logger = logging.getLogger(__name__)
# No se importa User aquí, se usa request.user directamente

# El ID del Rol de Administrador se ASUME como 1 en la base de datos de Oracle
ADMIN_ROL_ID = 1

class IsAdminUser(permissions.BasePermission):
    """
    Permite GET/HEAD/OPTIONS a cualquier usuario autenticado.
    Para métodos que modifican (POST/PUT/PATCH/DELETE) requiere que el usuario tenga rol admin
    (existencia de registro en Usuarios_Roles con Rol_Id=ADMIN_ROL_ID).
    """
    message = "Requiere el rol de Administrador (ROL_ID=1) para acceder."
    
    def has_permission(self, request, view):
        # Permitir métodos seguros a cualquier usuario autenticado
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        if not request.user or not request.user.is_authenticated:
            logger.info("❌ PERMISOS: Usuario no autenticado (AnonymousUser).")
            return False

        user_pk = getattr(request.user, 'pk', None)
        try:
            # Consulta a Oracle: Verificar existencia del par (Usuario_Id, Rol_Id=ADMIN_ROL_ID)
            es_admin = Usuarios_Roles.objects.filter(
                Usuario_Id__Usuario_Id=user_pk,
                Rol_Id__Rol_Id=ADMIN_ROL_ID
            ).exists()
            
            logger.info(f"✅ ROL CHECK (IsAdminUser): Usuario PK={user_pk}. ¿Es ADMIN? {es_admin}")
            return es_admin
            
        except Exception as e:
            logger.error(f"❌ FALLO CRÍTICO EN VERIFICACIÓN DE PERMISOS para PK={user_pk}: {e}")
            return False

class IsSelfOrAdmin(BasePermission):
    """
    Permite acceso total al ADMIN, o solo al propio usuario para ver/editar su perfil.
    """
    message = "No tiene permiso para realizar esta acción."
    
    def has_object_permission(self, request, view, obj):
        
        # 1. Verificar si es ADMIN (utiliza la lógica de IsAdminUser)
        if IsAdminUser().has_permission(request, view):
            return True
            
        # 2. Verificar si es su propio objeto (obj es instancia de User)
        is_self = obj.pk == request.user.pk
        
        logger.info(f"✅ PERMISOS (IsSelfOrAdmin): Usuario PK={request.user.pk}. ¿Es DUEÑO? {is_self}")
        return is_self