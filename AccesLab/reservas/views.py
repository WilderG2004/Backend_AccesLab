# ==============================================================================
# RESERVAS/VIEWS.PY - CON ELIMINACIÓN PARA USUARIOS (CORREGIDO)
# ==============================================================================

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    SolicitudesWriteSerializer, 
    SolicitudesReadSerializer,
    IntegranteSolicitudSerializer as UsuarioSolicitudSerializer 
)
from .models import Solicitudes, Integrante_Solicitud 
from usuarios.permissions import IsAdminUser 


class SolicitudesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar solicitudes.
    ✅ Usuarios pueden eliminar (DELETE) sus propias solicitudes.
    """
    lookup_field = 'Solicitud_Id' 

    queryset = Solicitudes.objects.all().select_related(
        'Usuario_Id', 'Tipo_Servicio_Id', 'Entrega_Id', 'Devolucion_Id',
        'Estado_Id', 'Laboratorio_Id', 'Horario_Id'
    ).prefetch_related(
        'solicitudes_objetos_set__Objetos_Id', 
        'usuarios_asociados' 
    ).order_by('-Fecha_solicitud', '-Solicitud_Id')

    def get_serializer_class(self):
        """
        Usa serializer de escritura para modificaciones, de lectura para consultas.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return SolicitudesWriteSerializer 
        return SolicitudesReadSerializer
    
    def get_permissions(self):
        """
        Permisos por acción:
        - list/retrieve/create: Requiere autenticación
        - destroy: Usuario puede eliminar sus propias solicitudes
        - update/partial_update: Requiere Admin
        """
        if self.action in ['list', 'retrieve', 'create']:
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
            # 🔥 PERMITIR que usuarios eliminen sus propias solicitudes
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            # update y partial_update requieren admin
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return super().get_permissions()

    def get_queryset(self):
        """
        Filtrado inteligente:
        - Admin: Ve todas las solicitudes (puede filtrar por Usuario_Id)
        - Usuario regular: Solo ve sus propias solicitudes
        """
        user = self.request.user
        base_queryset = super().get_queryset()
        
        if not user.is_authenticated:
            return Solicitudes.objects.none()

        # Identificar si es Admin
        perfil = getattr(user, 'perfil_oracle', None)
        is_admin = user.is_staff or (perfil and getattr(perfil, 'is_admin', False))
        
        # Admin: puede ver todas o filtrar por usuario
        if is_admin:
            usuario_param = self.request.query_params.get('Usuario_Id')
            if usuario_param:
                return base_queryset.filter(Usuario_Id__Usuario_Id=usuario_param)
            return base_queryset
        
        # Usuario regular: solo sus solicitudes
        try:
            if perfil:
                return base_queryset.filter(Usuario_Id__Usuario_Id=perfil.Usuario_Id)
            return Solicitudes.objects.none()
        except AttributeError:
            return Solicitudes.objects.none()

    # 🔥 MÉTODO PERSONALIZADO: DESTROY (ELIMINAR) - CORREGIDO
    def destroy(self, request, *args, **kwargs):
        """
        Eliminación de solicitudes.
        🔥 Usuarios normales solo pueden eliminar sus propias solicitudes.
        🔥 Admins pueden eliminar cualquier solicitud.
        """
        instance = self.get_object()
        
        print(f"🗑️ DELETE recibido para Solicitud {instance.Solicitud_Id}")
        
        # 🔥 VALIDACIÓN: Determinar si es admin
        perfil = getattr(request.user, 'perfil_oracle', None)
        is_admin = request.user.is_staff or (perfil and getattr(perfil, 'is_admin', False))
        
        print(f"🔐 ¿Es admin?: {is_admin}")
        
        if not is_admin:
            # 🔥 OBTENER EL ID DEL USUARIO DE ORACLE (NO DE DJANGO)
            if perfil is None:
                print("❌ Usuario no tiene perfil de Oracle")
                return Response(
                    {'error': 'Usuario sin perfil válido'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            usuario_oracle_id = perfil.Usuario_Id
            solicitud_usuario_id = instance.Usuario_Id.Usuario_Id
            
            print(f"👤 Usuario de Django (request.user.id): {request.user.id}")
            print(f"👤 Usuario de Oracle que hace petición: {usuario_oracle_id}")
            print(f"👤 Usuario dueño de la solicitud (Oracle): {solicitud_usuario_id}")
            print(f"👤 Nombre del usuario dueño: {instance.Usuario_Id.Nombres} {instance.Usuario_Id.Apellido1}")
            
            # 🔥 COMPARAR IDs DE ORACLE (NO DE DJANGO)
            if solicitud_usuario_id != usuario_oracle_id:
                print(f"❌ Usuario {usuario_oracle_id} intenta eliminar solicitud de usuario {solicitud_usuario_id}")
                return Response(
                    {'error': 'No tienes permiso para eliminar esta solicitud'},
                    status=status.HTTP_403_FORBIDDEN
                )
            print("✅ Usuario autorizado para eliminar su solicitud")
        else:
            print("✅ Admin autorizado para eliminar cualquier solicitud")
        
        # 🔥 ELIMINAR LA SOLICITUD
        self.perform_destroy(instance)
        print(f"✅ Solicitud {instance.Solicitud_Id} eliminada correctamente")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    # 🔥 MÉTODO: PARTIAL UPDATE (SOLO PARA ADMINS)
    def partial_update(self, request, *args, **kwargs):
        """
        Actualización parcial (PATCH) - Solo para admins.
        Los usuarios normales usan DELETE para cancelar.
        """
        instance = self.get_object()
        
        print(f"🔧 PATCH recibido para Solicitud {instance.Solicitud_Id}")
        print(f"📥 Datos recibidos: {request.data}")
        print(f"📊 Estado actual: {instance.Estado_Id}")
        
        # 🔥 ACTUALIZAR ESTADO EXPLÍCITAMENTE (si viene en la request)
        if 'Estado_Id' in request.data:
            from maestros.models import Estados
            
            nuevo_estado_id = request.data['Estado_Id']
            print(f"🔄 Cambiando estado de {instance.Estado_Id} a {nuevo_estado_id}")
            
            try:
                nuevo_estado = Estados.objects.get(Estado_Id=nuevo_estado_id)
                instance.Estado_Id = nuevo_estado
                instance.save()
                print(f"✅ Estado guardado correctamente: {instance.Estado_Id}")
            except Estados.DoesNotExist:
                print(f"❌ Estado {nuevo_estado_id} no existe")
                return Response(
                    {'error': f'Estado {nuevo_estado_id} no existe'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Continuar con el update normal para otros campos
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 🔥 VERIFICAR QUE EL ESTADO SE GUARDÓ
        instance.refresh_from_db()
        print(f"🔍 Estado después de guardar: {instance.Estado_Id}")
        
        # Usar el serializer de lectura para la respuesta
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        response_serializer = SolicitudesReadSerializer(instance, context=self.get_serializer_context())
        
        return Response(response_serializer.data)

    # 🔥 MÉTODO: UPDATE COMPLETO (SOLO ADMIN)
    def update(self, request, *args, **kwargs):
        """
        Actualización completa (PUT) - Solo para admins.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        print(f"🔧 UPDATE recibido para Solicitud {instance.Solicitud_Id}")
        print(f"📥 Datos recibidos: {request.data}")
        
        # 🔥 ACTUALIZAR ESTADO EXPLÍCITAMENTE (si viene en la request)
        if 'Estado_Id' in request.data:
            from maestros.models import Estados
            
            nuevo_estado_id = request.data['Estado_Id']
            print(f"🔄 Cambiando estado de {instance.Estado_Id} a {nuevo_estado_id}")
            
            try:
                nuevo_estado = Estados.objects.get(Estado_Id=nuevo_estado_id)
                instance.Estado_Id = nuevo_estado
                instance.save()
                print(f"✅ Estado guardado correctamente: {instance.Estado_Id}")
            except Estados.DoesNotExist:
                return Response(
                    {'error': f'Estado {nuevo_estado_id} no existe'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 🔥 VERIFICAR QUE EL ESTADO SE GUARDÓ
        instance.refresh_from_db()
        print(f"🔍 Estado después de guardar: {instance.Estado_Id}")
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        response_serializer = SolicitudesReadSerializer(instance, context=self.get_serializer_context())
        
        return Response(response_serializer.data)


class UsuarioSolicitudViewSet(viewsets.ModelViewSet):
    """
    ViewSet para asociar usuarios a solicitudes (Integrantes/Participantes).
    """
    queryset = Integrante_Solicitud.objects.all().select_related(
        'Usuario_Id', 
        'Solicitud_Id'
    )
    serializer_class = UsuarioSolicitudSerializer
    
    def get_permissions(self):
        """
        list/retrieve: Cualquier autenticado
        create/update/destroy: Solo Admin
        """
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return super().get_permissions()