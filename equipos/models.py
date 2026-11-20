from django.db import models
import qrcode
import threading
from io import BytesIO
from django.core.files import File
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# ==========================================
# CONFIGURACIÓN DEL MIDDLEWARE PARA AUDITORÍA
# ==========================================
# Este almacenamiento local nos permite saber quién está logueado en las señales
_thread_locals = threading.local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)


# ==========================================
# MODELOS
# ==========================================

class Equipo(models.Model):
    TIPO_CHOICES = [
        ('HILADORA', 'Hiladora'),
        ('BOBINADORA', 'Bobinadora'),
        ('CARDADORA', 'Cardadora'),
        ('OTRO', 'Otro'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre del Equipo")
    marca = models.CharField(max_length=50, verbose_name="Marca")
    modelo = models.CharField(max_length=50, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=50, unique=True, verbose_name="Número de Serie")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Equipo")
    ubicacion = models.CharField(max_length=100, verbose_name="Ubicación en Planta")
    estado = models.CharField(max_length=20, default='OPERATIVO', verbose_name="Estado")
    codigo_qr = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="Código QR")

    def __str__(self):
        return f"{self.nombre} ({self.numero_serie})"

    def save(self, *args, **kwargs):
        if not self.codigo_qr:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.numero_serie)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            nombre_archivo = f'qr_{self.numero_serie}.png'
            self.codigo_qr.save(nombre_archivo, File(buffer), save=False)
        super().save(*args, **kwargs)


class Mantenimiento(models.Model):
    TIPO_CHOICES = [
        ('PREVENTIVO', 'Preventivo'),
        ('CORRECTIVO', 'Correctivo'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='mantenimientos', verbose_name="Equipo")
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Técnico Responsable")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Mantenimiento")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_fin = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de Finalización")
    descripcion = models.TextField(verbose_name="Descripción del trabajo")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones (Opcional)")

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.equipo.nombre} ({self.fecha.strftime('%d/%m/%Y')})"


class OrdenTrabajo(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('TERMINADA', 'Terminada'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='ordenes', verbose_name="Equipo")
    tecnico_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Técnico Asignado")
    titulo = models.CharField(max_length=100, verbose_name="Título de la Tarea")
    descripcion = models.TextField(verbose_name="Descripción del trabajo a realizar")
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA', verbose_name="Prioridad")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    def __str__(self):
        return f"OT: {self.titulo} - {self.equipo.nombre} ({self.estado})"


class Repuesto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Repuesto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    stock_actual = models.IntegerField(default=0, verbose_name="Stock Actual")
    stock_minimo = models.IntegerField(default=5, verbose_name="Stock Mínimo (Alerta)")
    unidad_medida = models.CharField(max_length=20, default='Unidades', verbose_name="Unidad de Medida")
    
    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock_actual})"


class MovimientoRepuesto(models.Model):
    TIPO_MOVIMIENTO = [
        ('ENTRADA', 'Entrada (Compra/Ingreso)'),
        ('SALIDA', 'Salida (Uso en Mantenimiento)'),
    ]
    
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='movimientos', verbose_name="Repuesto")
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, verbose_name="Tipo de Movimiento")
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Movimiento")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Registrado por")
    
    def __str__(self):
        return f"{self.tipo} - {self.cantidad} {self.repuesto.nombre}"


class BitacoraAuditoria(models.Model):
    ACCIONES = [
        ('CREAR', 'Creación'),
        ('EDITAR', 'Edición'),
        ('ELIMINAR', 'Eliminación'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    accion = models.CharField(max_length=10, choices=ACCIONES, verbose_name="Acción")
    modelo_afectado = models.CharField(max_length=50, verbose_name="Tabla/Modelo Afectado")
    descripcion = models.TextField(verbose_name="Descripción del cambio")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Evento")
    
    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Bitácora de Auditoría"

    def __str__(self):
        return f"{self.usuario} - {self.accion} en {self.modelo_afectado} ({self.fecha.strftime('%d/%m/%Y')})"


# ==========================================
# SEÑALES DE AUDITORÍA (Ahora con el usuario correcto)
# ==========================================

@receiver(post_save, sender=Equipo)
def registrar_creacion_equipo(sender, instance, created, **kwargs):
    if created: 
        usuario = get_current_user()
        # Verificamos que el usuario exista y esté autenticado
        if usuario and not usuario.is_authenticated:
            usuario = None
            
        BitacoraAuditoria.objects.create(
            usuario=usuario,
            accion='CREAR',
            modelo_afectado='Equipo',
            descripcion=f"Se creó el equipo: {instance.nombre} (Serie: {instance.numero_serie})"
        )

@receiver(post_delete, sender=Equipo)
def registrar_eliminacion_equipo(sender, instance, **kwargs):
    usuario = get_current_user()
    if usuario and not usuario.is_authenticated:
        usuario = None
        
    BitacoraAuditoria.objects.create(
        usuario=usuario,
        accion='ELIMINAR',
        modelo_afectado='Equipo',
        descripcion=f"Se eliminó el equipo: {instance.nombre} (Serie: {instance.numero_serie})"
    )