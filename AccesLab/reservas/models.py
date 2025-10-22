# reservas/models.py

from django.db import models
# Asegúrate de que esta importación sea correcta si 'Usuarios' está en otra app
from usuarios.models import Usuarios 
from maestros.models import (
    Tipo_Servicio, 
    Entregas, 
    Devoluciones, 
    Objetos,
    # === NUEVAS IMPORTACIONES DE CATÁLOGO ===
    Estados, 
    Laboratorios, 
    Horarios_Laboratorio
    # =======================================
)

# ----------------------------------------------------------------------
# 1. Solicitudes (Tabla Principal) - INCLUYE CAMPOS DE TIEMPO AÑADIDOS ⏳
# ----------------------------------------------------------------------

class Solicitudes(models.Model):
    Solicitud_Id = models.AutoField(primary_key=True, db_column='SOLICITUD_ID')
    
    # Columnas de negocio de tu DDL
    Fecha_solicitud = models.DateField(db_column='FECHA_SOLICITUD')
    Asignatura = models.CharField(max_length=100, db_column='ASIGNATURA') 
    N_asistentes = models.IntegerField(db_column='N_ASISTENTES') 
    
    # 🟢 CAMPOS AÑADIDOS (Necesarios para la Reserva de Laboratorio)
    Fecha_Inicio = models.DateField(db_column='FECHA_INICIO', null=True, blank=True)
    Fecha_Fin = models.DateField(db_column='FECHA_FIN', null=True, blank=True)
    # NOTA: Se asume que estos campos son DATEFIELD y TIMEFIELD, pero se dejan como DATETIMEFIELD si tu DB lo requiere
    Hora_Inicio = models.DateTimeField(db_column='HORA_INICIO', null=True, blank=True)
    Hora_Fin = models.DateTimeField(db_column='HORA_FIN', null=True, blank=True)
    Observaciones_Solicitud = models.TextField(db_column='OBSERVACIONES_SOLICITUD', null=True, blank=True)
    # --------------------------------------------------------------------
    
    # FKs de tu DDL
    Usuario_Id = models.ForeignKey(
        Usuarios, 
        on_delete=models.DO_NOTHING, 
        db_column='USUARIO_ID',
        verbose_name="Usuario Solicitante",
        related_name='solicitudes_creadas'
    )
    Tipo_Servicio_Id = models.ForeignKey(
        Tipo_Servicio, 
        on_delete=models.DO_NOTHING, 
        db_column='TIPO_SERVICIO_ID'
    )
    Entrega_Id = models.ForeignKey(
        Entregas, 
        on_delete=models.DO_NOTHING, 
        db_column='ENTREGA_ID',
        null=True, blank=True
    )
    Devolucion_Id = models.ForeignKey(
        Devoluciones, 
        on_delete=models.DO_NOTHING, 
        db_column='DEVOLUCION_ID',
        null=True, blank=True
    )
    
    # === CLAVES FORÁNEAS (PARA GESTIÓN Y RESERVA) ===
    Estado_Id = models.ForeignKey(
        Estados, 
        on_delete=models.DO_NOTHING, 
        db_column='ESTADO_ID',
        default=1 # Asume que el ID 1 es 'Pendiente'
    )
    Laboratorio_Id = models.ForeignKey(
        Laboratorios, 
        on_delete=models.DO_NOTHING, 
        db_column='LABORATORIO_ID',
        null=True, blank=True # Nullable si la solicitud no es de laboratorio
    )
    Horario_Id = models.ForeignKey(
        Horarios_Laboratorio, 
        on_delete=models.DO_NOTHING, 
        db_column='HORARIO_ID',
        null=True, blank=True # Nullable si la solicitud no es de laboratorio
    )
    # =======================================================

    class Meta:
        db_table = 'SOLICITUDES'
        managed = False
        verbose_name_plural = "Solicitudes de Servicio/Objeto"

    def __str__(self):
        return f'Solicitud #{self.Solicitud_Id} - {self.Asignatura}'

# ----------------------------------------------------------------------
# 2. Solicitudes_Objetos (Tabla de Detalle N:M con atributos)
# ----------------------------------------------------------------------

class Solicitudes_Objetos(models.Model):
    Solicitud_Objetos_Id = models.AutoField(primary_key=True, db_column='SOLICITUD_OBJETOS_ID')
    
    Cantidad_Objetos = models.IntegerField(db_column='CANTIDAD_OBJETOS')
    
    # FKs
    Objetos_Id = models.ForeignKey(
        Objetos, 
        on_delete=models.DO_NOTHING, 
        db_column='OBJETOS_ID'
    )
    Solicitud_Id = models.ForeignKey(
        Solicitudes, 
        on_delete=models.CASCADE, 
        db_column='SOLICITUD_ID',
        related_name='solicitudes_objetos_set' # Añadido para mejor navegación desde Solicitudes
    )

    class Meta:
        db_table = 'SOLICITUDES_OBJETOS' 
        managed = False
        verbose_name_plural = "Objetos Solicitados"
        
    def __str__(self):
        return f'Detalle Objeto #{self.Solicitud_Objetos_Id}'
        
# ----------------------------------------------------------------------
# 3. Solicitudes_Detalle (Tabla de detalle general, si se usa)
# ----------------------------------------------------------------------

class Solicitudes_Detalle(models.Model):
    Detalle_Id = models.AutoField(primary_key=True, db_column='DETALLE_ID')
    
    Solicitud_Id = models.ForeignKey(
        Solicitudes, 
        on_delete=models.CASCADE, 
        db_column='SOLICITUD_ID'
    )
    Nombre_Detalle = models.CharField(max_length=100, db_column='NOMBRE_DETALLE')
    Valor = models.CharField(max_length=400, db_column='VALOR')
    
    class Meta:
        db_table = 'SOLICITUDES_DETALLE' 
        managed = False
        verbose_name_plural = "Detalles de Solicitud"
        
# ----------------------------------------------------------------------
# 4. Integrantes_Solicitud (IGNORADO/ELIMINADO por redundancia)
# ----------------------------------------------------------------------
# NOTA: Se recomienda eliminar esta clase si es redundante con el modelo #5

# class Integrantes_Solicitud(models.Model):
#     ... (cuerpo del modelo) ...

        
# ----------------------------------------------------------------------
# 5. Integrante_Solicitud (MODELO FINAL DE ASOCIACIÓN USUARIO-SOLICITUD)
# ----------------------------------------------------------------------

class Integrante_Solicitud(models.Model):
    # Se utiliza el campo del DDL que tiene la secuencia (USUARIO_SOLICITUD_ID)
    Usuario_Solicitud_Id = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        primary_key=True, 
        db_column='USUARIO_SOLICITUD_ID'
    ) 

    Usuario_Id = models.ForeignKey(
        Usuarios, 
        on_delete=models.CASCADE, 
        db_column='USUARIO_ID',
        related_name='solicitudes_participadas' # Nombre usado en Serializers/Views
    )
    Solicitud_Id = models.ForeignKey(
        Solicitudes, 
        on_delete=models.CASCADE, 
        db_column='SOLICITUD_ID',
        # Nombre usado en Views.py para el prefetch_related
        related_name='usuarios_asociados' 
    )

    class Meta:
        # Mantenemos el nombre de la tabla DB original (USUARIO_SOLICITUD)
        db_table = 'USUARIO_SOLICITUD'
        unique_together = (('Usuario_Id', 'Solicitud_Id'),)
        managed = False
        verbose_name_plural = "Integrantes de Solicitud"