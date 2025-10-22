from django.urls import path, include 
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter 

from .views import UsuarioAdminCreateView, UsuarioAdminViewSet, MeView, UsuariosProgramasViewSet # 🟢 ADD UsuariosProgramasViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioAdminViewSet, basename='auth_usuarios')
# 🟢 NUEVA RUTA
router.register(r'usuarios-programas', UsuariosProgramasViewSet, basename='usuarios-programas')


urlpatterns = [
    # 1. Login JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 2. Refresh JWT
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 3. Register (Creación de nuevos usuarios por un ADMIN)
    path('register/', UsuarioAdminCreateView.as_view(), name='auth_register'),
    
    # 4. PERFIL PERSONAL (GET/PATCH /me)
    path('me/', MeView.as_view(), name='auth_me'), 
    
    # 5. Gestión de Usuarios y Usuarios_Programas (CRUD)
    path('', include(router.urls)),
]