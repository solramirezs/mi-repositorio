from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from django.http import HttpResponse # <-- NUEVO: Para descargar archivos
import openpyxl # <-- NUEVO: Para crear el Excel

# Importación de modelos
from .models import Equipo, Mantenimiento, OrdenTrabajo, Repuesto, MovimientoRepuesto
from alertas.models import Alerta

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import io

# 1. Vista para ver la ficha pública del Equipo (Escaneo de QR)
def detalle_equipo_qr(request, numero_serie):
    equipo = get_object_or_404(Equipo, numero_serie=numero_serie)
    mantenimientos = equipo.mantenimientos.all().order_by('-fecha')
    return render(request, 'equipos/detalle_qr.html', {
        'equipo': equipo,
        'mantenimientos': mantenimientos
    })

# 2. Vista del Dashboard (Panel de Alertas)
def dashboard(request):
    alertas_pendientes = Alerta.objects.exclude(estado='COMPLETADA').order_by('fecha_programada')
    hoy = timezone.now().date()
    for alerta in alertas_pendientes:
        if alerta.fecha_programada < hoy and alerta.estado == 'PENDIENTE':
            alerta.estado = 'VENCIDA'
            alerta.save()
    return render(request, 'dashboard.html', {'alertas': alertas_pendientes})

# 3. Vista de Reportes (MTTR y MTBF)
from django.db.models import F, ExpressionWrapper, DurationField, Avg

def reporte_mantenimiento(request):
    # Traemos todos los equipos para el menú desplegable
    lista_equipos = Equipo.objects.all()
    
    # Vemos si el usuario seleccionó un equipo en el formulario
    equipo_id = request.GET.get('equipo')
    
    if equipo_id:
        # Si seleccionó uno, filtramos los mantenimientos de ese equipo
        correctivos = Mantenimiento.objects.filter(tipo='CORRECTIVO', equipo_id=equipo_id)
        total_correctivos = correctivos.count()
        # Simulamos el cálculo del MTTR (o usamos el real si tienen fecha_fin)
        mttr_estimado = total_correctivos * 2 
        
        # MTBF para ese equipo específico
        if total_correctivos > 0:
            mtbf_estimado = round(30 / total_correctivos, 2) # Simulación de 30 días
        else:
            mtbf_estimado = 30
    else:
        # Si no seleccionó ninguno, mostramos los datos globales
        correctivos = Mantenimiento.objects.filter(tipo='CORRECTIVO')
        total_correctivos = correctivos.count()
        mttr_estimado = total_correctivos * 2
        mtbf_estimado = round(30 / total_correctivos, 2) if total_correctivos > 0 else 30

    context = {
        'mttr': mttr_estimado,
        'mtbf': mtbf_estimado,
        'total_equipos': Equipo.objects.count(),
        'total_mantenimientos': Mantenimiento.objects.count(),
        'total_alertas': Alerta.objects.exclude(estado='COMPLETADA').count(),
        'lista_equipos': lista_equipos, # Pasamos la lista para el combo
        'equipo_seleccionado': equipo_id, # Para mantener la selección
    }
    return render(request, 'reportes.html', context)

# 4. NUEVA VISTA: Exportar Reporte a Excel
def exportar_excel(request):
    # Creamos un libro de trabajo (Workbook) de Excel
    wb = openpyxl.Workbook()
    
    # --- Hoja 1: Equipos ---
    ws_equipos = wb.active
    ws_equipos.title = "Equipos"
    # Cabeceras
    ws_equipos.append(['Nombre', 'Marca', 'Modelo', 'Número de Serie', 'Tipo', 'Ubicación', 'Estado'])
    # Datos
    for equipo in Equipo.objects.all():
        ws_equipos.append([
            equipo.nombre, equipo.marca, equipo.modelo, 
            equipo.numero_serie, equipo.tipo, equipo.ubicacion, equipo.estado
        ])

    # --- Hoja 2: Mantenimientos ---
    ws_mant = wb.create_sheet(title="Mantenimientos")
    ws_mant.append(['Equipo', 'Tipo', 'Técnico', 'Fecha', 'Descripción'])
    for m in Mantenimiento.objects.all():
        ws_mant.append([
            m.equipo.nombre, m.get_tipo_display(), 
            m.tecnico.username if m.tecnico else 'N/A', 
            m.fecha.strftime('%d/%m/%Y %H:%M'), m.descripcion
        ])

    # --- Hoja 3: Alertas ---
    ws_alertas = wb.create_sheet(title="Alertas")
    ws_alertas.append(['Equipo', 'Mensaje', 'Fecha Programada', 'Estado'])
    for a in Alerta.objects.all():
        ws_alertas.append([
            a.equipo.nombre, a.mensaje, 
            a.fecha_programada.strftime('%d/%m/%Y'), a.estado
        ])

    # Configuramos la respuesta HTTP para que se descargue como archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Senatex.xlsx"'
    
    # Guardamos el libro en la respuesta
    wb.save(response)
    
    return response

def exportar_pdf(request):
    # 1. Buscamos los datos (puedes personalizar qué datos quieres en el PDF)
    equipos = Equipo.objects.all()
    mantenimientos = Mantenimiento.objects.all()
    
    # 2. Renderizamos la plantilla HTML a un string
    template = get_template('reporte_pdf.html')
    html = template.render({'equipos': equipos, 'mantenimientos': mantenimientos})
    
    # 3. Creamos el PDF
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Reporte_Senatex.pdf"'
        return response
    return HttpResponse('Error al generar el PDF', status=500)