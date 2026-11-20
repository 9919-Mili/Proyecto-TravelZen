from django.db import models
from .servicios import DESTINOS, ALOJAMIENTOS, REGIMENES, EQUIPAJE



# Opciones

OPC_DESTINO = [(k, v["nombre"]) for k, v in DESTINOS.items()]
OPC_ALOJAMIENTO = [(k, v["nombre"]) for k, v in ALOJAMIENTOS.items()]
OPC_REGIMEN = [(k, v["nombre"]) for k, v in REGIMENES.items()]
OPC_EQUIPAJE = [(k, v["nombre"]) for k, v in EQUIPAJE.items()]
OPC_VUELO = [("directo", "Vuelo directo"), ("escala", "Vuelo con escala")]

# Tabla Destino
class Destino(models.Model):
    nombre = models.CharField(max_length=100)  # Nombre destino
    precio_vuelo_base = models.DecimalField(max_digits=10, decimal_places=2)  # PRecio de vuelo
    imagen = models.CharField(max_length=200)  # Ej: "destino_1.jpg"

    def __str__(self):
        return f"{self.nombre} - {self.get_destino_display()}"

# Tabla Solicitudes: guarda cada paquete confirmado por el usuario
class Solicitud(models.Model):

    # Datos del pasajero
    nombre = models.CharField(max_length=80)
    email = models.EmailField()

    # Datos del paquete
    destino = models.CharField(max_length=30, choices=OPC_DESTINO)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    adultos = models.PositiveIntegerField()
    ninios = models.PositiveIntegerField(default=0)
    tipo_vuelo = models.CharField(max_length=20, choices=OPC_VUELO)
    alojamiento = models.CharField(max_length=30, choices=OPC_ALOJAMIENTO)
    regimen = models.CharField(max_length=30, choices=OPC_REGIMEN)
    equipaje = models.CharField(max_length=30, choices=OPC_EQUIPAJE)


    # Resultado del cálculo
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Fecha en que se registró la solicitud (se completa sola)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'solicitudes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} - {self.destino}"