"""Cobertura educativa bilingüe, invariantes y contrato HTTP de idioma y voz grabada."""
from copy import deepcopy
from dataclasses import asdict
import http.client
import json
from threading import Thread
import unittest
from uuid import uuid4

from codigo.interfaz import idiomas
from codigo.interfaz.servidor import Servidor
from codigo.interfaz.servicio import ConflictoVista, SesionWeb
from codigo.nucleo.datos import BancoDatos
from codigo.respuestas.generador import GeneradorRespuestas


class Idiomas(unittest.TestCase):
    def setUp(self):
        self.banco = BancoDatos()
        self.s = SesionWeb(self.banco)

    def entrada(self, **campos):
        v = self.s.vista()
        return dict(revision=v["revision"], sesion_id=v["sesion_id"], reto_id=v["reto_id"], **campos)

    def actuar(self, tipo, **payload):
        return self.s.actuar(self.entrada(tipo=tipo, payload=payload, evento_id=uuid4().hex))

    def test_todas_las_respuestas_y_composiciones_tienen_traduccion(self):
        g = GeneradorRespuestas(self.banco)
        for mensaje in self.banco.mensajes:
            for habitat in self.banco.habitats:
                r = asdict(g.mensaje(mensaje, "A01", habitat))
                self.assertTrue(idiomas.respuesta(r, "pt-BR")["texto_voz"])
        for ayuda in self.banco.variantes.values():
            for prefijo in (None, g.mensaje("MSG_INCORRECTA_VALIDADA"), g.mensaje("MSG_APOYO_AUTO")):
                r = asdict(g.ayuda(ayuda, "A01", prefijo))
                pt = idiomas.respuesta(r, "pt-BR")
                self.assertEqual(r["pictogramas"], pt["pictogramas"])
                self.assertEqual(r["variante_id"], pt["variante_id"])
        for (animal, habitat), relacion in self.banco.asociaciones.items():
            if relacion["estado"] == "VALIDA":
                r = asdict(g.mensaje("MSG_VALIDA", animal, habitat, relacion.get("contexto")))
                self.assertTrue(idiomas.respuesta(r, "pt-BR")["texto_voz"].startswith("Sim!"))

    def test_cambiar_idioma_conserva_estado_observacion_y_modelo(self):
        self.actuar("iniciar", modalidad="AGENTE")
        self.actuar("ayuda")
        antes = deepcopy(self.s.revision_tecnica())
        recibos = deepcopy(self.s._recibos)
        respuesta = deepcopy(self.s.respuesta)
        v = self.s.cambiar_idioma(self.entrada(idioma="pt-BR"))
        despues = self.s.revision_tecnica()
        despues["idioma"] = antes["idioma"]
        self.assertEqual(antes, despues)
        self.assertEqual(recibos, self.s._recibos)
        self.assertEqual(respuesta, self.s.respuesta)
        self.assertEqual("pt-BR", v["idioma"])
        self.assertEqual("Capivara", v["catalogo_animales"][30]["nombre"])
        self.assertEqual(95, len(v["pictogramas"]))

    def test_recorrido_portugues_pendiente_confirmacion_repetir_pausa(self):
        self.s.cambiar_idioma(self.entrada(idioma="pt-BR"))
        self.actuar("iniciar", modalidad="JUGADOR", retos=1)
        self.actuar("elegir_animal", animal_id="A31")
        r = self.actuar("ayuda")["respuesta_emitida"]
        self.assertEqual(r, self.actuar("repetir")["respuesta_emitida"])
        self.actuar("pausar")
        self.assertEqual(r, self.actuar("reanudar")["respuesta_emitida"])
        apoyo = self.actuar("seleccionar_habitat", habitat_id="H03")["respuesta_emitida"]
        self.assertEqual("NEUTRAL", apoyo["tipo_respuesta"])
        self.assertEqual(2, apoyo["nivel"])
        self.assertTrue(apoyo["texto_voz"].startswith("Vamos procurar outro lugar."))
        self.assertEqual(apoyo, self.actuar("repetir")["respuesta_emitida"])
        confirmacion = self.actuar("seleccionar_habitat", habitat_id="H01")
        self.assertIn("floresta tropical", confirmacion["respuesta_emitida"]["texto_voz"])
        self.assertEqual("COMPLETADA", self.actuar("continuar")["vista"]["fase"])

    def test_idioma_invalido_y_pantalla_antigua_no_alteran_idioma(self):
        for idioma in (None, [], "pt", "fr", True):
            with self.assertRaises(ValueError):
                self.s.cambiar_idioma(self.entrada(idioma=idioma))
        e = self.entrada(idioma="pt-BR")
        self.actuar("iniciar", modalidad="AGENTE")
        with self.assertRaises(ConflictoVista):
            self.s.cambiar_idioma(e)
        self.assertEqual("es", self.s.idioma)

    def test_pregunta_de_modalidad_se_lee_sin_alterar_la_partida(self):
        for idioma, pregunta in [
            ("es", "¿Quién elige el animal?"),
            ("pt-BR", "Quem escolhe o animal?"),
            ("en", "Who chooses the animal?"),
        ]:
            self.s.cambiar_idioma(self.entrada(idioma=idioma))
            antes = deepcopy(self.s.revision_tecnica())
            self.assertEqual(pregunta, self.s.texto_voz(self.entrada(idioma=idioma, contexto="modalidad")))
            self.assertEqual(antes, self.s.revision_tecnica())

    def test_contexto_de_modalidad_fuera_de_inicio_se_rechaza(self):
        with self.assertRaises(ValueError):
            self.s.texto_voz(self.entrada(idioma="es", contexto="inventado"))
        with self.assertRaises(ConflictoVista):
            self.s.texto_voz(self.entrada(idioma="es", contexto="modalidad", prueba=True))
        self.actuar("iniciar", modalidad="AGENTE")
        with self.assertRaises(ConflictoVista):
            self.s.texto_voz(self.entrada(idioma="es", contexto="modalidad"))

    def test_lectura_previa_y_cambio_de_idioma_se_rechazan(self):
        e = self.entrada(idioma="es", prueba=True)
        self.assertEqual(idiomas.saludo("es"), self.s.texto_voz(e))
        self.s.cambiar_idioma(self.entrada(idioma="pt-BR"))
        with self.assertRaises(ConflictoVista):
            self.s.texto_voz(e)
        self.assertEqual(idiomas.saludo("pt-BR"), self.s.texto_voz(self.entrada(idioma="pt-BR", prueba=True)))


class HTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = Servidor(("127.0.0.1", 0))
        cls.hilo = Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

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
        return self.c.getresponse()

    def test_cambio_de_idioma_localiza_la_vista(self):
        r = self.post("/api/idioma", idioma="pt-BR")
        self.assertEqual(200, r.status)
        self.v = json.loads(r.read())["vista"]
        self.assertEqual("Floresta tropical úmida", self.v["opciones_habitat"][0]["nombre"])

    def test_sin_voces_sintetizadas(self):
        # Desde 2026-11-14 solo existe la voz grabada: no hay síntesis ni cancelación de síntesis.
        for ruta in ("/api/voz", "/api/voz/cancelar"):
            r = self.post(ruta, idioma="es", prueba=True)
            self.assertEqual(404, r.status); r.read()

    def test_origen_ajeno_bloqueado_y_configuracion_de_voz(self):
        self.c.request("POST", "/api/idioma", "{}", {"Origin": "https://otro.example", "Content-Type": "application/json"})
        r = self.c.getresponse(); self.assertEqual(403, r.status); r.read()
        self.c.request("GET", "/api/voz/config")
        r = self.c.getresponse(); configuracion = json.loads(r.read())
        self.assertEqual([], configuracion["voces"])
        self.assertEqual({"es", "pt-BR", "en"}, set(configuracion["grabadas"]))


if __name__ == "__main__":
    unittest.main()
