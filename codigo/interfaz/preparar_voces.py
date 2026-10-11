"""Descarga las voces públicas verificadas del catálogo; no requiere cuentas."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

from codigo.nucleo.datos import RAIZ_PROYECTO


def directorio_voces() -> Path:
    return Path(os.environ.get("ZOONAUTA_VOCES_DIR", RAIZ_PROYECTO / "modelos_voz")).resolve()


def catalogo() -> dict:
    return json.loads((RAIZ_PROYECTO / "datos/voces_locales.json").read_text(encoding="utf-8"))


def archivo_verificado(archivo: Path, ficha: dict) -> bool:
    if not archivo.is_file() or archivo.stat().st_size != ficha["bytes"]:
        return False
    h = hashlib.new(ficha["hash_tipo"])
    with archivo.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest() == ficha["hash"]


def descargar(ficha: dict, raiz: Path) -> None:
    destino = raiz / ficha["archivo"]
    if archivo_verificado(destino, ficha):
        print(f"Disponible: {destino.name}", flush=True)
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(destino.suffix + ".part")
    for intento in range(3):
        try:
            print(f"Descargando: {destino.name} ({ficha['bytes'] / 1e6:.1f} MB)", flush=True)
            req = Request(ficha["url"], headers={"User-Agent": "Zoonauta/4.0"})
            with urlopen(req, timeout=60) as respuesta, temporal.open("wb") as salida:
                total = 0
                for bloque in iter(lambda: respuesta.read(1024 * 1024), b""):
                    total += len(bloque)
                    if total > ficha["bytes"]:
                        raise ValueError("La descarga supera el tamaño esperado.")
                    salida.write(bloque)
            if not archivo_verificado(temporal, ficha):
                raise ValueError("La descarga no coincide con la huella del catálogo.")
            temporal.replace(destino)
            print(f"Verificado: {destino.name}", flush=True)
            return
        except Exception:
            temporal.unlink(missing_ok=True)
            if intento == 2:
                raise
            time.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comprobar", action="store_true", help="Comprobar archivos sin descargar.")
    args = parser.parse_args()
    c, raiz = catalogo(), directorio_voces()
    if args.comprobar:
        faltantes = [f["archivo"] for f in c["archivos"] if not archivo_verificado(raiz / f["archivo"], f)]
        if faltantes:
            print("Faltan archivos verificados: " + ", ".join(faltantes))
            raise SystemExit(1)
        print(f"Las {len(c['voces'])} opciones de voz están preparadas.")
        return
    print(f"Voces locales: {c['bytes_descarga'] / 1e6:.1f} MB en la primera descarga. Sin claves de API.", flush=True)
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda f: descargar(f, raiz), c["archivos"]))
    except Exception as exc:
        print(f"No se completó la preparación: {type(exc).__name__}: {exc}")
        print("Vuelve a ejecutar la preparación. Los archivos ya verificados se conservan.")
        raise SystemExit(1)
    print(f"Preparadas las {len(c['voces'])} opciones. Ya puedes iniciar Zoonauta.", flush=True)


if __name__ == "__main__":
    main()
