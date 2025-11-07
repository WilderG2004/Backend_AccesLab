# maestros/admin.py

from django.contrib import admin
from .models import (
    Roles, Frecuencia_Servicio, Entregas, Devoluciones, 
    Tipo_Servicio, Laboratorios, Tipo_Identificacion, 
    Tipo_Solicitantes, Facultades, Programas, 
    Categorias, Objetos, Estados, Horarios_Laboratorio
)

@admin.register(Objetos)
class ObjetosAdmin(admin.ModelAdmin):
    list_display = [
        'Objetos_Id',
        'Nombre_Objetos',
        'Categoria_Id',
        'Cant_Stock',
        'Activo',  # ⭐ AGREGADO ⭐
        'disponible'
    ]
    list_filter = ['Categoria_Id', 'Activo']  # ⭐ AGREGADO FILTRO ⭐
    search_fields = ['Nombre_Objetos', 'Descripcion']
    list_editable = ['Activo']  # Permite editar desde la lista
    fieldsets = (
        ('Información Básica', {
            'fields': ('Nombre_Objetos', 'Descripcion', 'Categoria_Id')
        }),
        ('Inventario', {
            'fields': ('Cant_Stock', 'Activo')  # ⭐ AGREGADO ⭐
        }),
        ('Multimedia', {
            'fields': ('Imagen_Url',)  # ⭐ AGREGADO ⭐
        }),
    )
    
    def disponible(self, obj):
        return obj.disponible
    disponible.boolean = True
    disponible.short_description = 'Disponible'


# Registra los demás modelos (opcional)
admin.site.register(Roles)
admin.site.register(Categorias)
admin.site.register(Facultades)
admin.site.register(Programas)
admin.site.register(Estados)
admin.site.register(Laboratorios)
admin.site.register(Horarios_Laboratorio)
admin.site.register(Tipo_Servicio)
admin.site.register(Tipo_Identificacion)
admin.site.register(Tipo_Solicitantes)
admin.site.register(Frecuencia_Servicio)
admin.site.register(Entregas)
admin.site.register(Devoluciones)