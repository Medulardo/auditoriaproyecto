# Proyecto PIE

Este es un proyecto Django para la gestión PIE (Programa de Integración Escolar).

## Requisitos Previos

- Python 3.x
- MySQL (debido a que el proyecto usa mysqlclient)

## Configuración del Entorno

### 1. Clonar el Repositorio

```bash
git clone https://github.com/poisomn/project_pie.git
cd project_pie
```

### 2. Crear un Entorno Virtual

En Windows, ejecuta los siguientes comandos en PowerShell:

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar Dependencias

Con el entorno virtual activado, instala las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

Las dependencias principales incluyen:
- Django 5.2.1
- django-crispy-forms 2.4
- crispy-bootstrap5 2025.6
- django-filter 25.2
- mysqlclient 2.2.7

### 4. Configuración de la Base de Datos

1. Asegúrate de tener MySQL instalado y corriendo
2. Crea una base de datos para el proyecto
3. Configura las credenciales de la base de datos en `config/settings.py`

### 5. Migraciones de la Base de Datos

Ejecuta las migraciones para crear las tablas en la base de datos:

```bash
python manage.py migrate
```

### 6. Crear un Superusuario (Opcional)

Para acceder al panel de administración, crea un superusuario:

```bash
python manage.py createsuperuser
```

### 7. Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

El proyecto estará disponible en `http://127.0.0.1:8000/`

## Estructura del Proyecto

- `config/`: Configuraciones principales del proyecto Django
- `gestion_pie/`: Aplicación principal con la lógica de negocio
- `templates/`: Plantillas HTML del proyecto
  - `gestion_pie/`: Plantillas específicas para la gestión PIE
- `manage.py`: Script de gestión de Django

## Funcionalidades Principales

El sistema incluye gestión de:
- Cursos
- Estudiantes
- Profesionales

Cada entidad cuenta con sus propias vistas para:
- Listado
- Detalle
- Creación
- Edición
- Eliminación

## Tecnologías Utilizadas

- Django 5.2.1
- Bootstrap 5 (via crispy-bootstrap5)
- MySQL
- django-crispy-forms para el manejo de formularios
- django-filter para filtrado de datos