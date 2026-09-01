#!/bin/bash
# Compila el frontend para producción y lo sube al servidor.
# Uso (desde Git Bash, en la raíz del repo): ./deploy-frontend.sh
#
# Requiere: haber corrido "git pull" antes si quieres desplegar los últimos
# cambios, y tener la llave ~/.ssh/id_tribuparidas autorizada en el servidor.
set -e

SERVER="root@146.190.217.223"
SSH_KEY="$HOME/.ssh/id_tribuparidas"
REMOTE_DIR="/opt/tribuparidas/frontend"

cd "$(dirname "$0")/frontend"

echo "==> Instalando dependencias..."
npm install

echo "==> Compilando (SPA, raíz del dominio, API de producción)..."
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"
export NUXT_PUBLIC_API_BASE="https://tribuparidas.com/api"
export NUXT_APP_BASE_URL="/"
export NUXT_PUBLIC_SITE_NAME="Tribu Paridas"
npm run generate

echo "==> Empaquetando..."
cd .output/public
tar -czf /tmp/tribuparidas-frontend.tar.gz .

echo "==> Subiendo al servidor..."
scp -i "$SSH_KEY" /tmp/tribuparidas-frontend.tar.gz "$SERVER:/tmp/frontend.tar.gz"

echo "==> Publicando..."
ssh -i "$SSH_KEY" "$SERVER" "
  rm -rf $REMOTE_DIR/* &&
  tar -xzf /tmp/frontend.tar.gz -C $REMOTE_DIR &&
  rm /tmp/frontend.tar.gz &&
  chown -R tribuparidas:tribuparidas $REMOTE_DIR &&
  chmod -R o+rX $REMOTE_DIR
"

rm /tmp/tribuparidas-frontend.tar.gz
echo "==> Listo: https://tribuparidas.com/"
