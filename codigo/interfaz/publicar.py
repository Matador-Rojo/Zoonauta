"""Arranca Zoonauta en un alojamiento (Render y similares): escucha en 0.0.0.0 y usa el puerto de PORT."""
import os

from codigo.interfaz.servidor import Servidor
from codigo.nucleo.datos import RAIZ_PROYECTO


def main():
    puerto = int(os.environ.get("PORT", 8000))
    servidor = Servidor(("0.0.0.0", puerto), registros=RAIZ_PROYECTO / "registros/interfaz")
    print(f"Zoonauta publicado en el puerto {puerto}.", flush=True)
    servidor.serve_forever()


if __name__ == "__main__":
    main()
