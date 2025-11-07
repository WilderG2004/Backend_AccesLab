# usuarios/urls.py

from django.urls import path, include 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter 

from .views import (
    UsuarioAdminCreateView, 
    UsuarioAdminViewSet, 
    MeView, 
    UsuariosProgramasViewSet
)

# ============================================
# ROUTER PARA ENDPOINTS CON CRUD COMPLETO
# ============================================
router = DefaultRouter()

# ViewSet para gestión completa de usuarios (GET, POST, PUT, PATCH, DELETE)
# Rutas generadas:
# - GET    /api/auth/usuarios/           -> Listar todos los usuarios
# - POST   /api/auth/usuarios/           -> Crear un nuevo usuario
# - GET    /api/auth/usuarios/{id}/      -> Obtener un usuario específico
# - PUT    /api/auth/usuarios/{id}/      -> Actualizar completamente un usuario
# - PATCH  /api/auth/usuarios/{id}/      -> Actualizar parcialmente un usuario
# - DELETE /api/auth/usuarios/{id}/      -> Eliminar un usuario
router.register(r'usuarios', UsuarioAdminViewSet, basename='auth_usuarios')

# ViewSet para gestión de asociación Usuario-Programa
# Rutas generadas:
# - GET    /api/auth/usuarios-programas/           -> Listar asociaciones
# - POST   /api/auth/usuarios-programas/           -> Crear asociación
# - GET    /api/auth/usuarios-programas/{id}/      -> Obtener asociación específica
# - DELETE /api/auth/usuarios-programas/{id}/      -> Eliminar asociación
router.register(r'usuarios-programas', UsuariosProgramasViewSet, basename='usuarios_programas')


# ============================================
# RUTAS INDIVIDUALES (NO MANEJADAS POR ROUTER)
# ============================================
urlpatterns = [
    # --- AUTENTICACIÓN JWT ---
    
    # Obtener token de acceso y refresh
    # POST /api/auth/token/
    # Body: {"username": "...", "password": "..."}
    # Response: {"access": "...", "refresh": "..."}
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Renovar token de acceso usando el refresh token
    # POST /api/auth/token/refresh/
    # Body: {"refresh": "..."}
    # Response: {"access": "..."}
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    
    # --- REGISTRO DE USUARIOS ---
    
    # Crear nuevo usuario (Solo Admin)
    # POST /api/auth/register/
    # Body: {"username": "...", "password": "...", "nombres": "...", ...}
    path('register/', UsuarioAdminCreateView.as_view(), name='auth_register'),
    
    
    # --- PERFIL PERSONAL ---
    
    # Obtener y actualizar perfil del usuario autenticado
    # GET   /api/auth/me/  -> Obtener mi perfil
    # PATCH /api/auth/me/  -> Actualizar mi perfil
    path('me/', MeView.as_view(), name='auth_me'), 
    
    
    # --- RUTAS DEL ROUTER ---
    
    # Incluir todas las rutas generadas por el router
    path('', include(router.urls)),
]