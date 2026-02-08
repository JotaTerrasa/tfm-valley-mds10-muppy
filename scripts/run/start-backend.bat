@echo off
REM Arranca el backend FastAPI (puerto 8000).
REM Ubicación: scripts\run\start-backend.bat
REM Doble clic o desde la raíz: scripts\run\start-backend.bat

cd /d "%~dp0..\.."

if not exist ".venv\Scripts\uvicorn.exe" (
    echo No se encuentra el venv. Crea uno en la raíz: python -m venv .venv
    pause
    exit /b 1
)

echo Iniciando backend en http://localhost:8000 ...
echo Ctrl+C para parar
.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
pause