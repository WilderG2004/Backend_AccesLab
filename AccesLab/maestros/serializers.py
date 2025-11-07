from rest_framework import serializers
from .models import (
    Roles, Tipo_Identificacion, Tipo_Solicitantes, Facultades, Programas, 
    Categorias, Objetos, Estados, Frecuencia_Servicio, Entregas, Devoluciones, 
    Tipo_Servicio, Laboratorios, Horarios_Laboratorio
)

# --- Catálogos Simples ---

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'
        read_only_fields = ('Rol_Id',)


class TipoIdentificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Identificacion
        fields = '__all__'
        read_only_fields = ('Tipo_Id',)


class TipoSolicitanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Solicitantes
        fields = '__all__'
        read_only_fields = ('Solicitante_Id',)


class FacultadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facultades
        fields = '__all__'
        read_only_fields = ('Facultad_Id',)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = '__all__'
        read_only_fields = ('Categoria_Id',)


class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estados
        fields = '__all__'
        read_only_fields = ('Estado_Id',)


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_Servicio
        fields = '__all__'
        read_only_fields = ('Tipo_Servicio_Id',)


class FrecuenciaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frecuencia_Servicio
        fields = '__all__'
        read_only_fields = ('Frecuencia_Servicio_Id',)


class LaboratoriosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorios
        fields = '__all__'
        read_only_fields = ('Laboratorio_Id',)


# --- Catálogos con Claves Foráneas (FK) ---

class ProgramaSerializer(serializers.ModelSerializer):
    nombre_facultad = serializers.CharField(source='Facultad_Id.Nombre_Facultad', read_only=True)
    
    class Meta:
        model = Programas
        fields = ('Programa_Id', 'Nombre_Programa', 'Facultad_Id', 'nombre_facultad')
        read_only_fields = ('Programa_Id', 'nombre_facultad')


# ⭐⭐⭐ SERIALIZER DE OBJETOS CON IMAGEN_URL Y ACTIVO ⭐⭐⭐
class ObjetoSerializer(serializers.ModelSerializer):
    nombre_categoria = serializers.CharField(source='Categoria_Id.Nombre_Categoria', read_only=True)
    disponible = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Objetos
        fields = (
            'Objetos_Id', 
            'Nombre_Objetos', 
            'Descripcion', 
            'Cant_Stock', 
            'Categoria_Id', 
            'nombre_categoria',
            'Imagen_Url',  # ⭐ AGREGADO ⭐
            'Activo',      # ⭐ AGREGADO ⭐
            'disponible'   # Propiedad calculada
        )
        read_only_fields = ('Objetos_Id', 'nombre_categoria', 'disponible')


class HorariosLaboratorioSerializer(serializers.ModelSerializer):
    nombre_laboratorio = serializers.CharField(source='Laboratorio_Id.Nombre_Laboratorio', read_only=True)
    
    class Meta:
        model = Horarios_Laboratorio
        fields = ('Horario_Id', 'Laboratorio_Id', 'nombre_laboratorio', 'Dia_Semana', 'Hora_Inicio', 'Hora_Fin')
        read_only_fields = ('Horario_Id', 'nombre_laboratorio')


# --- Modelos de Soporte y Tablas Transaccionales ---

class EntregasSerializer(serializers.ModelSerializer):
    nombre_frecuencia = serializers.CharField(source='Frecuencia_Servicio_Id.Nombre_Frecuencia_Servicio', read_only=True)
    
    class Meta:
        model = Entregas
        fields = '__all__'
        read_only_fields = ('Entrega_Id', 'nombre_frecuencia')


class DevolucionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devoluciones
        fields = '__all__'
        read_only_fields = ('Devolucion_Id',)