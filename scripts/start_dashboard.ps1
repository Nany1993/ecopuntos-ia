# ECOPUNTOS IA — dashboard Streamlit
# Uso: .\scripts\start_dashboard.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Entorno virtual no encontrado. Ejecuta: .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "data\smartsort.db")) {
    Write-Host "Base de datos no encontrada. Ejecuta: .\scripts\setup.ps1" -ForegroundColor Yellow
}

# Evitar instancia antigua con codigo en cache (puerto 8501)
& "$PSScriptRoot\stop_dashboard.ps1"

Write-Host "ECOPUNTOS IA Dashboard - http://127.0.0.1:8501" -ForegroundColor Green
Write-Host "Ctrl+C para detener" -ForegroundColor DarkGray

.venv\Scripts\python.exe -m streamlit run src/dashboard/app.py --server.headless true --server.runOnSave true
