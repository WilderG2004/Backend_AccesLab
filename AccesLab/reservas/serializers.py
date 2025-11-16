from rest_framework import serializers
from django.db import transaction, connection
from django.utils import timezone
from django.db import models
from django.db.models import Q 
import datetime

# Importaciones locales de la app 'reservas'
from .models import Solicitudes, Solicitudes_Objetos, Integrante_Solicitud 

# Importaciones desde la app 'maestros'
from maestros.models import (
    Tipo_Servicio, 
    Objetos, 
    Entregas, 
    Devoluciones, 
    Estados,
    Laboratorios,
    Horarios_Laboratorio,
    Programas 
) 

# Importaciones desde la app 'usuarios'
from usuarios.models import Usuarios, Usuarios_Programas 


# ----------------------------------------------------------------------
# UTILIDAD: Generar ID automático si no existe la secuencia
# ----------------------------------------------------------------------
def get_next_id(model_class, id_field_name):
    """
    Obtiene el siguiente ID disponible para un modelo.
    Intenta usar la secuencia de Oracle, si falla usa max(id) + 1
    """
    try:
        # Intentar obtener el siguiente valor de la secuencia
        sequence_name = f"C##_ACCESLAB_USER.{model_class.__name__.upper()}_SEQ"
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT {sequence_name}.NEXTVAL FROM DUAL")
            return cursor.fetchone()[0]
    except Exception:
        # Si falla, usar max(id) + 1
        max_id = model_class.objects.aggregate(
            max_id=models.Max(id_field_name)
        )['max_id'] or 0
        return max_id + 1


# ----------------------------------------------------------------------
# 1. Serializers para SOLICITUDES_OBJETOS (Detalle de Objetos)
# ----------------------------------------------------------------------

class SolicitudesObjetosSerializer(serializers.ModelSerializer):
    objetos_id = serializers.IntegerField(write_only=True, required=False)
    # Permitir crear objetos directamente
    nombre_objeto = serializers.CharField(write_only=True, required=False)
    descripcion_objeto = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Solicitudes_Objetos
        fields = ('objetos_id', 'nombre_objeto', 'descripcion_objeto', 'Cantidad_Objetos')

    def validate(self, data):
        """Valida que el stock sea suficiente o crea el objeto si no existe."""
        objeto_id = data.get('objetos_id')
        nombre_objeto = data.get('nombre_objeto')
        cantidad = data.get('Cantidad_Objetos', 0)
        
        # Si no hay objeto_id pero hay nombre, se creará dinámicamente
        if not objeto_id and not nombre_objeto:
            raise serializers.ValidationError({
                "objetos_id": "Debe proporcionar 'objetos_id' o 'nombre_objeto' para crear el objeto."
            })
        
        if cantidad <= 0:
            raise serializers.ValidationError({
                "Cantidad_Objetos": "La cantidad debe ser mayor a cero."
            })

        # Si se proporciona objeto_id, validar stock
        if objeto_id:
            try:
                objeto = Objetos.objects.get(Objetos_Id=objeto_id)
                if objeto.Cant_Stock < cantidad:
                    raise serializers.ValidationError({
                        "Cantidad_Objetos": f"El objeto '{objeto.Nombre_Objetos}' solo tiene {objeto.Cant_Stock} en stock, y se solicitan {cantidad}."
                    })
            except Objetos.DoesNotExist:
                raise serializers.ValidationError({
                    "objetos_id": "El Objetos_Id proporcionado no existe. Use 'nombre_objeto' para crear uno nuevo."
                })
        
        return data


class SolicitudesObjetosReadSerializer(serializers.ModelSerializer):
    nombre_objeto = serializers.CharField(source='Objetos_Id.Nombre_Objetos', read_only=True)
    
    class Meta:
        model = Solicitudes_Objetos
        fields = ('Solicitud_Objetos_Id', 'Objetos_Id', 'nombre_objeto', 'Cantidad_Objetos')


# ----------------------------------------------------------------------
# 2. Serializers para SOLICITUDES (Principal)
# ----------------------------------------------------------------------

class SolicitudesWriteSerializer(serializers.ModelSerializer):
    # Detalle de objetos: Anidado y solo para escritura (CREATE)
    objetos_solicitados = SolicitudesObjetosSerializer(many=True, write_only=True, required=False) 

    # Campos de FK - Ahora OPCIONALES y con auto-creación
    tipo_servicio_id = serializers.IntegerField(write_only=True, required=False)
    tipo_servicio_nombre = serializers.CharField(write_only=True, required=False)
    
    usuario_id = serializers.IntegerField(write_only=True, required=False)
    
    # Campos de gestión - OPCIONALES
    estado_id = serializers.IntegerField(write_only=True, required=False)
    estado_nombre = serializers.CharField(write_only=True, required=False)
    
    laboratorio_id = serializers.IntegerField(write_only=True, required=False)
    laboratorio_nombre = serializers.CharField(write_only=True, required=False)
    
    horario_id = serializers.IntegerField(write_only=True, required=False)
    
    # Campos requeridos en la cabecera
    # 🔥 CORRECCIÓN: Hacerlos no requeridos por defecto para que PATCH funcione.
    # La validación de 'create' se encargará de exigirlos.
    Asignatura = serializers.CharField(required=False)
    N_asistentes = serializers.IntegerField(required=False)

    class Meta:
        model = Solicitudes
        fields = (
            'Solicitud_Id', 'usuario_id', 
            'tipo_servicio_id', 'tipo_servicio_nombre',
            'estado_id', 'estado_nombre',
            'laboratorio_id', 'laboratorio_nombre',
            'horario_id',
            'Asignatura', 'N_asistentes', 
            'Fecha_Inicio', 'Fecha_Fin', 'Hora_Inicio', 'Hora_Fin',
            'Observaciones_Solicitud',
            'objetos_solicitados',
            'Fecha_solicitud' 
        )
        read_only_fields = ('Solicitud_Id', 'Fecha_solicitud')

    # ============================================
    # 🔥🔥 INICIO DE LA CORRECCIÓN 🔥🔥
    # ============================================
    def validate(self, data):
        """Validación flexible que permite crear o referenciar entidades existentes."""
        
        # self.instance es None en CREATE (POST)
        # self.instance existe en UPDATE (PUT/PATCH)
        is_update_or_patch = self.instance is not None

        # Validar que al menos haya una forma de identificar el tipo de servicio
        tipo_servicio_id = data.get('tipo_servicio_id')
        tipo_servicio_nombre = data.get('tipo_servicio_nombre')
        
        if is_update_or_patch:
            # Es un UPDATE/PATCH. Solo validamos si el campo viene en el request.
            if 'tipo_servicio_id' not in data and 'tipo_servicio_nombre' not in data:
                # El campo no se está actualizando, así que no lo validamos.
                # Esto permite que un PATCH a {'Estado_Id': 2} funcione.
                pass
            elif not tipo_servicio_id and not tipo_servicio_nombre:
                # El campo SÍ viene, pero viene vacío/nulo, lo cual es un error.
                raise serializers.ValidationError({
                    'tipo_servicio': 'Debe proporcionar tipo_servicio_id o tipo_servicio_nombre.'
                })
        else:
            # Es un CREATE. La validación es obligatoria.
            if not tipo_servicio_id and not tipo_servicio_nombre:
                raise serializers.ValidationError({
                    'tipo_servicio': 'Debe proporcionar tipo_servicio_id o tipo_servicio_nombre.'
                })
            
            # También validar los campos requeridos en CREATE
            if not data.get('Asignatura'):
                raise serializers.ValidationError({'Asignatura': 'Este campo es requerido.'})
            if not data.get('N_asistentes'):
                raise serializers.ValidationError({'N_asistentes': 'Este campo es requerido.'})

        # ============================================
        # 🔥🔥 FIN DE LA CORRECCIÓN 🔥🔥
        # ============================================
        
        # Validar fechas si se proporcionan
        fecha_inicio = data.get('Fecha_Inicio')
        fecha_fin = data.get('Fecha_Fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise serializers.ValidationError({
                'Fecha_Fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        
        # Validación de concurrencia SOLO si hay laboratorio Y fechas completas
        # Usar 'self.instance' para obtener el lab actual si no se está cambiando
        laboratorio_id = data.get('laboratorio_id', getattr(self.instance, 'Laboratorio_Id_id', None))
        
        if laboratorio_id and all([data.get('Fecha_Inicio'), data.get('Fecha_Fin'), 
                                   data.get('Hora_Inicio'), data.get('Hora_Fin')]):
            
            hora_inicio = data.get('Hora_Inicio')
            hora_fin = data.get('Hora_Fin')
            
            # Asegurarse de que las fechas/horas sean objetos correctos para comparar
            # (Depende de cómo lleguen los datos, si son strings, convertirlos a datetime)
            
            conflictos = Solicitudes.objects.filter(
                Laboratorio_Id=laboratorio_id,
                Fecha_Inicio__lte=fecha_inicio, 
                Fecha_Fin__gte=fecha_inicio, 
                Estado_Id__Estado_Id__in=[1, 2] # 1=Pendiente, 2=Aprobada
            ).exclude(
                Solicitud_Id=self.instance.Solicitud_Id if self.instance else None
            ).filter(
                Q(Hora_Inicio__lt=hora_fin) & Q(Hora_Fin__gt=hora_inicio)
            )

            if conflictos.exists():
                raise serializers.ValidationError({
                    "laboratorio_id": "El laboratorio ya está reservado en el horario solicitado."
                })

        return data

    def _get_or_create_tipo_servicio(self, validated_data):
        """Obtiene o crea el tipo de servicio."""
        tipo_servicio_id = validated_data.pop('tipo_servicio_id', None)
        tipo_servicio_nombre = validated_data.pop('tipo_servicio_nombre', None)
        
        if tipo_servicio_id:
            try:
                return Tipo_Servicio.objects.get(Tipo_Servicio_Id=tipo_servicio_id)
            except Tipo_Servicio.DoesNotExist:
                if not tipo_servicio_nombre:
                    raise serializers.ValidationError({
                        'tipo_servicio_id': f'No existe un tipo de servicio con ID {tipo_servicio_id}'
                    })
        
        # Crear nuevo tipo de servicio
        if tipo_servicio_nombre:
            tipo_servicio, created = Tipo_Servicio.objects.get_or_create(
                Nombre_Tipo_Servicio=tipo_servicio_nombre,
                defaults={
                    'Tipo_Servicio_Id': get_next_id(Tipo_Servicio, 'Tipo_Servicio_Id')
                }
            )
            return tipo_servicio
        
        return None

    def _get_or_create_estado(self, validated_data):
        """Obtiene o crea el estado."""
        estado_id = validated_data.pop('estado_id', None)
        estado_nombre = validated_data.pop('estado_nombre', None)
        
        if estado_id:
            try:
                return Estados.objects.get(Estado_Id=estado_id)
            except Estados.DoesNotExist:
                if not estado_nombre:
                    # Estado por defecto: PENDIENTE
                    return Estados.objects.get(Estado_Id=1)
        
        if estado_nombre:
            estado, created = Estados.objects.get_or_create(
                Nombre_Estado=estado_nombre,
                defaults={
                    'Estado_Id': get_next_id(Estados, 'Estado_Id')
                }
            )
            return estado
        
        # Estado por defecto
        return Estados.objects.get(Estado_Id=1)

    def _get_or_create_laboratorio(self, validated_data):
        """Obtiene o crea el laboratorio."""
        laboratorio_id = validated_data.pop('laboratorio_id', None)
        laboratorio_nombre = validated_data.pop('laboratorio_nombre', None)
        
        if laboratorio_id:
            try:
                return Laboratorios.objects.get(Laboratorio_Id=laboratorio_id)
            except Laboratorios.DoesNotExist:
                if not laboratorio_nombre:
                    return None
        
        if laboratorio_nombre:
            laboratorio, created = Laboratorios.objects.get_or_create(
                Nombre_Laboratorio=laboratorio_nombre,
                defaults={
                    'Laboratorio_Id': get_next_id(Laboratorios, 'Laboratorio_Id')
                }
            )
            return laboratorio
        
        return None

    def _get_or_create_horario(self, validated_data):
        """Obtiene el horario si existe."""
        horario_id = validated_data.pop('horario_id', None)
        
        if horario_id:
            try:
                return Horarios_Laboratorio.objects.get(Horario_Id=horario_id)
            except Horarios_Laboratorio.DoesNotExist:
                return None
        
        return None

    def _get_or_create_objeto(self, objeto_data):
        """Obtiene o crea un objeto."""
        objeto_id = objeto_data.get('objetos_id')
        nombre_objeto = objeto_data.get('nombre_objeto')
        
        if objeto_id:
            return Objetos.objects.get(Objetos_Id=objeto_id)
        
        if nombre_objeto:
            objeto, created = Objetos.objects.get_or_create(
                Nombre_Objetos=nombre_objeto,
                defaults={
                    'Objetos_Id': get_next_id(Objetos, 'Objetos_Id'),
                    'Descripcion_Objetos': objeto_data.get('descripcion_objeto', ''),
                    'Cant_Stock': objeto_data.get('Cantidad_Objetos', 0)
                }
            )
            return objeto
        
        return None

    @transaction.atomic
    def create(self, validated_data):
        objetos_data = validated_data.pop('objetos_solicitados', [])
        
        # Obtener o crear relaciones
        tipo_servicio = self._get_or_create_tipo_servicio(validated_data)
        estado = self._get_or_create_estado(validated_data)
        laboratorio = self._get_or_create_laboratorio(validated_data)
        horario = self._get_or_create_horario(validated_data)
        
        # Usuario
        user_id = validated_data.pop('usuario_id', None)
        if not user_id and self.context.get('request') and self.context['request'].user.is_authenticated:
            try:
                user_id = self.context['request'].user.perfil_oracle.Usuario_Id
            except AttributeError:
                pass

        try:
            # Generar ID para la solicitud
            solicitud_id = get_next_id(Solicitudes, 'Solicitud_Id')

            # Crear la Solicitud Principal
            solicitud = Solicitudes.objects.create(
                Solicitud_Id=solicitud_id, 
                Usuario_Id_id=user_id, 
                Tipo_Servicio_Id=tipo_servicio, 
                Fecha_solicitud=timezone.localdate(), 
                
                Asignatura=validated_data.get('Asignatura'),
                N_asistentes=validated_data.get('N_asistentes'),
                Fecha_Inicio=validated_data.get('Fecha_Inicio'),
                Fecha_Fin=validated_data.get('Fecha_Fin'),
                Hora_Inicio=validated_data.get('Hora_Inicio'),
                Hora_Fin=validated_data.get('Hora_Fin'),
                Observaciones_Solicitud=validated_data.get('Observaciones_Solicitud'),
                
                Estado_Id=estado,
                Laboratorio_Id=laboratorio, 
                Horario_Id=horario,
            )

            # Procesar objetos
            if objetos_data:
                for detalle_data in objetos_data:
                    cantidad = detalle_data.get('Cantidad_Objetos')
                    
                    # Obtener o crear objeto
                    objeto = self._get_or_create_objeto(detalle_data)
                    
                    if objeto:
                        # Generar ID para solicitud_objetos
                        solicitud_objetos_id = get_next_id(Solicitudes_Objetos, 'Solicitud_Objetos_Id')
                        
                        # Crear el Detalle
                        Solicitudes_Objetos.objects.create(
                            Solicitud_Objetos_Id=solicitud_objetos_id,
                            Solicitud_Id=solicitud,
                            Objetos_Id=objeto, 
                            Cantidad_Objetos=cantidad,
                        )

                        # Actualizar inventario si el objeto existía
                        if detalle_data.get('objetos_id'):
                            Objetos.objects.filter(Objetos_Id=objeto.Objetos_Id).update(
                                Cant_Stock=models.F('Cant_Stock') - cantidad 
                            )
                
            return solicitud
        except Exception as e:
            raise serializers.ValidationError({"detail": f"Error al guardar la solicitud: {str(e)}"})

    def update(self, instance, validated_data):
        """Actualización flexible de solicitudes."""
        validated_data.pop('objetos_solicitados', None)
        
        # Manejar relaciones si se proporcionan
        if 'tipo_servicio_id' in validated_data or 'tipo_servicio_nombre' in validated_data:
            tipo_servicio = self._get_or_create_tipo_servicio(validated_data)
            instance.Tipo_Servicio_Id = tipo_servicio
        
        if 'estado_id' in validated_data or 'estado_nombre' in validated_data:
            estado = self._get_or_create_estado(validated_data)
            instance.Estado_Id = estado
        
        if 'laboratorio_id' in validated_data or 'laboratorio_nombre' in validated_data:
            laboratorio = self._get_or_create_laboratorio(validated_data)
            instance.Laboratorio_Id = laboratorio
        
        if 'horario_id' in validated_data:
            horario = self._get_or_create_horario(validated_data)
            instance.Horario_Id = horario
        
        # Actualizar campos restantes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# ----------------------------------------------------------------------
# Serializer de Lectura (Sin cambios mayores)
# ----------------------------------------------------------------------

class SolicitudesReadSerializer(serializers.ModelSerializer):
    nombre_solicitante = serializers.SerializerMethodField()
    tipo_servicio_nombre = serializers.CharField(source='Tipo_Servicio_Id.Nombre_Tipo_Servicio', read_only=True)
    estado_nombre = serializers.CharField(source='Estado_Id.Nombre_Estado', read_only=True)
    laboratorio_nombre = serializers.CharField(source='Laboratorio_Id.Nombre_Laboratorio', read_only=True, allow_null=True)
    horario_inicio = serializers.SerializerMethodField() 

    objetos_solicitados_detalle = SolicitudesObjetosReadSerializer(
        source='solicitudes_objetos_set', 
        many=True, 
        read_only=True
    )
    
    programas_solicitante = serializers.SerializerMethodField()
    integrantes_asociados = serializers.SerializerMethodField() 
    
    class Meta:
        model = Solicitudes
        fields = (
            'Solicitud_Id', 'Fecha_solicitud', 'Asignatura', 'N_asistentes', 
            'Usuario_Id', 'Tipo_Servicio_Id', 
            'Fecha_Inicio', 'Fecha_Fin', 'Hora_Inicio', 'Hora_Fin', 
            'Observaciones_Solicitud',
            'nombre_solicitante', 'tipo_servicio_nombre', 'estado_nombre', 
            'laboratorio_nombre', 'horario_inicio',
            'objetos_solicitados_detalle',
            'programas_solicitante', 
            'integrantes_asociados'
        )
        
    def get_nombre_solicitante(self, obj):
        if not obj.Usuario_Id:
            return "Pendiente de Asignación / Anónimo"
        return f"{obj.Usuario_Id.Nombres} {obj.Usuario_Id.Apellido1}"

    def get_horario_inicio(self, obj):
        if obj.Horario_Id:
            return str(obj.Horario_Id)
        return None 
    
    def get_programas_solicitante(self, obj):
        if not obj.Usuario_Id:
            return []
        
        programas_asociados = Usuarios_Programas.objects.filter(Usuario_Id=obj.Usuario_Id)
        
        return [
            {
                "programa_id": p.Programa_Id_id, 
                "nombre": p.Programa_Id.Nombre_Programa
            }
            for p in programas_asociados
        ]
        
    def get_integrantes_asociados(self, obj):
        integrantes = Integrante_Solicitud.objects.filter(Solicitud_Id=obj)
        return IntegranteSolicitudSimpleSerializer(integrantes, many=True).data


# ----------------------------------------------------------------------
# 3. Serializers de Integrantes (Sin cambios mayores)
# ----------------------------------------------------------------------

class IntegranteSolicitudSimpleSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(source='Usuario_Id.Nombres', read_only=True)
    apellido_usuario = serializers.CharField(source='Usuario_Id.Apellido1', read_only=True)
    
    class Meta:
        model = Integrante_Solicitud
        fields = ('Usuario_Id_id', 'nombre_usuario', 'apellido_usuario')


class IntegranteSolicitudSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(write_only=True)
    solicitud_id = serializers.IntegerField(write_only=True)
    
    nombre_usuario = serializers.CharField(source='Usuario_Id.Nombres', read_only=True)
    apellido_usuario = serializers.CharField(source='Usuario_Id.Apellido1', read_only=True)

    class Meta:
        model = Integrante_Solicitud
        fields = (
            'Usuario_Solicitud_Id', 'usuario_id', 'solicitud_id', 
            'nombre_usuario', 'apellido_usuario'
        )
        read_only_fields = ('Usuario_Solicitud_Id',)

    def validate(self, data):
        usuario_id = data.get('usuario_id')
        solicitud_id = data.get('solicitud_id')

        if not Usuarios.objects.filter(Usuario_Id=usuario_id).exists():
            raise serializers.ValidationError({
                "usuario_id": "El Usuario_Id proporcionado no existe."
            })

        if not Solicitudes.objects.filter(Solicitud_Id=solicitud_id).exists():
            raise serializers.ValidationError({
                "solicitud_id": "La Solicitud_Id proporcionada no existe."
            })

        if Integrante_Solicitud.objects.filter(
            Usuario_Id_id=usuario_id, 
            Solicitud_Id_id=solicitud_id
        ).exists():
            raise serializers.ValidationError(
                "Este usuario ya está asociado a esta solicitud como integrante."
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        usuario_id = validated_data.pop('usuario_id')
        solicitud_id = validated_data.pop('solicitud_id')
        
        try:
            integrante_solicitud_id = get_next_id(Integrante_Solicitud, 'Usuario_Solicitud_Id')

            integrante_solicitud = Integrante_Solicitud.objects.create(
                Usuario_Solicitud_Id=integrante_solicitud_id,
                Usuario_Id_id=usuario_id,
                Solicitud_Id_id=solicitud_id
            )
            return integrante_solicitud
        except Exception as e:
            raise serializers.ValidationError({
                "error": f"Error al guardar la relación de integrante: {str(e)}"
            })