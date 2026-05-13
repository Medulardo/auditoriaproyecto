#!/usr/bin/env bash
# Detener el proceso si ocurre un error
set -o errexit

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Recopilando archivos estáticos..."
python manage.py collectstatic --no-input

echo "Aplicando migraciones a la base de datos..."
python manage.py migrate