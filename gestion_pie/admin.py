# gestion_pie/admin.py
from django.contrib import admin
from . import models

# Modelos Base
admin.site.register(models.Establecimiento)
admin.site.register(models.Curso)
admin.site.register(models.Profesional)
admin.site.register(models.Estudiante)

# Modelos de Formularios
admin.site.register(models.EvaluacionSalud)
admin.site.register(models.Anamnesis)
admin.site.register(models.AutorizacionEvaluacion)
admin.site.register(models.InformeFamilia)

# Modelos del DOC
admin.site.register(models.RegistroPieCurso)
admin.site.register(models.EstrategiaDiversificadaCurso)
admin.site.register(models.PlanApoyoIndividual)
# Register your models here.
