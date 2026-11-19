from datetime import date
import requests

URL_DOLAR_OFICIAL = "https://dolarapi.com/v1/dolares/oficial"


DESTINOS = {
    "1": {"nombre": "Bariloche", "precio_vuelo_base": 50000, "imagen": "bariloche.jpg"},
    "2": {"nombre": "Jujuy", "precio_vuelo_base": 40000, "imagen": "jujuy.jpg"},
    "3": {"nombre": "Mendoza", "precio_vuelo_base": 35000, "imagen": "mendoza.jpg"},
    "4": {"nombre": "Cordoba", "precio_vuelo_base": 30000, "imagen": "cordoba.jpg"},
}
ALOJAMIENTOS = {
    "1": {"nombre": "Hotel", "precio_por_persona_noche": 25000, "imagen": "aloj1.jpg"},
    "2": {"nombre": "Cabaña", "precio_por_persona_noche": 15000, "imagen": "aloj2.jpg"},
    "3": {"nombre": "Hostel", "precio_por_persona_noche": 10000, "imagen": "aloj3.jpg"},
}

REGIMENES = {
    "1": {"nombre": "Sin desayuno", "precio_por_persona_por_dia": 0},
    "2": {"nombre": "Desayuno", "precio_por_persona_por_dia": 10000},
    "3": {"nombre": "Media pensión", "precio_por_persona_por_dia": 25000},
    "4": {"nombre": "Pensión completa", "precio_por_persona_por_dia": 35000},
}

EQUIPAJE = {
    "1": {"nombre": "Mano/mochila", "precio": 0},
    "2": {"nombre": "Valija 15kg", "precio": 10000},
    "3": {"nombre": "Valija 23kg", "precio": 22000},
}

def calcular_vuelo(precio_base, tipo_vuelo, adultos, niños):
    precio_adulto = precio_base * 1.20 if tipo_vuelo == "directo" else precio_base
    precio_niño = precio_adulto * 0.70
    return precio_adulto * adultos + precio_niño * niños


def calcular_alojamiento(precio_noche, noches, adultos, niños):
    precio_niño = precio_noche * 0.80
    return (precio_noche * adultos + precio_niño * niños) * noches


def calcular_comidas(precio_dia, dias, adultos, niños):
    precio_niño = precio_dia * 0.50
    return (precio_dia * adultos + precio_niño * niños) * dias


def calcular_equipaje(precio, adultos):
    return precio * adultos


def calcular_descuentos(subtotal, noches, cant_viajeros, dias_anticipacion):

    porc_noches = 0
    if 5 <= noches <= 7:
        porc_noches = 0.05
    elif 8 <= noches <= 14:
        porc_noches = 0.10
    elif noches > 14:
        porc_noches = 0.15

    porc_viajeros = 0.05 if cant_viajeros >= 5 else 0
    porc_anticipacion = 0.05 if dias_anticipacion > 60 else 0

    descuento_noches = subtotal * porc_noches
    descuento_viajeros = subtotal * porc_viajeros
    descuento_anticipacion = subtotal * porc_anticipacion
    descuento_total = descuento_noches + descuento_viajeros + descuento_anticipacion

    return {
        "descuento_noches": descuento_noches,
        "descuento_viajeros": descuento_viajeros,
        "descuento_anticipacion": descuento_anticipacion,
        "descuento_total": descuento_total,
    }
def calcular_costos(datos):
        destino = DESTINOS[datos["destino_id"]]
        alojamiento = ALOJAMIENTOS[datos["alojamiento_id"]]
        regimen = REGIMENES[datos["regimen_id"]]
        equipaje = EQUIPAJE[datos["equipaje_id"]]

        adultos = datos["adultos"]
        ninios = datos["niños"]
        dias_viaje = datos["dias_viaje"]
        noches = dias_viaje -1

        costo_vuelo = calcular_vuelo(
            destino["precio_vuelo_base"], datos["tipo_vuelo"], adultos, ninios
        )

        costo_alojamiento = calcular_alojamiento(
            alojamiento["precio_por_persona_noche"], noches, adultos, ninios
        )

        costo_comidas = calcular_comidas(
            regimen["precio_por_persona_por_dia"], dias_viaje, adultos, ninios
        )

        costo_equipaje = calcular_equipaje(equipaje["precio"], adultos)

        subtotal = costo_vuelo + costo_alojamiento + costo_comidas + costo_equipaje

        descuento_total = calcular_descuentos(
            subtotal, noches, adultos + ninios, datos["dias_anticipacion"]
        )

        total = subtotal - descuento_total["descuento_total"]

        return {
            "costo_vuelo": costo_vuelo,
            "costo_alojamiento": costo_alojamiento,
            "costo_comidas": costo_comidas,
            "costo_equipaje": costo_equipaje,
            "descuento_noches": descuento_total["descuento_noches"],
            "descuento_viajeros": descuento_total["descuento_viajeros"],
            "descuento_anticipacion": descuento_total["descuento_anticipacion"],
            "descuento_total": descuento_total["descuento_total"],
            "subtotal": subtotal,
            "total": total,
            "noches": noches,
        }

def preparar_datos(cd):
    noches = (cd["fecha_fin"] - cd["fecha_inicio"]).days
    return {
        "destino_id": cd["destino"],
        "tipo_vuelo": cd["tipo_vuelo"],
        "alojamiento_id": cd["alojamiento"],
        "regimen_id": cd["regimen"],
        "equipaje_id": cd["equipaje"],
        "adultos": cd["adultos"],
        "niños": cd["ninios"],
        "dias_viaje": noches + 1,
        "dias_anticipacion": (cd["fecha_inicio"] - date.today()).days,
    }

def obtener_dolar_oficial():

    #Consulta DolaraApi y devuelve la cotizacion del dolar oficial.
    #Si la Api no responde, devuelve NONE

    try:
        respuesta = requests.get(URL_DOLAR_OFICIAL, timeout=5)  # espera como máx. 5 segundos
        respuesta.raise_for_status()                            # si la API respondió con error, salta al except
        datos = respuesta.json()                                # convierte el JSON en diccionario
        return {
            "compra": datos["compra"],
            "venta": datos["venta"],
            "fecha": datos["fechaActualizacion"],
        }
    except (requests.RequestException, KeyError, ValueError):
        return None