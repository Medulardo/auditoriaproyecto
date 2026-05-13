# gestion_pie/management/commands/seed_estudiantes.py
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from datetime import date
import random
import itertools
from dateutil.relativedelta import relativedelta

from gestion_pie.models import Estudiante, Curso  # ajusta si tu app/model difiere

# -----------------------
# Datos de ejemplo
# -----------------------
FIRST_M = ["Matías","Benjamín","Agustín","Sebastián","Tomás","Vicente","Joaquín","Martín","Diego","Lucas",
           "Cristóbal","Nicolás","Ignacio","Felipe","Francisco","Emilio","Maximiliano","Gabriel","Andrés","Bastián"]
FIRST_F = ["Sofía","Isabella","Martina","Josefa","Florencia","Valentina","Antonia","Emilia","Camila","Trinidad",
           "Catalina","Agustina","Victoria","Renata","Amanda","Maite","Javiera","Constanza","Fernanda","Paz"]
SURNAMES = ["González","Muñoz","Rojas","Díaz","Pérez","Soto","Contreras","Silva","Martínez","Sepúlveda",
            "Morales","Rodríguez","López","Fuentes","Hernández","Torres","Araya","Flores","Espinoza","Valenzuela",
            "Castillo","Ramírez","Reyes","Gutiérrez","Castro","Vargas","Fernández","Alarcón","Vera","Campos"]

NATIONALITIES = ["Chilena","Peruana","Venezolana","Haitiana","Colombiana","Argentina","Boliviana"]
NAT_W = [0.92,0.02,0.025,0.005,0.02,0.005,0.005]
HOME_LANGS = ["Español","Español + Mapudungun","Español + Quechua","Criollo haitiano","Inglés en casa"]
HOME_W = [0.95,0.01,0.01,0.01,0.02]

REF = date(2025, 1, 1)

BASICO_LABELS = ["1ro Básico","2do Básico","3ro Básico","4to Básico",
                 "5to Básico","6to Básico","7mo Básico","8vo Básico"]
MEDIO_LABELS = ["I Medio","II Medio","III Medio","IV Medio"]

# -----------------------
# Utilidades
# -----------------------
def rut_check_digit(num: int) -> str:
    s, m = 0, 2
    while num > 0:
        s += (num % 10) * m
        num //= 10
        m += 1
        if m == 8:
            m = 2
    dv = 11 - (s % 11)
    return '0' if dv == 11 else ('K' if dv == 10 else str(dv))

def gen_unique_rut(n, start=10_000_000, end=39_999_999, rng=None, existing=None):
    """
    Genera n RUN únicos (string '########-d') que NO colisionen con 'existing' (set de RUN ya en BD).
    """
    rng = rng or random
    existing = existing or set()
    used = set(existing)
    out = []
    tries = 0
    # margen amplio por si hay colisiones
    while len(out) < n and tries < n * 50:
        base = rng.randint(start, end)
        if base in used:
            tries += 1
            continue
        used.add(base)
        run = f"{base}-{rut_check_digit(base)}"
        if run in existing:
            tries += 1
            continue
        out.append(run)
    if len(out) < n:
        # backoff: amplía rango si hiciera falta
        while len(out) < n:
            base = rng.randint(40_000_000, 69_999_999)
            if base in used:
                continue
            used.add(base)
            run = f"{base}-{rut_check_digit(base)}"
            if run in existing:
                continue
            out.append(run)
    return out

def parse_base_level(label: str):
    """
    Devuelve ('basico', grado_num) o ('medio', grado_num) desde etiquetas tipo:
    '1ro Básico', '2do Básico', ..., '8vo Básico', 'I Medio', ..., 'IV Medio'
    """
    label = label.strip()
    if "Básico" in label:
        grado_txt = label.split()[0]  # '1ro', '2do', etc.
        mapping = {
            "1ro": 1, "2do": 2, "3ro": 3, "4to": 4,
            "5to": 5, "6to": 6, "7mo": 7, "8vo": 8
        }
        if grado_txt not in mapping:
            raise ValueError(f"Grado Básico no reconocido: {grado_txt}")
        return ("basico", mapping[grado_txt])
    elif "Medio" in label:
        grado_txt = label.split()[0]  # 'I','II','III','IV'
        romap = {"I":1, "II":2, "III":3, "IV":4}
        if grado_txt not in romap:
            raise ValueError(f"Grado Medio no reconocido: {grado_txt}")
        return ("medio", romap[grado_txt])
    else:
        raise ValueError(f"Etiqueta de nivel no reconocida: {label}")

def build_levels_from(desde_label: str):
    """
    Construye lista de niveles (sin sección), desde 'desde_label' inclusive,
    respetando tu nomenclatura local.
    """
    tipo, n = parse_base_level(desde_label)
    out = []
    if tipo == "basico":
        out.extend(BASICO_LABELS[n-1:])     # desde n hasta 8vo Básico
        out.extend(MEDIO_LABELS)            # luego I..IV Medio
    else:  # medio
        out.extend(MEDIO_LABELS[n-1:])      # desde n hasta IV Medio
    return out

def rand_birth_for_level(level_label, rng):
    """
    Genera fecha de nacimiento aproximada según el nivel dado ('1ro Básico', 'II Medio', etc.)
    """
    tipo, grado = parse_base_level(level_label)
    if tipo == "basico":
        # 1ro ~ 6 años, 2do ~ 7, ..., 8vo ~ 13
        min_age = 5 + grado   # ej 1 -> 6
        max_age = min_age + 1
    else:
        # I ~ 14, II ~ 15, III ~ 16, IV ~ 17
        min_age = 13 + grado  # 1 -> 14
        max_age = min_age + 1
    min_birth = REF - relativedelta(years=max_age+1) + relativedelta(days=1)
    max_birth = REF - relativedelta(years=min_age)
    delta_days = (max_birth - min_birth).days
    return min_birth + relativedelta(days=rng.randint(0, max(delta_days, 0)))

def pick_name(rng):
    first = rng.choice(FIRST_M if rng.random() < 0.5 else FIRST_F)
    a, b = rng.choice(SURNAMES), rng.choice(SURNAMES)
    if a == b:
        b = rng.choice([s for s in SURNAMES if s != a])
    return first, f"{a} {b}"

# -----------------------
# Comando principal
# -----------------------
class Command(BaseCommand):
    help = "Crea estudiantes por curso con una cantidad exacta de PIE (desde un nivel o solo un curso)."

    def add_arguments(self, parser):
        parser.add_argument("--por-curso", type=int, default=30)
        parser.add_argument("--pie-por-curso", type=int, default=5)
        parser.add_argument("--desde", type=str, default="2do Básico",
                            help="Punto de inicio (p.ej. '2do Básico' o 'II Medio'). Ignorado si usas --solo.")
        parser.add_argument("--secciones", type=str, default="A,B",
                            help="Secciones por nivel, p.ej: 'A,B' (ignorado si usas --solo).")
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--solo", type=str, default=None,
                            help="Curso exacto (incluye sección). Ej: '1ro Básico B'.")
        parser.add_argument("--reemplazar", action="store_true",
                            help="Si se especifica, elimina estudiantes existentes de los cursos objetivo antes de sembrar.")

    @transaction.atomic
    def handle(self, *args, **opts):
        rng = random.Random(opts["seed"])
        por_curso = opts.get("por-curso") or opts.get("por_curso")
        pie_n = opts.get("pie-por-curso") or opts.get("pie_por_curso")
        solo = opts.get("solo")
        desde = opts["desde"]
        secciones = [s.strip() for s in (opts.get("secciones") or "A,B").split(",") if s.strip()]
        reemplazar = bool(opts.get("reemplazar"))

        # Mapa de cursos por su __str__() -> asumimos __str__ = f"{nivel} {letra}"
        cursos_map = {f"{c.nivel} {c.letra}": c for c in Curso.objects.all()}

        # Targets
        if solo:
            targets = [solo]
        else:
            levels = build_levels_from(desde)
            targets = [f"{lv} {sec}" for lv, sec in itertools.product(levels, secciones)]

        faltantes = [c for c in targets if c not in cursos_map]
        if faltantes:
            self.stderr.write(self.style.ERROR(f"Cursos no encontrados: {faltantes}"))
            return

        # Reemplazar si procede
        if reemplazar:
            for course in targets:
                curso_obj = cursos_map[course]
                Estudiante.objects.filter(curso=curso_obj).delete()

        # Prepara RUNs que no choquen con los existentes
        existing_runs = set(Estudiante.objects.values_list("run", flat=True))
        total = por_curso * len(targets)
        runs = gen_unique_rut(total, rng=rng, existing=existing_runs)
        riter = iter(runs)

        creados = 0
        for course in targets:
            curso_obj = cursos_map[course]
            # Para edad: base sin sección
            base_level = " ".join(course.split()[:2])  # "1ro Básico", "II Medio", etc.

            # Posiciones PIE dentro del curso
            pie_positions = set(rng.sample(range(por_curso), min(max(pie_n, 0), por_curso)))

            for i in range(por_curso):
                run = next(riter)
                nombre, apellidos = pick_name(rng)
                nac = rng.choices(NATIONALITIES, weights=NAT_W, k=1)[0]
                lf = rng.choices(HOME_LANGS, weights=HOME_W, k=1)[0]
                fnac = rand_birth_for_level(base_level, rng)
                es_pie = i in pie_positions

                try:
                    Estudiante.objects.create(
                        run=run,
                        nombres=nombre,
                        apellidos=apellidos,
                        fecha_nacimiento=fnac,
                        nacionalidad=nac,
                        lengua_familia=lf,
                        lengua_habitual="Español",
                        curso=curso_obj,
                        es_pie=es_pie,
                    )
                    creados += 1
                except IntegrityError:
                    # Si por algún motivo chocó (p.ej. otro proceso creó ese RUN), intentamos otro rápidamente
                    alt = gen_unique_rut(1, rng=rng, existing=existing_runs)
                    if not alt:
                        continue
                    run_alt = alt[0]
                    existing_runs.add(run_alt)
                    Estudiante.objects.create(
                        run=run_alt,
                        nombres=nombre,
                        apellidos=apellidos,
                        fecha_nacimiento=fnac,
                        nacionalidad=nac,
                        lengua_familia=lf,
                        lengua_habitual="Español",
                        curso=curso_obj,
                        es_pie=es_pie,
                    )
                    creados += 1

        self.stdout.write(self.style.SUCCESS(f"Estudiantes creados: {creados}"))
