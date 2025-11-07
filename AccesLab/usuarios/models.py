from django.db import models
from django.contrib.auth.models import User
# Asegúrate de que los modelos de 'maestros' estén en el path correcto
from maestros.models import Roles, Tipo_Identificacion, Tipo_Solicitantes, Objetos, Programas 
import logging 
logger = logging.getLogger(__name__) 

# -------------------------------------------------------------------
# --- CLASE DE UNIÓN (USUARIOS_ROLES) ---
# -------------------------------------------------------------------
class Usuarios_Roles(models.Model):
    Usuario_Id = models.ForeignKey(
        'Usuarios', 
        on_delete=models.CASCADE, 
        db_column='USUARIO_ID',
        related_name='roles_usuario_detalle', 
        primary_key=True 
    )
    Rol_Id = models.ForeignKey(
        Roles, 
        on_delete=models.CASCADE, 
        db_column='ROL_ID',
    )

    class Meta:
        db_table = 'USUARIOS_ROLES'
        managed = False
        unique_together = (('Usuario_Id', 'Rol_Id'),) 
        verbose_name = "Rol de Usuario (Oracle)"
        verbose_name_plural = "Roles de Usuarios (Oracle)"
        
    def __str__(self):
        return f'Usuario {self.Usuario_Id.Usuario_Id} - Rol: {self.Rol_Id.Nombre_Roles}'


# -------------------------------------------------------------------
# --- MODELO DE ASOCIACIÓN PARA PROGRAMAS ---
# -------------------------------------------------------------------
class Usuarios_Programas(models.Model):
    Usuario_Id = models.ForeignKey(
        'Usuarios', 
        models.DO_NOTHING, 
        db_column='USUARIO_ID',
        related_name='programas_asociados',
        primary_key=True
    )
    Programa_Id = models.ForeignKey(
        Programas, 
        models.DO_NOTHING, 
        db_column='PROGRAMA_ID'
    )
    
    class Meta:
        managed = False
        db_table = 'USUARIOS_PROGRAMAS'
        unique_together = (('Usuario_Id', 'Programa_Id'),) 
        verbose_name = "Programa de Usuario (Oracle)"
        verbose_name_plural = "Programas de Usuarios (Oracle)"
        
    def __str__(self):
        return f'Usuario {self.Usuario_Id.Usuario_Id} asociado al Programa {self.Programa_Id.Programa_Id}'


# -------------------------------------------------------------------
# --- CLASE DE PERFIL (USUARIOS) - ⭐ CAMPO CAMPUS AGREGADO ⭐ ---
# -------------------------------------------------------------------
class Usuarios(models.Model):
    Usuario_Id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='USUARIO_ID',
        related_name='perfil_oracle' 
    )
    
    Tipo_Id = models.ForeignKey(
        Tipo_Identificacion,
        on_delete=models.DO_NOTHING,
        db_column='TIPO_ID',
    )
    Solicitante_Id = models.ForeignKey(
        Tipo_Solicitantes,
        on_delete=models.DO_NOTHING,
        db_column='SOLICITANTE_ID',
        null=True, blank=True 
    )

    Roles = models.ManyToManyField(
        Roles,
        through=Usuarios_Roles,
        related_name='usuarios_con_rol'
    )
    
    Programas = models.ManyToManyField(
        Programas,
        through=Usuarios_Programas,
        related_name='usuarios_en_programa'
    )
    
    Nombres = models.CharField(max_length=100, db_column='NOMBRES')
    Apellido1 = models.CharField(max_length=50, db_column='APELLIDO1')
    Apellido2 = models.CharField(max_length=50, db_column='APELLIDO2', null=True, blank=True)
    Correo_electronico = models.CharField(max_length=250, db_column='CORREO_ELECTRONICO', null=True, blank=True)
    Direccion = models.CharField(max_length=250, db_column='DIRECCION', null=True, blank=True)
    Telefono = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, db_column='TELEFONO')
    Numero_celular = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, db_column='NUMERO_CELULAR')
    

    Campus = models.CharField(
        max_length=100, 
        db_column='CAMPUS', 
        null=True, 
        blank=True,
        help_text='Campus al que pertenece el usuario'
    )

    class Meta:
        db_table = 'USUARIOS' 
        managed = False
        verbose_name = "Perfil de Usuario (Oracle)"
        verbose_name_plural = "Perfiles de Usuarios (Oracle)"
    
    def __str__(self):
        return f'{self.Nombres} {self.Apellido1} ({self.Usuario_Id.username})'
    
    @property
    def is_admin(self):
        try:
            es_admin = Usuarios_Roles.objects.filter(
                Usuario_Id__Usuario_Id=self.pk, 
                Rol_Id__Rol_Id=1 
            ).exists()
            
            logger.debug(f"ROL CHECK: Usuario ID {self.pk}. ¿Es ADMIN? {es_admin}")
            return es_admin
            
        except Exception as e:
            logger.error(f"FALLO CRÍTICO EN VERIFICACIÓN DE ROL para usuario ID {self.pk}: {e}")
            return False