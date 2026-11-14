"""Genera copias ligeras de los pictogramas para servirlas en la interfaz.

Los originales (hasta 1254 px y 746 KB) se conservan sin cambios en su carpeta. Las
copias se derivan de ellos: lado mayor de 384 px (el doble del tamaño máximo en
pantalla), WebP calidad 82. `indice.json` guarda la huella SHA-256 de cada original
para detectar copias desactualizadas. Solo hace falta Pillow para regenerarlas; el
juego no lo necesita para servirlas.

Uso: python -m codigo.interfaz.preparar_pictogramas_ligeros
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO

CARPETA = RAIZ_PROYECTO / "assets/pictogramas_ligeros"
LADO = 384
CALIDAD = 82


def huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def pictogramas() -> dict[str, Path]:
    """Todos los pictogramas de ambos catálogos (ampliado y original)."""
    resultado = {}
    for ampliado in (True, False):
        for pid, datos in BancoDatos(ampliado=ampliado).pictogramas.items():
            resultado.setdefault(pid, RAIZ_PROYECTO / datos["archivo_imagen"])
    return resultado


def leer_indice() -> dict:
    ruta = CARPETA / "indice.json"
    return json.loads(ruta.read_text("utf-8")) if ruta.is_file() else {"items": {}}


def main():
    from PIL import Image  # Solo para regenerar.

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todo", action="store_true", help="Regenera también las copias al día.")
    args = parser.parse_args()
    CARPETA.mkdir(parents=True, exist_ok=True)
    indice = leer_indice()
    items = {}
    generadas = 0
    for pid, original in sorted(pictogramas().items()):
        if original.suffix not in {".webp", ".png", ".jpg"}:
            continue  # Los SVG ya son ligeros: se sirven tal cual.
        h = huella(original)
        destino = CARPETA / f"{pid}.webp"
        previo = indice["items"].get(pid)
        if args.todo or not destino.is_file() or not previo or previo["sha256_original"] != h:
            with Image.open(original) as imagen:
                imagen = imagen.convert("RGBA")
                imagen.thumbnail((LADO, LADO), Image.LANCZOS)
                imagen.save(destino, "WEBP", quality=CALIDAD, method=4)
            generadas += 1
        items[pid] = {"original": original.relative_to(RAIZ_PROYECTO).as_posix(), "sha256_original": h}
    documento = {"schema_version": "1.0.0", "lado_maximo": LADO, "calidad_webp": CALIDAD,
                 "procedencia": "Derivadas de los originales sin otra edición que el cambio de tamaño; "
                                "conservan la licencia y los créditos del original.",
                 "items": items}
    (CARPETA / "indice.json").write_text(json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    print(json.dumps({"pictogramas": len(items), "generadas": generadas}, ensure_ascii=False))


if __name__ == "__main__":
    main()
