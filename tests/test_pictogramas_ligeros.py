"""Las copias ligeras de los pictogramas existen, están al día y se sirven en /media."""
import hashlib
import json
import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.request import urlopen

from codigo.interfaz.preparar_pictogramas_ligeros import CARPETA, LADO, pictogramas
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


class PruebasPictogramasLigeros(unittest.TestCase):
    def test_todas_las_copias_existen_y_estan_al_dia(self):
        indice = json.loads((CARPETA / "indice.json").read_text("utf-8"))["items"]
        for pid, original in pictogramas().items():
            if original.suffix == ".svg":
                continue
            with self.subTest(pictograma=pid):
                self.assertIn(pid, indice)
                self.assertEqual(indice[pid]["sha256_original"], hashlib.sha256(original.read_bytes()).hexdigest(),
                                 "Copia desactualizada: ejecuta python -m codigo.interfaz.preparar_pictogramas_ligeros")
                copia = (CARPETA / f"{pid}.webp").read_bytes()
                self.assertLessEqual(max(tamano_webp(copia)), LADO)
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
            finally:
                servidor.shutdown()
                servidor.server_close()


if __name__ == "__main__":
    unittest.main()
