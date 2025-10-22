# maestros/models.py

from django.db import models

class Roles(models.Model):
    Rol_Id = models.IntegerField(primary_key=True, db_column='ROL_ID')
    Nombre_Roles = models.CharField(max_length=80, db_column='NOMBRE_ROLES')

    class Meta:
        db_table = 'ROLES' 
        managed = False
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
    
    def __str__(self):
        return self.Nombre_Roles

class Frecuencia_Servicio(models.Model):
    Frecuencia_Servicio_Id = models.IntegerField(primary_key=True, db_column='FRECUENCIA_SERVICIO_ID')
    Nombre_Frecuencia_Servicio = models.CharField(max_length=80, db_column='NOMBRE_FRECUENCIA_SERVICIO')

    class Meta:
        db_table = 'FRECUENCIA_SERVICIO'
        managed = False
        
    def __str__(self):
        return self.Nombre_Frecuencia_Servicio

class Entregas(models.Model):
    Entrega_Id = models.IntegerField(primary_key=True, db_column='ENTREGA_ID')
    Fecha_Entrega = models.DateField(db_column='FECHA_ENTREGA')
    # Mapea TIMESTAMP(6) de Oracle
    Hora_Entrega = models.DateTimeField(db_column='HORA_ENTREGA') 
    Observacion_Entrega = models.CharField(max_length=600, db_column='OBSERVACION_ENTREGA')
    
    Frecuencia_Servicio_Id = models.ForeignKey(
        Frecuencia_Servicio, 
        on_delete=models.DO_NOTHING, 
        db_column='FRECUENCIA_SERVICIO_ID'
    )

    class Meta:
        db_table = 'ENTREGAS'
        managed = False
        
    def __str__(self):
        return f'Entrega #{self.Entrega_Id}'
    
class Devoluciones(models.Model):
    Devolucion_Id = models.IntegerField(primary_key=True, db_column='DEVOLUCION_ID')
    Fecha_Devolucion = models.DateField(db_column='FECHA_DEVOLUCION')
    # Mapea TIMESTAMP(6) de Oracle
    Hora_Devolucion = models.DateTimeField(db_column='HORA_DEVOLUCION') 
    Observaciones_Devolucion = models.CharField(max_length=600, db_column='OBSERVACIONES_DEVOLUCION')

    class Meta:
        db_table = 'DEVOLUCIONES'
        managed = False
        
    def __str__(self):
        return f'Devolución #{self.Devolucion_Id}'

class Tipo_Servicio(models.Model):
    Tipo_Servicio_Id = models.IntegerField(primary_key=True, db_column='TIPO_SERVICIO_ID')
    Nombre_Tipo_Servicio = models.CharField(max_length=80, db_column='NOMBRE_TIPO_SERVICIO')

    class Meta:
        db_table = 'TIPO_SERVICIO'
        managed = False
        
    def __str__(self):
        return self.Nombre_Tipo_Servicio

# =======================================================
# NUEVOS MODELOS DE LABORATORIO Y ESTADO
# =======================================================

class Laboratorios(models.Model):
    # La PK es Integer, no AutoField, si ya está creada con IDENTITY o secuencia.
    Laboratorio_Id = models.IntegerField(primary_key=True, db_column='LABORATORIO_ID')
    Nombre_Laboratorio = models.CharField(db_column='NOMBRE_LABORATORIO', max_length=100)
    Capacidad = models.IntegerField(db_column='CAPACIDAD')
    # Tu DDL usa VARCHAR2(250)
    Ubicacion = models.CharField(db_column='UBICACION', max_length=250) 

    class Meta:
        managed = False
        db_table = 'LABORATORIOS'
    
    def __str__(self):
        return self.Nombre_Laboratorio
        
class Horarios_Laboratorio(models.Model):
    # Corregido el nombre de la clase a snake_case para consistencia con tu DDL
    Horario_Id = models.IntegerField(primary_key=True, db_column='HORARIO_ID')
    
    # Clave Foránea a Laboratorios
    Laboratorio_Id = models.ForeignKey(Laboratorios, models.DO_NOTHING, db_column='LABORATORIO_ID') 
    
    Dia_Semana = models.CharField(db_column='DIA_SEMANA', max_length=20) # DDL usa 20
    # CORRECCIÓN: Si Oracle usa TIMESTAMP(6), debes usar DateTimeField, no TimeField
    Hora_Inicio = models.DateTimeField(db_column='HORA_INICIO')
    Hora_Fin = models.DateTimeField(db_column='HORA_FIN')

    class Meta:
        managed = False
        db_table = 'HORARIOS_LABORATORIO'
    
    def __str__(self):
        return f'Horario #{self.Horario_Id} - {self.Dia_Semana}'
        
class Estados(models.Model):
    Estado_Id = models.IntegerField(primary_key=True, db_column='ESTADO_ID')
    # Tu DDL usa VARCHAR2(50), no 80.
    Nombre_Estado = models.CharField(max_length=50, db_column='NOMBRE_ESTADO')
    # DDL no tiene Descripcion. Se elimina si no existe en BD.
    # Descripcion = models.CharField(max_length=250, db_column='DESCRIPCION', null=True, blank=True)

    class Meta:
        db_table = 'ESTADOS'
        managed = False
        
    def __str__(self):
        return self.Nombre_Estado

# =======================================================
# OTROS MODELOS EXISTENTES
# =======================================================

class Tipo_Identificacion(models.Model):
    Tipo_Id = models.IntegerField(primary_key=True, db_column='TIPO_ID')
    Nombre_Tipo_Identificacion = models.CharField(max_length=80, db_column='NOMBRE_TIPO_IDENTIFICACION')
    
    class Meta:
        db_table = 'TIPO_IDENTIFICACION' 
        managed = False
        
    def __str__(self):
        return self.Nombre_Tipo_Identificacion

class Tipo_Solicitantes(models.Model):
    Solicitante_Id = models.IntegerField(primary_key=True, db_column='SOLICITANTE_ID')
    Nombre_Solicitante = models.CharField(max_length=80, db_column='NOMBRE_SOLICITANTE')
    
    class Meta:
        db_table = 'TIPO_SOLICITANTES' 
        managed = False
        
    def __str__(self):
        return self.Nombre_Solicitante

class Facultades(models.Model):
    Facultad_Id = models.IntegerField(primary_key=True, db_column='FACULTAD_ID')
    Nombre_Facultad = models.CharField(max_length=80, db_column='NOMBRE_FACULTAD')

    class Meta:
        db_table = 'FACULTADES'
        managed = False

    def __str__(self):
        return self.Nombre_Facultad

class Programas(models.Model):
    Programa_Id = models.IntegerField(primary_key=True, db_column='PROGRAMA_ID')
    Nombre_Programa = models.CharField(max_length=80, db_column='NOMBRE_PROGRAMA')
    Facultad_Id = models.ForeignKey(
        Facultades, 
        on_delete=models.DO_NOTHING, 
        db_column='FACULTAD_ID'
    )

    class Meta:
        db_table = 'PROGRAMAS'
        managed = False

    def __str__(self):
        return self.Nombre_Programa

class Categorias(models.Model):
    Categoria_Id = models.IntegerField(primary_key=True, db_column='CATEGORIA_ID')
    Nombre_Categoria = models.CharField(max_length=250, db_column='NOMBRE_CATEGORIA')

    class Meta:
        db_table = 'CATEGORIAS'
        managed = False

    def __str__(self):
        return self.Nombre_Categoria

class Objetos(models.Model):
    Objetos_Id = models.IntegerField(primary_key=True, db_column='OBJETOS_ID')
    Nombre_Objetos = models.CharField(max_length=80, db_column='NOMBRE_OBJETOS') 
    
    Categoria_Id = models.ForeignKey(
        Categorias, 
        on_delete=models.DO_NOTHING, 
        db_column='CATEGORIA_ID'
    )
    Descripcion = models.CharField(max_length=250, db_column='DESCRIPCION', null=True, blank=True)
    Cant_Stock = models.IntegerField(db_column='CANT_STOCK', null=True, blank=True) 

    class Meta:
        db_table = 'OBJETOS'
        managed = False

    def __str__(self):
        return self.Nombre_Objetos