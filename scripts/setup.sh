#!/usr/bin/env bash
# ECOPUNTOS IA — instalacion inicial (Linux / macOS)
# Uso: chmod +x scripts/setup.sh && ./scripts/setup.sh

set -euo pipefail
cd "$(dirname "$0")/.."

echo ""
echo "ECOPUNTOS IA - Instalacion"
echo "=========================="
echo ""

if ! command -v python3 &>/dev/null; then
  echo "Python 3 no encontrado. Instala Python 3.11+."
  exit 1
fi
echo "Python: $(python3 --version)"

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
fi

echo "Instalando dependencias..."
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "Archivo .env creado. OBLIGATORIO editarlo antes de usar el bot:"
  echo "  TELEGRAM_BOT_TOKEN    -> token de @BotFather"
  echo "  TELEGRAM_BOT_USERNAME -> nombre de tu bot (sin @)"
  echo "  GEMINI_API_KEY        -> https://aistudio.google.com/apikey"
  echo ""
else
  echo ".env ya existe (no se sobrescribe)"
fi

echo "Inicializando base de datos..."
.venv/bin/python -m scripts.init_db

echo "Generando codigos QR de canecas..."
.venv/bin/python -m scripts.generate_qr

echo ""
echo "Instalacion completada."
echo ""
echo "Siguiente paso:"
echo "  1. Edita .env con tus claves"
echo "  2. Terminal 1: ./scripts/start.sh"
echo "  3. Terminal 2: ./scripts/start_dashboard.sh"
echo "  4. Dashboard: http://127.0.0.1:8501"
echo ""
