# Stress test: 500 usuarios, rampa 50/s, 5 min.
# Ubicación: scripts/run/run-stress.ps1
# Requisito: backend en marcha (ej. .\scripts\run\start-backend.ps1 en otro terminal).
# Locust está en requirements.txt
# Ejecutar desde cualquier sitio: .\scripts\run\run-stress.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $projectRoot

$HostUrl = if ($env:STRESS_HOST) { $env:STRESS_HOST } else { "http://localhost:8000" }
$Users = if ($env:STRESS_USERS) { [int]$env:STRESS_USERS } else { 500 }
$Rate = if ($env:STRESS_RATE) { [int]$env:STRESS_RATE } else { 50 }
$Time = if ($env:STRESS_TIME) { $env:STRESS_TIME } else { "5m" }

Write-Host "Stress test: $Users usuarios, rampa $Rate/s, duracion $Time"
Write-Host "Host: $HostUrl"
Write-Host ""

$locust = Join-Path $projectRoot ".venv\Scripts\locust.exe"
if (Test-Path $locust) {
    & $locust -f load_tests/locustfile.py --host=$HostUrl --headless -u $Users -r $Rate -t $Time
} else {
    & locust -f load_tests/locustfile.py --host=$HostUrl --headless -u $Users -r $Rate -t $Time
}
exit $LASTEXITCODE