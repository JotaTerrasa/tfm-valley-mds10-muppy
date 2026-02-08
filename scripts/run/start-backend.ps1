# Arranca el backend FastAPI (puerto 8000).
# Ubicación: scripts/run/start-backend.ps1
# Ejecutar desde cualquier sitio (el script cambia a la raíz del proyecto):
#   .\scripts\run\start-backend.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $projectRoot

$uvicorn = Join-Path $projectRoot ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path $uvicorn)) {
    Write-Host "No se encuentra el venv. Crea uno en la raíz: python -m venv .venv" -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando backend en http://0.0.0.0:8000 ..." -ForegroundColor Green
Write-Host "(Ctrl+C para parar)" -ForegroundColor Gray
& $uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
exit $LASTEXITCODE