from rest_framework import serializers
from .models import Solicitud


# Campos que en la base se guardan como código numerico, pero tienen una descripción.

CAMPOS_CON_OPCIONES = ["destino", "tipo_vuelo", "alojamiento", "regimen", "equipaje"]


# Convierte objetos Solicitud a JSON (y JSON a Solicitud) para Postman
class SolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = '__all__'

    # Al DEVOLVER datos (GET): cambia cada código por su descripción
    def to_representation(self, instance):
        datos = super().to_representation(instance)
        for campo in CAMPOS_CON_OPCIONES:
            # get_FOO_display() lo crea Django solo para los campos con choices
            datos[campo] = getattr(instance, f"get_{campo}_display")()
        return datos

    # Al RECIBIR datos (POST/PUT): acepta la descripción o el código
    def to_internal_value(self, data):
        data = data.copy()
        for campo in CAMPOS_CON_OPCIONES:
            valor = str(data.get(campo, "")).strip().lower()
            for codigo, descripcion in Solicitud._meta.get_field(campo).choices:
                if valor == descripcion.lower():
                    data[campo] = codigo
        return super().to_internal_value(data)