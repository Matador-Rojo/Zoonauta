"""Cobertura educativa bilingüe, invariantes y contrato de audio local."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import http.client
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch
from uuid import uuid4
import wave

from codigo.interfaz import idiomas
from codigo.interfaz.preparar_voces import archivo_verificado
from codigo.interfaz.servidor import Servidor
from codigo.interfaz.servicio import ConflictoVista, SesionWeb
from codigo.interfaz.voz import MotorVoz, VozNoDisponible
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
        for idioma in (None, [], "pt", "en", True):
            with self.assertRaises(ValueError):
                self.s.cambiar_idioma(self.entrada(idioma=idioma))
        e = self.entrada(idioma="pt-BR")
        self.actuar("iniciar", modalidad="AGENTE")
        with self.assertRaises(ConflictoVista):
            self.s.cambiar_idioma(e)
        self.assertEqual("es", self.s.idioma)

    def test_pregunta_de_modalidad_se_lee_sin_alterar_la_partida(self):
        for idioma, pregunta in [("es", "¿Quién elige el animal?"), ("pt-BR", "Quem escolhe o animal?")]:
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


class Voz(unittest.TestCase):
    def test_catalogo_completo_sin_voces_del_navegador(self):
        m = MotorVoz()
        voces = m.configuracion()["voces"]
        self.assertEqual(14, len(voces))
        for idioma in ("es", "pt-BR"):
            self.assertEqual(7, sum(v["idioma"] == idioma for v in voces))
        self.assertEqual(3, sum(v["motor"] == "piper" and v["region"] == "MX" for v in voces))
        self.assertEqual(1, sum(v["motor"] == "piper" and v["region"] == "AR" for v in voces))

    def test_voz_invalida_o_idioma_incorrecto_no_cargan_modelos(self):
        m = MotorVoz()
        for voz, idioma in [("google", "es"), ("kokoro:ef_dora", "pt-BR"), ([], "es")]:
            with self.assertRaises(ValueError):
                m.sintetizar(voz, "Hola.", idioma)
        self.assertFalse(m.modelos)

    def test_modelos_ausentes_error_y_juego_sigue_disponible(self):
        with TemporaryDirectory() as carpeta:
            m = MotorVoz(Path(carpeta))
            self.assertFalse(any(v["disponible"] for v in m.configuracion()["voces"]))
            with self.assertRaises(VozNoDisponible):
                m.sintetizar("kokoro:ef_dora", "Hola.", "es")

    def test_wav_repetible_cache_limitada_y_fallo_recuperable(self):
        class Sintetizador:
            llamadas = 0
            def synthesize_wav(self, texto, wav):
                self.llamadas += 1
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050)
                wav.writeframes(b"\x01\x02" * 100)
        sintetizador = Sintetizador()
        m = MotorVoz(max_cache_bytes=500)
        with patch.object(m, "_disponible", return_value=True), patch.object(m, "_modelo", return_value=sintetizador):
            a = m.sintetizar("piper:es_MX-claude-high", "Hola.", "es")
            self.assertEqual(a, m.sintetizar("piper:es_MX-claude-high", "Hola.", "es"))
            self.assertEqual(1, sintetizador.llamadas)
            with wave.open(io.BytesIO(a)) as wav:
                self.assertEqual(100, wav.getnframes())
            for texto in ["Uno.", "Dos.", "Tres."]:
                m.sintetizar("piper:es_MX-claude-high", texto, "es")
            self.assertLessEqual(m.bytes_cache, 500)
            self.assertLessEqual(len(m.cache), 2)
        with patch.object(m, "_disponible", return_value=True), patch.object(m, "_modelo", side_effect=RuntimeError):
            with self.assertRaises(VozNoDisponible):
                m.sintetizar("piper:es_MX-claude-high", "Otro.", "es")

    def test_descarga_se_comprueba_con_tamano_y_huella(self):
        with TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "modelo"
            archivo.write_bytes(b"modelo correcto")
            ficha = {"bytes": 15, "hash_tipo": "sha256", "hash": hashlib.sha256(archivo.read_bytes()).hexdigest()}
            self.assertTrue(archivo_verificado(archivo, ficha))
            archivo.write_bytes(b"modelo cambiado")
            self.assertFalse(archivo_verificado(archivo, ficha))


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

    def test_endpoint_solo_lee_texto_de_sesion(self):
        with patch.object(self.servidor.voz, "sintetizar", return_value=b"RIFFprueba") as generar:
            r = self.post("/api/voz", idioma="es", prueba=True, voz="kokoro:ef_dora")
            self.assertEqual(200, r.status)
            self.assertEqual("audio/wav", r.getheader("Content-Type"))
            self.assertIn("media-src 'self' blob:", r.getheader("Content-Security-Policy"))
            r.read()
            generar.assert_called_once_with("kokoro:ef_dora", idiomas.saludo("es"), "es")
            r = self.post("/api/voz", idioma="es", voz="kokoro:ef_dora", texto="Texto externo.")
            self.assertEqual(400, r.status); r.read()
            self.assertEqual(1, generar.call_count)

    def test_cambio_y_error_localizados_voz_sin_modelos(self):
        r = self.post("/api/idioma", idioma="pt-BR")
        self.assertEqual(200, r.status)
        self.v = json.loads(r.read())["vista"]
        self.assertEqual("Floresta tropical", self.v["opciones_habitat"][0]["nombre"])
        with patch.object(self.servidor.voz, "_disponible", return_value=False):
            r = self.post("/api/voz", idioma="pt-BR", voz="kokoro:pf_dora", prueba=True)
            self.assertEqual(503, r.status)
            self.assertIn("Não há vozes", json.loads(r.read())["error"])

    def test_audio_generado_despues_de_cambiar_idioma_se_descarta(self):
        sid = self.cookie.split("=", 1)[1]
        sesion = self.servidor.sesiones[sid]
        def generar(*_):
            # Simula cambiar de idioma mientras el motor trabaja sin mantener
            # bloqueada la sesión. El audio de la vista anterior no se entrega.
            entrada = {k: self.v[k] for k in ("revision", "sesion_id", "reto_id")}
            sesion.cambiar_idioma({**entrada, "idioma": "pt-BR"})
            return b"RIFFobsoleto"
        with patch.object(self.servidor.voz, "sintetizar", side_effect=generar):
            r = self.post("/api/voz", idioma="es", voz="kokoro:ef_dora", prueba=True)
            self.assertEqual(409, r.status)
            datos = json.loads(r.read())
            self.assertEqual("pt-BR", datos["vista"]["idioma"])
            self.assertIn("A tela mudou", datos["error"])

    def test_origen_ajeno_bloqueado_y_catalogo_sin_rutas_locales(self):
        self.c.request("POST", "/api/idioma", "{}", {"Origin": "https://otro.example", "Content-Type": "application/json"})
        r = self.c.getresponse(); self.assertEqual(403, r.status); r.read()
        self.c.request("GET", "/api/voz/config")
        r = self.c.getresponse(); voces = json.loads(r.read())["voces"]
        self.assertEqual(14, len(voces))
        self.assertTrue(all("modelo" not in v and "ruta" not in v for v in voces))


if __name__ == "__main__":
    unittest.main()
