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
# 1. Serializers para SOLICITUDES_OBJETOS (Detalle de Objetos)
# ----------------------------------------------------------------------

# --- 1A. Serializer para el Detalle de Objetos Solicitados (ESCRITURA) ---
class SolicitudesObjetosSerializer(serializers.ModelSerializer):
    objetos_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Solicitudes_Objetos
        fields = ('objetos_id', 'Cantidad_Objetos')

    def validate(self, data):
        """Valida que el stock sea suficiente antes de procesar la solicitud."""
        objeto_id = data.get('objetos_id')
        cantidad = data.get('Cantidad_Objetos')
        
        try:
            objeto = Objetos.objects.get(Objetos_Id=objeto_id)
        except Objetos.DoesNotExist:
            raise serializers.ValidationError({"objetos_id": "El Objetos_Id proporcionado no existe en el catálogo."})
        
        if cantidad <= 0:
            raise serializers.ValidationError({"Cantidad_Objetos": "La cantidad debe ser mayor a cero."})

        # Control de Stock
        if objeto.Cant_Stock < cantidad:
            raise serializers.ValidationError(
                {"Cantidad_Objetos": f"El objeto '{objeto.Nombre_Objetos}' solo tiene {objeto.Cant_Stock} en stock, y se solicitan {cantidad}."}
            )
        
        return data


# --- 1B. Serializer para el Detalle de Objetos Solicitados (LECTURA) ---
class SolicitudesObjetosReadSerializer(serializers.ModelSerializer):
    nombre_objeto = serializers.CharField(source='Objetos_Id.Nombre_Objetos', read_only=True)
    
    class Meta:
        model = Solicitudes_Objetos
        fields = ('Solicitud_Objetos_Id', 'Objetos_Id', 'nombre_objeto', 'Cantidad_Objetos')


# ----------------------------------------------------------------------
# 2. Serializers para SOLICITUDES (Principal)
# ----------------------------------------------------------------------

# --- 2A. Serializer para la Solicitud Principal (ESCRITURA/ACTUALIZACIÓN) ---
class SolicitudesWriteSerializer(serializers.ModelSerializer):
    # Detalle de objetos: Anidado y solo para escritura (CREATE)
    objetos_solicitados = SolicitudesObjetosSerializer(many=True, write_only=True, required=False) 

    # Campos de FK que se envían como IDs (write_only)
    tipo_servicio_id = serializers.IntegerField(write_only=True, required=False) 
    usuario_id = serializers.IntegerField(write_only=True, required=False)
    
    # Campos de gestión (Permiten IDs de objetos FK)
    Estado_Id = serializers.PrimaryKeyRelatedField(queryset=Estados.objects.all(), required=False, allow_null=True)
    Laboratorio_Id = serializers.PrimaryKeyRelatedField(queryset=Laboratorios.objects.all(), required=False, allow_null=True)
    Horario_Id = serializers.PrimaryKeyRelatedField(queryset=Horarios_Laboratorio.objects.all(), required=False, allow_null=True)
    
    # Campos requeridos en la cabecera
    Asignatura = serializers.CharField(required=True)
    N_asistentes = serializers.IntegerField(required=True)

    class Meta:
        model = Solicitudes
        fields = (
            'Solicitud_Id', 'usuario_id', 'tipo_servicio_id', 
            'Asignatura', 'N_asistentes', 
            # CAMPOS DE TIEMPO
            'Fecha_Inicio', 'Fecha_Fin', 'Hora_Inicio', 'Hora_Fin',
            'Observaciones_Solicitud',
            # Campos de gestión
            'Estado_Id', 'Laboratorio_Id', 'Horario_Id',
            'objetos_solicitados' # Campo anidado
        )
        read_only_fields = ('Solicitud_Id', 'Fecha_solicitud', 'Entrega_Id', 'Devolucion_Id')

    # --- MÉTODO DE VALIDACIÓN PRINCIPAL (DINÁMICO Y FLEXIBLE) ---
    def validate(self, data):
        
        # 1. Obtener tipo_servicio_id y cargar el objeto dinámicamente
        tipo_servicio_id = data.get('tipo_servicio_id')
        if self.instance and tipo_servicio_id is None:
            tipo_servicio_id = self.instance.Tipo_Servicio_Id_id
        
        if tipo_servicio_id is None:
            raise serializers.ValidationError({'tipo_servicio_id': 'Tipo de servicio es obligatorio para la creación.'})
        
        try:
            tipo_servicio_id = int(tipo_servicio_id)
        except (ValueError, TypeError):
            raise serializers.ValidationError({'tipo_servicio_id': 'El ID del tipo de servicio debe ser un número válido.'})
        
        # 🟢 CARGA DINÁMICA: Cargar el objeto Tipo_Servicio
        try:
            tipo_servicio_obj = Tipo_Servicio.objects.get(Tipo_Servicio_Id=tipo_servicio_id)
            nombre_servicio = tipo_servicio_obj.Nombre_Tipo_Servicio.upper().strip() 
        except Tipo_Servicio.DoesNotExist:
            raise serializers.ValidationError({'tipo_servicio_id': 'El Tipo de Servicio seleccionado no existe.'})
        
        
        # 2. Obtener Laboratorio y Horario (Lógica de PATCH/POST)
        laboratorio_obj = data.get('Laboratorio_Id')
        horario_obj = data.get('Horario_Id')
        objetos_solicitados = data.get('objetos_solicitados')
        
        if self.instance:
            laboratorio_id = laboratorio_obj.pk if laboratorio_obj is not None else self.instance.Laboratorio_Id_id
            horario_id = horario_obj.pk if horario_obj is not None else self.instance.Horario_Id_id
        else:
            laboratorio_id = laboratorio_obj.pk if laboratorio_obj else None
            horario_id = horario_obj.pk if horario_obj else None
            
        # ----------------------------------------------------------------------
        # 🛑 NUEVA LÓGICA DE VALIDACIÓN FLEXIBLE 🛑
        # Se requiere AL MENOS que se solicite un laboratorio/horario O que se pidan objetos.
        # ----------------------------------------------------------------------
        
        # A. Chequeo de dependencia mínima
        tiene_laboratorio_horario = laboratorio_id is not None and horario_id is not None
        tiene_objetos = bool(objetos_solicitados)
        
        if not tiene_laboratorio_horario and not tiene_objetos:
            raise serializers.ValidationError(
                {'general': 'La solicitud debe incluir la asignación de un Laboratorio/Horario O el detalle de Objetos Solicitados, pero no ambos campos vacíos.'}
            )

        # B. Validación de Concurrencia (Solo si Laboratorio/Horario está presente)
        if tiene_laboratorio_horario:
            
            # Revisa que las fechas y horas estén presentes si se asignó un laboratorio/horario.
            fecha_inicio = data.get('Fecha_Inicio', self.instance.Fecha_Inicio if self.instance else None)
            fecha_fin = data.get('Fecha_Fin', self.instance.Fecha_Fin if self.instance else None)
            hora_inicio = data.get('Hora_Inicio', self.instance.Hora_Inicio if self.instance else None)
            hora_fin = data.get('Hora_Fin', self.instance.Hora_Fin if self.instance else None)
            
            if not all([fecha_inicio, fecha_fin, hora_inicio, hora_fin]):
                raise serializers.ValidationError({
                    'Fecha_Inicio': 'Se requieren Fecha_Inicio, Fecha_Fin, Hora_Inicio y Hora_Fin si se asigna Laboratorio/Horario.'
                })
            
            # Buscar conflictos en estado PENDIENTE (1) o APROBADA (2)
            conflictos = Solicitudes.objects.filter(
                Laboratorio_Id=laboratorio_id,
                Fecha_Inicio__lte=fecha_inicio, 
                Fecha_Fin__gte=fecha_inicio, 
                Estado_Id__Estado_Id__in=[1, 2] 
            ).exclude(
                Solicitud_Id=self.instance.Solicitud_Id if self.instance else None 
            ).filter(
                Q(Hora_Inicio__lt=hora_fin) & Q(Hora_Fin__gt=hora_inicio)
            )

            if conflictos.exists():
                raise serializers.ValidationError({
                    "Laboratorio_Id": "El laboratorio ya está reservado o pendiente de aprobación en el horario y fecha solicitados. Conflicto encontrado."
                })

        return data

    # --- MÉTODO CREATE ANIDADO (Transacción Atómica) ---
    @transaction.atomic
    def create(self, validated_data):
        objetos_data = validated_data.pop('objetos_solicitados', [])
        tipo_servicio_id = validated_data.pop('tipo_servicio_id')
        
        user_id = validated_data.pop('usuario_id', None)
        if not user_id and self.context['request'].user.is_authenticated:
            try:
                user_id = self.context['request'].user.perfil_oracle.Usuario_Id
            except AttributeError:
                pass
            
        laboratorio_obj = validated_data.pop('Laboratorio_Id', None)
        horario_obj = validated_data.pop('Horario_Id', None)
        
        validated_data.pop('Estado_Id', None)

        try:
            # 1. Obtener ID de SOLICITUDES usando la secuencia de Oracle
            with connection.cursor() as cursor:
                cursor.execute("SELECT C##_ACCESLAB_USER.SOLICITUDES_SEQ.NEXTVAL FROM DUAL") 
                solicitud_id = cursor.fetchone()[0]

            # 2. Crear la Solicitud Principal
            solicitud = Solicitudes.objects.create(
                Solicitud_Id=solicitud_id, 
                Usuario_Id_id=user_id, 
                Tipo_Servicio_Id_id=tipo_servicio_id, 
                Fecha_solicitud=timezone.localdate(), 
                
                Asignatura=validated_data.get('Asignatura'),
                N_asistentes=validated_data.get('N_asistentes'),
                Fecha_Inicio=validated_data.get('Fecha_Inicio'),
                Fecha_Fin=validated_data.get('Fecha_Fin'),
                Hora_Inicio=validated_data.get('Hora_Inicio'),
                Hora_Fin=validated_data.get('Hora_Fin'),
                Observaciones_Solicitud=validated_data.get('Observaciones_Solicitud'),
                
                Entrega_Id=None, 
                Devolucion_Id=None,
                Estado_Id_id=1, # SIEMPRE INICIA EN PENDIENTE (ID 1)
                
                Laboratorio_Id=laboratorio_obj, 
                Horario_Id=horario_obj,
            )

            # 3. Procesar el Detalle de Objetos y Descontar Inventario
            if objetos_data:
                for detalle_data in objetos_data:
                    objeto_id = detalle_data.pop('objetos_id')
                    cantidad = detalle_data.get('Cantidad_Objetos')
                    
                    # Obtener ID de SOLICITUDES_OBJETOS
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT C##_ACCESLAB_USER.SOLICITUDES_OBJETOS_SEQ.NEXTVAL FROM DUAL") 
                        solicitud_objetos_id = cursor.fetchone()[0]
                    
                    # Crear el Detalle
                    Solicitudes_Objetos.objects.create(
                        Solicitud_Objetos_Id=solicitud_objetos_id,
                        Solicitud_Id=solicitud,
                        Objetos_Id_id=objeto_id, 
                        Cantidad_Objetos=cantidad,
                    )

                    # 4. ACTUALIZAR/DESCONTAR INVENTARIO (Operación Atómica)
                    Objetos.objects.filter(Objetos_Id=objeto_id).update(
                        Cant_Stock=models.F('Cant_Stock') - cantidad 
                    )
                
            return solicitud
        except Exception as e:
            raise serializers.ValidationError({"detail": f"Error transaccional al guardar la solicitud: {e}"})

    # --- MÉTODO UPDATE (Para PATCH de Estado, Laboratorio, Horario) ---
    def update(self, instance, validated_data):
        validated_data.pop('objetos_solicitados', None)
        validated_data.pop('tipo_servicio_id', None)
        validated_data.pop('usuario_id', None)
        
        return super().update(instance, validated_data)


# --- 2B. Serializer para la Solicitud Principal (LECTURA) ---
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
    
    # Programas del Solicitante
    programas_solicitante = serializers.SerializerMethodField()
    
    # INTEGRANTES: Integrantes Asociados (Participantes)
    integrantes_asociados = serializers.SerializerMethodField() 
    
    class Meta:
        model = Solicitudes
        fields = (
            'Solicitud_Id', 'Fecha_solicitud', 'Asignatura', 'N_asistentes', 
            'Usuario_Id', 'Tipo_Servicio_Id', 
            'Fecha_Inicio', 'Fecha_Fin', 'Hora_Inicio', 'Hora_Fin', 
            'Observaciones_Solicitud',
            # Campos de relación (lectura)
            'nombre_solicitante', 'tipo_servicio_nombre', 'estado_nombre', 
            'laboratorio_nombre', 'horario_inicio',
            'objetos_solicitados_detalle',
            # Nuevos campos
            'programas_solicitante', 
            'integrantes_asociados'
        )
        
    def get_nombre_solicitante(self, obj):
        if not obj.Usuario_Id:
            return "Pendiente de Asignación / Anónimo"
        return f"{obj.Usuario_Id.Nombres} {obj.Usuario_Id.Apellido1}"

    def get_horario_inicio(self, obj):
        """Retorna el __str__ del horario si existe, o None."""
        if obj.Horario_Id:
            return str(obj.Horario_Id)
        return None 
    
    def get_programas_solicitante(self, obj):
        """
        Obtiene los Programas Académicos asociados al usuario principal de la solicitud 
        navegando a través de la tabla USUARIOS_PROGRAMAS.
        """
        if not obj.Usuario_Id:
            return []
        
        # Filtra la tabla de asociación Usuarios_Programas por el Usuario_Id
        programas_asociados = Usuarios_Programas.objects.filter(Usuario_Id=obj.Usuario_Id)
        
        # Retorna el ID y el nombre del programa
        return [
            {
                "programa_id": p.Programa_Id_id, 
                "nombre": p.Programa_Id.Nombre_Programa
            }
            for p in programas_asociados
        ]
        
    def get_integrantes_asociados(self, obj):
        """
        Obtiene los Integrantes asociados a la solicitud usando el IntegranteSolicitudSerializer.
        """
        # Filtra la tabla de asociación Integrante_Solicitud por la Solicitud_Id
        integrantes = Integrante_Solicitud.objects.filter(Solicitud_Id=obj)
        # Se usa el serializer simple para el detalle
        return IntegranteSolicitudSimpleSerializer(integrantes, many=True).data


# ----------------------------------------------------------------------
# 3. Serializer para INTEGRANTE_SOLICITUD (Relación N:M)
# ----------------------------------------------------------------------

# SERIALIZER SIMPLE PARA LECTURA ANIDADA (SOLICITUDES_READ)
class IntegranteSolicitudSimpleSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(source='Usuario_Id.Nombres', read_only=True)
    apellido_usuario = serializers.CharField(source='Usuario_Id.Apellido1', read_only=True)
    
    class Meta:
        # Usamos el modelo Integrante_Solicitud
        model = Integrante_Solicitud
        fields = ('Usuario_Id_id', 'nombre_usuario', 'apellido_usuario')

# SERIALIZER COMPLETO PARA ESCRITURA (POST/DELETE del endpoint de Integrantes)
class IntegranteSolicitudSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(write_only=True)
    solicitud_id = serializers.IntegerField(write_only=True)
    
    nombre_usuario = serializers.CharField(source='Usuario_Id.Nombres', read_only=True)
    apellido_usuario = serializers.CharField(source='Usuario_Id.Apellido1', read_only=True)

    class Meta:
        # Usamos el modelo Integrante_Solicitud
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
            raise serializers.ValidationError({"usuario_id": "El Usuario_Id proporcionado no existe."})

        if not Solicitudes.objects.filter(Solicitud_Id=solicitud_id).exists():
            raise serializers.ValidationError({"solicitud_id": "La Solicitud_Id proporcionada no existe."})

        # Validamos contra Integrante_Solicitud
        if Integrante_Solicitud.objects.filter(Usuario_Id_id=usuario_id, Solicitud_Id_id=solicitud_id).exists():
            raise serializers.ValidationError("Este usuario ya está asociado a esta solicitud como integrante.")

        return data

    @transaction.atomic
    def create(self, validated_data):
        usuario_id = validated_data.pop('usuario_id')
        solicitud_id = validated_data.pop('solicitud_id')
        
        SEQUENCE_NAME = 'C##_ACCESLAB_USER.USUARIO_SOLICITUD_SEQ' 
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT {SEQUENCE_NAME}.NEXTVAL FROM DUAL") 
                integrante_solicitud_id = cursor.fetchone()[0]

            # Creamos la instancia en Integrante_Solicitud
            integrante_solicitud = Integrante_Solicitud.objects.create(
                Usuario_Solicitud_Id=integrante_solicitud_id,
                Usuario_Id_id=usuario_id,
                Solicitud_Id_id=solicitud_id
            )
            return integrante_solicitud
        except Exception as e:
            raise serializers.ValidationError({"error": f"Error al guardar la relación de integrante: {e}"})