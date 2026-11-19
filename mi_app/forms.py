from datetime import date
from django import forms
from .servicios import DESTINOS, ALOJAMIENTOS, REGIMENES, EQUIPAJE




#--- Armado de opciones ----
def opciones(diccionario):
    return [(clave, datos["nombre"]) for clave, datos in diccionario.items()]


class PaqueteForm(forms.Form):
    nombre = forms.CharField(max_length=80, label="Nombre y Apellido")
    email = forms.EmailField(label="Email")


    destino = forms.ChoiceField(choices=opciones(DESTINOS), widget=forms.RadioSelect)
    fecha_inicio = forms.DateField(
        label="Fecha de inicio del viaje",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin del viaje",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    #--- Exige minimo un adulto

    adultos = forms.IntegerField(min_value=1, label="Cantidad de adultos")
    ninios = forms.IntegerField(min_value=0, label="Cantidad de niños (menores de 12 años)")


    tipo_vuelo = forms.ChoiceField(
        choices=[("directo", "Vuelo directo"), ("escala", "Vuelo con escala")],
        widget=forms.RadioSelect,
    )


    alojamiento = forms.ChoiceField(choices=opciones(ALOJAMIENTOS), widget=forms.RadioSelect)


    regimen = forms.ChoiceField(choices=opciones(REGIMENES), widget=forms.RadioSelect)
    equipaje = forms.ChoiceField(choices=opciones(EQUIPAJE), widget=forms.RadioSelect)


    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"]
        if not nombre.replace(" ", "").isalpha():
            raise forms.ValidationError("El nombre no puede contener números ni símbolos.")
        return nombre


    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("fecha_inicio")
        fin = cleaned.get("fecha_fin")
        if inicio and inicio < date.today():
            self.add_error("fecha_inicio", "La fecha de inicio no puede ser anterior a hoy.")
        if inicio and fin and fin <= inicio:
            self.add_error("fecha_fin", "La fecha de fin debe ser posterior a la de inicio.")
        return cleaned

    # Formulario para el Dashboard: mismos campos y validaciones que PaqueteForm,
    # pero cambia la estetca

class ModificarSolicitudForm(PaqueteForm):
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.fields["destino"].label = "Destino"
            self.fields["tipo_vuelo"].label = "Tipo de vuelo"
            self.fields["alojamiento"].label = "Alojamiento"
            self.fields["regimen"].label = "Régimen de comidas"
            self.fields["equipaje"].label = "Equipaje"
            self.fields["ninios"].label = "Cantidad de niños"

            for campo in self.fields.values():
                if isinstance(campo.widget, forms.RadioSelect):
                    campo.widget = forms.Select(choices=campo.choices)  # radios → lista desplegable
                if isinstance(campo.widget, forms.Select):
                    campo.widget.attrs["class"] = "form-select"
                else:
                    campo.widget.attrs["class"] = "form-control"