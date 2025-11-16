from rest_framework import serializers
from django.db import transaction, models
from datetime import datetime, time
from .models import (
    Roles, Tipo_Identificacion, Tipo_Solicitantes, Facultades, Programas, 
    Categorias, Objetos, Estados, Frecuencia_Servicio, Entregas, Devoluciones, 
    Tipo_Servicio, Laboratorios, Horarios_Laboratorio
)


# ----------------------------------------------------------------------
# UTILIDAD: Generar ID automático
# ----------------------------------------------------------------------
def get_next_id(model_class, id_field_name):
    """
    Obtiene el siguiente ID disponible para un modelo.
    Usa max(id) + 1 para compatibilidad con Oracle e Identity columns.
    """
    max_id = model_class.objects.aggregate(
        max_id=models.Max(id_field_name)
    )['max_id'] or 0
    return max_id + 1


# ----------------------------------------------------------------------
# 🔥 NUEVO: Campo personalizado para convertir Time a DateTime
# ----------------------------------------------------------------------
class TimeToDateTimeField(serializers.DateTimeField):
    """
    Campo personalizado que acepta:
    - DateTime completo: "2025-11-14T14:30:00Z"
    - Solo hora: "14:30:00" o "14:30"
    
    Convierte horas simples a datetime usando la fecha actual.
    """
    def to_internal_value(self, value):
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, time):
            # Convertir time a datetime usando fecha actual
            return datetime.combine(datetime.today(), value)
        
        if isinstance(value, str):
            # Intentar parsear como datetime completo primero
            try:
                return super().to_internal_value(value)
            except serializers.ValidationError:
                # Si falla, intentar parsear como hora simple
                try:
                    # Formatos aceptados: "HH:MM:SS", "HH:MM"
                    if len(value.split(':')) == 2:
                        value += ':00'  # Agregar segundos si no vienen
                    
                    hour, minute, second = map(int, value.split(':'))
                    time_obj = time(hour, minute, second)
                    
                    # Convertir a datetime usando fecha actual
                    return datetime.combine(datetime.today(), time_obj)
                except (ValueError, AttributeError):
                    raise serializers.ValidationError(
                        'Formato de hora inválido. Use "HH:MM:SS" o "YYYY-MM-DDTHH:MM:SS"'
                    )
        
        raise serializers.ValidationError(
            'Tipo de dato inválido para hora. Proporcione una cadena de texto.'
        )


# ----------------------------------------------------------------------
# SERIALIZERS DE CATÁLOGOS SIMPLES (Con auto-generación de ID)
# ----------------------------------------------------------------------

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'
        read_only_fields = ('Rol_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Rol_Id' not in validated_data or validated_data['Rol_Id'] is None:
            validated_data['Rol_Id'] = get_next_id(Roles, 'Rol_Id')
        return Roles.objects.create(**validated_data)


class TipoIdentificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Identificacion
        fields = '__all__'
        read_only_fields = ('Tipo_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Tipo_Id' not in validated_data or validated_data['Tipo_Id'] is None:
            validated_data['Tipo_Id'] = get_next_id(Tipo_Identificacion, 'Tipo_Id')
        return Tipo_Identificacion.objects.create(**validated_data)


class TipoSolicitanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Solicitantes
        fields = '__all__'
        read_only_fields = ('Solicitante_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Solicitante_Id' not in validated_data or validated_data['Solicitante_Id'] is None:
            validated_data['Solicitante_Id'] = get_next_id(Tipo_Solicitantes, 'Solicitante_Id')
        return Tipo_Solicitantes.objects.create(**validated_data)


class FacultadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facultades
        fields = '__all__'
        read_only_fields = ('Facultad_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Facultad_Id' not in validated_data or validated_data['Facultad_Id'] is None:
            validated_data['Facultad_Id'] = get_next_id(Facultades, 'Facultad_Id')
        return Facultades.objects.create(**validated_data)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = '__all__'
        read_only_fields = ('Categoria_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Categoria_Id' not in validated_data or validated_data['Categoria_Id'] is None:
            validated_data['Categoria_Id'] = get_next_id(Categorias, 'Categoria_Id')
        return Categorias.objects.create(**validated_data)


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estados
        fields = '__all__'
        read_only_fields = ('Estado_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Estado_Id' not in validated_data or validated_data['Estado_Id'] is None:
            validated_data['Estado_Id'] = get_next_id(Estados, 'Estado_Id')
        return Estados.objects.create(**validated_data)


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Servicio
        fields = '__all__'
        read_only_fields = ('Tipo_Servicio_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Tipo_Servicio_Id' not in validated_data or validated_data['Tipo_Servicio_Id'] is None:
            validated_data['Tipo_Servicio_Id'] = get_next_id(Tipo_Servicio, 'Tipo_Servicio_Id')
        return Tipo_Servicio.objects.create(**validated_data)


class FrecuenciaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frecuencia_Servicio
        fields = '__all__'
        read_only_fields = ('Frecuencia_Servicio_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Frecuencia_Servicio_Id' not in validated_data or validated_data['Frecuencia_Servicio_Id'] is None:
            validated_data['Frecuencia_Servicio_Id'] = get_next_id(Frecuencia_Servicio, 'Frecuencia_Servicio_Id')
        return Frecuencia_Servicio.objects.create(**validated_data)


class LaboratoriosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorios
        fields = '__all__'
        read_only_fields = ('Laboratorio_Id',)

    @transaction.atomic
    def create(self, validated_data):
        if 'Laboratorio_Id' not in validated_data or validated_data['Laboratorio_Id'] is None:
            validated_data['Laboratorio_Id'] = get_next_id(Laboratorios, 'Laboratorio_Id')
        return Laboratorios.objects.create(**validated_data)


# ----------------------------------------------------------------------
# SERIALIZERS CON RELACIONES FK (Creación Flexible)
# ----------------------------------------------------------------------

class ProgramaSerializer(serializers.ModelSerializer):
    # Campos para lectura
    nombre_facultad = serializers.CharField(source='Facultad_Id.Nombre_Facultad', read_only=True)
    
    # Campos para escritura flexible
    facultad_id = serializers.IntegerField(write_only=True, required=False)
    facultad_nombre = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Programas
        fields = (
            'Programa_Id', 'Nombre_Programa', 
            'Facultad_Id', 'nombre_facultad',
            'facultad_id', 'facultad_nombre'
        )
        read_only_fields = ('Programa_Id', 'nombre_facultad')

    def validate(self, data):
        """Validar que se proporcione facultad_id O facultad_nombre."""
        facultad_id = data.get('facultad_id')
        facultad_nombre = data.get('facultad_nombre')
        
        # Si se está actualizando y no se proporciona ninguno, está OK
        if self.instance and not facultad_id and not facultad_nombre:
            return data
            
        # Para creación, al menos uno debe existir
        if not self.instance and not facultad_id and not facultad_nombre:
            raise serializers.ValidationError({
                'facultad': 'Debe proporcionar facultad_id o facultad_nombre.'
            })
        
        return data

    def _get_or_create_facultad(self, validated_data):
        """Obtiene o crea la facultad."""
        facultad_id = validated_data.pop('facultad_id', None)
        facultad_nombre = validated_data.pop('facultad_nombre', None)
        
        if facultad_id:
            try:
                return Facultades.objects.get(Facultad_Id=facultad_id)
            except Facultades.DoesNotExist:
                if not facultad_nombre:
                    raise serializers.ValidationError({
                        'facultad_id': f'No existe una facultad con ID {facultad_id}'
                    })
        
        if facultad_nombre:
            facultad, created = Facultades.objects.get_or_create(
                Nombre_Facultad=facultad_nombre,
                defaults={
                    'Facultad_Id': get_next_id(Facultades, 'Facultad_Id')
                }
            )
            return facultad
        
        return None

    @transaction.atomic
    def create(self, validated_data):
        facultad = self._get_or_create_facultad(validated_data)
        
        if 'Programa_Id' not in validated_data or validated_data['Programa_Id'] is None:
            validated_data['Programa_Id'] = get_next_id(Programas, 'Programa_Id')
        
        return Programas.objects.create(
            Facultad_Id=facultad,
            **validated_data
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'facultad_id' in validated_data or 'facultad_nombre' in validated_data:
            facultad = self._get_or_create_facultad(validated_data)
            instance.Facultad_Id = facultad
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# 🔥🔥 OBJETO SERIALIZER CORREGIDO 🔥🔥
class ObjetoSerializer(serializers.ModelSerializer):
    # Campos para lectura
    nombre_categoria = serializers.CharField(source='Categoria_Id.Nombre_Categoria', read_only=True)
    disponible = serializers.BooleanField(read_only=True)
    
    # 🔥 Campos para escritura flexible
    categoria_id = serializers.IntegerField(write_only=True, required=False)
    categoria_nombre = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Objetos
        fields = (
            'Objetos_Id', 
            'Nombre_Objetos', 
            'Descripcion', 
            'Cant_Stock', 
            'Categoria_Id',  # Campo del modelo (solo lectura)
            'nombre_categoria',
            'categoria_id',  # Campo para enviar ID existente
            'categoria_nombre',  # Campo para crear nueva categoría
            'Imagen_Url',
            'Activo',
            'disponible'
        )
        read_only_fields = ('Objetos_Id', 'nombre_categoria', 'disponible', 'Categoria_Id')  # 🔥 AGREGADO Categoria_Id aquí
        
        # 🔥 ALTERNATIVA: Usar extra_kwargs
        extra_kwargs = {
            'Categoria_Id': {'read_only': True, 'required': False}  # Ignorar en POST/PATCH
        }

    def validate(self, data):
        """Validar que se proporcione categoria_id O categoria_nombre."""
        categoria_id = data.get('categoria_id')
        categoria_nombre = data.get('categoria_nombre')
        
        print(f"🔍 Validando Objeto:")
        print(f"   - categoria_id: {categoria_id}")
        print(f"   - categoria_nombre: {categoria_nombre}")
        print(f"   - Es actualización: {self.instance is not None}")
        
        # Si se está actualizando y no se proporciona ninguno, está OK
        if self.instance and not categoria_id and not categoria_nombre:
            return data
            
        # Para creación, al menos uno debe existir
        if not self.instance and not categoria_id and not categoria_nombre:
            raise serializers.ValidationError({
                'categoria': 'Debe proporcionar categoria_id o categoria_nombre para crear el objeto.'
            })
        
        # Validar stock no negativo
        cant_stock = data.get('Cant_Stock')
        if cant_stock is not None and cant_stock < 0:
            raise serializers.ValidationError({
                'Cant_Stock': 'El stock no puede ser negativo.'
            })
        
        return data

    def _get_or_create_categoria(self, validated_data):
        """Obtiene o crea la categoría."""
        categoria_id = validated_data.pop('categoria_id', None)
        categoria_nombre = validated_data.pop('categoria_nombre', None)
        
        print(f"🔍 _get_or_create_categoria:")
        print(f"   - categoria_id: {categoria_id}")
        print(f"   - categoria_nombre: {categoria_nombre}")
        
        if categoria_id:
            try:
                categoria = Categorias.objects.get(Categoria_Id=categoria_id)
                print(f"   ✅ Categoría encontrada: {categoria.Nombre_Categoria}")
                return categoria
            except Categorias.DoesNotExist:
                if not categoria_nombre:
                    raise serializers.ValidationError({
                        'categoria_id': f'No existe una categoría con ID {categoria_id}'
                    })
                print(f"   ⚠️ Categoría {categoria_id} no existe, intentando crear con nombre...")
        
        if categoria_nombre:
            categoria, created = Categorias.objects.get_or_create(
                Nombre_Categoria=categoria_nombre,
                defaults={
                    'Categoria_Id': get_next_id(Categorias, 'Categoria_Id')
                }
            )
            if created:
                print(f"   ✅ Categoría CREADA: {categoria.Nombre_Categoria} (ID: {categoria.Categoria_Id})")
            else:
                print(f"   ✅ Categoría existente encontrada: {categoria.Nombre_Categoria}")
            return categoria
        
        return None

    @transaction.atomic
    def create(self, validated_data):
        print(f"🔧 CREATE Objeto - validated_data: {validated_data}")
        
        categoria = self._get_or_create_categoria(validated_data)
        
        if 'Objetos_Id' not in validated_data or validated_data['Objetos_Id'] is None:
            validated_data['Objetos_Id'] = get_next_id(Objetos, 'Objetos_Id')
        
        # Valores por defecto
        if 'Activo' not in validated_data:
            validated_data['Activo'] = True
        if 'Cant_Stock' not in validated_data:
            validated_data['Cant_Stock'] = 0
        
        objeto = Objetos.objects.create(
            Categoria_Id=categoria,
            **validated_data
        )
        
        print(f"✅ Objeto creado: {objeto.Nombre_Objetos} (ID: {objeto.Objetos_Id})")
        return objeto

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'categoria_id' in validated_data or 'categoria_nombre' in validated_data:
            categoria = self._get_or_create_categoria(validated_data)
            instance.Categoria_Id = categoria
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# 🔥🔥 HORARIOS SERIALIZER CORREGIDO 🔥🔥
class HorariosLaboratorioSerializer(serializers.ModelSerializer):
    # Campos para lectura
    nombre_laboratorio = serializers.CharField(source='Laboratorio_Id.Nombre_Laboratorio', read_only=True)
    
    # Campos para escritura flexible (Laboratorio)
    laboratorio_id = serializers.IntegerField(write_only=True, required=False)
    laboratorio_nombre = serializers.CharField(write_only=True, required=False)

    # 🔥 CORRECCIÓN: Usar el campo personalizado para aceptar horas simples
    Hora_Inicio = TimeToDateTimeField()
    Hora_Fin = TimeToDateTimeField()
    
    class Meta:
        model = Horarios_Laboratorio
        fields = (
            'Horario_Id', 
            'Laboratorio_Id', 
            'nombre_laboratorio',
            'laboratorio_id',
            'laboratorio_nombre',
            'Dia_Semana', 
            'Hora_Inicio', 
            'Hora_Fin'
        )
        read_only_fields = ('Horario_Id', 'nombre_laboratorio')

    def validate(self, data):
        """Validar horarios y laboratorio."""
        laboratorio_id = data.get('laboratorio_id')
        laboratorio_nombre = data.get('laboratorio_nombre')
        
        print(f"🔍 Validando Horario:")
        print(f"   - laboratorio_id: {laboratorio_id}")
        print(f"   - laboratorio_nombre: {laboratorio_nombre}")
        print(f"   - Hora_Inicio: {data.get('Hora_Inicio')}")
        print(f"   - Hora_Fin: {data.get('Hora_Fin')}")
        
        # Si se está actualizando y no se proporciona ninguno, está OK
        if self.instance and not laboratorio_id and not laboratorio_nombre:
            pass
        elif not self.instance and not laboratorio_id and not laboratorio_nombre:
            raise serializers.ValidationError({
                'laboratorio': 'Debe proporcionar laboratorio_id o laboratorio_nombre.'
            })
        
        # Validar que Hora_Fin sea posterior a Hora_Inicio
        hora_inicio = data.get('Hora_Inicio')
        hora_fin = data.get('Hora_Fin')
        
        if hora_inicio and hora_fin:
            # Comparar solo las horas (ignorar fechas)
            if hora_inicio.time() >= hora_fin.time():
                raise serializers.ValidationError({
                    'Hora_Fin': 'La hora de fin debe ser posterior a la hora de inicio.'
                })
        
        return data

    def _get_or_create_laboratorio(self, validated_data):
        """Obtiene o crea el laboratorio."""
        laboratorio_id = validated_data.pop('laboratorio_id', None)
        laboratorio_nombre = validated_data.pop('laboratorio_nombre', None)
        
        if laboratorio_id:
            try:
                return Laboratorios.objects.get(Laboratorio_Id=laboratorio_id)
            except Laboratorios.DoesNotExist:
                if not laboratorio_nombre:
                    raise serializers.ValidationError({
                        'laboratorio_id': f'No existe un laboratorio con ID {laboratorio_id}'
                    })
        
        if laboratorio_nombre:
            laboratorio, created = Laboratorios.objects.get_or_create(
                Nombre_Laboratorio=laboratorio_nombre,
                defaults={
                    'Laboratorio_Id': get_next_id(Laboratorios, 'Laboratorio_Id'),
                    'Capacidad': 20,  # Valor por defecto
                    'Ubicacion': 'Por definir'  # Valor por defecto
                }
            )
            return laboratorio
        
        return None

    @transaction.atomic
    def create(self, validated_data):
        print(f"🔧 CREATE Horario - validated_data: {validated_data}")
        
        laboratorio = self._get_or_create_laboratorio(validated_data)
        
        if 'Horario_Id' not in validated_data or validated_data['Horario_Id'] is None:
            validated_data['Horario_Id'] = get_next_id(Horarios_Laboratorio, 'Horario_Id')
        
        horario = Horarios_Laboratorio.objects.create(
            Laboratorio_Id=laboratorio,
            **validated_data
        )
        
        print(f"✅ Horario creado: ID {horario.Horario_Id}")
        return horario

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'laboratorio_id' in validated_data or 'laboratorio_nombre' in validated_data:
            laboratorio = self._get_or_create_laboratorio(validated_data)
            instance.Laboratorio_Id = laboratorio
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class EntregasSerializer(serializers.ModelSerializer):
    # Campos para lectura
    nombre_frecuencia = serializers.CharField(source='Frecuencia_Servicio_Id.Nombre_Frecuencia_Servicio', read_only=True)
    
    # Campos para escritura flexible
    frecuencia_id = serializers.IntegerField(write_only=True, required=False)
    frecuencia_nombre = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Entregas
        fields = '__all__'
        extra_kwargs = {
            'Entrega_Id': {'read_only': True},
        }

    def validate(self, data):
        """Validar que se proporcione frecuencia_id O frecuencia_nombre."""
        frecuencia_id = data.get('frecuencia_id')
        frecuencia_nombre = data.get('frecuencia_nombre')
        
        # Si se está actualizando y no se proporciona ninguno, está OK
        if self.instance and not frecuencia_id and not frecuencia_nombre:
            return data
            
        # Para creación, al menos uno debe existir
        if not self.instance and not frecuencia_id and not frecuencia_nombre:
            raise serializers.ValidationError({
                'frecuencia': 'Debe proporcionar frecuencia_id o frecuencia_nombre.'
            })
        
        return data

    def _get_or_create_frecuencia(self, validated_data):
        """Obtiene o crea la frecuencia de servicio."""
        frecuencia_id = validated_data.pop('frecuencia_id', None)
        frecuencia_nombre = validated_data.pop('frecuencia_nombre', None)
        
        if frecuencia_id:
            try:
                return Frecuencia_Servicio.objects.get(Frecuencia_Servicio_Id=frecuencia_id)
            except Frecuencia_Servicio.DoesNotExist:
                if not frecuencia_nombre:
                    raise serializers.ValidationError({
                        'frecuencia_id': f'No existe una frecuencia con ID {frecuencia_id}'
                    })
        
        if frecuencia_nombre:
            frecuencia, created = Frecuencia_Servicio.objects.get_or_create(
                Nombre_Frecuencia_Servicio=frecuencia_nombre,
                defaults={
                    'Frecuencia_Servicio_Id': get_next_id(Frecuencia_Servicio, 'Frecuencia_Servicio_Id')
                }
            )
            return frecuencia
        
        return None

    @transaction.atomic
    def create(self, validated_data):
        frecuencia = self._get_or_create_frecuencia(validated_data)
        
        if 'Entrega_Id' not in validated_data or validated_data['Entrega_Id'] is None:
            validated_data['Entrega_Id'] = get_next_id(Entregas, 'Entrega_Id')
        
        return Entregas.objects.create(
            Frecuencia_Servicio_Id=frecuencia,
            **validated_data
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'frecuencia_id' in validated_data or 'frecuencia_nombre' in validated_data:
            frecuencia = self._get_or_create_frecuencia(validated_data)
            instance.Frecuencia_Servicio_Id = frecuencia
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class DevolucionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devoluciones
        fields = '__all__'
        read_only_fields = ('Devolucion_Id',)
    
    @transaction.atomic
    def create(self, validated_data):
        if 'Devolucion_Id' not in validated_data or validated_data['Devolucion_Id'] is None:
            validated_data['Devolucion_Id'] = get_next_id(Devoluciones, 'Devolucion_Id')
        return Devoluciones.objects.create(**validated_data)