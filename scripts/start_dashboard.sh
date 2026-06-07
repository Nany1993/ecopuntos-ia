#!/usr/bin/env bash
# ECOPUNTOS IA — dashboard Streamlit
# Uso: ./scripts/start_dashboard.sh

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f ".venv/bin/python" ]; then
  echo "Entorno virtual no encontrado. Ejecuta: ./scripts/setup.sh"
  exit 1
fi

if [ ! -f "data/smartsort.db" ]; then
  echo "Base de datos no encontrada. Ejecuta: .venv/bin/python -m scripts.init_db"
fi

"$(dirname "$0")/stop_dashboard.sh" 2>/dev/null || true

echo "ECOPUNTOS IA Dashboard - http://127.0.0.1:8501 (Ctrl+C para detener)"
.venv/bin/python -m streamlit run src/dashboard/app.py --server.headless true --server.runOnSave true
