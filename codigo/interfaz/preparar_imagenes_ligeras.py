"""Genera copias ligeras de las imágenes que la interfaz muestra pequeñas.

Los originales se conservan sin cambios en su carpeta. Cada copia se deriva del
original solo cambiando su tamaño (WebP) y conserva su licencia y créditos. Cada
grupo tiene un `indice.json` con la huella SHA-256 de los originales para detectar
copias desactualizadas (tests/test_imagenes_ligeras.py). Solo hace falta Pillow para
regenerarlas; el juego no lo necesita para servirlas.

| Grupo | Origen | Lado mayor | Uso |
|---|---|---|---|
| pictogramas | datos de ambos catálogos | 384 px | /media/<id> |
| paisajes | paisaje de cada hábitat | 560 px (calidad 75) | /habitats/<id>.webp |
| ilustraciones | robot de pausa y de despedida | 640 px | /ilustraciones/<nombre>.webp |

Uso: python -m codigo.interfaz.preparar_imagenes_ligeras [--todo]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO

CALIDAD = 82
GRUPOS = {
    "pictogramas": {"carpeta": RAIZ_PROYECTO / "assets/pictogramas_ligeros", "lado": 384},
    "paisajes": {"carpeta": RAIZ_PROYECTO / "assets/paisajes_ligeros", "lado": 560, "calidad": 75},
    "ilustraciones": {"carpeta": RAIZ_PROYECTO / "assets/ilustraciones_ligeras", "lado": 640},
}
# Compatibilidad con el nombre anterior del grupo de pictogramas.
CARPETA = GRUPOS["pictogramas"]["carpeta"]


def huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def pictogramas() -> dict[str, Path]:
    """Todos los pictogramas de ambos catálogos (ampliado y original)."""
    resultado = {}
    for ampliado in (True, False):
        for pid, datos in BancoDatos(ampliado=ampliado).pictogramas.items():
            resultado.setdefault(pid, RAIZ_PROYECTO / datos["archivo_imagen"])
    return resultado


def paisajes() -> dict[str, Path]:
    """Paisaje de cada hábitat del catálogo ampliado (las tarjetas del tablero)."""
    return {h: RAIZ_PROYECTO / datos["paisaje"] for h, datos in BancoDatos(ampliado=True).habitats.items()}


def ilustraciones() -> dict[str, Path]:
    return {n: RAIZ_PROYECTO / "assets/ilustraciones" / f"{n}.webp" for n in ("robot_pausa", "robot_despedida")}


ORIGENES = {"pictogramas": pictogramas, "paisajes": paisajes, "ilustraciones": ilustraciones}


def leer_indice(grupo: str = "pictogramas") -> dict:
    ruta = GRUPOS[grupo]["carpeta"] / "indice.json"
    return json.loads(ruta.read_text("utf-8")) if ruta.is_file() else {"items": {}}


def preparar(grupo: str, todo: bool = False) -> dict:
    from PIL import Image  # Solo para regenerar.

    carpeta, lado = GRUPOS[grupo]["carpeta"], GRUPOS[grupo]["lado"]
    calidad = GRUPOS[grupo].get("calidad", CALIDAD)
    carpeta.mkdir(parents=True, exist_ok=True)
    previo = leer_indice(grupo)["items"]
    items, generadas = {}, 0
    for clave, original in sorted(ORIGENES[grupo]().items()):
        if original.suffix not in {".webp", ".png", ".jpg"}:
            continue  # Los SVG ya son ligeros: se sirven tal cual.
        h = huella(original)
        destino = carpeta / f"{clave}.webp"
        if todo or not destino.is_file() or previo.get(clave, {}).get("sha256_original") != h:
            with Image.open(original) as imagen:
                imagen = imagen.convert("RGBA")
                imagen.thumbnail((lado, lado), Image.LANCZOS)
                imagen.save(destino, "WEBP", quality=calidad, method=4)
            generadas += 1
        items[clave] = {"original": original.relative_to(RAIZ_PROYECTO).as_posix(), "sha256_original": h}
    documento = {"schema_version": "1.0.0", "lado_maximo": lado, "calidad_webp": calidad,
                 "procedencia": "Derivadas de los originales sin otra edición que el cambio de tamaño; "
                                "conservan la licencia y los créditos del original.",
                 "items": items}
    (carpeta / "indice.json").write_text(json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    return {"grupo": grupo, "imagenes": len(items), "generadas": generadas}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todo", action="store_true", help="Regenera también las copias al día.")
    parser.add_argument("--grupos", nargs="*", default=list(GRUPOS))
    args = parser.parse_args()
    for grupo in args.grupos:
        print(json.dumps(preparar(grupo, args.todo), ensure_ascii=False))


if __name__ == "__main__":
    main()
