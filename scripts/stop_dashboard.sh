#!/usr/bin/env bash
# Detiene instancias del dashboard ECOPUNTOS IA en ejecucion
# Uso: ./scripts/stop_dashboard.sh

set +e
cd "$(dirname "$0")/.."

detenidos=0
while IFS= read -r pid; do
  if [ -n "$pid" ]; then
    echo "Deteniendo dashboard (PID $pid)..."
    kill -9 "$pid" 2>/dev/null
    detenidos=$((detenidos + 1))
  fi
done < <(pgrep -f "streamlit run src/dashboard/app.py" 2>/dev/null)

if [ "$detenidos" -eq 0 ]; then
  echo "No habia instancias del dashboard en ejecucion."
else
  echo "Listo: $detenidos instancia(s) detenida(s)."
  sleep 2
fi
