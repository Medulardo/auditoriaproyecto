from django import forms
from datetime import date
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Div, Row, Column

from .models import (
    Estudiante, Curso, Profesional, InformePIE,
    InformePIEProfesional, ActividadApoyo, ActividadInforme
)

# -------------------------------
# FORMULARIO DE ESTUDIANTE
# -------------------------------
class EstudianteForm(forms.ModelForm):
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento*",
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        input_formats=['%Y-%m-%d'],
        required=True,
    )

    class Meta:
        model = Estudiante
        fields = [
            'run', 'nombres', 'apellidos', 'fecha_nacimiento',
            'nacionalidad', 'lengua_familia', 'lengua_habitual',
            'curso', 'es_pie',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        curso = None
        if 'initial' in kwargs and 'curso' in kwargs['initial']:
            curso = kwargs['initial']['curso']
        elif self.instance and getattr(self.instance, 'curso_id', None):
            curso = self.instance.curso_id
        if curso:
            self.fields['curso'].widget = forms.HiddenInput()


# -------------------------------
# FORMULARIO DE CURSO
# -------------------------------
class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['establecimiento', 'nivel', 'letra', 'anio']
        widgets = {'anio': forms.NumberInput(attrs={'min': 2020, 'max': 2050})}


# -------------------------------
# FORMULARIO DE PROFESIONAL
# -------------------------------
class ProfesionalForm(forms.ModelForm):
    class Meta:
        model = Profesional
        fields = ['user', 'nombre_completo', 'rut', 'especialidad', 'telefono', 'email']


# -------------------------------
# FORMULARIO DE INFORME PIE
# -------------------------------
BASE_TEXTAREA_ATTRS = {
    "rows": 4,
    "class": "form-control",
    "style": "resize: vertical; min-height: 120px;",
    "placeholder": "Escribe aquí…",
}

class InformePIEForm(forms.ModelForm):
    class Meta:
        model = InformePIE
        exclude = ['estudiante', 'profesional', 'rut_profesional', 'fecha_creacion']
        widgets = {
            'periodo_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'periodo_fin':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'diagnostico':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Diagnóstico principal'}),
            'frecuencia_apoyo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2/semana, 45 min'}),

            # Habilitados (enviarán el valor)
            'nombre_establecimiento': forms.TextInput(attrs={'class': 'form-control'}),
            'rbd':          forms.TextInput(attrs={'class': 'form-control'}),
            'dependencia':  forms.Select(attrs={'class': 'form-select'}),

            'curso': forms.TextInput(attrs={'class': 'form-control'}),
            'edad':  forms.NumberInput(attrs={'class': 'form-control'}),

            'objetivos_generales':     forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'estrategias_apoyo':       forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'recursos_utilizados':     forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'antecedentes':            forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'evaluacion':              forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'logros_alcanzados':       forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'dificultades_detectadas': forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'sugerencias':             forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
            'observaciones':           forms.Textarea(attrs=BASE_TEXTAREA_ATTRS),
        }
        labels = {
            'nombre_establecimiento': 'Nombre del establecimiento',
            'rbd': 'RBD',
            'dependencia': 'Dependencia',
            'curso': 'Curso',
            'edad': 'Edad (años)',
            'periodo_inicio': 'Periodo: inicio',
            'periodo_fin': 'Periodo: fin',
        }

    def __init__(self, *args, estudiante=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Prefill desde el sistema
        if estudiante:
            curso = getattr(estudiante, "curso", None)
            if curso:
                self.fields['curso'].initial = f"{curso.nivel} {curso.letra} ({curso.anio})"
                estb = getattr(curso, 'establecimiento', None)
                if estb:
                    self.fields['nombre_establecimiento'].initial = getattr(estb, 'nombre', '') or ''
                    self.fields['rbd'].initial = getattr(estb, 'rbd', '') or ''
                    dep_field = self.fields.get('dependencia')
                    if dep_field and getattr(estb, 'dependencia', None):
                        # Acepta label o value
                        choices = list(dep_field.choices)
                        code_to_label = dict(choices)
                        label_to_code = {lbl.lower(): val for val, lbl in choices if val != ''}
                        raw_dep = estb.dependencia
                        if raw_dep in code_to_label:
                            dep_field.initial = raw_dep
                        else:
                            mapped = label_to_code.get(str(raw_dep).lower())
                            if mapped:
                                dep_field.initial = mapped

            if getattr(estudiante, "fecha_nacimiento", None):
                fn = estudiante.fecha_nacimiento
                hoy = date.today()
                edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))
                self.fields['edad'].initial = max(0, edad)

        # Apariencia readonly sin deshabilitar
        self.fields['nombre_establecimiento'].widget.attrs.update({
            'readonly': True, 'tabindex': '-1', 'style': 'background:#f8f9fa;'
        })
        self.fields['rbd'].widget.attrs.update({
            'readonly': True, 'tabindex': '-1', 'style': 'background:#f8f9fa;'
        })
        self.fields['curso'].widget.attrs.update({
            'readonly': True, 'tabindex': '-1', 'style': 'background:#f8f9fa;'
        })
        self.fields['edad'].widget.attrs.update({
            'readonly': True, 'tabindex': '-1', 'style': 'background:#f8f9fa;'
        })

        # Crispy layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'I. Identificación del Establecimiento',
                Row(
                    Column('nombre_establecimiento', css_class='col-md-6'),
                    Column('rbd', css_class='col-md-3'),
                    Column('dependencia', css_class='col-md-3'),
                ),
            ),
            Fieldset(
                'II. Identificación del Estudiante',
                Row(
                    Column('curso', css_class='col-md-4'),
                    Column('edad', css_class='col-md-2'),
                    Column('diagnostico', css_class='col-md-6'),
                ),
                Row(
                    Column('periodo_inicio', css_class='col-md-3'),
                    Column('periodo_fin',   css_class='col-md-3'),
                ),
            ),
            Fieldset(
                'III. Planificación y Apoyos',
                'objetivos_generales',
                Row(
                    Column('estrategias_apoyo',   css_class='col-md-6'),
                    Column('recursos_utilizados', css_class='col-md-6'),
                ),
                'frecuencia_apoyo',
            ),
            Fieldset(
                'IV. Evaluación y Seguimiento',
                'logros_alcanzados',
                'dificultades_detectadas',
                'sugerencias',
                Row(
                    Column('antecedentes', css_class='col-md-6'),
                    Column('evaluacion',   css_class='col-md-6'),
                ),
            ),
            Fieldset('V. Observaciones Finales', 'observaciones'),
            Div(Submit('submit', 'Guardar Informe', css_class='btn btn-success'), css_class='text-center mt-3'),
        )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('dependencia') and self.fields['dependencia'].initial:
            cleaned['dependencia'] = self.fields['dependencia'].initial
        return cleaned


# ======= NUEVOS FORMS: Colaborador y Actividad =======

class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = InformePIEProfesional
        fields = ["rol", "resumen_aporte"]
        labels = {
            "rol": "Rol en el informe",
            "resumen_aporte": "Resumen del aporte (opcional)",
        }
        widgets = {
            "rol": forms.Select(attrs={"class": "form-select"}),
            "resumen_aporte": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe brevemente tu aporte…"
            }),
        }

# --- Actividad (por si el otro template usaba add_class) ---
class ActividadApoyoForm(forms.ModelForm):
    class Meta:
        model = ActividadApoyo
        fields = ["fecha", "tipo", "objetivo", "descripcion",
                  "duracion_min", "instrumentos", "observaciones"]
        labels = {
            "fecha": "Fecha",
            "tipo": "Tipo de actividad",
            "objetivo": "Objetivo",
            "descripcion": "Descripción",
            "duracion_min": "Duración (min)",
            "instrumentos": "Instrumentos",
            "observaciones": "Observaciones",
        }
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "objetivo": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "duracion_min": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "instrumentos": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ActividadInformeForm(forms.ModelForm):
    class Meta:
        model = ActividadInforme
        fields = ["fecha", "titulo", "descripcion", "tipo"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la actividad"}),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "style": "resize: vertical; min-height: 120px;",
                "placeholder": "Describe brevemente la actividad realizada"
            }),
            "tipo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Psicología / Fono / Ed. Dif."}),
        }