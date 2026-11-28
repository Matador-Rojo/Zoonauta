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
                    # La mitad de los animales pide las tres pistas antes de elegir; la otra
                    # mitad falla antes de pedir ayuda (apoyo automático tras los fallos).
                    if indice % 2 == 0:
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
                # La pregunta del selector de modalidad (Comenzar) también tiene grabación.
                pregunta = "¿Quién elige el animal?"
                leidos.add(pregunta)
                if voz_grabada.buscar(pregunta, "es", banco) is None:
                    faltan[pregunta] = "INTERFAZ_MODALIDAD"
            finally:
                servidor.shutdown()
                servidor.server_close()

            print(f"\n{len(leidos)} mensajes distintos leídos; {len(leidos) - len(faltan)} con grabación")
            self.assertGreater(len(leidos), 100)
            self.assertEqual(faltan, {}, f"{len(faltan)} mensajes sin grabación de {len(leidos)} leídos")

    def test_voces_multiples_es(self):
        carpeta_valeria = CARPETA_AUDIO / "es-419-valeria"
        carpeta_gaby = CARPETA_AUDIO / "es-419-gaby"
        carpeta_diego = CARPETA_AUDIO / "es-419-diego"
        if not (
            carpeta_valeria.is_dir()
            and any(carpeta_valeria.glob("*.mp3"))
            and carpeta_gaby.is_dir()
            and any(carpeta_gaby.glob("*.mp3"))
            and carpeta_diego.is_dir()
            and any(carpeta_diego.glob("*.mp3"))
        ):
            self.skipTest("sin grabaciones locales de Valeria, Gaby o Diego")
        with TemporaryDirectory() as carpeta:
            servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
            Thread(target=servidor.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{servidor.server_port}"
            try:
                cfg, _ = _pedir(base, "/api/voz/config")
                voces_es = cfg.get("voces_grabadas", {}).get("es", [])
                ids = [v["id"] for v in voces_es]
                self.assertEqual(ids, ["marcela", "valeria", "gaby", "diego"])
                for v in voces_es:
                    self.assertEqual(v["cantidad"], 412)
                # Comprueba que los cuatro archivos existen y son distintos en disco
                banco = servidor.banco
                rutas = [
                    voz_grabada.buscar("¿Dónde puede vivir este animal?", "es", banco, voz=vid)
                    for vid in ids
                ]
                for ruta in rutas:
                    self.assertIsNotNone(ruta)
                contenidos = {ruta.read_bytes() for ruta in rutas if ruta is not None}
                self.assertEqual(len(contenidos), 4)
            finally:
                servidor.shutdown()
                servidor.server_close()

    def test_cobertura_completa_pt_br_roberta_y_will(self):
        carpeta_pt = CARPETA_AUDIO / "pt-BR"
        carpeta_will = CARPETA_AUDIO / "pt-BR-will"
        if not (
            carpeta_pt.is_dir()
            and any(carpeta_pt.glob("*.mp3"))
            and carpeta_will.is_dir()
            and any(carpeta_will.glob("*.mp3"))
        ):
            self.skipTest("sin grabaciones locales de Roberta o Will (pt-BR)")
        with TemporaryDirectory() as carpeta:
            servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
            Thread(target=servidor.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{servidor.server_port}"
            try:
                cfg, _ = _pedir(base, "/api/voz/config")
                self.assertEqual(cfg["grabadas"]["pt-BR"], 412)
                voces_pt = cfg.get("voces_grabadas", {}).get("pt-BR", [])
                self.assertEqual(
                    voces_pt,
                    [
                        {"id": "roberta", "etiqueta": "Roberta · ElevenLabs", "cantidad": 412},
                        {"id": "will", "etiqueta": "Will · ElevenLabs", "cantidad": 412},
                    ],
                )
                banco = servidor.banco
                r = voz_grabada.buscar("Onde este animal pode viver?", "pt-BR", banco, voz="roberta")
                w = voz_grabada.buscar("Onde este animal pode viver?", "pt-BR", banco, voz="will")
                self.assertIsNotNone(r)
                self.assertIsNotNone(w)
                self.assertGreater(r.stat().st_size, 1000)
                self.assertGreater(w.stat().st_size, 1000)
                self.assertNotEqual(r.read_bytes(), w.read_bytes())
            finally:
                servidor.shutdown()
                servidor.server_close()

    def test_cobertura_completa_en_mark_y_jessica(self):
        carpeta_en = CARPETA_AUDIO / "en"
        carpeta_jessica = CARPETA_AUDIO / "en-jessica"
        if not (
            carpeta_en.is_dir()
            and any(carpeta_en.glob("*.mp3"))
            and carpeta_jessica.is_dir()
            and any(carpeta_jessica.glob("*.mp3"))
        ):
            self.skipTest("sin grabaciones locales de Mark o Jessica (en)")
        with TemporaryDirectory() as carpeta:
            servidor = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
            Thread(target=servidor.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{servidor.server_port}"
            try:
                cfg, _ = _pedir(base, "/api/voz/config")
                self.assertEqual(cfg["grabadas"]["en"], 412)
                voces_en = cfg.get("voces_grabadas", {}).get("en", [])
                self.assertEqual(
                    voces_en,
                    [
                        {"id": "jessica", "etiqueta": "Jessica · ElevenLabs", "cantidad": 412},
                        {"id": "mark", "etiqueta": "Mark · ElevenLabs", "cantidad": 412},
                    ],
                )
                banco = servidor.banco
                m = voz_grabada.buscar("Where can this animal live?", "en", banco, voz="mark")
                j = voz_grabada.buscar("Where can this animal live?", "en", banco, voz="jessica")
                self.assertIsNotNone(m)
                self.assertIsNotNone(j)
                self.assertGreater(m.stat().st_size, 1000)
                self.assertGreater(j.stat().st_size, 1000)
                self.assertNotEqual(m.read_bytes(), j.read_bytes())
            finally:
                servidor.shutdown()
                servidor.server_close()


if __name__ == "__main__":
    unittest.main()
