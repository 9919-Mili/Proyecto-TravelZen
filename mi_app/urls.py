from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from django.urls import path, include


router = DefaultRouter()
router.register(r'solicitudes', views.SolicitudViewSet)

urlpatterns = [
    path('', views.pagina_inicio, name='index'),
    path("calcular/", views.calcular, name="calcular"),
    path("enviar/", views.enviar, name="enviar"),
    path("validar-paso/", views.validar_paso, name="validar_paso"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("modificarSolicitud/<int:solicitud_id>/", views.modificar_solicitud, name="modificar_solicitud"),
    path("eliminarSolicitud/<int:solicitud_id>/", views.eliminar_solicitud, name="eliminar_solicitud"),
    path("registro/", views.registro, name="registro"),
    path("login/", auth_views.LoginView.as_view(template_name="mi_app/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/dolar/", views.cotizacion_dolar, name="cotizacion_dolar"),
    path("api/", include(router.urls)),
]

