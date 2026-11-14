"""Inventario de grabaciones: mensajes completos, textos exactos y respaldo sintético."""
import csv
import http.client
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from codigo.interfaz import catalogo_voz, idiomas, voz_grabada
from codigo.interfaz.servidor import Servidor
from codigo.nucleo.datos import BancoDatos
from codigo.respuestas.generador import GeneradorRespuestas


class Inventario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos(ampliado=True)
        cls.locuciones = catalogo_voz.extraer(cls.banco)
        cls.tabla = catalogo_voz.filas(cls.locuciones)

    def emitibles(self):
        """Cada texto_voz que la partida web del catálogo ampliado puede leer."""
        g = GeneradorRespuestas(self.banco)
        textos = {g.mensaje(m, "A01").texto_voz for m in catalogo_voz.FIJOS}
        textos.add("¿Quién elige el animal?")
        apoyo = g.mensaje("MSG_APOYO_AUTO")
        for pista in self.banco.variantes.values():
            textos |= {g.ayuda(pista, "A01").texto_voz, g.ayuda(pista, "A01", apoyo).texto_voz}
        # Ayudas por rasgo del agente 6.0 (se emiten cuando existen sus grabaciones).
        for ayuda in self.banco.ayudas_rasgo.values():
            plantilla = {**ayuda, "nivel": 1, "variante_id": "RASGO"}
            textos |= {g.ayuda(plantilla, "A01").texto_voz, g.ayuda(plantilla, "A01", apoyo).texto_voz}
        for (animal, habitat), a in self.banco.asociaciones.items():
            if a["estado"] == "VALIDA":
                textos.add(g.mensaje("MSG_VALIDA", animal, habitat, a["contexto"]).texto_voz)
        return textos

    def test_inventario_exhaustivo_y_exacto_en_ambos_idiomas(self):
        es = {f["texto"] for f in self.tabla if f["idioma"] == "es-419"}
        pt = {f["texto"] for f in self.tabla if f["idioma"] == "pt-BR"}
        emitibles = self.emitibles()
        self.assertEqual(emitibles, es)
        self.assertEqual({idiomas.texto(t, "pt-BR", self.banco) if t != "¿Quién elige el animal?"
                          else idiomas.PORTUGUES["interfaz"][t] for t in emitibles}, pt)

    def test_ids_y_conteos(self):
        ids = [loc.id for loc in self.locuciones]
        self.assertEqual(len(ids), len(set(ids)))
        cuenta = {}
        for loc in self.locuciones:
            cuenta[loc.categoria] = cuenta.get(loc.categoria, 0) + 1
        self.assertEqual(144, cuenta["pista"])
        self.assertEqual(144, cuenta["apoyo_con_pista"])
        self.assertEqual(48, cuenta["confirmacion"])
        self.assertEqual(10, cuenta["confirmacion_con_contexto"])
        self.assertEqual(32, cuenta["pista_rasgo"])
        self.assertEqual(32, cuenta["apoyo_con_pista_rasgo"])
        self.assertTrue({p for p in self.banco.variantes} <= set(ids))
        for f in self.tabla:
            self.assertRegex(f["archivo"], r"^(es-419|pt-BR)/[A-Z0-9_]+\.mp3$")

    def test_solo_se_reutiliza_un_mensaje_identico(self):
        for idioma in catalogo_voz.IDIOMAS_GRABACION.values():
            propias = {f["id"]: f for f in self.tabla if f["idioma"] == idioma}
            grabar = [f["texto"] for f in propias.values() if f["grabar"] == "si"]
            self.assertEqual(len(grabar), len(set(grabar)))
            for f in propias.values():
                if f["duplicado_de"]:
                    original = propias[f["duplicado_de"]]
                    self.assertEqual(original["texto"], f["texto"])
                    self.assertEqual(original["archivo"], f["archivo"])
                    self.assertEqual(0, f["creditos_estimados"])

    def test_creditos_por_modelo_y_estado_conservado(self):
        with TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "c.csv"
            catalogo_voz.escribir(self.tabla, ruta, Path(tmp) / "r.json")
            anteriores = catalogo_voz.leer_csv(ruta)
            fila = anteriores[("MSG_INICIO", "es-419")]
            fila.update(estado_generacion="verificado", modelo_elevenlabs="eleven_flash_v2_5", voz_elevenlabs="X")
            nueva = {(f["id"], f["idioma"]): f for f in catalogo_voz.filas(self.locuciones, anteriores)}
            f = nueva[("MSG_INICIO", "es-419")]
            self.assertEqual(("verificado", "X"), (f["estado_generacion"], f["voz_elevenlabs"]))
            self.assertEqual(f["caracteres"] * 0.5, f["creditos_estimados"])
            anteriores[("MSG_PAUSA", "pt-BR")].update(texto="otro", estado_generacion="verificado")
            nueva = {(f["id"], f["idioma"]): f for f in catalogo_voz.filas(self.locuciones, anteriores)}
            self.assertEqual("pendiente", nueva[("MSG_PAUSA", "pt-BR")]["estado_generacion"])
            with ruta.open(encoding="utf-8-sig", newline="") as h:
                self.assertIn("contexto_reproduccion", next(csv.reader(h)))

    def test_busca_solo_el_mensaje_completo(self):
        g = GeneradorRespuestas(self.banco)
        pista = self.banco.variantes["AY_H01_L1"]
        completo = g.ayuda(pista, "A01", g.mensaje("MSG_APOYO_AUTO")).texto_voz
        with TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "es-419").mkdir()
            # Tener las dos partes por separado no basta: nunca se unen audios.
            for nombre in ("MSG_APOYO_AUTO", "AY_H01_L1"):
                (carpeta / f"es-419/{nombre}.mp3").write_bytes(b"ID3" + b"x" * 2048)
            self.assertIsNone(voz_grabada.buscar(completo, "es", self.banco, carpeta))
            self.assertIsNone(voz_grabada.buscar("Texto inventado.", "es", self.banco, carpeta))
            (carpeta / "es-419/MSG_APOYO_AUTO__AY_H01_L1.wav").write_bytes(b"RIFF" + b"x" * 2048)
            self.assertEqual("MSG_APOYO_AUTO__AY_H01_L1.wav",
                             voz_grabada.buscar(completo, "es", self.banco, carpeta).name)
            self.assertIsNone(voz_grabada.buscar(completo, "pt-BR", self.banco, carpeta))
            # El duplicado AY_H05_L1 usa el archivo de AY_H04_L1.
            (carpeta / "es-419/AY_H04_L1.mp3").write_bytes(b"ID3" + b"x" * 2048)
            texto = self.banco.variantes["AY_H05_L1"]["texto"]
            self.assertEqual("AY_H04_L1.mp3", voz_grabada.buscar(texto, "es", self.banco, carpeta).name)
            self.assertEqual(3, catalogo_voz.verificar_audios(self.tabla, carpeta)["presentes"])


class HTTPGrabada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = Servidor(("127.0.0.1", 0))
        Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown(); cls.servidor.server_close()

    def setUp(self):
        self.c = http.client.HTTPConnection("127.0.0.1", self.servidor.server_port)
        self.c.request("GET", "/api/vista")
        r = self.c.getresponse()
        self.cookie = r.getheader("Set-Cookie").split(";")[0]
        self.v = json.loads(r.read())

    def tearDown(self):
        self.c.close()

    def post(self, ruta, **campos):
        entrada = {k: self.v[k] for k in ("revision", "sesion_id", "reto_id")}
        entrada.update(campos)
        self.c.request("POST", ruta, json.dumps(entrada), {"Content-Type": "application/json", "Cookie": self.cookie})
        r = self.c.getresponse()
        return r, r.read()

    def test_grabacion_primero_y_404_para_respaldo(self):
        with TemporaryDirectory() as tmp, patch.object(voz_grabada, "CARPETA_AUDIO", Path(tmp)):
            r, _ = self.post("/api/voz/grabada", idioma="es")
            self.assertEqual(404, r.status)
            (Path(tmp) / "es-419").mkdir()
            (Path(tmp) / "es-419/MSG_INICIO.mp3").write_bytes(b"ID3grabacion")
            r, cuerpo = self.post("/api/voz/grabada", idioma="es")
            self.assertEqual((200, "audio/mpeg", b"ID3grabacion"), (r.status, r.getheader("Content-Type"), cuerpo))
            r, _ = self.post("/api/voz/grabada", idioma="es", texto="Texto externo.")
            self.assertEqual(400, r.status)
            self.c.request("GET", "/api/voz/config", headers={"Cookie": self.cookie})
            config = json.loads(self.c.getresponse().read())
            self.assertEqual({"es": 1, "pt-BR": 0}, config["grabadas"])

    def test_grabacion_permite_reproducir_blob_y_rechaza_pantalla_antigua(self):
        with TemporaryDirectory() as tmp, patch.object(voz_grabada, "CARPETA_AUDIO", Path(tmp)):
            (Path(tmp) / "es-419").mkdir()
            (Path(tmp) / "es-419/MSG_INICIO.mp3").write_bytes(b"ID3grabacion")
            entrada = {k: self.v[k] for k in ("revision", "sesion_id", "reto_id")}
            self.c.request("POST", "/api/voz/grabada", json.dumps({**entrada, "idioma": "es"}),
                           {"Content-Type": "application/json", "Cookie": self.cookie})
            r = self.c.getresponse(); r.read()
            self.assertEqual(200, r.status)
            # El cliente reproduce el audio desde un blob: la CSP debe permitirlo.
            self.assertIn("media-src 'self' blob:", r.getheader("Content-Security-Policy"))
            # Tras cambiar de idioma, la petición de la pantalla anterior se rechaza (409).
            r, _ = self.post("/api/idioma", idioma="pt-BR")
            self.assertEqual(200, r.status)
            self.c.request("POST", "/api/voz/grabada", json.dumps({**entrada, "idioma": "es"}),
                           {"Content-Type": "application/json", "Cookie": self.cookie})
            r = self.c.getresponse(); r.read()
            self.assertEqual(409, r.status)


if __name__ == "__main__":
    unittest.main()
