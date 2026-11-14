"""Cobertura de la voz grabada de Zoonauta (Marcela, ElevenLabs) en español.

La 6.0 solo usa grabaciones (decisión del propietario, 2026-11-14): si un mensaje no tiene
su mp3, la guía se quedaría callada. Esta prueba juega por la API todos los animales del
catálogo ampliado (Pista hasta el nivel 3, un fallo, el acierto, Repetir, Pausar, Reanudar,
Continuar, Salir y el cierre) y comprueba que cada texto que la guía leería tiene grabación.
Se omite si las grabaciones no están en assets/voz/grabada/es-419 (son locales).
"""
from __future__ import annotations

import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from codigo.interfaz import voz_grabada
from codigo.interfaz.catalogo_voz import CARPETA_AUDIO
from codigo.interfaz.servidor import Servidor
from tests.lighthouse_v6 import _pedir

CARPETA = CARPETA_AUDIO / "es-419"


@unittest.skipUnless(CARPETA.is_dir() and any(CARPETA.glob("*.mp3")), "sin grabaciones locales")
class CoberturaVozGrabada(unittest.TestCase):
    def test_todos_los_mensajes_de_la_partida_tienen_grabacion(self):
        with TemporaryDirectory() as carpeta:
            servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
            Thread(target=servidor.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{servidor.server_port}"
            banco = servidor.banco
            faltan: dict[str, str] = {}
            leidos: set[str] = set()

            def revisar(vista):
                texto = vista["respuesta"]["texto_voz"]
                if not texto or texto in leidos:
                    return
                leidos.add(texto)
                if voz_grabada.buscar(texto, "es", banco) is None:
                    faltan[texto] = vista["respuesta"].get("contenido_id", "?")

            try:
                vista, cookie = _pedir(base, "/api/vista")
                revisar(vista)

                def actuar(tipo, payload=None):
                    nonlocal vista, cookie
                    entrada = {"tipo": tipo, "payload": payload or {}, "evento_id": uuid.uuid4().hex,
                               "revision": vista["revision"], "sesion_id": vista["sesion_id"],
                               "reto_id": vista["reto_id"]}
                    resultado, cookie = _pedir(base, "/api/accion", cookie, entrada)
                    vista = resultado["vista"]
                    revisar(vista)
                    return resultado

                total = len(vista["catalogo_animales"])
                actuar("iniciar", {"modalidad": "JUGADOR", "retos": 48, "cantidad_opciones": 8})
                ids = [a["id"] for a in vista["catalogo_animales"]]
                jugados = 0
                for indice, animal in enumerate(ids):
                    if vista["fase"] != "SELECCION_ANIMAL":
                        actuar("nueva_partida")
                        actuar("iniciar", {"modalidad": "JUGADOR", "retos": 48, "cantidad_opciones": 8})
                    actuar("elegir_animal", {"animal_id": animal})
                    for _ in range(3):
                        if "ayuda" in vista["controles_disponibles"]:
                            actuar("ayuda")
                    if indice % 24 == 0:  # controles de partida en una muestra de retos
                        actuar("repetir")
                        actuar("pausar")
                        actuar("reanudar")
                    for habitat in list(vista["opciones_habitat"]):
                        if vista["fase"] != "ESPERANDO_RESPUESTA":
                            break
                        actuar("seleccionar_habitat", {"habitat_id": habitat["id"]})
                    actuar("continuar")
                    jugados += 1
                actuar("salir")
                self.assertEqual(jugados, total)
            finally:
                servidor.shutdown()
                servidor.server_close()

            print(f"\n{len(leidos)} mensajes distintos leídos; {len(leidos) - len(faltan)} con grabación")
            self.assertGreater(len(leidos), 100)
            self.assertEqual(faltan, {}, f"{len(faltan)} mensajes sin grabación de {len(leidos)} leídos")


if __name__ == "__main__":
    unittest.main()
