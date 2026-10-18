"""Verificar el manifiesto local, incluidos los saltos de línea declarados de BAT."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

from codigo.nucleo.datos import RAIZ_PROYECTO


def verificar(raiz: Path) -> dict:
    raiz = raiz.resolve()
    manifiesto = json.loads((raiz / "datos/manifest.json").read_text("utf-8"))
    atributos = (raiz / ".gitattributes").read_text("utf-8") if (raiz / ".gitattributes").exists() else ""
    bat_crlf = "*.bat text eol=crlf" in atributos.splitlines()
    errores, normalizados, vistos = [], [], set()
    for ficha in manifiesto["archivos"]:
        nombre = ficha["ruta"]
        ruta = PurePosixPath(nombre)
        if ruta.is_absolute() or ".." in ruta.parts or "\\" in nombre or ":" in nombre or nombre in vistos:
            errores.append({"ruta": nombre, "motivo": "RUTA_INVALIDA_O_DUPLICADA"})
            continue
        vistos.add(nombre)
        archivo = (raiz / nombre).resolve()
        if not archivo.is_relative_to(raiz) or not archivo.is_file():
            errores.append({"ruta": nombre, "motivo": "ARCHIVO_AUSENTE_O_EXTERNO"})
            continue
        contenido = archivo.read_bytes()
        coincide = lambda b: len(b) == ficha["bytes"] and hashlib.sha256(b).hexdigest() == ficha["sha256"]
        if coincide(contenido):
            continue
        # GitHub exporta estos iniciadores con CRLF por .gitattributes. Solo se
        # acepta esa transformación exacta; el resto se comprueba por su huella.
        if ruta.suffix == ".bat" and bat_crlf and coincide(contenido.replace(b"\r\n", b"\n")):
            normalizados.append(nombre)
        else:
            errores.append({"ruta": nombre, "motivo": "CONTENIDO_O_TAMANO_DISTINTO"})
    return {"schema_version": "1.0.0", "correcto": not errores, "archivos": len(vistos),
            "normalizaciones_crlf_declaradas": normalizados, "errores": errores}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--carpeta", type=Path, default=RAIZ_PROYECTO)
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    resultado = verificar(args.carpeta)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8", newline="\n")
    print(texto)
    raise SystemExit(0 if resultado["correcto"] else 1)


if __name__ == "__main__":
    main()
