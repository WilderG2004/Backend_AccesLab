# reportes/urls.py

from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('kpis/', views.obtener_kpis, name='obtener-kpis'),
    path('actividad-mensual/', views.obtener_actividad_mensual, name='actividad-mensual'),
    path('distribucion-programas/', views.obtener_distribucion_programas, name='distribucion-programas'),
    path('equipos-mas-usados/', views.obtener_equipos_mas_usados, name='equipos-mas-usados'),
    path('historial/', views.obtener_historial, name='historial'),
    
    # === AÑADE ESTA LÍNEA ===
    path('entregas-devoluciones/', views.obtener_entregas_devoluciones, name='entregas-devoluciones'),
    
    path('exportar/', views.exportar_reporte, name='exportar-reporte'),
]