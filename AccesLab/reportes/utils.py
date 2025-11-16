# reportes/utils.py
# Archivo nuevo con utilidades para generar reportes

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os
from django.conf import settings


def generar_reporte_pdf(kpis_data, actividad_data, programas_data, equipos_data, historial_data):
    """
    Genera un PDF completo con todos los datos del reporte
    """
    # Crear directorio si no existe
    reportes_dir = os.path.join(settings.MEDIA_ROOT, 'reportes')
    os.makedirs(reportes_dir, exist_ok=True)
    
    # Nombre del archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'reporte_{timestamp}.pdf'
    filepath = os.path.join(reportes_dir, filename)
    
    # Crear documento
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#4FC3C3'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Título principal
    elements.append(Paragraph("Reporte AccesLab", title_style))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # ========================================
    # SECCIÓN 1: KPIs
    # ========================================
    elements.append(Paragraph("📊 Indicadores Clave (KPIs)", heading_style))
    
    kpis_table_data = [
        ['Métrica', 'Valor'],
        ['Usuarios Activos', str(kpis_data.get('usuarios_activos', 0))],
        ['Préstamos Activos', str(kpis_data.get('prestamos_activos', 0))],
        ['Reservas esta Semana', str(kpis_data.get('reservas_semana', 0))],
        ['Equipos Fuera de Servicio', str(kpis_data.get('equipos_fuera_servicio', 0))],
        ['Comparación', kpis_data.get('comparacion_mes_anterior', 'N/A')],
    ]
    
    kpis_table = Table(kpis_table_data, colWidths=[3*inch, 2*inch])
    kpis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4FC3C3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(kpis_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========================================
    # SECCIÓN 2: Actividad Mensual
    # ========================================
    elements.append(Paragraph("📈 Actividad Mensual", heading_style))
    
    if actividad_data:
        actividad_table_data = [['Mes', 'Reservas', 'Préstamos']]
        for item in actividad_data:
            actividad_table_data.append([
                item.get('mes', 'N/A'),
                str(item.get('reservas', 0)),
                str(item.get('prestamos', 0))
            ])
        
        actividad_table = Table(actividad_table_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        actividad_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(actividad_table)
    else:
        elements.append(Paragraph("No hay datos disponibles", styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # ========================================
    # SECCIÓN 3: Distribución por Programas
    # ========================================
    elements.append(Paragraph("🎓 Distribución por Programas", heading_style))
    
    if programas_data:
        programas_table_data = [['Programa', 'Cantidad', 'Porcentaje']]
        for item in programas_data[:10]:  # Top 10
            programas_table_data.append([
                item.get('programa', 'N/A')[:30],  # Truncar si es muy largo
                str(item.get('cantidad', 0)),
                f"{item.get('porcentaje', 0)}%"
            ])
        
        programas_table = Table(programas_table_data, colWidths=[3*inch, 1*inch, 1*inch])
        programas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4FC3C3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(programas_table)
    else:
        elements.append(Paragraph("No hay datos disponibles", styles['Normal']))
    
    elements.append(PageBreak())
    
    # ========================================
    # SECCIÓN 4: Equipos Más Usados
    # ========================================
    elements.append(Paragraph("🔧 Equipos Más Utilizados", heading_style))
    
    if equipos_data:
        equipos_table_data = [['#', 'Equipo', 'Horas de Uso']]
        for idx, item in enumerate(equipos_data[:10], 1):
            equipos_table_data.append([
                str(idx),
                item.get('equipo', 'N/A')[:40],
                str(item.get('horas', 0))
            ])
        
        equipos_table = Table(equipos_table_data, colWidths=[0.5*inch, 3.5*inch, 1*inch])
        equipos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(equipos_table)
    else:
        elements.append(Paragraph("No hay datos disponibles", styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # ========================================
    # SECCIÓN 5: Historial (últimos 20)
    # ========================================
    elements.append(Paragraph("📜 Historial Reciente (Últimas 20 actividades)", heading_style))
    
    if historial_data:
        historial_table_data = [['Fecha', 'Tipo', 'Usuario', 'Estado']]
        for item in historial_data[:20]:
            historial_table_data.append([
                item.get('fecha', 'N/A')[:16],
                item.get('tipo', 'N/A'),
                item.get('usuario', 'N/A')[:20],
                item.get('estado', 'N/A')
            ])
        
        historial_table = Table(historial_table_data, colWidths=[1.3*inch, 1*inch, 1.5*inch, 1.2*inch])
        historial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4FC3C3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(historial_table)
    else:
        elements.append(Paragraph("No hay datos disponibles", styles['Normal']))
    
    # Pie de página
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        f"Reporte generado por AccesLab - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Normal']
    ))
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar la ruta relativa para la URL
    return f'/media/reportes/{filename}'