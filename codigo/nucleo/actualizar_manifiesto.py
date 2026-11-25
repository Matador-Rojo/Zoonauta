"""Actualizar datos/manifest.json con los archivos cambiados según Git.

Uso: python -m codigo.nucleo.actualizar_manifiesto [--incluir RUTA ...]

- Recalcula bytes y sha256 de los archivos ya listados que cambiaron.
- Añade archivos nuevos solo de frontend/ y web6/, o los indicados con --incluir.
- Quita entradas de archivos borrados (p. ej. compilados viejos de web6/).
- Conserva el orden y el formato del manifiesto. No toca archivos fuera de las
  carpetas del paquete ni los JSON con CRLF heredados.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from codigo.nucleo.datos import RAIZ_PROYECTO

CARPETAS = ("codigo/", "frontend/", "tests/", "assets/", "datos/expedicion/")
# Solo aquí se registran archivos nuevos sin pedirlo; el resto exige --incluir
# (evita registrar trabajo ajeno en curso, como grabaciones sin revisar).
NUEVOS_AUTOMATICOS = ("frontend/", "codigo/interfaz/web6/")
EXCLUIDOS = ("datos/manifest.json", "frontend/node_modules/")


def _git(*args: str) -> list[str]:
    salida = subprocess.run(["git", *args], cwd=RAIZ_PROYECTO, capture_output=True, text=True, check=True).stdout
    return [linea for linea in salida.splitlines() if linea]


def _ficha(ruta: str) -> dict:
    datos = (RAIZ_PROYECTO / ruta).read_bytes()
    return {"ruta": ruta, "bytes": len(datos), "sha256": hashlib.sha256(datos).hexdigest()}


def actualizar(incluir: list[str]) -> dict:
    archivo = RAIZ_PROYECTO / "datos/manifest.json"
    manifiesto = json.loads(archivo.read_text("utf-8"))
    cambiados = set(_git("diff", "--name-only", "HEAD")) | set(_git("ls-files", "--others", "--exclude-standard"))
    cambiados |= set(incluir)
    candidatos = {r for r in cambiados if r.startswith(CARPETAS) and not r.startswith(EXCLUIDOS)} | set(incluir)
    resumen = {"actualizados": [], "nuevos": [], "quitados": []}
    conservados, vistos = [], set()
    for ficha in manifiesto["archivos"]:
        ruta = ficha["ruta"]
        if not (RAIZ_PROYECTO / ruta).is_file():
            resumen["quitados"].append(ruta)
            continue
        if ruta in candidatos:
            nueva = _ficha(ruta)
            if nueva != ficha:
                ficha.update(nueva)
                resumen["actualizados"].append(ruta)
        conservados.append(ficha)
        vistos.add(ruta)
    for ruta in sorted(candidatos - vistos):
        if not (ruta.startswith(NUEVOS_AUTOMATICOS) or ruta in incluir):
            resumen.setdefault("omitidos_nuevos", []).append(ruta)
            continue
        if (RAIZ_PROYECTO / ruta).is_file():
            conservados.append(_ficha(ruta))
            resumen["nuevos"].append(ruta)
    manifiesto["archivos"] = conservados
    archivo.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incluir", nargs="*", default=[], help="Rutas adicionales a registrar.")
    args = parser.parse_args()
    print(json.dumps(actualizar(args.incluir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
