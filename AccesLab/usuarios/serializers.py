from django.contrib.auth.models import User
from rest_framework import serializers
import logging 
from django.db import transaction
from django.db.models import F 

# Importaciones de Modelos
from .models import Usuarios, Usuarios_Roles, Usuarios_Programas
from maestros.models import Roles, Tipo_Identificacion, Tipo_Solicitantes, Objetos, Programas

logger = logging.getLogger(__name__)

class UsuarioAdminSerializer(serializers.ModelSerializer):
    """
    Serializador para la gestión completa (CRUD) de usuarios. 
    Sincroniza User (Django) con Usuarios y Usuarios_Roles (Oracle).
    ⭐ INCLUYE CAMPO CAMPUS ⭐
    """
    
    # --- CAMPOS DE ESCRITURA DE RELACIONES Y CONTROL ---
    password = serializers.CharField(write_only=True, required=False, allow_blank=True) 
    is_admin = serializers.BooleanField(write_only=True, required=False, default=False) 
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Roles.objects.all(), 
        write_only=True, 
        required=True,
        source='rol_del_usuario'
    ) 
    
    # --- CAMPOS MAPEADOS (Lectura/Escritura) ---
    tipo_id = serializers.PrimaryKeyRelatedField(
        source='perfil_oracle.Tipo_Id', 
        queryset=Tipo_Identificacion.objects.all(), 
        required=True, 
        allow_null=False
    ) 
    solicitante_id = serializers.PrimaryKeyRelatedField(
        source='perfil_oracle.Solicitante_Id', 
        queryset=Tipo_Solicitantes.objects.all(), 
        required=False, 
        allow_null=True
    )

    nombres = serializers.CharField(source='perfil_oracle.Nombres', required=True)
    apellido1 = serializers.CharField(source='perfil_oracle.Apellido1', required=True)
    apellido2 = serializers.CharField(source='perfil_oracle.Apellido2', required=False, allow_null=True, allow_blank=True)
    direccion = serializers.CharField(source='perfil_oracle.Direccion', required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField(required=True) 
    
    telefono = serializers.CharField(source='perfil_oracle.Telefono', required=False, allow_null=True, allow_blank=True)
    numero_celular = serializers.CharField(source='perfil_oracle.Numero_celular', required=False, allow_null=True, allow_blank=True)
    
    # ⭐ NUEVO CAMPO: CAMPUS ⭐
    campus = serializers.CharField(
        source='perfil_oracle.Campus', 
        required=False, 
        allow_null=True, 
        allow_blank=True
    )
    
    # --- CAMPOS DE SOLO LECTURA ---
    rol_nombre = serializers.SerializerMethodField(read_only=True)
    tipo_id_nombre = serializers.CharField(source='perfil_oracle.Tipo_Id.Nombre_Tipo_Identificacion', read_only=True) 
    
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 
            'nombres', 'apellido1', 'apellido2', 'direccion', 
            'telefono', 'numero_celular',
            'campus',  # ⭐ AGREGADO ⭐
            'tipo_id', 'solicitante_id', 'rol_id', 'rol_nombre', 'tipo_id_nombre',
            'password', 'is_admin', 
        )
        read_only_fields = ('id', 'is_active') 

    def get_rol_nombre(self, obj):
        try:
            return obj.perfil_oracle.roles_usuario_detalle.all().first().Rol_Id.Nombre_Roles
        except Exception:
            return None

    def validate(self, attrs):
        if not self.instance and not attrs.get('rol_del_usuario'):
            raise serializers.ValidationError({"rol_id": "El rol es obligatorio para la creación."})
        return attrs

    # --- LÓGICA CREATE ---
    @transaction.atomic
    def create(self, validated_data):
        profile_data_raw = validated_data.pop('perfil_oracle', {})
        
        def safe_to_decimal(value):
            if value is None or (isinstance(value, str) and not value.strip()):
                return None
            try:
                return float(value) 
            except (ValueError, TypeError):
                logger.warning(f"Valor no numérico para campo Decimal: {value}")
                return None

        # Preparar data del perfil (modelo Usuarios)
        profile_data = {
            'Nombres': profile_data_raw.get('Nombres'), 
            'Apellido1': profile_data_raw.get('Apellido1'),
            'Apellido2': profile_data_raw.get('Apellido2') or None,
            'Direccion': profile_data_raw.get('Direccion') or None,
            'Telefono': safe_to_decimal(profile_data_raw.get('Telefono')),
            'Numero_celular': safe_to_decimal(profile_data_raw.get('Numero_celular')),
            'Correo_electronico': validated_data.get('email', None) or None,
            'Campus': profile_data_raw.get('Campus') or None,  # ⭐ AGREGADO ⭐
        }
        
        is_admin_flag = validated_data.pop('is_admin', False) 
        password = validated_data.pop('password')
        rol_a_asignar = validated_data.pop('rol_del_usuario') 
        tipo_id_instance = profile_data_raw.get('Tipo_Id', None)
        solicitante_id_instance = profile_data_raw.get('Solicitante_Id', None)
        
        # 1. Crear usuario de Django
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', None),
            password=password,
            is_staff=is_admin_flag 
        )
        
        # 2. Crear perfil de Oracle
        perfil_usuario = Usuarios.objects.create(
            Usuario_Id=user,
            Tipo_Id=tipo_id_instance, 
            Solicitante_Id=solicitante_id_instance, 
            **profile_data, 
        )
        
        # 3. Asignar rol en Oracle
        Usuarios_Roles.objects.create(
            Usuario_Id=perfil_usuario, 
            Rol_Id=rol_a_asignar
        )
        
        logger.info(f"Usuario {user.username} creado con rol {rol_a_asignar.Nombre_Roles}.")
        return user


    # --- LÓGICA UPDATE ---
    @transaction.atomic
    def update(self, instance, validated_data):
        
        def safe_to_decimal(value):
            if value is None or (isinstance(value, str) and not value.strip()):
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"Valor no numérico en update para campo Decimal: {value}")
                return None
        
        profile_data_raw = validated_data.pop('perfil_oracle', {})
        rol_instance_input = validated_data.pop('rol_del_usuario', None)
        new_password = validated_data.pop('password', None)
        is_admin_flag = validated_data.pop('is_admin', None)

        # 2. ACTUALIZAR MODELO DJANGO (User)
        instance.username = validated_data.get('username', instance.username)
        
        if 'email' in validated_data:
            instance.email = validated_data['email']
        
        if new_password and new_password.strip():
            instance.set_password(new_password)
            
        if is_admin_flag is not None:
            instance.is_staff = is_admin_flag
            
        instance.save() 

        # 3. ACTUALIZAR MODELO ORACLE (Usuarios/Perfil)
        try:
            perfil_oracle = instance.perfil_oracle
        except Usuarios.DoesNotExist:
            raise serializers.ValidationError({"perfil": "No se encontró el perfil de Oracle asociado."})
        
        perfil_oracle.Nombres = profile_data_raw.get('Nombres', perfil_oracle.Nombres)
        perfil_oracle.Apellido1 = profile_data_raw.get('Apellido1', perfil_oracle.Apellido1)
        perfil_oracle.Apellido2 = profile_data_raw.get('Apellido2', perfil_oracle.Apellido2) or None
        perfil_oracle.Direccion = profile_data_raw.get('Direccion', perfil_oracle.Direccion) or None
        perfil_oracle.Correo_electronico = instance.email.strip() if instance.email else None
        
        # ⭐ ACTUALIZAR CAMPUS ⭐
        if 'Campus' in profile_data_raw:
            perfil_oracle.Campus = profile_data_raw.get('Campus') or None
        
        if 'Telefono' in profile_data_raw:
            perfil_oracle.Telefono = safe_to_decimal(profile_data_raw.get('Telefono'))
        if 'Numero_celular' in profile_data_raw:
            perfil_oracle.Numero_celular = safe_to_decimal(profile_data_raw.get('Numero_celular'))
            
        tipo_id_instance = profile_data_raw.get('Tipo_Id')
        if tipo_id_instance is not None:
            perfil_oracle.Tipo_Id = tipo_id_instance
            
        solicitante_id_instance = profile_data_raw.get('Solicitante_Id')
        if solicitante_id_instance is not None:
            perfil_oracle.Solicitante_Id = solicitante_id_instance
            
        perfil_oracle.save() 

        # 4. ACTUALIZAR TABLA DE ROLES
        if rol_instance_input is not None:
            perfil_oracle.roles_usuario_detalle.all().delete()
            Usuarios_Roles.objects.create(
                Usuario_Id=perfil_oracle, 
                Rol_Id=rol_instance_input
            )
        
        logger.info(f"Usuario {instance.username} actualizado.")
        return instance
    

# ----------------------------------------------------------------------
# Serializador para la relación Usuarios_Programas (N:M)
# ----------------------------------------------------------------------
class UsuariosProgramasSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(write_only=True)
    programa_id = serializers.IntegerField(write_only=True)
    
    nombre_programa = serializers.CharField(source='Programa_Id.Nombre_Programa', read_only=True)
    nombre_usuario = serializers.CharField(source='Usuario_Id.Nombres', read_only=True)

    class Meta:
        model = Usuarios_Programas 
        fields = ('usuario_id', 'programa_id', 'nombre_programa', 'nombre_usuario')
        read_only_fields = ('nombre_programa', 'nombre_usuario')

    def validate(self, data):
        usuario_id = data.get('usuario_id')
        programa_id = data.get('programa_id')

        if not Usuarios.objects.filter(Usuario_Id=usuario_id).exists():
            raise serializers.ValidationError({"usuario_id": "El Usuario_Id proporcionado no existe."})

        if not Programas.objects.filter(Programa_Id=programa_id).exists():
            raise serializers.ValidationError({"programa_id": "El Programa_Id proporcionado no existe."})

        if not self.instance:
            existe = Usuarios_Programas.objects.filter(
                Usuario_Id_id=usuario_id, 
                Programa_Id_id=programa_id
            ).exists()
            
            if existe:
                raise serializers.ValidationError({
                    "general": "Este usuario ya está asociado a este programa."
                })

        return data
    
    @transaction.atomic
    def create(self, validated_data):
        usuario_id = validated_data.pop('usuario_id')
        programa_id = validated_data.pop('programa_id')

        return Usuarios_Programas.objects.create(
            Usuario_Id_id=usuario_id, 
            Programa_Id_id=programa_id
        )