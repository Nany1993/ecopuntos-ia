#!/usr/bin/env bash
# ECOPUNTOS IA — bot Telegram
# Uso: ./scripts/start.sh

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f ".venv/bin/python" ]; then
  echo "Entorno virtual no encontrado. Ejecuta: ./scripts/setup.sh"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Falta .env — copia .env.example y configura TELEGRAM_BOT_TOKEN y GEMINI_API_KEY"
  exit 1
fi

echo "ECOPUNTOS IA - bot Telegram (Ctrl+C para detener)"
.venv/bin/python -m src.bot.telegram_bot
