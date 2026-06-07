#!/usr/bin/env bash
# Detiene instancias del bot ECOPUNTOS IA
# Uso: ./scripts/stop_bot.sh

set -euo pipefail
cd "$(dirname "$0")/.."

detenidos=0
while IFS= read -r pid; do
  echo "Deteniendo bot (PID $pid)..."
  kill "$pid" 2>/dev/null || true
  detenidos=$((detenidos + 1))
done < <(pgrep -f 'src\.bot\.telegram_bot' || true)

rm -f data/bot.lock

if [ "$detenidos" -eq 0 ]; then
  echo "No habia instancias del bot en ejecucion."
else
  echo "Listo: $detenidos instancia(s) detenida(s)."
  sleep 2
fi
