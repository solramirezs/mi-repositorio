from django.contrib import admin
from django.utils.html import format_html
from .models import Equipo, Mantenimiento
from .models import Equipo, Mantenimiento, OrdenTrabajo # Asegúrate de importar OrdenTrabajo
from .models import Equipo, Mantenimiento, OrdenTrabajo, Repuesto, MovimientoRepuesto, BitacoraAuditoria

# 1. Creamos el "Inline" para ver los mantenimientos DENTRO del equipo
class MantenimientoInline(admin.TabularInline):
    model = Mantenimiento
    extra = 0 # No muestra filas vacías extra
    readonly_fields = ('fecha',)

# 2. Registramos el Equipo con todas sus funciones visuales
@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    # Columnas de la tabla
    list_display = ('ver_foto_qr', 'nombre', 'marca', 'numero_serie', 'tipo', 'estado_coloreado')
    
    # Filtros laterales
    list_filter = ('tipo', 'estado', 'marca')
    
    # Barra de búsqueda
    search_fields = ('nombre', 'numero_serie', 'marca')
    
    # Miniatura del QR de solo lectura
    readonly_fields = ('ver_foto_qr',)
    
    # Magia: Muestra el historial de mantenimientos abajo del equipo
    inlines = [MantenimientoInline] 

    # Función para la miniatura del QR
    def ver_foto_qr(self, obj):
        if obj.codigo_qr:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.codigo_qr.url)
        return "Sin QR"
    ver_foto_qr.short_description = 'QR'

    # Función para colorear el estado
    def estado_coloreado(self, obj):
        color = 'green' if obj.estado == 'OPERATIVO' else 'red'
        return format_html('<b style="color: {};">{}</b>', color, obj.estado)
    estado_coloreado.short_description = 'Estado'

# 3. Registramos el Mantenimiento en el menú lateral
@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'tipo', 'tecnico', 'fecha')
    list_filter = ('tipo', 'fecha', 'tecnico')
    search_fields = ('equipo__nombre', 'descripcion')
    date_hierarchy = 'fecha'



@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'equipo', 'tecnico_asignado', 'prioridad_coloreada', 'estado_coloreado', 'fecha_creacion')
    list_filter = ('estado', 'prioridad', 'tecnico_asignado')
    search_fields = ('titulo', 'equipo__nombre', 'descripcion')
    date_hierarchy = 'fecha_creacion'

    # Color para la prioridad
    def prioridad_coloreada(self, obj):
        if obj.prioridad == 'ALTA':
            color = '#e74c3c' # Rojo
        elif obj.prioridad == 'MEDIA':
            color = '#f39c12' # Naranja
        else:
            color = '#2ecc71' # Verde
        return format_html('<b style="color: {};">{}</b>', color, obj.get_prioridad_display())
    prioridad_coloreada.short_description = 'Prioridad'

    # Color para el estado
    def estado_coloreado(self, obj):
        if obj.estado == 'PENDIENTE':
            color = '#f39c12'
        elif obj.estado == 'EN_PROCESO':
            color = '#3498db' # Azul
        else:
            color = '#2ecc71'
        return format_html('<b style="color: {};">{}</b>', color, obj.get_estado_display())
    estado_coloreado.short_description = 'Estado'

from .models import Equipo, Mantenimiento, OrdenTrabajo, Repuesto, MovimientoRepuesto

@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock_actual', 'stock_minimo', 'alerta_stock', 'unidad_medida')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('unidad_medida',)

    def alerta_stock(self, obj):
        if obj.stock_actual <= obj.stock_minimo:
            return format_html('<b style="color: red;">¡Reponer Urgente!</b>')
        return format_html('<b style="color: green;">Stock OK</b>')
    alerta_stock.short_description = 'Alerta de Stock'


@admin.register(MovimientoRepuesto)
class MovimientoRepuestoAdmin(admin.ModelAdmin):
    list_display = ('repuesto', 'tipo', 'cantidad', 'fecha', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('repuesto__nombre',)

    # Esta función hace la magia matemática al guardar desde el admin
    def save_model(self, request, obj, form, change):
        # Si es un movimiento nuevo
        if not change: 
            obj.usuario = request.user # Asigna al usuario que está logueado
            
            if obj.tipo == 'ENTRADA':
                obj.repuesto.stock_actual += obj.cantidad
            elif obj.tipo == 'SALIDA':
                obj.repuesto.stock_actual -= obj.cantidad
                
            obj.repuesto.save() # Guarda el nuevo stock en la base de datos
        super().save_model(request, obj, form, change)


@admin.register(BitacoraAuditoria)
class BitacoraAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion', 'modelo_afectado', 'descripcion_corta')
    list_filter = ('accion', 'modelo_afectado', 'fecha')
    search_fields = ('usuario__username', 'descripcion')
    readonly_fields = ('usuario', 'accion', 'modelo_afectado', 'descripcion', 'fecha')
    date_hierarchy = 'fecha'

    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
    descripcion_corta.short_description = 'Descripción'