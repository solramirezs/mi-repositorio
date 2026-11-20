from django.contrib import admin
from django.utils.html import format_html
from .models import Alerta

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'mensaje', 'fecha_programada', 'estado_coloreado')
    list_filter = ('estado', 'fecha_programada', 'equipo')
    search_fields = ('equipo__nombre', 'mensaje')
    date_hierarchy = 'fecha_programada'

    def estado_coloreado(self, obj):
        if obj.estado == 'PENDIENTE':
            color = '#f39c12' # Naranja
        elif obj.estado == 'VENCIDA':
            color = '#e74c3c' # Rojo
        else:
            color = '#2ecc71' # Verde
        return format_html('<b style="color: {};">{}</b>', color, obj.get_estado_display())
    
    estado_coloreado.short_description = 'Estado de Alerta'