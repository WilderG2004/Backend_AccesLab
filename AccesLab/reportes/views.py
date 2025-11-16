# ==============================================================================
# REPORTES/VIEWS.PY - Optimizado con Mejor Manejo de Errores
# ==============================================================================

# Imports de Django y DRF
from django.db.models import Count, Sum, Q, F, Max, Avg, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Imports de tus Modelos
from maestros.models import Objetos, Estados
from usuarios.models import Usuarios
from reservas.models import Solicitudes, Solicitudes_Objetos


# ==============================================================================
# VISTA 1: KPIs GENERALES
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_kpis(request):
    """
    KPIs principales del sistema:
    - Usuarios activos (últimos 30 días)
    - Préstamos activos (Estado_Id = 2)
    - Reservas esta semana
    - Equipos fuera de servicio (Activo = False)
    """
    try:
        hoy = timezone.now().date()
        hace_30_dias = hoy - timedelta(days=30)
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        
        # Usuarios activos
        usuarios_activos = Usuarios.objects.filter(
            solicitudes_creadas__Fecha_solicitud__gte=hace_30_dias
        ).distinct().count()
        
        # Préstamos activos (Estado APROBADA = 2)
        prestamos_activos = Solicitudes.objects.filter(Estado_Id=2).count()
        
        # Reservas esta semana
        reservas_semana = Solicitudes.objects.filter(
            Fecha_solicitud__gte=inicio_semana,
            Fecha_solicitud__lte=hoy
        ).count()
        
        # Equipos fuera de servicio
        equipos_fuera_servicio = Objetos.objects.filter(Activo=False).count()
        
        # Comparación con mes anterior
        hace_60_dias = hoy - timedelta(days=60)
        usuarios_mes_anterior = Usuarios.objects.filter(
            solicitudes_creadas__Fecha_solicitud__gte=hace_60_dias,
            solicitudes_creadas__Fecha_solicitud__lt=hace_30_dias
        ).distinct().count()
        
        # Calcular diferencia porcentual
        comparacion = "Sin datos del mes anterior"
        if usuarios_mes_anterior > 0:
            diferencia = ((usuarios_activos - usuarios_mes_anterior) / usuarios_mes_anterior) * 100
            comparacion = f"{'+' if diferencia > 0 else ''}{diferencia:.1f}% vs mes anterior"
        elif usuarios_activos > 0:
            comparacion = "Primeros datos del sistema"
        
        return Response({
            'usuarios_activos': usuarios_activos,
            'prestamos_activos': prestamos_activos,
            'reservas_semana': reservas_semana,
            'equipos_fuera_servicio': equipos_fuera_servicio,
            'comparacion_mes_anterior': comparacion
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error al obtener KPIs: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# VISTA 2: ACTIVIDAD MENSUAL
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_actividad_mensual(request):
    """
    Actividad de los últimos N meses:
    - Reservas por mes (Tipo_Servicio_Id = 21)
    - Préstamos por mes (Tipo_Servicio_Id = 1)
    """
    try:
        meses = int(request.GET.get('meses', 6))
        fecha_inicio = timezone.now().date() - timedelta(days=meses * 30)
        
        # Agrupar por mes y tipo de servicio
        actividad_mensual = Solicitudes.objects.filter(
            Fecha_solicitud__gte=fecha_inicio
        ).extra(
            select={
                'mes': "TO_CHAR(Fecha_solicitud, 'Mon')",
                'mes_num': "EXTRACT(MONTH FROM Fecha_solicitud)",
                'anio': "EXTRACT(YEAR FROM Fecha_solicitud)"
            }
        ).values('mes', 'mes_num', 'anio').annotate(
            reservas=Count('Solicitud_Id', filter=Q(Tipo_Servicio_Id=21)),
            prestamos=Count('Solicitud_Id', filter=Q(Tipo_Servicio_Id=1))
        ).order_by('anio', 'mes_num')
        
        # Traducir meses
        meses_es = {
            'Jan': 'Ene', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Abr',
            'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
            'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dic'
        }
        
        resultado = [
            {
                'mes': meses_es.get(item['mes'], item['mes']),
                'reservas': item['reservas'],
                'prestamos': item['prestamos'],
                'anio': item['anio']
            }
            for item in actividad_mensual
        ]
        
        return Response(resultado)
        
    except ValueError:
        return Response(
            {'error': 'El parámetro "meses" debe ser un número válido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error al obtener actividad mensual: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# VISTA 3: DISTRIBUCIÓN POR PROGRAMAS
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_distribucion_programas(request):
    """
    Distribución de solicitudes por programa académico.
    Filtros opcionales: fecha_desde, fecha_hasta
    """
    try:
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        query = Solicitudes.objects.all()
        
        # Aplicar filtros
        if fecha_desde:
            query = query.filter(Fecha_solicitud__gte=fecha_desde)
        if fecha_hasta:
            query = query.filter(Fecha_solicitud__lte=fecha_hasta)
        
        # Agrupar por programa
        distribucion = query.values(
            programa_nombre=F('Usuario_Id__programas_asociados__Programa_Id__Nombre_Programa'),
            programa_id=F('Usuario_Id__programas_asociados__Programa_Id__Programa_Id')
        ).annotate(
            cantidad=Count('Solicitud_Id')
        ).filter(
            cantidad__gt=0,
            programa_nombre__isnull=False
        ).order_by('-cantidad')
        
        # Calcular porcentajes
        total = sum(item['cantidad'] for item in distribucion)
        
        resultado = [
            {
                'programa': item['programa_nombre'],
                'programa_id': item['programa_id'],
                'cantidad': item['cantidad'],
                'porcentaje': round((item['cantidad'] / total * 100), 1) if total > 0 else 0
            }
            for item in distribucion
        ]
        
        return Response(resultado)
        
    except Exception as e:
        return Response(
            {'error': f'Error al obtener distribución por programas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# VISTA 4: EQUIPOS MÁS USADOS
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_equipos_mas_usados(request):
    """
    Equipos más utilizados (basado en cantidad total solicitada).
    Parámetros: limite (default: 10), fecha_desde, fecha_hasta
    """
    try:
        limite = int(request.GET.get('limite', 10))
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        query = Solicitudes_Objetos.objects.select_related('Objetos_Id')
        
        # Filtrar por fecha
        if fecha_desde:
            query = query.filter(Solicitud_Id__Fecha_solicitud__gte=fecha_desde)
        if fecha_hasta:
            query = query.filter(Solicitud_Id__Fecha_solicitud__lte=fecha_hasta)
        
        # Agrupar y sumar
        equipos_usados = query.values(
            equipo=F('Objetos_Id__Nombre_Objetos'),
            objeto_id=F('Objetos_Id__Objetos_Id')
        ).annotate(
            total_usos=Sum('Cantidad_Objetos')
        ).order_by('-total_usos')[:limite]
        
        equipos_lista = list(equipos_usados)
        
        # Calcular horas y porcentajes
        max_horas = equipos_lista[0]['total_usos'] * 2 if equipos_lista else 1
        
        resultado = [
            {
                'equipo': item['equipo'],
                'objeto_id': item['objeto_id'],
                'horas': item['total_usos'] * 2,
                'porcentaje_uso': round((item['total_usos'] * 2 / max_horas * 100), 1) if max_horas > 0 else 0
            }
            for item in equipos_lista
        ]
        
        return Response(resultado)
        
    except ValueError:
        return Response(
            {'error': 'El parámetro "limite" debe ser un número válido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Error al obtener equipos más usados: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# VISTA 5: HISTORIAL GENERAL
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_historial(request):
    """
    Historial completo de solicitudes.
    Parámetros: limite (default: 50), fecha_desde, fecha_hasta, estado_id
    """
    try:
        limite = request.GET.get('limite', '50')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        estado_id = request.GET.get('estado_id')
        
        query = Solicitudes.objects.select_related(
            'Usuario_Id',
            'Estado_Id',
            'Tipo_Servicio_Id',
            'Laboratorio_Id'
        ).prefetch_related('solicitudes_objetos_set__Objetos_Id')
        
        # Aplicar filtros
        if fecha_desde:
            query = query.filter(Fecha_solicitud__gte=fecha_desde)
        if fecha_hasta:
            query = query.filter(Fecha_solicitud__lte=fecha_hasta)
        if estado_id:
            query = query.filter(Estado_Id=estado_id)
        
        # Ordenar y limitar
        query = query.order_by('-Fecha_solicitud', '-Solicitud_Id')
        
        try:
            limite_int = int(limite)
            query = query[:limite_int]
        except ValueError:
            pass  # Si no es número válido, no limitar
        
        # Construir respuesta
        resultado = []
        for solicitud in query:
            # Determinar qué mostrar
            equipo_lab = ''
            if solicitud.Laboratorio_Id:
                equipo_lab = solicitud.Laboratorio_Id.Nombre_Laboratorio
            elif solicitud.Asignatura:
                equipo_lab = solicitud.Asignatura
            else:
                primer_objeto = solicitud.solicitudes_objetos_set.first()
                if primer_objeto:
                    equipo_lab = primer_objeto.Objetos_Id.Nombre_Objetos
            
            # Fecha formateada
            fecha_hora = solicitud.Fecha_solicitud.strftime('%Y-%m-%d %H:%M') if solicitud.Fecha_solicitud else 'N/A'
            
            # Tipo de actividad
            tipo_actividad = 'Solicitud'
            if solicitud.Tipo_Servicio_Id:
                if solicitud.Tipo_Servicio_Id.Tipo_Servicio_Id == 21:
                    tipo_actividad = 'Reserva'
                elif solicitud.Tipo_Servicio_Id.Tipo_Servicio_Id == 1:
                    tipo_actividad = 'Préstamo'
            
            resultado.append({
                'id': solicitud.Solicitud_Id,
                'fecha': fecha_hora,
                'tipo': tipo_actividad,
                'usuario': f"{solicitud.Usuario_Id.Nombres} {solicitud.Usuario_Id.Apellido1}",
                'equipo': equipo_lab,
                'estado': solicitud.Estado_Id.Nombre_Estado if solicitud.Estado_Id else 'Pendiente',
                'solicitud_id': solicitud.Solicitud_Id
            })
        
        return Response(resultado)
        
    except Exception as e:
        return Response(
            {'error': f'Error al obtener historial: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# VISTA 6: (NUEVA) RESUMEN DE ENTREGAS Y DEVOLUCIONES
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_entregas_devoluciones(request):
    """
    Obtiene un resumen de las métricas de entrega y devolución.
    - Entregas pendientes (Préstamos Aprobados)
    - % Devoluciones a tiempo vs retrasadas
    - Promedio de tiempo de uso (PLANIFICADO)
    - Próximas devoluciones ('En Uso')
    """
    try:
        # --- IDs de Estado (¡¡DEBES VERIFICAR ESTOS IDs!!) ---
        # Basado en tu kpis, ID_APROBADA = 2 (Préstamo Activo/Pendiente de Entrega)
        ID_APROBADA = 2
        # --- Asunciones (VERIFICAR EN TU MODELO 'Estados') ---
        ID_EN_USO = 3
        ID_DEVUELTO = 4
        ID_DEVUELTO_TARDE = 5
        
        # Basado en tu actividad_mensual, ID_TIPO_PRESTAMO = 1
        ID_TIPO_PRESTAMO = 1 

        # 1. Entregas Pendientes (KPI)
        # Préstamos de Tipo 1 que están en estado 'Aprobada' (2)
        entregas_pendientes = Solicitudes.objects.filter(
            Tipo_Servicio_Id=ID_TIPO_PRESTAMO,
            Estado_Id=ID_APROBADA 
        ).count()

        # 2. % Devoluciones
        devoluciones_completadas_qs = Solicitudes.objects.filter(
            Tipo_Servicio_Id=ID_TIPO_PRESTAMO,
            Estado_Id__in=[ID_DEVUELTO, ID_DEVUELTO_TARDE]
        )
        
        total_completadas = devoluciones_completadas_qs.count()
        
        devoluciones_retrasadas_count = devoluciones_completadas_qs.filter(
            Estado_Id=ID_DEVUELTO_TARDE
        ).count()
        
        porcentaje_a_tiempo = 0.0
        if total_completadas > 0:
            a_tiempo_count = total_completadas - devoluciones_retrasadas_count
            porcentaje_a_tiempo = round((a_tiempo_count / total_completadas) * 100, 1)

        # 3. Promedio tiempo de uso (PLANIFICADO)
        # NOTA: Esto calcula la duración *planificada* (Fecha_Fin - Fecha_Inicio)
        # Para la duración *real*, necesitarías un campo 'Fecha_Devolucion_Real'.
        avg_duration_data = Solicitudes.objects.filter(
            Tipo_Servicio_Id=ID_TIPO_PRESTAMO,
            Estado_Id__in=[ID_DEVUELTO, ID_DEVUELTO_TARDE],
            Fecha_Inicio__isnull=False,
            Fecha_Fin__isnull=False
        ).annotate(
            duracion=ExpressionWrapper(F('Fecha_Fin') - F('Fecha_Inicio'), output_field=DurationField())
        ).aggregate(avg_duracion=Avg('duracion'))
        
        promedio_dias = 0.0
        if avg_duration_data['avg_duracion']:
            # Extraemos los días de la duración promedio
            promedio_dias = round(avg_duration_data['avg_duracion'].days, 1)

        # 4. Próximas devoluciones
        hoy = timezone.now().date()
        manana = hoy + timedelta(days=1)
        fin_semana = hoy + timedelta(days=(6 - hoy.weekday()))
        
        prestamos_en_uso = Solicitudes.objects.filter(
            Tipo_Servicio_Id=ID_TIPO_PRESTAMO,
            Estado_Id=ID_EN_USO,
            Fecha_Fin__isnull=False
        )
        
        proximas_hoy = prestamos_en_uso.filter(Fecha_Fin=hoy).count()
        proximas_manana = prestamos_en_uso.filter(Fecha_Fin=manana).count()
        proximas_semana = prestamos_en_uso.filter(
            Fecha_Fin__gte=hoy, 
            Fecha_Fin__lte=fin_semana
        ).count()

        # --- Compilar respuesta ---
        resumen_data = {
            'entregas_pendientes': entregas_pendientes,
            'porcentaje_devoluciones_a_tiempo': porcentaje_a_tiempo,
            'devoluciones_retrasadas': devoluciones_retrasadas_count,
            'promedio_tiempo_uso_dias': promedio_dias
        }
        
        proximas_data = {
            'hoy': proximas_hoy,
            'manana': proximas_manana,
            'esta_semana': proximas_semana,
        }

        return Response({
            'resumen': resumen_data,
            'proximas_devoluciones': proximas_data
        })

    except Exception as e:
        return Response(
            {'error': f'Error al procesar resumen de entregas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# VISTA 7: EXPORTAR REPORTE (STUB)
# ==============================================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exportar_reporte(request):
    """
    Genera un archivo de reporte en el formato solicitado.
    Formatos soportados: PDF, Excel, CSV
    """
    try:
        formato = request.data.get('formato', 'pdf').lower()
        
        if formato not in ['pdf', 'excel', 'csv']:
            return Response(
                {'error': 'Formato no soportado. Use: pdf, excel, o csv'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implementar generación real de archivos
        # Aquí llamarías a tu utils.py: generar_reporte_pdf(...)
        url_archivo = f'/media/reportes/reporte_{timezone.now().strftime("%Y%m%d_%H%M%S")}.{formato}'
        
        return Response({
            'message': f'Reporte generado en formato {formato.upper()}',
            'url': url_archivo,
            'formato': formato
        })
        
    except Exception as e:
        return Response(
            {'error': f'Error al exportar reporte: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )