"""Inicia un servidor de prueba aislado y verifica la UI con Playwright.

Requiere Node y el módulo Playwright con Chromium instalado, solo para probar.
"""
import argparse
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread

from codigo.interfaz.servidor import Servidor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-real", action="store_true", help="Comprueba WAV con el reproductor nativo; requiere voces preparadas.")
    args = parser.parse_args()
    with TemporaryDirectory() as carpeta:
        servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta))
        hilo = Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        env = {**os.environ, "INTERFAZ_URL": f"http://127.0.0.1:{servidor.server_port}"}
        try:
            prueba = "verificar_audio_real.cjs" if args.audio_real else "verificar_interfaz.cjs"
            resultado = subprocess.run(["node", str(Path(__file__).with_name(prueba))], env=env)
        finally:
            servidor.shutdown()
            servidor.server_close()
        raise SystemExit(resultado.returncode)


if __name__ == "__main__":
    main()
