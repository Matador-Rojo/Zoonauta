"""Probar un paquete extraído sin entorno ni voces, con seis partidas por HTTP."""
from __future__ import annotations

import argparse
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

from codigo.nucleo.verificar_paquete import verificar


def comprobar(raiz: Path, salida: Path) -> dict:
    raiz, salida = raiz.resolve(), salida.resolve()
    integridad = verificar(raiz)
    if not integridad["correcto"]:
        raise ValueError(f"El paquete no coincide con su manifiesto: {integridad['errores']}")
    if (raiz / ".venv-voz").exists() or (raiz / "modelos_voz").exists():
        raise ValueError("La copia debe comenzar sin entorno ni modelos de voz.")
    salida.mkdir(parents=True, exist_ok=True)
    ganchos = salida / "ganchos"
    ganchos.mkdir(exist_ok=True)
    # Solo se suprime la apertura de una ventana. El iniciador y el servidor
    # originales se ejecutan como procesos separados desde la copia extraída.
    (ganchos / "sitecustomize.py").write_text(
        "import webbrowser\nwebbrowser.open = lambda *args, **kwargs: True\n",
        encoding="utf-8", newline="\n")
    with socket.socket() as reserva:
        reserva.bind(("127.0.0.1", 0))
        puerto = reserva.getsockname()[1]
    base = f"http://127.0.0.1:{puerto}"
    cliente = build_opener(HTTPCookieProcessor(CookieJar()))

    def obtener(ruta):
        with cliente.open(base + ruta, timeout=10) as r:
            return json.load(r)

    def actuar(tipo, **payload):
        v = obtener("/api/vista")
        entrada = {"tipo": tipo, "payload": payload, "evento_id": uuid4().hex,
            "revision": v["revision"], "sesion_id": v["sesion_id"], "reto_id": v["reto_id"]}
        req = Request(base + "/api/accion", json.dumps(entrada).encode(), {"Content-Type": "application/json"})
        with cliente.open(req, timeout=10) as r:
            respuesta = json.load(r)
        if not respuesta["aceptada"]:
            raise AssertionError(f"Acción rechazada: {tipo}, {respuesta['motivo']}")
        return respuesta["vista"]

    entorno = {**os.environ, "PYTHONPATH": str(ganchos), "PYTHONUTF8": "1",
               "PYTHONDONTWRITEBYTECODE": "1", "ZOONAUTA_VOCES_DIR": str(raiz / "modelos_voz")}
    comando = [sys.executable, "-m", "codigo.interfaz.iniciar", "--sin-descargas", "--puerto", str(puerto)]
    partidas = []
    with (salida / "inicio.log").open("wb") as log:
        proceso = subprocess.Popen(comando, cwd=raiz, env=entorno, stdin=subprocess.DEVNULL,
            stdout=log, stderr=log, **({"start_new_session": True} if os.name != "nt" else {}))
        try:
            limite = time.monotonic() + 20
            while True:
                try:
                    v = obtener("/api/vista")
                    break
                except OSError:
                    if proceso.poll() is not None or time.monotonic() >= limite:
                        raise AssertionError("El iniciador no abrió el juego sin descargas.")
                    time.sleep(0.1)
            assert len(v["catalogo_animales"]) == 48
            voces = obtener("/api/voz/config")["voces"]
            assert len(voces) == 14 and not any(v["disponible"] for v in voces)
            for modalidad in ("AGENTE", "JUGADOR"):
                for n in (2, 4, 8):
                    v = actuar("iniciar", modalidad=modalidad, retos=1, cantidad_opciones=n)
                    if modalidad == "JUGADOR":
                        v = actuar("elegir_animal", animal_id="A02")
                    opciones = v["opciones_habitat"]
                    assert len(opciones) == n and v["fase"] == "ESPERANDO_RESPUESTA"
                    guia = obtener("/api/revision")["estado"]["habitat_guia_id"]
                    assert guia in [h["id"] for h in opciones]
                    v = actuar("ayuda")
                    contenido = v["respuesta"]
                    assert actuar("repetir")["respuesta"] == contenido
                    assert actuar("pausar")["fase"] == "PAUSADA"
                    v = actuar("reanudar")
                    assert v["respuesta"] == contenido and v["opciones_habitat"] == opciones
                    v = actuar("seleccionar_habitat", habitat_id=guia)
                    assert v["fase"] == "RETO_RESUELTO" and v["progreso"]["completados"] == 1
                    assert actuar("continuar")["fase"] == "COMPLETADA"
                    actuar("nueva_partida")
                    partidas.append({"modalidad": modalidad, "opciones": n, "resultado": "OK"})
            assert not (raiz / ".venv-voz").exists() and not (raiz / "modelos_voz").exists()
        finally:
            if proceso.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(proceso.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                else:
                    os.killpg(proceso.pid, signal.SIGTERM)
            proceso.wait(timeout=10)
    resultado = {"schema_version": "1.0.0", "correcto": True, "integridad": integridad,
        "sin_instalaciones_ni_descargas": True, "sin_modelos_voz": True,
        "voces_catalogadas_no_preparadas": len(voces), "partidas": partidas,
        "alcance": "Iniciador real sin descargas y partidas HTTP completas. No verifica escucha de voz ni comprensión humana."}
    (salida / "revision_copia_limpia.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--carpeta", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    resultado = comprobar(args.carpeta, args.salida)
    print(json.dumps({"correcto": resultado["correcto"], "partidas": len(resultado["partidas"])}))


if __name__ == "__main__":
    main()
