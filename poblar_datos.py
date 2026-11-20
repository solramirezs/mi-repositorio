import os
import django
import datetime
from django.utils import timezone

# 1. PRIMERO: Configuramos el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'senatex.settings')
django.setup()

# 2. DESPUÉS: Importamos los modelos (ahora sí funciona)
from django.contrib.auth.models import User
from equipos.models import Equipo, Mantenimiento, Repuesto, OrdenTrabajo
from alertas.models import Alerta

print("--- Creando Usuarios ---")
# Creamos los usuarios (si ya existen, no da error)
User.objects.get_or_create(username='tecnico_juan', defaults={'first_name': 'Juan', 'last_name': 'Perez', 'email': 'juan@senatex.com'})
User.objects.get_or_create(username='tecnico_maria', defaults={'first_name': 'Maria', 'last_name': 'Lopez', 'email': 'maria@senatex.com'})
User.objects.get_or_create(username='almacen_carlos', defaults={'first_name': 'Carlos', 'last_name': 'Gomez', 'email': 'carlos@senatex.com'})

# Asignamos contraseña a los usuarios creados
for username in ['tecnico_juan', 'tecnico_maria', 'almacen_carlos']:
    user = User.objects.get(username=username)
    user.set_password('senatex123')
    user.save()

print("--- Creando Equipos ---")
equipos_data = [
    {"nombre": "Hiladora de Anillo 01", "marca": "Rieter", "modelo": "G 32", "numero_serie": "HIL-001", "tipo": "HILADORA", "ubicacion": "Sala de Hilado 1", "estado": "OPERATIVO"},
    {"nombre": "Hiladora de Anillo 02", "marca": "Rieter", "modelo": "G 32", "numero_serie": "HIL-002", "tipo": "HILADORA", "ubicacion": "Sala de Hilado 1", "estado": "EN MANTENIMIENTO"},
    {"nombre": "Bobinadora Automática 01", "marca": "Murata", "modelo": "QPRO", "numero_serie": "BOB-001", "tipo": "BOBINADORA", "ubicacion": "Sala de Bobinado", "estado": "OPERATIVO"},
    {"nombre": "Cardadora 01", "marca": "Trützschler", "modelo": "TC 10", "numero_serie": "CAR-001", "tipo": "CARDADORA", "ubicacion": "Sala de Cardado", "estado": "OPERATIVO"},
]
for data in equipos_data:
    Equipo.objects.get_or_create(numero_serie=data["numero_serie"], defaults=data)

print("--- Creando Repuestos ---")
repuestos_data = [
    {"nombre": "Rodamiento SKF 6205", "stock_actual": 25, "stock_minimo": 10, "unidad_medida": "Unidades"},
    {"nombre": "Aceite Hidráulico ISO 68", "stock_actual": 8, "stock_minimo": 15, "unidad_medida": "Litros"},
    {"nombre": "Correa de Transmisión", "stock_actual": 50, "stock_minimo": 20, "unidad_medida": "Unidades"},
    {"nombre": "Filtro de Aire", "stock_actual": 4, "stock_minimo": 5, "unidad_medida": "Unidades"},
]
for data in repuestos_data:
    Repuesto.objects.get_or_create(nombre=data["nombre"], defaults=data)

print("--- Creando Mantenimientos y Alertas ---")
eq1 = Equipo.objects.get(numero_serie="HIL-001")
eq2 = Equipo.objects.get(numero_serie="HIL-002")
eq4 = Equipo.objects.get(numero_serie="CAR-001")
user_juan = User.objects.get(username='tecnico_juan')

# Mantenimiento Correctivo (Con fecha de fin para el MTTR)
Mantenimiento.objects.get_or_create(
    equipo=eq1, tipo='CORRECTIVO',
    defaults={'tecnico': user_juan, 'descripcion': "Cambio de rodamientos del husillo", 'fecha_fin': timezone.now() + datetime.timedelta(hours=3)}
)

# Alertas
Alerta.objects.get_or_create(
    equipo=eq1, mensaje="Cambio de aceite de husillo programado",
    defaults={'fecha_programada': timezone.now().date() + datetime.timedelta(days=5), 'estado': 'PENDIENTE'}
)
Alerta.objects.get_or_create(
    equipo=eq4, mensaje="Revisión de cardas y cintas",
    defaults={'fecha_programada': timezone.now().date() - datetime.timedelta(days=2), 'estado': 'VENCIDA'}
)

# Orden de trabajo
OrdenTrabajo.objects.get_or_create(
    equipo=eq2, titulo="Reparación de motor de arrastre",
    defaults={'tecnico_asignado': user_juan, 'descripcion': 'El motor presenta sobrecalentamiento.', 'prioridad': 'ALTA', 'estado': 'EN_PROCESO'}
)

print("✅ ¡Datos cargados exitosamente!")