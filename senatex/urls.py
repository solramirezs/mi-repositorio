from django.contrib import admin
from django.urls import path
from equipos import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('reportes/', views.reporte_mantenimiento, name='reportes'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'), # <--- NUEVA RUTA
    path('equipo/<str:numero_serie>/', views.detalle_equipo_qr, name='detalle_equipo'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)