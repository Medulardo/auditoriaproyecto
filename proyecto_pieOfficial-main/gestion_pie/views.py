from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from django.db.models import Prefetch
from .models import (
    InformePIE, Estudiante, Curso, Profesional,
    InformePIEProfesional, ActividadApoyo, ActividadInforme
)
from .forms import EstudianteForm, CursoForm, ProfesionalForm, InformePIEForm, ColaboradorForm, ActividadApoyoForm, ActividadInformeForm
from django.http import HttpResponse
from .utils import generar_docx_informe

from django.utils import timezone
from django.utils.timezone import localtime
from datetime import date
import re

# --- HOME ---
@login_required
def home(request):
    total_estudiantes = Estudiante.objects.count()
    total_cursos = Curso.objects.count()
    ultimos_informes = InformePIE.objects.select_related('estudiante', 'profesional').order_by('-fecha_creacion')[:5]
    
    return render(request, 'home.html', {
        'total_estudiantes': total_estudiantes,
        'total_cursos': total_cursos,
        'ultimos_informes': ultimos_informes,
    })


# --- Estudiantes ---
class EstudianteListView(LoginRequiredMixin, ListView):
    model = Curso
    template_name = 'gestion_pie/estudiante_list.html'
    context_object_name = 'cursos'

    def get_queryset(self):
        return Curso.objects.prefetch_related('estudiantes').order_by('nivel', 'letra')


class EstudianteDetailView(LoginRequiredMixin, DetailView):
    model = Estudiante
    template_name = 'gestion_pie/estudiante_detail.html'
    context_object_name = 'estudiante'


class EstudianteCreateView(LoginRequiredMixin, CreateView):
    model = Estudiante
    template_name = 'gestion_pie/estudiante_form.html'
    success_url = reverse_lazy('estudiante-list')
    form_class = EstudianteForm

    def get_initial(self):
        initial = super().get_initial()
        curso_id = self.request.GET.get('curso_id')
        if curso_id:
            initial['curso'] = curso_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        curso_id = self.request.GET.get('curso_id')
        if curso_id:
            form.fields['curso'].widget = form.fields['curso'].hidden_widget()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cursos'] = Curso.objects.all()
        return context


class EstudianteUpdateView(LoginRequiredMixin, UpdateView):
    model = Estudiante
    template_name = 'gestion_pie/estudiante_form.html'
    success_url = reverse_lazy('estudiante-list')
    form_class = EstudianteForm


class EstudianteDeleteView(LoginRequiredMixin, DeleteView):
    model = Estudiante
    template_name = 'gestion_pie/estudiante_confirm_delete.html'
    success_url = reverse_lazy('estudiante-list')


# --- Cursos ---
class CursoListView(LoginRequiredMixin, ListView):
    model = Curso
    template_name = 'gestion_pie/curso_list.html'
    context_object_name = 'cursos'

    def get_queryset(self):
        cursos = Curso.objects.order_by('nivel', 'letra').prefetch_related('estudiantes')
        for curso in cursos:
            estudiantes_qs = curso.estudiantes.all()
            curso.total_estudiantes = estudiantes_qs.count()
            curso.total_pie = estudiantes_qs.filter(es_pie=True).count()
            curso.estudiantes_pie = estudiantes_qs.filter(es_pie=True)[:5]
        return cursos


class CursoDetailView(LoginRequiredMixin, DetailView):
    model = Curso
    template_name = 'gestion_pie/curso_detail.html'
    context_object_name = 'curso'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.get_object()
        context['estudiantes'] = curso.estudiantes.all().order_by('-es_pie', 'nombres')
        return context


class CursoCreateView(LoginRequiredMixin, CreateView):
    model = Curso
    template_name = 'gestion_pie/curso_form.html'
    success_url = reverse_lazy('curso-list')
    form_class = CursoForm


class CursoUpdateView(LoginRequiredMixin, UpdateView):
    model = Curso
    template_name = 'gestion_pie/curso_form.html'
    success_url = reverse_lazy('curso-list')
    form_class = CursoForm


class CursoDeleteView(LoginRequiredMixin, DeleteView):
    model = Curso
    template_name = 'gestion_pie/curso_confirm_delete.html'
    success_url = reverse_lazy('curso-list')


# --- Profesionales ---
class ProfesionalListView(LoginRequiredMixin, ListView):
    model = Profesional
    template_name = 'gestion_pie/profesional_list.html'
    context_object_name = 'profesionales'


class ProfesionalDetailView(LoginRequiredMixin, DetailView):
    model = Profesional
    template_name = 'gestion_pie/profesional_detail.html'
    context_object_name = 'profesional'


class ProfesionalCreateView(LoginRequiredMixin, CreateView):
    model = Profesional
    template_name = 'gestion_pie/profesional_form.html'
    success_url = reverse_lazy('profesional-list')
    form_class = ProfesionalForm


class ProfesionalUpdateView(LoginRequiredMixin, UpdateView):
    model = Profesional
    template_name = 'gestion_pie/profesional_form.html'
    success_url = reverse_lazy('profesional-list')
    form_class = ProfesionalForm


class ProfesionalDeleteView(LoginRequiredMixin, DeleteView):
    model = Profesional
    template_name = 'gestion_pie/profesional_confirm_delete.html'
    success_url = reverse_lazy('profesional-list')


# --- INFORME PIE (crear/editar/detalle) ---
class InformePIECreateView(LoginRequiredMixin, CreateView):
    form_class = InformePIEForm
    model = InformePIE
    template_name = 'gestion_pie/informe_pie_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.estudiante = get_object_or_404(Estudiante, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["estudiante"] = self.estudiante
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estudiante'] = self.estudiante
        try:
            context['profesional'] = Profesional.objects.get(user=self.request.user)
        except Profesional.DoesNotExist:
            context['profesional'] = None
        # Mostrar dependencia legible (si existe)
        dep_display = None
        curso = getattr(self.estudiante, "curso", None)
        estb = getattr(curso, "establecimiento", None) if curso else None
        if estb and getattr(estb, "dependencia", None):
            dep_display = getattr(estb, "get_dependencia_display", lambda: estb.dependencia)()
        context["dep_display"] = dep_display
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.estudiante = self.estudiante
        profesional = Profesional.objects.get(user=self.request.user)
        obj.profesional = profesional
        obj.rut_profesional = profesional.rut

        curso = getattr(self.estudiante, "curso", None)
        if curso:
            obj.curso = f"{curso.nivel} {curso.letra} ({curso.anio})"
            estb = getattr(curso, "establecimiento", None)
            if estb:
                obj.nombre_establecimiento = getattr(estb, 'nombre', '') or ''
                obj.rbd = getattr(estb, 'rbd', '') or ''
                obj.dependencia = getattr(estb, 'dependencia', '') or ''

        fn = getattr(self.estudiante, "fecha_nacimiento", None)
        if fn:
            hoy = date.today()
            obj.edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

        obj.save()

        # Registra al autor como colaborador (si no existe)
        InformePIEProfesional.objects.get_or_create(
            informe=obj, profesional=profesional, defaults={"rol": "autor"}
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('estudiante-detail', kwargs={'pk': self.estudiante.pk})


class InformePIEDetailView(LoginRequiredMixin, DetailView):
    model = InformePIE
    template_name = 'gestion_pie/informe_pie_detail.html'
    context_object_name = 'informe'


class InformePIEUpdateView(LoginRequiredMixin, UpdateView):
    model = InformePIE
    template_name = 'gestion_pie/informe_pie_form.html'
    form_class = InformePIEForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        informe = self.get_object()
        context['estudiante'] = informe.estudiante
        context['profesional'] = informe.profesional
        return context

    def get_success_url(self):
        informe = self.get_object()
        return reverse('estudiante-detail', kwargs={'pk': informe.estudiante.pk})


class InformePIEDeleteView(LoginRequiredMixin, DeleteView):
    model = InformePIE
    template_name = 'gestion_pie/informe_pie_confirm_delete.html'
    context_object_name = 'informe'

    def get_success_url(self):
        informe = self.get_object()
        return reverse('estudiante-detail', kwargs={'pk': informe.estudiante.pk})


# ======= NUEVO: Colaboradores y Actividades =======

class InformeAgregarColaboradorView(LoginRequiredMixin, CreateView):
    model = InformePIEProfesional
    form_class = ColaboradorForm
    template_name = "gestion_pie/informe_colaborar_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.informe = get_object_or_404(InformePIE, pk=kwargs["pk"])
        self.pro = request.user.profesional
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {"rol": "otra"}

    def form_valid(self, form):
        obj, created = InformePIEProfesional.objects.get_or_create(
            informe=self.informe, profesional=self.pro, defaults=form.cleaned_data
        )
        if not created:
            for f, v in form.cleaned_data.items():
                setattr(obj, f, v)
            obj.save()
        messages.success(self.request, "Te sumaste como colaborador del informe.")
        return redirect("informe-pie-detail", pk=self.informe.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["informe"] = self.informe
        return ctx


class ActividadCrearView(LoginRequiredMixin, CreateView):
    model = ActividadApoyo
    form_class = ActividadApoyoForm
    template_name = "gestion_pie/actividad_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.informe = get_object_or_404(InformePIE, pk=kwargs["pk"])
        self.pro = request.user.profesional
        self.colab, _ = InformePIEProfesional.objects.get_or_create(
            informe=self.informe, profesional=self.pro, defaults={"rol": "otra"}
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.informe = self.informe
        form.instance.autor = self.pro
        form.instance.colaborador = self.colab
        messages.success(self.request, "Actividad creada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("informe-pie-detail", kwargs={"pk": self.informe.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["informe"] = self.informe
        return ctx


class ActividadUpdateView(LoginRequiredMixin, UpdateView):
    model = ActividadApoyo
    form_class = ActividadApoyoForm
    template_name = "gestion_pie/actividad_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.obj = self.get_object()
        if request.user.profesional != self.obj.autor:
            messages.error(request, "No puedes editar actividades de otro profesional.")
            return redirect("informe-pie-detail", pk=self.obj.informe_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("informe-pie-detail", kwargs={"pk": self.object.informe_id})


class ActividadDeleteView(LoginRequiredMixin, DeleteView):
    model = ActividadApoyo
    template_name = "gestion_pie/actividad_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.obj = self.get_object()
        if request.user.profesional != self.obj.autor:
            messages.error(request, "No puedes borrar actividades de otro profesional.")
            return redirect("informe-pie-detail", pk=self.obj.informe_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Actividad eliminada.")
        return reverse("informe-pie-detail", kwargs={"pk": self.object.informe_id})

class ActividadCreateView(LoginRequiredMixin, CreateView):
    model = ActividadInforme
    form_class = ActividadInformeForm
    template_name = "gestion_pie/actividad_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.informe = get_object_or_404(InformePIE, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        actividad = form.save(commit=False)
        actividad.informe = self.informe
        try:
            actividad.profesional = Profesional.objects.get(user=self.request.user)
        except Profesional.DoesNotExist:
            actividad.profesional = None
        actividad.save()
        return redirect("informe-pie-detail", pk=self.informe.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["informe"] = self.informe
        return ctx

@login_required
def actividad_create(request, pk):
    """Crea una ActividadApoyo para el informe `pk` con el profesional logeado."""
    informe = get_object_or_404(InformePIE, pk=pk)

    # Debe existir Profesional vinculado al user
    try:
        profesional = Profesional.objects.get(user=request.user)
    except Profesional.DoesNotExist:
        messages.error(request, "Tu usuario no está vinculado a un Profesional.")
        return redirect('informe-pie-detail', pk=informe.pk)

    # Asegurar colaborador (se crea automático si no existe)
    colaborador, _ = InformePIEProfesional.objects.get_or_create(
        informe=informe,
        profesional=profesional,
        defaults={'rol': 'colaborador'}
    )

    if request.method == 'POST':
        form = ActividadApoyoForm(request.POST)
        if form.is_valid():
            act = form.save(commit=False)
            act.informe = informe
            act.autor = profesional
            act.colaborador = colaborador
            act.save()
            messages.success(request, "Actividad registrada.")
            return redirect('informe-pie-detail', pk=informe.pk)
        else:
            messages.error(request, "Revisa los campos del formulario.")
    else:
        form = ActividadApoyoForm(initial={
            'fecha': timezone.now().date(),
            'duracion_min': 45,
        })

    return render(request, 'gestion_pie/actividad_form.html', {
        'form': form,
        'informe': informe,
        'modo': 'crear',
    })


@login_required
def actividad_update(request, pk):
    act = get_object_or_404(ActividadApoyo, pk=pk)
    informe = act.informe

    # Sólo el autor puede editar
    try:
        profesional = Profesional.objects.get(user=request.user)
    except Profesional.DoesNotExist:
        messages.error(request, "Tu usuario no está vinculado a un Profesional.")
        return redirect('informe-pie-detail', pk=informe.pk)

    if act.autor_id != profesional.pk:
        messages.error(request, "No puedes editar una actividad de otro profesional.")
        return redirect('informe-pie-detail', pk=informe.pk)

    if request.method == 'POST':
        form = ActividadApoyoForm(request.POST, instance=act)
        if form.is_valid():
            form.save()
            messages.success(request, "Actividad actualizada.")
            return redirect('informe-pie-detail', pk=informe.pk)
        else:
            messages.error(request, "Revisa los campos del formulario.")
    else:
        form = ActividadApoyoForm(instance=act)

    return render(request, 'gestion_pie/actividad_form.html', {
        'form': form,
        'informe': informe,
        'modo': 'editar',
    })


@login_required
def actividad_delete(request, pk):
    act = get_object_or_404(ActividadApoyo, pk=pk)
    informe = act.informe

    try:
        profesional = Profesional.objects.get(user=request.user)
    except Profesional.DoesNotExist:
        messages.error(request, "Tu usuario no está vinculado a un Profesional.")
        return redirect('informe-pie-detail', pk=informe.pk)

    if act.autor_id != profesional.pk:
        messages.error(request, "No puedes borrar una actividad de otro profesional.")
        return redirect('informe-pie-detail', pk=informe.pk)

    if request.method == 'POST':
        act.delete()
        messages.success(request, "Actividad eliminada.")
        return redirect('informe-pie-detail', pk=informe.pk)

    return render(request, 'gestion_pie/actividad_confirm_delete.html', {
        'actividad': act,
        'informe': informe,
    })

# ---- VISTA DE DESCARGA (incluye colaboradores y actividades) ----
@login_required
def descargar_informe_pie(request, pk):
    informe = get_object_or_404(InformePIE, pk=pk)
    
    # Generar el documento usando la utilidad
    doc = generar_docx_informe(informe)

    # Nombre de archivo
    est = informe.estudiante
    def slug(s): 
        return re.sub(r'[^A-Za-z0-9_]+', '_', s or "").strip('_')
    filename = f"Informe_PIE_{slug(getattr(est,'apellidos',''))}_{slug(getattr(est,'nombres',''))}_{localtime(informe.fecha_creacion):%Y-%m-%d}.docx"

    # Respuesta HTTP
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    doc.save(response)
    return response

@login_required
def informe_colaborar(request, pk):
    informe = get_object_or_404(InformePIE, pk=pk)

    # el usuario debe estar vinculado a un Profesional
    try:
        profesional = Profesional.objects.get(user=request.user)
    except Profesional.DoesNotExist:
        messages.error(request, "Tu usuario no está vinculado a un Profesional. Pide a un admin que te registre.")
        return redirect('informe-pie-detail', pk=informe.pk)

    # crea si no existe; si existe, lo edita
    colaborador, created = InformePIEProfesional.objects.get_or_create(
        informe=informe,
        profesional=profesional,
        defaults={'rol': 'colaborador'}  # valor por defecto
    )

    if request.method == "POST":
        form = ColaboradorForm(request.POST, instance=colaborador)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Se guardó tu participación en este informe."
                if not created else "Te sumaste como colaborador."
            )
            return redirect('informe-pie-detail', pk=informe.pk)
        else:
            messages.error(request, "Revisa los campos del formulario.")
    else:
        form = ColaboradorForm(instance=colaborador)

    return render(
        request,
        'gestion_pie/informe_colaborar_form.html',
        {'form': form, 'informe': informe, 'colaborador': colaborador}
    )