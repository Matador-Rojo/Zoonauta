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

FRONTEND = Path(__file__).resolve().parent.parent / "frontend" / "node_modules"
CHROME_WINDOWS = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")


def entorno_herramientas(base):
    """Usa por defecto las herramientas fijadas en frontend/ (npm ci) y Chrome del sistema.

    Las variables de entorno que ya estén definidas tienen prioridad.
    """
    env = dict(base)
    defectos = {
        "PLAYWRIGHT_MODULE": FRONTEND / "playwright-core",
        "AXE_SOURCE": FRONTEND / "axe-core" / "axe.min.js",
        "CHROMIUM_EXECUTABLE": CHROME_WINDOWS,
    }
    for clave, ruta in defectos.items():
        if clave not in env and ruta.exists():
            env[clave] = str(ruta)
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-real", action="store_true", help="Comprueba WAV con el reproductor nativo; requiere voces preparadas.")
    parser.add_argument("--voces-navegador", action="store_true", help="Comprueba Microsoft/Google con voces controladas y sus reglas de región.")
    parser.add_argument("--hito2", action="store_true", help="Comprueba 2, 4 y 8 opciones, historial y recarga en ambos idiomas.")
    parser.add_argument("--hito3", action="store_true", help="Comprueba Preferencias en dos columnas, pantallas pequeñas y teclado.")
    parser.add_argument("--catalogo", action="store_true", help="Comprueba tarjetas grandes, paginación adaptable y controles visibles.")
    parser.add_argument("--voz-v6", action="store_true", help="Comprueba la cadena de voz del frontend 6.0 con audio simulado.")
    parser.add_argument("--v6", action="store_true", help="Comprueba el prototipo 6.0 en /v6/: portada de 8 paisajes, Pista, Repetir y recarga.")
    parser.add_argument("--portada", action="store_true", help="Comprueba la portada 6.0 (/v6/): ocho paisajes, rotación, pausa, movimiento reducido y móvil.")
    parser.add_argument("--portada-5", action="store_true", help="Comprueba los 48 fondos de la portada 5.0 y su correspondencia con el catálogo.")
    args = parser.parse_args()
    with TemporaryDirectory() as carpeta:
        servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=args.portada or args.portada_5 or args.v6 or args.voz_v6)
        hilo = Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        env = {**entorno_herramientas(os.environ), "INTERFAZ_URL": f"http://127.0.0.1:{servidor.server_port}"}
        try:
            prueba = ("verificar_voz_v6.cjs" if args.voz_v6 else "verificar_v6.cjs" if args.v6 else "verificar_portada.cjs" if args.portada else "verificar_portada_5.cjs" if args.portada_5 else
                      "verificar_catalogo.cjs" if args.catalogo else "verificar_hito3.cjs" if args.hito3 else "verificar_hito2.cjs" if args.hito2 else "verificar_voces_navegador.cjs" if args.voces_navegador else
                      "verificar_audio_real.cjs" if args.audio_real else "verificar_interfaz.cjs")
            resultado = subprocess.run(["node", str(Path(__file__).with_name(prueba))], env=env)
        finally:
            servidor.shutdown()
            servidor.server_close()
        raise SystemExit(resultado.returncode)


if __name__ == "__main__":
    main()
