#!/bin/bash

set -e

SERVER="root@146.190.217.223"
SSH_KEY="$HOME/.ssh/id_tribuparidas"

echo "==> Conectando al servidor..."
echo "==> Desplegando backend..."

ssh -i "$SSH_KEY" "$SERVER" 'bash -s' <<'REMOTE_SCRIPT'

set -e

cd /opt/tribuparidas/repo

echo "==> Descargando últimos cambios de GitHub..."
sudo -u tribuparidas git pull origin main

echo "==> Instalando dependencias de Python..."
sudo -u tribuparidas backend/venv/bin/pip install -q -r backend/requirements.txt

echo "==> Ejecutando migraciones..."
cd backend

sudo -u tribuparidas bash -c '
  set -a
  source .env
  set +a
  venv/bin/python manage.py migrate --noinput
'

echo "==> Recopilando archivos estáticos..."

sudo -u tribuparidas bash -c '
  set -a
  source .env
  set +a
  venv/bin/python manage.py collectstatic --noinput
'

echo "==> Ajustando permisos..."
chmod -R o+rX staticfiles media

echo "==> Reiniciando backend..."
systemctl restart tribuparidas-backend

sleep 1

if systemctl is-active --quiet tribuparidas-backend; then
    echo "======================================"
    echo "OK: backend activo"
    echo "======================================"
else
    echo "======================================"
    echo "ERROR: el backend no arrancó"
    echo "======================================"
    echo "Revisa:"
    echo "journalctl -u tribuparidas-backend -n 50"
    exit 1
fi

REMOTE_SCRIPT

echo "==> Deploy terminado."