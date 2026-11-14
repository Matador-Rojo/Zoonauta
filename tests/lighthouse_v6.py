"""Lighthouse sobre las pantallas de la interfaz 6.0 (/v6/), en escritorio y móvil.

Crea por HTTP una sesión en cada pantalla (portada, catálogo, tablero, pausa) y pasa
su cookie a Lighthouse. Usa Lighthouse de frontend/node_modules (npm ci) y el Chrome
del sistema. Ejecutar: python -m tests.lighthouse_v6 [--salida CARPETA]
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
from urllib.request import Request, urlopen

from codigo.interfaz.servidor import Servidor
from tests.ejecutar_navegador import CHROME_WINDOWS, FRONTEND

LIGHTHOUSE = FRONTEND / "lighthouse" / "cli" / "index.js"
CATEGORIAS = ["performance", "accessibility", "best-practices", "seo"]


def _pedir(base: str, ruta: str, cookie: str | None = None, cuerpo: dict | None = None):
    cabeceras = {"Content-Type": "application/json"}
    if cookie:
        cabeceras["Cookie"] = cookie
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    with urlopen(Request(base + ruta, data=datos, headers=cabeceras)) as r:
        nueva = r.headers.get("Set-Cookie")
        return json.loads(r.read()), (nueva.split(";")[0] if nueva else cookie)


def _sesion(base: str, acciones: list[tuple[str, dict]]) -> str:
    vista, cookie = _pedir(base, "/api/vista")
    for tipo, payload in acciones:
        if tipo == "elegir_animal":
            payload = {"animal_id": vista["catalogo_animales"][0]["id"]}
        entrada = {"tipo": tipo, "payload": payload, "evento_id": uuid.uuid4().hex, "revision": vista["revision"],
                   "sesion_id": vista["sesion_id"], "reto_id": vista["reto_id"]}
        resultado, cookie = _pedir(base, "/api/accion", cookie, entrada)
        vista = resultado["vista"]
    return cookie


PANTALLAS = {
    "portada": [],
    "catalogo": [("iniciar", {"modalidad": "JUGADOR", "retos": 8, "cantidad_opciones": 8})],
    "tablero": [("iniciar", {"modalidad": "JUGADOR", "retos": 8, "cantidad_opciones": 8}), ("elegir_animal", {})],
    "pausa": [("iniciar", {"modalidad": "AGENTE", "retos": 8, "cantidad_opciones": 4}), ("pausar", {})],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=Path("output/lighthouse"))
    parser.add_argument("--pantallas", nargs="*", default=list(PANTALLAS))
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    env = {**os.environ}
    if "CHROME_PATH" not in env and CHROME_WINDOWS.exists():
        env["CHROME_PATH"] = str(CHROME_WINDOWS)
    resumen = {}
    with TemporaryDirectory() as carpeta:
        servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
        Thread(target=servidor.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{servidor.server_port}"
        try:
            for nombre in args.pantallas:
                cookie = _sesion(base, PANTALLAS[nombre])
                for dispositivo in ("escritorio", "movil"):
                    informe = args.salida / f"{nombre}_{dispositivo}.json"
                    orden = ["node", str(LIGHTHOUSE), base + "/v6/", "--quiet", "--output=json",
                             f"--output-path={informe}", f"--only-categories={','.join(CATEGORIAS)}",
                             f"--extra-headers={json.dumps({'Cookie': cookie})}",
                             "--chrome-flags=--headless=new --no-first-run"]
                    if dispositivo == "escritorio":
                        orden.append("--preset=desktop")
                    subprocess.run(orden, env=env, check=True)
                    datos = json.loads(informe.read_text("utf-8"))
                    puntos = {c: round(datos["categories"][c]["score"] * 100) for c in CATEGORIAS}
                    fallos = sorted(a["id"] for a in datos["audits"].values()
                                    if a.get("score") is not None and a["score"] < 0.9
                                    and a.get("scoreDisplayMode") in ("binary", "numeric", "metricSavings"))
                    metricas = {m: datos["audits"][m]["displayValue"] for m in
                                ("first-contentful-paint", "largest-contentful-paint", "total-blocking-time",
                                 "cumulative-layout-shift") if m in datos["audits"]}
                    resumen[f"{nombre}/{dispositivo}"] = {"puntos": puntos, "metricas": metricas, "a_revisar": fallos}
                    print(json.dumps({f"{nombre}/{dispositivo}": puntos}, ensure_ascii=False), flush=True)
        finally:
            servidor.shutdown()
            servidor.server_close()
    (args.salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
