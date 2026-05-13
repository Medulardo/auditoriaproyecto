from django.db import models
from django.conf import settings
from django.utils import timezone

# --- MODELOS BASE ---

class Establecimiento(models.Model):
    """ Representa al colegio o escuela """
    nombre = models.CharField(max_length=255)
    rbd = models.CharField(max_length=20, unique=True, null=True, blank=True)
    DEP_CHOICES = [
        ('municipal', 'Municipal'),
        ('particular_subvencionado', 'Particular Subvencionado'),
        ('particular_pagado', 'Particular Pagado'),
    ]
    dependencia = models.CharField(max_length=30, choices=DEP_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """ Representa un curso específico en un año (Ej: 1ro Básico A, 2025) """
    establecimiento = models.ForeignKey(Establecimiento, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=50, help_text="Ej: 1ro Básico, Kinder")
    letra = models.CharField(max_length=10, help_text="Ej: A, B, Único")
    anio = models.IntegerField(default=2025)

    def __str__(self):
        return f"{self.nivel} {self.letra} ({self.anio}) - {self.establecimiento.nombre}"


class Profesional(models.Model):
    """
    Representa a los profesionales (Docentes, Psicólogos, Fonoaudiólogos)
    vinculados al User de Django para login.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    nombre_completo = models.CharField(max_length=255)
    rut = models.CharField(max_length=12, unique=True)
    especialidad = models.CharField(max_length=100, help_text="Ej: Educ. Diferencial, Fonoaudiólogo")
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.especialidad})"


class Estudiante(models.Model):
    """ Modelo central. Representa al estudiante con NEE. """
    run = models.CharField(max_length=12, unique=True, primary_key=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField()

    # Datos de identificación
    nacionalidad = models.CharField(max_length=100, blank=True)
    lengua_familia = models.CharField(max_length=100, blank=True)
    lengua_habitual = models.CharField(max_length=100, blank=True)

    # Vinculación escolar
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="estudiantes"
    )

    # Identificador PIE
    es_pie = models.BooleanField(default=False, verbose_name="¿Es estudiante PIE?")

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.run})"


class InformePIE(models.Model):
    # --- Campos base ---
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="informes_pie")
    profesional = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True, blank=True)
    rut_profesional = models.CharField(max_length=12, blank=True)
    diagnostico = models.CharField(max_length=255)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    antecedentes = models.TextField(blank=True)
    evaluacion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # --- Extensión: Informe profesional completo ---
    # I. Establecimiento
    nombre_establecimiento = models.CharField(max_length=255, blank=True, null=True)
    rbd = models.CharField(max_length=10, blank=True, null=True)
    dependencia = models.CharField(
        max_length=100,
        choices=[
            ('municipal', 'Municipal'),
            ('particular_subvencionado', 'Particular Subvencionado'),
            ('particular_pagado', 'Particular Pagado'),
        ],
        blank=True, null=True
    )

    # II. Estudiante
    curso = models.CharField(max_length=50, blank=True, null=True)
    edad = models.PositiveIntegerField(blank=True, null=True)

    # III. Planificación y apoyos
    objetivos_generales = models.TextField(blank=True, null=True)
    estrategias_apoyo = models.TextField(blank=True, null=True)
    recursos_utilizados = models.TextField(blank=True, null=True)
    frecuencia_apoyo = models.CharField(max_length=100, blank=True, null=True)

    # IV. Evaluación y seguimiento
    logros_alcanzados = models.TextField(blank=True, null=True)
    dificultades_detectadas = models.TextField(blank=True, null=True)
    sugerencias = models.TextField(blank=True, null=True)

    # V. Observaciones finales
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Informe PIE"
        verbose_name_plural = "Informes PIE"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Informe PIE - {self.estudiante.nombres} {self.estudiante.apellidos} ({self.fecha_creacion:%d/%m/%Y})"


# ======= NUEVO: Colaboradores y Actividades por Informe =======

class InformePIEProfesional(models.Model):
    """Vincula un Informe con un Profesional que aporta (autor o colaborador)."""
    ROL_CHOICES = [
        ("autor", "Autor/a"),
        ("fono", "Fonoaudiólogo/a"),
        ("psico", "Psicólogo/a"),
        ("tea", "Educación Diferencial"),
        ("otra", "Otro"),
    ]
    informe = models.ForeignKey(InformePIE, related_name="colaboradores", on_delete=models.CASCADE)
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="autor")
    resumen_aporte = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("informe", "profesional")
        ordering = ["creado_en"]

    def __str__(self):
        return f"{self.informe_id} · {self.profesional.nombre_completo} ({self.get_rol_display()})"

class ActividadInforme(models.Model):
    informe = models.ForeignKey(InformePIE, on_delete=models.CASCADE, related_name="actividades")
    profesional = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateField(default=timezone.now)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=50, blank=True)  # opcional (p. ej. "Psicología", "Fono", etc.)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-created_at"]

    def __str__(self):
        return f"{self.titulo} ({self.fecha:%d/%m/%Y})"

class ActividadApoyo(models.Model):
    """Actividad/sesión concreta que aporta un profesional al Informe."""
    TIPO_CHOICES = [
        ("sesion_ind", "Sesión individual"),
        ("sesion_grup", "Sesión grupal"),
        ("coord", "Coordinación/entrevista"),
        ("eval", "Evaluación"),
        ("otra", "Otra"),
    ]
    informe = models.ForeignKey(InformePIE, related_name="actividades_apoyo", on_delete=models.CASCADE)
    autor = models.ForeignKey(Profesional, on_delete=models.PROTECT)
    colaborador = models.ForeignKey(InformePIEProfesional, related_name="actividades", on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo = models.CharField(max_length=12, choices=TIPO_CHOICES)
    objetivo = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    duracion_min = models.PositiveIntegerField(default=45)
    instrumentos = models.CharField(max_length=255, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["fecha", "id"]

    def __str__(self):
        return f"{self.fecha} · {self.get_tipo_display()} · {self.autor.nombre_completo}"


# --- MODELOS DE FORMULARIOS (BASADOS EN LOS PDF y DOC) ---

class EvaluacionSalud(models.Model):
    """ FU_EVALUACION-DE_SALUD_2024-3.pdf """
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="evaluaciones_salud")
    motivo_consulta = models.TextField(blank=True)
    diagnostico_discapacidad_deficit = models.TextField(blank=True,
        help_text="DIAGNÓSTICO DE DISCAPACIDAD O DÉFICIT")

    # Profesional Médico
    medico_nombre = models.CharField(max_length=200)
    medico_especialidad = models.CharField(max_length=100)
    medico_rut = models.CharField(max_length=12)
    medico_registro_profesional = models.CharField(max_length=50, blank=True)
    medico_procedencia = models.CharField(max_length=50, blank=True,
        help_text="Salud pública, Particular, Escuela, Otro")

    fecha_evaluacion = models.DateField(default=timezone.now)
    fecha_reevaluacion = models.DateField(null=True, blank=True)

    examen_salud_general = models.TextField(blank=True, help_text="Presencia/ausencia de patologías...")
    diagnostico_medico = models.TextField(blank=True,
        help_text="DIAGNÓSTICO (Presencia de un trastorno, déficit o discapacidad)")
    indicaciones = models.TextField(blank=True, help_text="Tratamiento médico, interconsulta, exámenes...")

    def __str__(self):
        return f"Eval. Salud de {self.estudiante} ({self.fecha_evaluacion})"


class Anamnesis(models.Model):
    """ ANAMNESIS_2010.pdf — 1 a 1 con Estudiante """
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, related_name="anamnesis")
    informante_nombre = models.CharField(max_length=200, blank=True)
    informante_relacion = models.CharField(max_length=100, blank=True)
    entrevistador = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_entrevista = models.DateField(default=timezone.now, null=True, blank=True)
    motivo_entrevista = models.TextField(blank=True)
    diagnostico_previo_json = models.JSONField(null=True, blank=True,
        help_text="Almacena diagnósticos previos (Pediatría, Psicología, etc.)")
    antecedentes_embarazo_parto = models.TextField(blank=True)
    desarrollo_primer_anio = models.TextField(blank=True, help_text="Enfermedades, hospitalizaciones, etc.")
    desarrollo_sensorio_motriz = models.TextField(blank=True, help_text="Hitos como fijar cabeza, caminar, control esfínter.")
    desarrollo_lenguaje = models.TextField(blank=True)
    desarrollo_social = models.TextField(blank=True)
    estado_actual_salud = models.TextField(blank=True)
    antecedentes_familiares_texto = models.TextField(blank=True, help_text="Con quién vive y antecedentes de salud.")
    edad_ingreso_escolar = models.IntegerField(null=True, blank=True)
    asistio_jardin = models.BooleanField(null=True)
    ha_repetido = models.BooleanField(null=True)
    cursos_repetidos = models.CharField(max_length=100, blank=True)
    actitud_familia_desempeno = models.CharField(max_length=50, blank=True)
    expectativas_familia = models.CharField(max_length=50, blank=True)
    ambiente_aprendizaje_hogar = models.TextField(blank=True)
    observaciones_generales = models.TextField(blank=True)

    def __str__(self):
        return f"Anamnesis de {self.estudiante}"


class AutorizacionEvaluacion(models.Model):
    """ AUTORIZACION_EVALUACION_2010.pdf — 1 a 1 con Estudiante """
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, related_name="autorizacion")
    fecha_autorizacion = models.DateField(default=timezone.now)
    ciudad = models.CharField(max_length=100)
    nombre_apoderado = models.CharField(max_length=200)
    rut_apoderado = models.CharField(max_length=12)
    relacion_apoderado = models.CharField(max_length=50, help_text="Ej: Madre, Padre, Tutor")
    profesional_informa = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True, blank=True)
    da_consentimiento = models.BooleanField(default=False, help_text="Marcar si el apoderado marca 'Doy mi consentimiento'")
    autoriza_reevaluaciones = models.BooleanField(default=False)

    def __str__(self):
        estado = "Autorizado" if self.da_consentimiento else "No Autorizado"
        return f"Autorización de {self.estudiante} ({estado})"


class InformeFamilia(models.Model):
    """ INFORME_PARA_LA_FAMILIA_2025.pdf — 1 a muchos con Estudiante """
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="informes_familia")
    profesional_entrega = models.ForeignKey(Profesional, on_delete=models.SET_NULL, null=True, blank=True)
    receptor_nombre = models.CharField(max_length=200)
    receptor_rut = models.CharField(max_length=12)
    receptor_relacion = models.CharField(max_length=100)
    fecha_entrega = models.DateField(default=timezone.now)
    TIPO_EVALUACION_CHOICES = [
        ('ingreso', 'Evaluación de Ingreso'),
        ('reevaluacion', 'Reevaluación fin año 2'),
    ]
    motivo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION_CHOICES)
    fecha_evaluacion = models.DateField(default=timezone.now, help_text="fecha Informe psicopedagógico")
    instrumentos_aplicados = models.TextField(blank=True)
    diagnostico_nee = models.TextField(help_text="Diagnóstico asociado a NEE por el que recibe subvención")
    ambito_pedagogico_fortalezas = models.TextField(blank=True)
    ambito_pedagogico_necesidades = models.TextField(blank=True)
    ambito_social_fortalezas = models.TextField(blank=True)
    ambito_social_necesidades = models.TextField(blank=True)
    trabajo_colaborativo_apoyos = models.TextField(blank=True)
    apoyos_requeridos_hogar = models.TextField(blank=True)
    acuerdos_compromisos_escuela_familia = models.TextField(blank=True)
    fechas_evaluacion_avances = models.TextField(blank=True)

    def __str__(self):
        return f"Informe a Familia de {self.estudiante} ({self.fecha_entrega})"


# --- REGISTRO PIE 2013 (Nivel Curso) ---

class RegistroPieCurso(models.Model):
    curso = models.OneToOneField(Curso, on_delete=models.CASCADE, related_name="registro_pie")
    docentes_regulares = models.ManyToManyField(Profesional, related_name="pie_docentes_regulares", blank=True)
    profesores_especializados = models.ManyToManyField(Profesional, related_name="pie_especialistas", blank=True)
    asistentes_educacion = models.ManyToManyField(Profesional, related_name="pie_asistentes", blank=True)
    estilos_aprendizaje_curso = models.TextField(blank=True)
    fortalezas_curso = models.TextField(blank=True)
    necesidades_apoyo_curso = models.TextField(blank=True)
    observaciones_generales = models.TextField(blank=True)

    def __str__(self):
        return f"Registro PIE para {self.curso}"


class EstrategiaDiversificadaCurso(models.Model):
    registro_pie = models.ForeignKey(RegistroPieCurso, on_delete=models.CASCADE, related_name="estrategias_diversificadas")
    estrategia = models.TextField()
    ambito_asignatura = models.CharField(max_length=200, blank=True)
    periodo_tiempo = models.CharField(max_length=200, blank=True)
    criterios_evaluacion = models.TextField(blank=True)


class PlanApoyoIndividual(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="planes_apoyo")
    registro_pie_curso = models.ForeignKey(RegistroPieCurso, on_delete=models.CASCADE, related_name="planes_individuales")
    apoyos_planificados_texto = models.TextField(blank=True, help_text="Detalle de apoyos, horarios, fechas (Sección II.4)")
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"PAI para {self.estudiante} (Curso: {self.registro_pie_curso.curso.nivel})"
