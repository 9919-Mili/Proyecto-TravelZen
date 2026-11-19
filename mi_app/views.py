from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from .models import Solicitud
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from . import servicios
from .forms import PaqueteForm, ModificarSolicitudForm
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import SolicitudSerializer
import logging

logger = logging.getLogger(__name__)


def pagina_inicio(request):
    return render(request, 'mi_app/index.html', {
        "form": PaqueteForm(),
        "destinos": servicios.DESTINOS,
        "alojamientos": servicios.ALOJAMIENTOS,
    })

def _errores_como_dict(form):
    return {
        campo: [error["message"] for error in lista_errores]
        for campo, lista_errores in form.errors.get_json_data().items()
    }


def _armar_resumen(datos_validados):
    datos_calculo = servicios.preparar_datos(datos_validados)
    resultados = servicios.calcular_costos(datos_calculo)
    dolar = servicios.obtener_dolar_oficial()

    return {
        "nombre": datos_validados["nombre"],
        "email": datos_validados["email"],
        "destino": servicios.DESTINOS[datos_validados["destino"]]["nombre"],
        "tipo_vuelo": "Directo" if datos_validados["tipo_vuelo"] == "directo" else "Con escala",
        "alojamiento": servicios.ALOJAMIENTOS[datos_validados["alojamiento"]]["nombre"],
        "regimen": servicios.REGIMENES[datos_validados["regimen"]]["nombre"],
        "equipaje": servicios.EQUIPAJE[datos_validados["equipaje"]]["nombre"],
        "adultos": datos_validados["adultos"],
        "ninios": datos_validados["ninios"],
        "fecha_inicio": datos_validados["fecha_inicio"].strftime("%d/%m/%Y"),
        "fecha_fin": datos_validados["fecha_fin"].strftime("%d/%m/%Y"),
        "dias_anticipacion": datos_calculo["dias_anticipacion"],
        "costos": resultados,
        "dolar": dolar,
        "total_usd": round(resultados["total"] / dolar["venta"], 2) if dolar else None,


    }


def _armar_cuerpo_mail(resumen):
    c = resumen["costos"]

    # Línea del total en dólares
    linea_usd = ""
    if resumen["total_usd"]:
        linea_usd = f"TOTAL: US$ {resumen['total_usd']:,.2f} (dólar oficial ${resumen['dolar']['venta']:,.2f})\n"

    return (
        f"Hola {resumen['nombre']},\n\n"
        f"Te confirmamos tu paquete turístico a {resumen['destino']}.\n\n"
        f"--- Detalles del paquete ---\n"
        f"Fechas: {resumen['fecha_inicio']} al {resumen['fecha_fin']}\n"
        f"Viajeros: {resumen['adultos']} adulto(s), {resumen['ninios']} niño(s)\n"
        f"Vuelo: {resumen['tipo_vuelo']}\n"
        f"Alojamiento: {resumen['alojamiento']}\n"
        f"Régimen de comidas: {resumen['regimen']}\n"
        f"Equipaje: {resumen['equipaje']}\n\n"
        f"--- Costos ---\n"
        f"Vuelos: ${c['costo_vuelo']:,.2f}\n"
        f"Alojamiento: ${c['costo_alojamiento']:,.2f}\n"
        f"Comidas: ${c['costo_comidas']:,.2f}\n"
        f"Equipaje: ${c['costo_equipaje']:,.2f}\n"
        f"Subtotal: ${c['subtotal']:,.2f}\n"
        f"Descuentos: -${c['descuento_total']:,.2f}\n\n"
        f"TOTAL: ${c['total']:,.2f} ARS\n"
        f"{linea_usd}\n"
        f"¡Gracias por elegir TravelZen, espero que lo disfrutes!"
    )


@require_POST
def calcular(request):
    form = PaqueteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errores": _errores_como_dict(form)}, status=400)
    resumen = _armar_resumen(form.cleaned_data)
    return JsonResponse({"ok": True, "resumen": resumen})


@require_POST
def enviar(request):
    form = PaqueteForm(request.POST)
    if not form.is_valid():
        dolar = servicios.obtener_dolar_oficial()  # consulta DolarApi
        return JsonResponse({"ok": False, "errores": _errores_como_dict(form)}, status=400)

    resumen = _armar_resumen(form.cleaned_data)

    # Guarda la solicitud en la base de datos (CREATE)
    Solicitud.objects.create(**form.cleaned_data, total=round(resumen["costos"]["total"], 2))

    cuerpo = _armar_cuerpo_mail(resumen)

    try:
        send_mail("Confirmación de tu paquete TravelZen", cuerpo, None, [resumen["email"]])
    except Exception:
        # Escribe en la terminal el motivo real del error
        logger.exception("Error al enviar el mail de confirmación")
        # La solicitud ya se guardó: avisamos sin pedir que reintente (evita duplicados)
        return JsonResponse({
            "ok": True,
            "aviso": "Registramos tu solicitud, pero no pudimos enviarte el mail de confirmación.",
        })
    return JsonResponse({"ok": True})

CAMPOS_POR_PASO = {
    "1": ["destino", "nombre", "email", "fecha_inicio", "fecha_fin", "adultos", "ninios"],
    "2": ["tipo_vuelo"],
    "3": ["alojamiento"],
    "4": ["regimen", "equipaje"],
}


@require_POST
def validar_paso(request):
    paso = request.POST.get("paso")
    campos_del_paso = CAMPOS_POR_PASO.get(paso, [])

    form = PaqueteForm(request.POST)
    form.is_valid()  # corre todas las validaciones, incluidas las de fechas.


    errores = {
        campo: mensajes
        for campo, mensajes in _errores_como_dict(form).items()
        if campo in campos_del_paso
    }
    if errores:
        return JsonResponse({"ok": False, "errores": errores}, status=400)
    return JsonResponse({"ok": True})


# Dashboard
@login_required
def dashboard(request):
    solicitudes = Solicitud.objects.all()  # trae todas las filas de la tabla solicitudes
    return render(request, "mi_app/dashboard.html", {"solicitudes": solicitudes})

# Modificar solicitud

@login_required
def modificar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)

    if request.method == "POST":
        form = ModificarSolicitudForm(request.POST)
        if not form.is_valid():
            return JsonResponse({"success": False, "errors": _errores_como_dict(form)}, status=400)

        # Recalcular el total con los datos nuevos
        resumen = _armar_resumen(form.cleaned_data)

        # Actualizar los valores de la solicitud
        solicitud.nombre = form.cleaned_data["nombre"]
        solicitud.email = form.cleaned_data["email"]
        solicitud.destino = form.cleaned_data["destino"]
        solicitud.fecha_inicio = form.cleaned_data["fecha_inicio"]
        solicitud.fecha_fin = form.cleaned_data["fecha_fin"]
        solicitud.adultos = form.cleaned_data["adultos"]
        solicitud.ninios = form.cleaned_data["ninios"]
        solicitud.tipo_vuelo = form.cleaned_data["tipo_vuelo"]
        solicitud.alojamiento = form.cleaned_data["alojamiento"]
        solicitud.regimen = form.cleaned_data["regimen"]
        solicitud.equipaje = form.cleaned_data["equipaje"]
        solicitud.total = round(resumen["costos"]["total"], 2)
        solicitud.save()  # Guardar cambios en la base de datos

        return JsonResponse({"success": True, "message": "Solicitud modificada correctamente."})

    # Llena el formulario con los datos actuales de la solicitud
    form = ModificarSolicitudForm(initial={
        "nombre": solicitud.nombre,
        "email": solicitud.email,
        "destino": solicitud.destino,
        "fecha_inicio": solicitud.fecha_inicio,
        "fecha_fin": solicitud.fecha_fin,
        "adultos": solicitud.adultos,
        "ninios": solicitud.ninios,
        "tipo_vuelo": solicitud.tipo_vuelo,
        "alojamiento": solicitud.alojamiento,
        "regimen": solicitud.regimen,
        "equipaje": solicitud.equipaje,
    })
    return render(request, "mi_app/modificar_solicitud.html", {"form": form, "solicitud": solicitud})

# Eliminar solicitud

@login_required
@require_POST
def eliminar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)  # Obtener la solicitud
    solicitud.delete()  # Eliminar de la base de datos
    return JsonResponse({"success": True, "message": "Solicitud eliminada correctamente."})

# Registro de usuarios
def registro(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)      # Inicia sesión automáticamente tras registrarse
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "mi_app/registro.html", {"form": form})


class SolicitudViewSet(viewsets.ModelViewSet):
    queryset = Solicitud.objects.all()            # Todas las solicitudes de la base
    serializer_class = SolicitudSerializer        # Cómo convertirlas a JSON
    permission_classes = [AllowAny]               # Sin credenciales



# Cotización del dólar: consume DolarApi y la expone con Django REST Framework
@api_view(["GET"])
@permission_classes([AllowAny])
def cotizacion_dolar(request):
    dolar = servicios.obtener_dolar_oficial()   # consulta DolarApi con requests
    if dolar is None:
        return Response(
            {"error": "No se pudo obtener la cotización del dólar."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(dolar)