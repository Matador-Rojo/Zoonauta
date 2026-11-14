"""Compara la 5.0 («/») y la 6.0 («/v6/») pantalla por pantalla, lado a lado.

Es la comprobación obligatoria antes de presentar un cambio visual como «mejora»
(ver CLAUDE.md): obliga a mirar lo anterior y lo nuevo con el mismo estado de partida.
Crea una sesión real en cada pantalla, captura ambas versiones en escritorio y móvil y
guarda un PNG por pareja con la 5.0 a la izquierda y la 6.0 a la derecha.

Uso: python -m tests.comparar_versiones [--salida CARPETA] [--pantallas portada tablero ...]
Salida por defecto: output/comparacion (carpeta local, fuera de Git).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from codigo.interfaz.servidor import Servidor
from tests.ejecutar_navegador import entorno_herramientas
from tests.lighthouse_v6 import _pedir

INICIO = ("iniciar", {"modalidad": "JUGADOR", "retos": 8, "cantidad_opciones": 8})


def _sesion(base: str, hasta: str) -> str:
    """Cookie de una sesión llevada hasta la pantalla pedida, solo por la API."""
    vista, cookie = _pedir(base, "/api/vista")

    def actuar(tipo, payload=None):
        nonlocal vista, cookie
        entrada = {"tipo": tipo, "payload": payload or {}, "evento_id": uuid.uuid4().hex, "revision": vista["revision"],
                   "sesion_id": vista["sesion_id"], "reto_id": vista["reto_id"]}
        resultado, cookie = _pedir(base, "/api/accion", cookie, entrada)
        vista = resultado["vista"]

    if hasta == "portada":
        return cookie
    actuar(*INICIO)
    if hasta == "catalogo":
        return cookie
    actuar("elegir_animal", {"animal_id": vista["catalogo_animales"][0]["id"]})
    if hasta == "tablero":
        return cookie
    if hasta == "acierto":
        for habitat in list(vista["opciones_habitat"]):
            if vista["fase"] != "ESPERANDO_RESPUESTA":
                break
            actuar("seleccionar_habitat", {"habitat_id": habitat["id"]})
        return cookie
    if hasta == "pausa":
        actuar("pausar")
        return cookie
    raise ValueError(f"Pantalla desconocida: {hasta}")


PANTALLAS = ["portada", "catalogo", "tablero", "acierto", "pausa"]


def juntar(carpeta: Path, pantalla: str, dispositivo: str) -> Path:
    from PIL import Image, ImageDraw

    izquierda = Image.open(carpeta / f"5.0_{pantalla}_{dispositivo}.png").convert("RGB")
    derecha = Image.open(carpeta / f"6.0_{pantalla}_{dispositivo}.png").convert("RGB")
    franja, hueco = 44, 16
    alto = max(izquierda.height, derecha.height)
    lienzo = Image.new("RGB", (izquierda.width + derecha.width + hueco, alto + franja), "#222222")
    lienzo.paste(izquierda, (0, franja))
    lienzo.paste(derecha, (izquierda.width + hueco, franja))
    dibujo = ImageDraw.Draw(lienzo)
    dibujo.text((12, 14), f"5.0 (anterior) · {pantalla} · {dispositivo}", fill="white")
    dibujo.text((izquierda.width + hueco + 12, 14), "6.0 (nueva)", fill="white")
    destino = carpeta / f"comparacion_{pantalla}_{dispositivo}.png"
    lienzo.save(destino)
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path("output/comparacion"))
    parser.add_argument("--pantallas", nargs="*", default=PANTALLAS, choices=PANTALLAS)
    args = parser.parse_args()
    env = entorno_herramientas(os.environ)
    with TemporaryDirectory() as carpeta:
        servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
        Thread(target=servidor.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{servidor.server_port}"
        try:
            cookies = {p: _sesion(base, p).split("=", 1)[1] for p in args.pantallas}
            subprocess.run(["node", str(Path(__file__).with_name("comparar_versiones.cjs")), base,
                            str(args.salida), json.dumps(cookies)], env=env, check=True)
        finally:
            servidor.shutdown()
            servidor.server_close()
    for pantalla in args.pantallas:
        for dispositivo in ("escritorio", "movil"):
            print(juntar(args.salida, pantalla, dispositivo))


if __name__ == "__main__":
    main()
