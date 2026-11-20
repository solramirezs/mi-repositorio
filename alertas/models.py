from django.db import models
from equipos.models import Equipo

class Alerta(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('VENCIDA', 'Vencida'),
        ('COMPLETADA', 'Completada'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='alertas', verbose_name="Equipo")
    mensaje = models.CharField(max_length=200, verbose_name="Mensaje de Alerta", default="Mantenimiento preventivo requerido")
    fecha_programada = models.DateField(verbose_name="Fecha Programada")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerta: {self.equipo.nombre} - {self.fecha_programada} ({self.estado})"

