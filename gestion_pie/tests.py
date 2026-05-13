from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profesional, Estudiante, Curso, Establecimiento, InformePIE
from .utils import generar_docx_informe
from django.utils import timezone
from datetime import date

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.profesional = Profesional.objects.create(
            user=self.user,
            nombre_completo='Test Profesional',
            rut='12345678-9',
            especialidad='Psicopedagogo'
        )

    def test_home_view_redirects_if_not_logged_in(self):
        response = self.client.get(reverse('home'))
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(response.status_code in [301, 302])

    def test_home_view_accessible_if_logged_in(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

class DocxGenerationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='docuser', password='password')
        self.profesional = Profesional.objects.create(
            user=self.user,
            nombre_completo='Doc Profesional',
            rut='98765432-1',
            especialidad='Educador'
        )
        self.establecimiento = Establecimiento.objects.create(
            nombre='Escuela Test',
            rbd='12345'
        )
        self.curso = Curso.objects.create(
            establecimiento=self.establecimiento,
            nivel='1ro Basico',
            letra='A',
            anio=2025
        )
        self.estudiante = Estudiante.objects.create(
            run='11223344-5',
            nombres='Juan',
            apellidos='Perez',
            fecha_nacimiento=date(2015, 1, 1),
            curso=self.curso,
            es_pie=True
        )
        self.informe = InformePIE.objects.create(
            estudiante=self.estudiante,
            profesional=self.profesional,
            diagnostico='TEA',
            periodo_inicio=date(2025, 3, 1),
            periodo_fin=date(2025, 12, 31),
            fecha_creacion=timezone.now()
        )

    def test_generar_docx_informe(self):
        # Test that the function runs without error and returns a Document object
        doc = generar_docx_informe(self.informe)
        self.assertIsNotNone(doc)
        # Check if some content is present in the document (basic check)
        # Note: python-docx objects are complex, checking paragraphs is a simple way
        # But tables are separate, so we need to check them too
        text_content = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text_content.append(cell.text)
        
        self.assertTrue(any('INFORME PIE' in t for t in text_content))
        self.assertTrue(any('Juan Perez' in t for t in text_content))
        self.assertTrue(any('I. Identificación' in t for t in text_content))
