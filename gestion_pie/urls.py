# gestion_pie/urls.py
from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='home'),

    # Estudiantes
    path('estudiantes/', views.EstudianteListView.as_view(), name='estudiante-list'),
    path('estudiante/crear/', views.EstudianteCreateView.as_view(), name='estudiante-create'),
    path('estudiante/<str:pk>/', views.EstudianteDetailView.as_view(), name='estudiante-detail'),
    path('estudiante/<str:pk>/editar/', views.EstudianteUpdateView.as_view(), name='estudiante-update'),
    path('estudiante/<str:pk>/borrar/', views.EstudianteDeleteView.as_view(), name='estudiante-delete'),

    # Informes PIE
    path('estudiante/<str:pk>/informe/nuevo/', views.InformePIECreateView.as_view(), name='informe-pie-create'),
    path('informe/<int:pk>/', views.InformePIEDetailView.as_view(), name='informe-pie-detail'),
    path('informe/<int:pk>/editar/', views.InformePIEUpdateView.as_view(), name='informe-pie-update'),
    path('informe/<int:pk>/borrar/', views.InformePIEDeleteView.as_view(), name='informe-pie-delete'),

    # Descarga Word (bonito)
    path('informe/<int:pk>/descargar/', views.descargar_informe_pie, name='informe-pie-descargar'),
    path('informe/<int:pk>/colaborar/', views.informe_colaborar, name='informe-colaborar'),
    path('informe/<int:pk>/actividad/nueva/', views.actividad_create, name='actividad-create'),
    path('actividad/<int:pk>/editar/', views.actividad_update, name='actividad-update'),
    path('actividad/<int:pk>/borrar/', views.actividad_delete, name='actividad-delete'),
    # (Opcional) Ruta a la clase si la estás usando aún
    #path('informe/<int:pk>/word/', views.InformePIEWordView.as_view(), name='informe-pie-word'),

    # Cursos
    path('cursos/', views.CursoListView.as_view(), name='curso-list'),
    path('curso/crear/', views.CursoCreateView.as_view(), name='curso-create'),
    path('curso/<int:pk>/', views.CursoDetailView.as_view(), name='curso-detail'),
    path('curso/<int:pk>/editar/', views.CursoUpdateView.as_view(), name='curso-update'),
    path('curso/<int:pk>/borrar/', views.CursoDeleteView.as_view(), name='curso-delete'),

    # Profesionales
    path('profesionales/', views.ProfesionalListView.as_view(), name='profesional-list'),
    path('profesional/crear/', views.ProfesionalCreateView.as_view(), name='profesional-create'),
    path('profesional/<int:pk>/', views.ProfesionalDetailView.as_view(), name='profesional-detail'),
    path('profesional/<int:pk>/editar/', views.ProfesionalUpdateView.as_view(), name='profesional-update'),
    path('profesional/<int:pk>/borrar/', views.ProfesionalDeleteView.as_view(), name='profesional-delete'),
]
