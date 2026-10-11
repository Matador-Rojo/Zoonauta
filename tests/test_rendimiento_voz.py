"""Regresiones de cambios de voz: reutilización, cola y audio en caché."""
import http.client
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Event, Thread
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

from codigo.interfaz.servidor import Servidor
from codigo.interfaz.voz import ControlLecturasVoz, LecturaCancelada, MotorVoz, VozNoDisponible


class Sintetizador:
    def synthesize_wav(self, texto, wav):
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(22050)
        wav.writeframes(b"\x01\x02" * 100)


class RendimientoVoz(unittest.TestCase):
    def test_alternar_tres_voces_reutiliza_modelos_y_limita_hilos(self):
        sesiones = []
        def sesion(ruta, **opciones):
            sesiones.append(opciones)
            return object()
        ort = SimpleNamespace(SessionOptions=SimpleNamespace, InferenceSession=sesion)
        piper = SimpleNamespace(PiperVoice=lambda **kwargs: kwargs)
        config = SimpleNamespace(PiperConfig=SimpleNamespace(from_dict=lambda d: d))
        with TemporaryDirectory() as carpeta, patch.dict(sys.modules, {
                "onnxruntime": ort, "piper": piper, "piper.config": config}):
            m = MotorVoz(Path(carpeta))
            voces = [v for v in m.voces.values() if v["motor"] == "piper"]
            (m.raiz / "piper").mkdir()
            for v in voces:
                (m.raiz / "piper" / v["configuracion"]).write_text("{}")
            modelos = [m._modelo(v) for v in voces[:3]]
            self.assertIs(modelos[0], m._modelo(voces[0]))
            self.assertEqual(3, len(sesiones))
            for opciones in sesiones:
                self.assertEqual(2, opciones["sess_options"].intra_op_num_threads)
                self.assertEqual(1, opciones["sess_options"].inter_op_num_threads)
            for v in voces[3:]:
                m._modelo(v)
            self.assertEqual(4, len(m.modelos))
            self.assertIn((voces[-1]["motor"], voces[-1]["modelo"]), m.modelos)

    def test_cache_responde_mientras_otra_voz_esta_generando(self):
        m = MotorVoz()
        iniciado, liberar, cache_lista = Event(), Event(), Event()
        errores, respuestas = [], []
        class Lento(Sintetizador):
            def synthesize_wav(self, texto, wav):
                if texto == "Lento.":
                    iniciado.set()
                    if not liberar.wait(3):
                        raise TimeoutError()
                super().synthesize_wav(texto, wav)
        def generar(texto, listo=None):
            try:
                respuestas.append(m.sintetizar("piper:es_MX-claude-high", texto, "es"))
            except Exception as exc:
                errores.append(exc)
            finally:
                if listo:
                    listo.set()
        with patch.object(m, "_disponible", return_value=True), patch.object(m, "_modelo", return_value=Lento()):
            esperado = m.sintetizar("piper:es_MX-claude-high", "Listo.", "es")
            lento = Thread(target=generar, args=("Lento.",))
            rapido = Thread(target=generar, args=("Listo.", cache_lista))
            lento.start()
            try:
                self.assertTrue(iniciado.wait(2))
                rapido.start()
                self.assertTrue(cache_lista.wait(1), "El WAV en caché no debe esperar la inferencia.")
                self.assertEqual(esperado, respuestas[0])
            finally:
                liberar.set()
                lento.join(3)
                if rapido.ident:
                    rapido.join(3)
            self.assertFalse(errores)

    def test_cancelar_durante_carga_conserva_modelo_y_evade_sintesis(self):
        m = MotorVoz()
        control = ControlLecturasVoz()
        control.registrar("pagina", 1)
        modelo = Sintetizador()
        clave = ("piper", m.voces["piper:es_MX-claude-high"]["modelo"])
        def cargar(_):
            m.modelos[clave] = modelo
            control.registrar("pagina", 2)
            return modelo
        with patch.object(m, "_disponible", return_value=True), patch.object(m, "_modelo", side_effect=cargar), patch.object(modelo, "synthesize_wav") as generar:
            with self.assertRaises(LecturaCancelada):
                m.sintetizar("piper:es_MX-claude-high", "Hola.", "es",
                             vigente=lambda: control.vigente("pagina", 1))
            generar.assert_not_called()
            self.assertIs(modelo, m.modelos[clave])

    def test_fallo_de_una_voz_no_descarta_las_otras(self):
        m = MotorVoz()
        sano = ("kokoro", "otro-modelo")
        m.modelos[sano] = object()
        with patch.object(m, "_disponible", return_value=True), patch.object(m, "_modelo", side_effect=RuntimeError):
            with self.assertRaises(VozNoDisponible):
                m.sintetizar("piper:es_MX-claude-high", "Hola.", "es")
        self.assertIn(sano, m.modelos)

    def test_cancelacion_adelantada_no_se_revierte_y_paginas_independientes(self):
        c = ControlLecturasVoz()
        c.registrar("pagina", 2)
        with self.assertRaises(LecturaCancelada):
            c.registrar("pagina", 1)
        c.registrar("otra", 1)
        self.assertTrue(c.vigente("otra", 1))
        self.assertFalse(c.vigente("pagina", 1))
        for canal, turno in [(None, 1), ("pagina", True), ("pagina", -1), ("pagina", 2**53)]:
            with self.assertRaises(ValueError):
                c.registrar(canal, turno)


class ColaHTTP(unittest.TestCase):
    def test_cambio_rapido_omite_la_voz_cancelada_en_cola(self):
        servidor = Servidor(("127.0.0.1", 0))
        hilo = Thread(target=servidor.serve_forever, daemon=True)
        hilo.start()
        c = http.client.HTTPConnection("127.0.0.1", servidor.server_port, timeout=5)
        c.request("GET", "/api/vista")
        r = c.getresponse()
        cookie = r.getheader("Set-Cookie").split(";")[0]
        vista = json.loads(r.read())
        c.close()
        iniciado, liberar = Event(), Event()
        resultados, errores = {}, []
        class Lento(Sintetizador):
            def synthesize_wav(self, texto, wav):
                if not iniciado.is_set():
                    iniciado.set()
                    if not liberar.wait(3):
                        raise TimeoutError()
                super().synthesize_wav(texto, wav)
        def post(clave, ruta, campos):
            conexion = http.client.HTTPConnection("127.0.0.1", servidor.server_port, timeout=5)
            try:
                entrada = {k: vista[k] for k in ("revision", "sesion_id", "reto_id")}
                entrada.update(canal_voz="pagina", **campos)
                conexion.request("POST", ruta, json.dumps(entrada), {"Content-Type": "application/json", "Cookie": cookie})
                respuesta = conexion.getresponse()
                resultados[clave] = (respuesta.status, respuesta.read())
            except Exception as exc:
                errores.append(exc)
            finally:
                conexion.close()
        lectores = []
        try:
            with patch.object(servidor.voz, "_disponible", return_value=True), patch.object(servidor.voz, "_modelo", return_value=Lento()) as cargar:
                for turno, voz in [(1, "piper:es_MX-claude-high"), (2, "piper:es_MX-ald-medium")]:
                    lector = Thread(target=post, args=(turno, "/api/voz", dict(turno_voz=turno, idioma="es", prueba=True, voz=voz)))
                    lectores.append(lector)
                    lector.start()
                    if turno == 1:
                        self.assertTrue(iniciado.wait(2))
                # El turno 3 invalida incluso una solicitud del turno 2 que
                # aún no haya alcanzado el servidor; no depende de sleeps.
                post("cancelar", "/api/voz/cancelar", dict(turno_voz=3))
                lector = Thread(target=post, args=(3, "/api/voz", dict(turno_voz=3, idioma="es", prueba=True, voz="piper:es_AR-daniela-high")))
                lectores.append(lector)
                lector.start()
                liberar.set()
                for lector in lectores:
                    lector.join(5)
                self.assertFalse(errores)
                self.assertEqual(200, resultados["cancelar"][0])
                self.assertEqual(409, resultados[1][0])
                self.assertEqual(409, resultados[2][0])
                self.assertEqual(200, resultados[3][0])
                with wave.open(io.BytesIO(resultados[3][1])) as wav:
                    self.assertEqual(100, wav.getnframes())
                self.assertEqual(2, cargar.call_count)
                self.assertEqual(0, servidor.sesiones[cookie.split("=", 1)[1]].revision)
        finally:
            liberar.set()
            for lector in lectores:
                lector.join(5)
            servidor.shutdown()
            servidor.server_close()


if __name__ == "__main__":
    unittest.main()
