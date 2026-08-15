#!/bin/sh
set -e

echo "Esperando a Postgres en ${POSTGRES_HOST}:${POSTGRES_PORT}..."
while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"; do
  sleep 0.5
done
echo "Postgres disponible."

# Sin argumentos (docker compose up): arranque normal del servidor de desarrollo.
# Con argumentos (docker compose run backend <comando>): se ejecuta tal cual,
# sin forzar migrate/runserver (útil para makemigrations, shell, pytest, etc).
if [ "$#" -eq 0 ]; then
  python manage.py migrate --noinput

  if [ -n "${DJANGO_SUPERUSER_EMAIL}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
    python manage.py ensure_superuser
  fi

  exec python manage.py runserver 0.0.0.0:8000
else
  exec "$@"
fi
