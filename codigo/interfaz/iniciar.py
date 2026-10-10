"""Abre el juego y prepara las voces locales cuando la conexión lo permite."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

from codigo.nucleo.datos import RAIZ_PROYECTO


def ejecutar(*argumentos):
    subprocess.run(list(map(str, argumentos)), cwd=RAIZ_PROYECTO, check=True)


def python_disponible():
    entorno = RAIZ_PROYECTO / ".venv-voz"
    python = entorno / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return python if python.is_file() else Path(sys.executable)


def preparar():
    entorno = RAIZ_PROYECTO / ".venv-voz"
    python = entorno / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requisitos = RAIZ_PROYECTO / "requirements_voz.txt"
    huella = hashlib.sha256(requisitos.read_bytes()).hexdigest()
    marca = entorno / "zoonauta-dependencias.sha256"
    listo = python.is_file() and marca.is_file() and marca.read_text().strip() == huella
    if not listo:
        print("Preparando las voces locales con Python 3.12. La primera vez requiere Internet.", flush=True)
        if importlib.util.find_spec("uv") is None:
            ejecutar(sys.executable, "-m", "pip", "install", "--user", "uv>=0.8,<1")
        if not python.is_file():
            ejecutar(sys.executable, "-m", "uv", "venv", "--python", "3.12", "--managed-python", entorno)
        ejecutar(sys.executable, "-m", "uv", "pip", "install", "--python", python, "-r", requisitos)
        marca.write_text(huella + "\n")
    resultado = subprocess.run([str(python), "-m", "codigo.interfaz.preparar_voces", "--comprobar"], cwd=RAIZ_PROYECTO)
    if resultado.returncode:
        ejecutar(python, "-m", "codigo.interfaz.preparar_voces")
    return python


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto", type=int, default=8766)
    parser.add_argument("--solo-preparar", action="store_true")
    parser.add_argument("--sin-descargas", action="store_true",
                        help="Abrir con los recursos disponibles, sin instalar ni descargar voces.")
    args = parser.parse_args()
    if args.solo_preparar and args.sin_descargas:
        parser.error("--solo-preparar y --sin-descargas no se pueden combinar.")
    try:
        if args.sin_descargas:
            python = python_disponible()
        else:
            try:
                python = preparar()
            except (OSError, subprocess.CalledProcessError):
                if args.solo_preparar:
                    raise
                print("No se pudo completar la preparación de las voces. "
                      "Abriendo Zoonauta con los recursos disponibles.\n"
                      "Las voces locales completas y las voces compatibles del navegador "
                      "se pueden elegir en Preferencias. El juego también funciona con texto y pictogramas.\n"
                      "Las descargas verificadas se conservan. Para omitir la preparación "
                      "en próximos inicios, usa --sin-descargas.", flush=True)
                python = python_disponible()
        if not args.solo_preparar:
            ejecutar(python, "-m", "codigo.interfaz.servidor", "--abrir", "--puerto", args.puerto)
    except KeyboardInterrupt:
        print("\nZoonauta detenido.")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"No se pudo completar {'la preparación' if args.solo_preparar else 'el inicio'}: {exc}\nLas descargas comprobadas se conservan.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
