from django.contrib.auth.models import User
from rest_framework import serializers
import logging 
from django.db import transaction, models

# Importaciones de Modelos
from .models import Usuarios, Usuarios_Roles, Usuarios_Programas
from maestros.models import Roles, Tipo_Identificacion, Tipo_Solicitantes, Objetos, Programas

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# UTILIDAD: Generar ID automático
# ----------------------------------------------------------------------
def get_next_id(model_class, id_field_name):
    """
    Obtiene el siguiente ID disponible para un modelo.
    Usa max(id) + 1 para compatibilidad con Oracle.
    """
    max_id = model_class.objects.aggregate(
        max_id=models.Max(id_field_name)
    )['max_id'] or 0
    return max_id + 1


# ----------------------------------------------------------------------
# Serializador FLEXIBLE para Usuarios (CRUD Completo)
# ----------------------------------------------------------------------
class UsuarioAdminSerializer(serializers.ModelSerializer):
    """
    Serializador para la gestión completa (CRUD) de usuarios. 
    Sincroniza User (Django) con Usuarios y Usuarios_Roles (Oracle).
    ⭐ CREACIÓN FLEXIBLE: Puede crear roles, tipos, programas si no existen ⭐
    """
    
    # --- CAMPO PASSWORD (Solo escritura) ---
    password = serializers.CharField(write_only=True, required=False, allow_blank=True) 
    
    # --- CAMPOS DE ROL (Lectura y Escritura) ---
    is_admin = serializers.SerializerMethodField(read_only=True)
    is_admin_input = serializers.BooleanField(write_only=True, required=False, default=False)
    
    # Campos flexibles para ROL
    rol_id_input = serializers.IntegerField(write_only=True, required=False)
    rol_nombre_input = serializers.CharField(write_only=True, required=False)
    
    # --- CAMPOS FLEXIBLES PARA TIPO DE IDENTIFICACIÓN (Solo Escritura) ---
    # Estos campos se manejan solo para escritura/actualización en el validador/create/update,
    # El valor de lectura se obtiene del perfil_oracle.Tipo_Id
    tipo_id = serializers.IntegerField(write_only=True, required=False) 
    tipo_nombre = serializers.CharField(write_only=True, required=False)
    
    # --- CAMPOS FLEXIBLES PARA TIPO DE SOLICITANTE (Solo Escritura) ---
    solicitante_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    solicitante_nombre = serializers.CharField(write_only=True, required=False, allow_null=True)

    # --- CAMPOS DE PERFIL (CORRECCIÓN: Se usa 'source' para acceder al perfil de Oracle) ---
    # Nota: Se asume que la relación inversa desde User a Usuarios se llama 'perfil_oracle'
    # Nota: Se usan los nombres de campos de Django (minúsculas) en el serializador, 
    # pero el 'source' apunta a los nombres del modelo Usuarios (Oracle) (ej. Nombres, Apellido1).
    nombres = serializers.CharField(source='perfil_oracle.Nombres', required=True)
    apellido1 = serializers.CharField(source='perfil_oracle.Apellido1', required=True)
    apellido2 = serializers.CharField(source='perfil_oracle.Apellido2', required=False, allow_null=True, allow_blank=True)
    direccion = serializers.CharField(source='perfil_oracle.Direccion', required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField(required=True) # Este campo está directamente en el modelo User
    telefono = serializers.CharField(source='perfil_oracle.Telefono', required=False, allow_null=True, allow_blank=True)
    numero_celular = serializers.CharField(source='perfil_oracle.Numero_celular', required=False, allow_null=True, allow_blank=True)
    campus = serializers.CharField(source='perfil_oracle.Campus', required=False, allow_null=True, allow_blank=True)
    
    # --- CAMPOS DE SOLO LECTURA ---
    rol_nombre = serializers.SerializerMethodField(read_only=True)
    tipo_id_nombre = serializers.SerializerMethodField(read_only=True)
    solicitante_nombre_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 
            'nombres', 'apellido1', 'apellido2', 'direccion', 
            'telefono', 'numero_celular', 'campus',
            # Campos de solo escritura para relaciones
            'tipo_id', 'tipo_nombre', 
            'solicitante_id', 'solicitante_nombre',
            'rol_id_input', 'rol_nombre_input',
            # Campos de solo lectura para display
            'rol_nombre', 'tipo_id_nombre', 'solicitante_nombre_display',
            'password', 
            'is_admin', 'is_admin_input',
        )
        read_only_fields = ('id',)

    def get_rol_nombre(self, obj):
        """Obtiene el nombre del rol asignado al usuario"""
        try:
            rol_usuario = obj.perfil_oracle.roles_usuario_detalle.first()
            return rol_usuario.Rol_Id.Nombre_Roles if rol_usuario else None
        except Exception as e:
            logger.warning(f"Error obteniendo rol_nombre para usuario {obj.username}: {e}")
            return None

    def get_is_admin(self, obj):
        """Determina si el usuario es admin basado en is_staff o rol_id=1"""
        try:
            if obj.is_staff:
                return True
            
            rol_usuario = obj.perfil_oracle.roles_usuario_detalle.first()
            if rol_usuario and rol_usuario.Rol_Id.Rol_Id == 1:
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Error determinando is_admin para usuario {obj.username}: {e}")
            return False

    def get_tipo_id_nombre(self, obj):
        """Obtiene el nombre del tipo de identificación"""
        try:
            return obj.perfil_oracle.Tipo_Id.Nombre_Tipo_Identificacion if obj.perfil_oracle.Tipo_Id else None
        except Exception:
            return None

    def get_solicitante_nombre_display(self, obj):
        """Obtiene el nombre del tipo de solicitante"""
        try:
            return obj.perfil_oracle.Solicitante_Id.Nombre_Tipo_Solicitante if obj.perfil_oracle.Solicitante_Id else None
        except Exception:
            return None

    def validate(self, attrs):
        """Validación flexible: al menos un método para identificar rol y tipo"""
        
        # Eliminar las claves con source para que no interfieran con la validación si son solo de lectura
        # NOTA: En este diseño, los campos con 'source' de perfil se pasan al diccionario attrs
        # cuando se está en modo 'create' o 'update', ya que son requeridos. 
        # DRF los incluye, pero aquí vamos a operar con los campos tal como los recibimos
        # y como los usamos en create/update.
        
        # Validar ROL (solo en creación, o si se proporcionan en actualización)
        if not self.instance: # Creación
            rol_id = attrs.get('rol_id_input')
            rol_nombre = attrs.get('rol_nombre_input')
            
            if not rol_id and not rol_nombre:
                raise serializers.ValidationError({
                    "rol": "Debe proporcionar rol_id_input o rol_nombre_input."
                })
            
            # Validar TIPO DE IDENTIFICACIÓN
            tipo_id = attrs.get('tipo_id')
            tipo_nombre = attrs.get('tipo_nombre')
            
            if not tipo_id and not tipo_nombre:
                raise serializers.ValidationError({
                    "tipo": "Debe proporcionar tipo_id o tipo_nombre."
                })
        
        # Validar email único
        email = attrs.get('email')
        if email:
            if self.instance:
                # Actualización: verificar que no exista en otro usuario
                if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError({
                        "email": "Este correo ya está registrado."
                    })
            else:
                # Creación: verificar que no exista
                if User.objects.filter(email=email).exists():
                    raise serializers.ValidationError({
                        "email": "Este correo ya está registrado."
                    })
        
        return attrs

    def _get_or_create_rol(self, validated_data):
        """Obtiene o crea el rol."""
        rol_id = validated_data.pop('rol_id_input', None)
        rol_nombre = validated_data.pop('rol_nombre_input', None)
        
        if rol_id:
            try:
                return Roles.objects.get(Rol_Id=rol_id)
            except Roles.DoesNotExist:
                if not rol_nombre:
                    raise serializers.ValidationError({
                        'rol_id_input': f'No existe un rol con ID {rol_id}'
                    })
        
        if rol_nombre:
            rol, created = Roles.objects.get_or_create(
                Nombre_Roles=rol_nombre,
                defaults={
                    'Rol_Id': get_next_id(Roles, 'Rol_Id')
                }
            )
            return rol
        
        return None

    def _get_or_create_tipo_identificacion(self, validated_data):
        """Obtiene o crea el tipo de identificación."""
        tipo_id = validated_data.pop('tipo_id', None)
        tipo_nombre = validated_data.pop('tipo_nombre', None)
        
        if tipo_id:
            try:
                return Tipo_Identificacion.objects.get(Tipo_Id=tipo_id)
            except Tipo_Identificacion.DoesNotExist:
                if not tipo_nombre:
                    raise serializers.ValidationError({
                        'tipo_id': f'No existe un tipo de identificación con ID {tipo_id}'
                    })
        
        if tipo_nombre:
            tipo, created = Tipo_Identificacion.objects.get_or_create(
                Nombre_Tipo_Identificacion=tipo_nombre,
                defaults={
                    'Tipo_Id': get_next_id(Tipo_Identificacion, 'Tipo_Id')
                }
            )
            return tipo
        
        return None

    def _get_or_create_tipo_solicitante(self, validated_data):
        """Obtiene o crea el tipo de solicitante."""
        solicitante_id = validated_data.pop('solicitante_id', None)
        solicitante_nombre = validated_data.pop('solicitante_nombre', None)
        
        if solicitante_id:
            try:
                return Tipo_Solicitantes.objects.get(Solicitante_Id=solicitante_id)
            except Tipo_Solicitantes.DoesNotExist:
                if not solicitante_nombre:
                    return None
        
        if solicitante_nombre:
            solicitante, created = Tipo_Solicitantes.objects.get_or_create(
                Nombre_Tipo_Solicitante=solicitante_nombre,
                defaults={
                    'Solicitante_Id': get_next_id(Tipo_Solicitantes, 'Solicitante_Id')
                }
            )
            return solicitante
        
        return None

    def _safe_to_decimal(self, value):
        """Convierte valores a decimal de forma segura."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        try:
            # Usar float() para flexibilidad antes de la inserción a la DB
            # si el campo del modelo es DecimalField
            return float(value) 
        except (ValueError, TypeError):
            logger.warning(f"Valor no numérico para campo Decimal: {value}")
            return None

    @transaction.atomic
    def create(self, validated_data):
        """Creación flexible de usuario con auto-generación de dependencias."""
        
        # Obtener o crear relaciones (estos métodos eliminan las claves de validated_data)
        rol_a_asignar = self._get_or_create_rol(validated_data)
        tipo_id_instance = self._get_or_create_tipo_identificacion(validated_data)
        solicitante_id_instance = self._get_or_create_tipo_solicitante(validated_data)
        
        # Extraer datos de User y de control
        is_admin_flag = validated_data.pop('is_admin_input', False)
        password = validated_data.pop('password')
        
        # Datos de perfil (usando los nombres de campos del serializador, ej: 'nombres')
        profile_data = {
            'Nombres': validated_data.pop('nombres'),
            'Apellido1': validated_data.pop('apellido1'),
            'Apellido2': validated_data.pop('apellido2', None) or None,
            'Direccion': validated_data.pop('direccion', None) or None,
            'Telefono': self._safe_to_decimal(validated_data.pop('telefono', None)),
            'Numero_celular': self._safe_to_decimal(validated_data.pop('numero_celular', None)),
            'Correo_electronico': validated_data.get('email', None) or None, # Usa el email de User
            'Campus': validated_data.pop('campus', None) or None,
        }
        
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

    @transaction.atomic
    def update(self, instance, validated_data):
        """Actualización flexible de usuario."""
        
        # Obtener o crear relaciones si se proporcionan (estos métodos eliminan las claves)
        rol_instance_input = None
        if 'rol_id_input' in validated_data or 'rol_nombre_input' in validated_data:
            rol_instance_input = self._get_or_create_rol(validated_data)
        
        tipo_id_instance = None
        if 'tipo_id' in validated_data or 'tipo_nombre' in validated_data:
            tipo_id_instance = self._get_or_create_tipo_identificacion(validated_data)
        
        solicitante_id_instance = None
        if 'solicitante_id' in validated_data or 'solicitante_nombre' in validated_data:
            solicitante_id_instance = self._get_or_create_tipo_solicitante(validated_data)
        
        # Extraer datos de User y de control
        new_password = validated_data.pop('password', None)
        is_admin_flag = validated_data.pop('is_admin_input', None)

        # Actualizar modelo Django (User)
        instance.username = validated_data.get('username', instance.username)
        
        if 'email' in validated_data:
            instance.email = validated_data['email']
        
        if new_password and new_password.strip():
            instance.set_password(new_password)
            
        if is_admin_flag is not None:
            instance.is_staff = is_admin_flag
            
        instance.save() 

        # Actualizar modelo Oracle (Usuarios/Perfil)
        try:
            perfil_oracle = instance.perfil_oracle
        except Usuarios.DoesNotExist:
            raise serializers.ValidationError({
                "perfil": "No se encontró el perfil de Oracle asociado."
            })
        
        # Actualizar campos de perfil (usando los nombres del modelo Oracle)
        if 'nombres' in validated_data:
            perfil_oracle.Nombres = validated_data['nombres']
        if 'apellido1' in validated_data:
            perfil_oracle.Apellido1 = validated_data['apellido1']
        if 'apellido2' in validated_data:
            perfil_oracle.Apellido2 = validated_data['apellido2'] or None
        if 'direccion' in validated_data:
            perfil_oracle.Direccion = validated_data['direccion'] or None
        if 'campus' in validated_data:
            perfil_oracle.Campus = validated_data['campus'] or None
        if 'telefono' in validated_data:
            perfil_oracle.Telefono = self._safe_to_decimal(validated_data['telefono'])
        if 'numero_celular' in validated_data:
            perfil_oracle.Numero_celular = self._safe_to_decimal(validated_data['numero_celular'])
        
        perfil_oracle.Correo_electronico = instance.email.strip() if instance.email else None
        
        # Actualizar relaciones
        if tipo_id_instance is not None:
            perfil_oracle.Tipo_Id = tipo_id_instance
            
        if solicitante_id_instance is not None:
            perfil_oracle.Solicitante_Id = solicitante_id_instance
            
        perfil_oracle.save() 

        # Actualizar tabla de roles
        if rol_instance_input is not None:
            perfil_oracle.roles_usuario_detalle.all().delete()
            Usuarios_Roles.objects.create(
                Usuario_Id=perfil_oracle, 
                Rol_Id=rol_instance_input
            )
        
        logger.info(f"Usuario {instance.username} actualizado.")
        return instance


# ----------------------------------------------------------------------
# Serializador FLEXIBLE para Usuarios_Programas (N:M)
# ----------------------------------------------------------------------
class UsuariosProgramasSerializer(serializers.ModelSerializer):
    # Campos para escribir IDs
    usuario_id = serializers.IntegerField(write_only=True, required=False)
    programa_id = serializers.IntegerField(write_only=True, required=False)
    
    # Campos para crear nuevos registros
    programa_nombre = serializers.CharField(write_only=True, required=False)
    facultad_id = serializers.IntegerField(write_only=True, required=False)
    facultad_nombre = serializers.CharField(write_only=True, required=False)
    
    # Campos de lectura
    nombre_programa = serializers.CharField(source='Programa_Id.Nombre_Programa', read_only=True)
    nombre_usuario = serializers.CharField(source='Usuario_Id.Nombres', read_only=True)
    nombre_facultad = serializers.CharField(source='Programa_Id.Facultad_Id.Nombre_Facultad', read_only=True)

    class Meta:
        model = Usuarios_Programas 
        fields = (
            'usuario_id', 'programa_id', 'programa_nombre',
            'facultad_id', 'facultad_nombre',
            'nombre_programa', 'nombre_usuario', 'nombre_facultad'
        )
        read_only_fields = ('nombre_programa', 'nombre_usuario', 'nombre_facultad')

    def validate(self, data):
        """Validación flexible para usuarios y programas."""
        usuario_id = data.get('usuario_id')
        programa_id = data.get('programa_id')
        programa_nombre = data.get('programa_nombre')

        # Validar usuario
        if not usuario_id:
            raise serializers.ValidationError({
                "usuario_id": "El usuario_id es obligatorio."
            })

        if not Usuarios.objects.filter(Usuario_Id=usuario_id).exists():
            raise serializers.ValidationError({
                "usuario_id": "El Usuario_Id proporcionado no existe."
            })

        # Validar programa (ID o nombre)
        if not programa_id and not programa_nombre:
            raise serializers.ValidationError({
                "programa": "Debe proporcionar programa_id o programa_nombre."
            })

        # Si se proporciona programa_id, validar existencia
        if programa_id and not Programas.objects.filter(Programa_Id=programa_id).exists():
            if not programa_nombre:
                raise serializers.ValidationError({
                    "programa_id": "El Programa_Id proporcionado no existe."
                })

        # Validar duplicados (solo en creación)
        if not self.instance:
            # Si ya existe el programa_id, verificar duplicado
            if programa_id:
                existe = Usuarios_Programas.objects.filter(
                    Usuario_Id_id=usuario_id, 
                    Programa_Id_id=programa_id
                ).exists()
                
                if existe:
                    raise serializers.ValidationError({
                        "general": "Este usuario ya está asociado a este programa."
                    })

        return data

    def _get_or_create_facultad(self, validated_data):
        """Obtiene o crea la facultad."""
        facultad_id = validated_data.pop('facultad_id', None)
        facultad_nombre = validated_data.pop('facultad_nombre', None)
        
        if facultad_id:
            try:
                # Esto asume que el campo Facultad_Id es el ID directo.
                # Si es una instancia, deberías importarla y usar .get()
                return facultad_id 
            except Exception:
                if not facultad_nombre:
                    return None
        
        if facultad_nombre:
            from maestros.models import Facultades
            facultad, created = Facultades.objects.get_or_create(
                Nombre_Facultad=facultad_nombre,
                defaults={
                    'Facultad_Id': get_next_id(Facultades, 'Facultad_Id')
                }
            )
            return facultad.Facultad_Id
        
        return None

    def _get_or_create_programa(self, validated_data):
        """Obtiene o crea el programa."""
        programa_id = validated_data.pop('programa_id', None)
        programa_nombre = validated_data.pop('programa_nombre', None)
        
        if programa_id:
            try:
                return Programas.objects.get(Programa_Id=programa_id)
            except Programas.DoesNotExist:
                if not programa_nombre:
                    raise serializers.ValidationError({
                        'programa_id': f'No existe un programa con ID {programa_id}'
                    })
        
        if programa_nombre:
            # Obtener o crear la facultad si se proporciona
            facultad_id = self._get_or_create_facultad(validated_data)
            
            programa, created = Programas.objects.get_or_create(
                Nombre_Programa=programa_nombre,
                defaults={
                    'Programa_Id': get_next_id(Programas, 'Programa_Id'),
                    'Facultad_Id_id': facultad_id
                }
            )
            return programa
        
        return None

    @transaction.atomic
    def create(self, validated_data):
        """Creación flexible de relación usuario-programa."""
        usuario_id = validated_data.pop('usuario_id')
        programa = self._get_or_create_programa(validated_data)

        return Usuarios_Programas.objects.create(
            Usuario_Id_id=usuario_id, 
            Programa_Id=programa
        )