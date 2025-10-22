# usuarios/permissions.py

from rest_framework.permissions import BasePermission
from .models import Usuarios_Roles 
import logging
logger = logging.getLogger(__name__)
# No se importa User aquí, se usa request.user directamente

# El ID del Rol de Administrador se ASUME como 1 en la base de datos de Oracle
ADMIN_ROL_ID = 1

class IsAdminUser(BasePermission):
    """
    Permiso que comprueba si el usuario autenticado tiene el ROL_ID=1 (ADMIN) en la 
    tabla USUARIOS_ROLES de Oracle.
    """
    message = "Requiere el rol de Administrador (ROL_ID=1) para acceder."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            # Si no está autenticado, no tiene permisos
            logger.info("❌ PERMISOS: Usuario no autenticado (AnonymousUser).")
            return False
            
        try:
            user_pk = request.user.pk
            
            # Consulta a Oracle: Verificar existencia del par (Usuario_Id, Rol_Id=1)
            # El lookup es: CampoFK_en_Usuarios_Roles__Campo_en_Modelo_Usuario__Campo_en_User
            es_admin = Usuarios_Roles.objects.filter(
                # Usamos la FK implícita del OneToOneField a la tabla Usuarios
                Usuario_Id__Usuario_Id=user_pk,  
                # Usamos la FK al modelo Roles y el campo ROL_ID (asumido como 1)
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
            
        # 2. Verificar si es su propio objeto
        # 'obj' es una instancia del modelo 'User' (en el caso de UsuarioAdminViewSet/MeView)
        is_self = obj.pk == request.user.pk
        
        logger.info(f"✅ PERMISOS (IsSelfOrAdmin): Usuario PK={request.user.pk}. ¿Es DUEÑO? {is_self}")
        return is_self