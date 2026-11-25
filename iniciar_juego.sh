#!/usr/bin/env bash
set -euo pipefail
export PYTHONUTF8=1
cd -- "$(dirname -- "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró python3. Instala Python 3.10 o posterior para ejecutar Zoonauta." >&2
  exit 1
fi

exec python3 -m codigo.interfaz.iniciar "$@"
