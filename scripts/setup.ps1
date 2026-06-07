# ECOPUNTOS IA — instalacion inicial (Windows)
# Uso: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host ""
Write-Host "ECOPUNTOS IA - Instalacion" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "Python: $pyVersion" -ForegroundColor DarkGray
} catch {
    Write-Host "Python no encontrado. Instala Python 3.11+ desde https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Entorno virtual
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Instalando dependencias..." -ForegroundColor Yellow
.venv\Scripts\python.exe -m pip install --upgrade pip -q
.venv\Scripts\pip install -r requirements.txt -q

# .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Archivo .env creado. OBLIGATORIO editarlo antes de usar el bot:" -ForegroundColor Yellow
    Write-Host "  TELEGRAM_BOT_TOKEN   -> token de @BotFather" -ForegroundColor White
    Write-Host "  TELEGRAM_BOT_USERNAME -> nombre de tu bot (sin @)" -ForegroundColor White
    Write-Host "  GEMINI_API_KEY       -> https://aistudio.google.com/apikey" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ".env ya existe (no se sobrescribe)" -ForegroundColor DarkGray
}

# Base de datos y QR
Write-Host "Inicializando base de datos..." -ForegroundColor Yellow
.venv\Scripts\python.exe -m scripts.init_db

Write-Host "Generando codigos QR de canecas..." -ForegroundColor Yellow
.venv\Scripts\python.exe -m scripts.generate_qr

Write-Host ""
Write-Host "Instalacion completada." -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor Cyan
Write-Host "  1. Edita .env con tus claves (si aun no lo hiciste)" -ForegroundColor White
Write-Host "  2. Terminal 1: .\scripts\start.ps1" -ForegroundColor White
Write-Host "  3. Terminal 2: .\scripts\start_dashboard.ps1" -ForegroundColor White
Write-Host "  4. Dashboard: http://127.0.0.1:8501" -ForegroundColor White
Write-Host ""
Write-Host "Datos demo (opcional): .venv\Scripts\python.exe -m scripts.seed_demo_data --limpiar" -ForegroundColor DarkGray
Write-Host ""
