"""Abre Zoonauta en el navegador (http://127.0.0.1:8766).

Desde la 6.0 (2026-11-14) no se descarga ni se instala nada: la voz de la guía son las
grabaciones de Zoonauta que vienen en el repositorio (assets/voz/grabada) y el servidor
solo usa la biblioteca estándar de Python. Basta con Python 3.10 o posterior.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from codigo.nucleo.datos import RAIZ_PROYECTO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto", type=int, default=8766)
    args = parser.parse_args()
    try:
        subprocess.run([sys.executable, "-m", "codigo.interfaz.servidor", "--abrir", "--puerto", str(args.puerto)],
                       cwd=RAIZ_PROYECTO, check=True)
    except KeyboardInterrupt:
        print("\nZoonauta detenido.")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"No se pudo iniciar Zoonauta: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
