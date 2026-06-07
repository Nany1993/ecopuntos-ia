# ECOPUNTOS IA — bot Telegram
# Uso: .\scripts\start.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Entorno virtual no encontrado. Ejecuta:" -ForegroundColor Red
    Write-Host "  .\scripts\setup.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Host "Falta .env - ejecuta .\scripts\setup.ps1 y edita tus claves" -ForegroundColor Red
    exit 1
}

# Evitar error 409: una sola instancia de polling por token
& "$PSScriptRoot\stop_bot.ps1"

Write-Host "ECOPUNTOS IA - bot Telegram..." -ForegroundColor Cyan
Write-Host "Usuario bot: definido en TELEGRAM_BOT_USERNAME (.env)" -ForegroundColor DarkGray
Write-Host "Ctrl+C para detener" -ForegroundColor DarkGray
Write-Host ""

.venv\Scripts\python.exe -m src.bot.telegram_bot
