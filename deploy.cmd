@echo off
setlocal

cd /d "%~dp0"

echo ============================================
echo   Tribu Paridas - Subir cambios a produccion
echo ============================================
echo.
set /p CONFIRM="Vas a subir cambios a https://tribuparidas.com - continuar? (S/N): "
if /i not "%CONFIRM%"=="S" (
    echo Cancelado.
    exit /b 0
)

echo.
echo ===== 1/3: Commit y push a GitHub =====
set /p MSG="Mensaje del commit (vacio = omitir commit): "
if not "%MSG%"=="" (
    git add -A
    git commit -m "%MSG%"
)
git push origin main
if errorlevel 1 (
    echo ERROR al hacer push. Revisa el mensaje de arriba. Abortando.
    pause
    exit /b 1
)

echo.
echo ===== 2/3: Backend en el servidor =====
ssh -i "%USERPROFILE%\.ssh\id_tribuparidas" root@146.190.217.223 "/opt/tribuparidas/deploy-backend.sh"
if errorlevel 1 (
    echo ERROR desplegando el backend. Revisa el mensaje de arriba.
    pause
    exit /b 1
)

echo.
echo ===== 3/3: Frontend (build + subida) =====
bash deploy-frontend.sh
if errorlevel 1 (
    echo ERROR desplegando el frontend. Revisa el mensaje de arriba.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Listo: https://tribuparidas.com/directorio/
echo ============================================
pause
