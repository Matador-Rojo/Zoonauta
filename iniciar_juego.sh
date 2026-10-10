#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"
python3 -m codigo.interfaz.iniciar "$@"
