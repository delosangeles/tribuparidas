#!/bin/bash
# Despliega la última versión de main del backend en producción.
# Copia de referencia versionada en el repo; el que realmente se ejecuta
# vive en el servidor en /opt/tribuparidas/deploy-backend.sh.
#
# Uso (conectado por SSH al servidor): sudo /opt/tribuparidas/deploy-backend.sh
set -e
cd /opt/tribuparidas/repo

echo "==> Descargando últimos cambios de GitHub..."
sudo -u tribuparidas git pull origin main

echo "==> Instalando dependencias de Python..."
sudo -u tribuparidas backend/venv/bin/pip install -q -r backend/requirements.txt

echo "==> Migraciones y estáticos..."
cd backend
sudo -u tribuparidas bash -c 'set -a; source .env; set +a; venv/bin/python manage.py migrate --noinput'
sudo -u tribuparidas bash -c 'set -a; source .env; set +a; venv/bin/python manage.py collectstatic --noinput'
chmod -R o+rX staticfiles media

echo "==> Reiniciando el servicio..."
systemctl restart tribuparidas-backend
sleep 1
systemctl is-active --quiet tribuparidas-backend && echo "OK: backend activo" || echo "ERROR: el backend no arrancó, revisa: journalctl -u tribuparidas-backend -n 50"
