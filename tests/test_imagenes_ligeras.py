"""Las copias ligeras (pictogramas, paisajes, robot) existen, están al día y se sirven."""
import hashlib
import json
import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import urlopen

from codigo.interfaz.preparar_imagenes_ligeras import CARPETA, GRUPOS, ORIGENES
from codigo.interfaz.servidor import Servidor
from codigo.nucleo.datos import RAIZ_PROYECTO


def tamano_webp(datos: bytes) -> tuple[int, int]:
    """Ancho y alto de un WebP (VP8, VP8L o VP8X) sin dependencias externas."""
    fragmento = datos[12:16]
    if fragmento == b"VP8X":
        ancho = int.from_bytes(datos[24:27], "little") + 1
        alto = int.from_bytes(datos[27:30], "little") + 1
        return ancho, alto
    if fragmento == b"VP8L":
        bits = struct.unpack("<I", datos[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    ancho, alto = struct.unpack("<HH", datos[26:30])
    return ancho & 0x3FFF, alto & 0x3FFF


class PruebasImagenesLigeras(unittest.TestCase):
    def test_todas_las_copias_existen_y_estan_al_dia(self):
        for grupo, datos in GRUPOS.items():
            indice = json.loads((datos["carpeta"] / "indice.json").read_text("utf-8"))["items"]
            for clave, original in ORIGENES[grupo]().items():
                if original.suffix == ".svg":
                    continue
                with self.subTest(grupo=grupo, imagen=clave):
                    self.assertIn(clave, indice)
                    self.assertEqual(indice[clave]["sha256_original"], hashlib.sha256(original.read_bytes()).hexdigest(),
                                     "Copia desactualizada: ejecuta python -m codigo.interfaz.preparar_imagenes_ligeras")
                    copia = (datos["carpeta"] / f"{clave}.webp").read_bytes()
                    self.assertLessEqual(max(tamano_webp(copia)), datos["lado"])
                    self.assertLess(len(copia), original.stat().st_size)

    def test_el_servidor_entrega_la_copia_ligera(self):
        with TemporaryDirectory() as carpeta:
            servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta))
            hilo = Thread(target=servidor.serve_forever, daemon=True)
            hilo.start()
            try:
                pid = "P_AYUDA"
                with urlopen(f"http://127.0.0.1:{servidor.server_port}/media/{pid}") as respuesta:
                    self.assertEqual(respuesta.headers["Content-Type"], "image/webp")
                    self.assertEqual(respuesta.read(), (CARPETA / f"{pid}.webp").read_bytes())
                original = RAIZ_PROYECTO / servidor.banco.pictogramas[pid]["archivo_imagen"]
                self.assertTrue(original.is_file(), "el original se conserva")
                base = f"http://127.0.0.1:{servidor.server_port}"
                for ruta, copia in (("/habitats/H01.webp", GRUPOS["paisajes"]["carpeta"] / "H01.webp"),
                                    ("/ilustraciones/robot_pausa.webp", GRUPOS["ilustraciones"]["carpeta"] / "robot_pausa.webp")):
                    with urlopen(base + ruta) as respuesta:
                        self.assertEqual(respuesta.read(), copia.read_bytes(), ruta)
            finally:
                servidor.shutdown()
                servidor.server_close()


if __name__ == "__main__":
    unittest.main()
