"""Contratos de la interfaz que podrían alterar el juego con clics reales."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from random import Random
import unittest
from unittest.mock import Mock
from uuid import uuid4

from codigo.interfaz.servicio import ConflictoVista, MODELO_DEMO, SesionWeb
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO


class PruebasInterfaz(unittest.TestCase):
    def setUp(self):
        self.s = SesionWeb(BancoDatos())

    def entrada(self, tipo, **payload):
        v = self.s.vista()
        return dict(tipo=tipo, payload=payload, evento_id=uuid4().hex,
            revision=v["revision"], sesion_id=v["sesion_id"], reto_id=v["reto_id"])

    def actuar(self, tipo, **payload):
        return self.s.actuar(self.entrada(tipo, **payload))

    def test_catalogo_completo_y_api_sin_estimaciones(self):
        v = self.s.vista()
        self.assertEqual(48, len(v["catalogo_animales"]))
        self.assertEqual(8, len(v["opciones_habitat"]))
        self.assertEqual(95, len(v["pictogramas"]))
        for prohibido in ["probabilidades", "habitat_guia_id", "modelo_version", "K"]:
            self.assertNotIn(prohibido, v)

    def test_ambos_inicios_y_cantidad_48(self):
        self.actuar("iniciar", modalidad="JUGADOR", retos=48)
        self.assertEqual("SELECCION_ANIMAL", self.s.vista()["fase"])
        self.actuar("elegir_animal", animal_id="A48")
        self.assertEqual("A48", self.s.vista()["animal"]["id"])
        self.actuar("salir")
        self.actuar("nueva_partida")
        v = self.actuar("iniciar", modalidad="AGENTE", retos=48)["vista"]
        self.assertEqual("ESPERANDO_RESPUESTA", v["fase"])
        self.assertEqual(48, v["progreso"]["total"])

    def test_agente_recorrido_aleatorio_de_48_sin_repeticiones(self):
        self.s = SesionWeb(self.s.banco, aleatorio=Random(38))
        primeros = []
        for partida in range(2):
            self.actuar("iniciar", modalidad="AGENTE", retos=48)
            vistos = []
            for _ in range(48):
                animal = self.s.vista()["animal"]["id"]
                vistos.append(animal)
                habitat = next(h for (a, h), r in self.s.banco.asociaciones.items()
                               if a == animal and r["estado"] == "VALIDA")
                self.actuar("seleccionar_habitat", habitat_id=habitat)
                self.actuar("continuar")
            self.assertEqual(set(self.s.banco.animales), set(vistos))
            self.assertEqual(48, len(set(vistos)))
            self.assertEqual("COMPLETADA", self.s.vista()["fase"])
            primeros.append(vistos[0])
            if partida == 0:
                self.actuar("nueva_partida")
        self.assertNotEqual(primeros[0], primeros[1])

    def test_nueva_partida_evitar_mismo_inicio_y_pausa_conserva_orden(self):
        orden = list(self.s.banco.escenarios)
        azar = Mock()
        azar.sample.side_effect = [list(orden), list(orden)]
        self.s = SesionWeb(self.s.banco, aleatorio=azar)
        self.actuar("iniciar", modalidad="AGENTE", retos=8)
        primero = self.s.vista()["animal"]["id"]
        self.actuar("pausar")
        self.actuar("reanudar")
        self.assertEqual(primero, self.s.vista()["animal"]["id"])
        self.assertEqual(1, azar.sample.call_count)
        self.actuar("salir")
        self.actuar("nueva_partida")
        self.actuar("iniciar", modalidad="AGENTE", retos=8)
        self.assertNotEqual(primero, self.s.vista()["animal"]["id"])
        self.assertEqual(set(orden), set(self.s.gestor.orden_escenarios))
        self.assertEqual(2, azar.sample.call_count)

    def test_clic_duplicado_o_tardio_no_repite_ayuda(self):
        self.actuar("iniciar", modalidad="AGENTE")
        e = self.entrada("ayuda")
        self.s.actuar(e)
        self.assertFalse(self.s.actuar(e)["aceptada"])
        self.assertEqual(1, self.s.gestor.estado.nivel)
        tardio = copy.deepcopy(e)
        tardio["evento_id"] = uuid4().hex
        with self.assertRaises(ConflictoVista):
            self.s.actuar(tardio)
        self.assertEqual(1, self.s.gestor.estado.nivel)

    def test_clics_concurrentes_aplican_solo_una_accion(self):
        self.actuar("iniciar", modalidad="AGENTE")
        a, b = self.entrada("ayuda"), self.entrada("ayuda")
        def ejecutar(e):
            try:
                return self.s.actuar(e)["aceptada"]
            except ConflictoVista:
                return False
        with ThreadPoolExecutor(2) as pool:
            resultados = list(pool.map(ejecutar, [a, b]))
        self.assertEqual(1, sum(resultados))
        self.assertEqual(1, self.s.gestor.estado.nivel)

    def test_repetir_pausa_y_consulta_no_toman_nueva_decision(self):
        self.actuar("iniciar", modalidad="AGENTE")
        r = self.actuar("ayuda")["respuesta_emitida"]
        observacion = copy.deepcopy(self.s.gestor.estado.observacion)
        self.assertEqual(r, self.actuar("repetir")["respuesta_emitida"])
        self.assertEqual(observacion, self.s.gestor.estado.observacion)
        self.actuar("pausar")
        self.assertEqual("NAVEGACION", self.s.vista()["respuesta"]["tipo_respuesta"])
        revision = self.s.revision
        self.s.vista(); self.s.revision_tecnica()
        self.assertEqual(revision, self.s.revision)
        self.assertEqual(r, self.actuar("reanudar")["respuesta_emitida"])

    def test_capibara_pendiente_y_asociacion_adicional(self):
        self.actuar("iniciar", modalidad="JUGADOR", retos=1)
        self.actuar("elegir_animal", animal_id="A31")
        self.actuar("ayuda")
        r = self.actuar("seleccionar_habitat", habitat_id="H03")
        self.assertEqual("NEUTRAL", r["respuesta_emitida"]["tipo_respuesta"])
        self.assertEqual(2, self.s.gestor.estado.nivel)
        self.assertEqual(2, r["respuesta_emitida"]["nivel"])
        self.assertTrue(r["respuesta_emitida"]["texto_voz"].startswith("Vamos a buscar otro lugar."))
        self.assertIsNone(self.s.gestor.observaciones_cerradas[-1]["resultado"])
        r = self.actuar("seleccionar_habitat", habitat_id="H01")
        self.assertEqual("RETO_RESUELTO", r["vista"]["fase"])
        self.assertEqual(1, r["vista"]["progreso"]["completados"])
        self.assertEqual("COMPLETADA", self.actuar("continuar")["vista"]["fase"])

    def test_ayuda_automatica_no_penaliza_ni_duplica_y_se_puede_repetir(self):
        self.actuar("iniciar", modalidad="JUGADOR", retos=1)
        self.actuar("elegir_animal", animal_id="A31")
        parametros = dict(self.s.gestor.motor.parametros)
        for nivel in (1, 3, 3, 3):
            e = self.entrada("seleccionar_habitat", habitat_id="H03")
            r = self.s.actuar(e)
            self.assertEqual(nivel, self.s.gestor.estado.nivel)
            self.assertEqual("PENDIENTE", self.s.gestor.estado.resultado)
            self.assertEqual(0, r["vista"]["progreso"]["completados"])
            self.assertIn("P_EXPLORAR", r["respuesta_emitida"]["pictogramas"])
            observacion = copy.deepcopy(self.s.gestor.estado.observacion)
            self.assertFalse(self.s.actuar(e)["aceptada"])
            self.assertEqual(observacion, self.s.gestor.estado.observacion)
            self.assertEqual(r["respuesta_emitida"], self.actuar("repetir")["respuesta_emitida"])
            self.actuar("pausar")
            self.assertEqual(r["respuesta_emitida"], self.actuar("reanudar")["respuesta_emitida"])
        cierres = self.s.gestor.observaciones_cerradas
        self.assertEqual(3, len(cierres))
        self.assertTrue(all(o["resultado"] is None and not o["etiqueta_disponible"] for o in cierres))
        self.assertEqual(parametros, dict(self.s.gestor.motor.parametros))
        self.actuar("seleccionar_habitat", habitat_id="H01")
        self.assertEqual(1, self.s.gestor.observaciones_cerradas[-1]["resultado"])
        self.assertEqual(1, self.s.gestor.estado.completados)

    def test_ayuda_automatica_en_las_315_relaciones_pendientes(self):
        banco = self.s.banco
        for (animal, habitat), fila in banco.asociaciones.items():
            if fila["estado"] != "PENDIENTE":
                continue
            with self.subTest(animal=animal, habitat=habitat):
                self.s = SesionWeb(banco)
                self.actuar("iniciar", modalidad="JUGADOR", retos=1)
                self.actuar("elegir_animal", animal_id=animal)
                r = self.actuar("seleccionar_habitat", habitat_id=habitat)
                nivel = r["respuesta_emitida"]["nivel"]
                self.assertIn(nivel, (1, 2, 3))
                atributo = self.s.gestor.registro.filas[-1]["decision"]["atributo_guia"]
                if atributo:
                    perfil_elegido = banco.perfiles[habitat]["atributos"]
                    self.assertNotEqual(perfil_elegido[atributo["nombre"]], atributo["valor"])
                self.assertEqual("NEUTRAL", r["respuesta_emitida"]["tipo_respuesta"])
                self.assertEqual("ESPERANDO_RESPUESTA", r["vista"]["fase"])
                self.assertEqual(0, self.s.gestor.estado.completados)

    def test_modelo_aprendido_permanece_congelado(self):
        antes = hashlib.sha256(MODELO_DEMO.read_bytes()).hexdigest()
        parametros = dict(self.s.gestor.motor.parametros)
        self.actuar("iniciar", modalidad="AGENTE")
        self.actuar("ayuda"); self.actuar("ayuda"); self.actuar("salir")
        self.assertEqual(parametros, dict(self.s.gestor.motor.parametros))
        self.assertEqual(antes, hashlib.sha256(MODELO_DEMO.read_bytes()).hexdigest())
        self.assertTrue(self.s.revision_tecnica()["parametros_congelados"])
        self.assertTrue(all(not o["modelo_actualizado"] for o in self.s.gestor.observaciones_cerradas))

    def test_limites_y_eventos_internos_bloqueados(self):
        for n in [0,49,True,"8"]:
            with self.assertRaises(ValueError):
                self.actuar("iniciar", modalidad="AGENTE", retos=n)
        self.assertEqual("INICIO", self.s.vista()["fase"])
        self.assertFalse(self.actuar("generar_reto", animal_id="A01")["aceptada"])

    def test_todos_los_recursos_tienen_bytes_creditos_y_huella(self):
        for p in self.s.banco.pictogramas.values():
            archivo = RAIZ_PROYECTO / p["archivo_imagen"]
            self.assertTrue(archivo.is_file(), p["id"])
            self.assertEqual(p["sha256_imagen"], hashlib.sha256(archivo.read_bytes()).hexdigest())
            self.assertTrue(p["licencia"])
            self.assertTrue(p["autor_imagen"])

    def test_servidor_listo_para_web_https_cache_gzip_y_healthz(self):
        import gzip
        from tempfile import TemporaryDirectory
        from threading import Thread
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from codigo.interfaz.servidor import Servidor

        with TemporaryDirectory() as carpeta:
            srv = Servidor(("127.0.0.1", 0), registros=Path(carpeta), ampliado=True)
            Thread(target=srv.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{srv.server_port}"
            try:
                # 1. /healthz
                with urlopen(f"{base}/healthz") as r:
                    self.assertEqual(r.status, 200)
                    self.assertTrue(json.loads(r.read())["ok"])

                # 2. Compresión gzip en JSON grande (/api/vista)
                req_gz = Request(f"{base}/api/vista", headers={"Accept-Encoding": "gzip", "X-Forwarded-Proto": "https"})
                with urlopen(req_gz) as r:
                    self.assertEqual(r.headers.get("Content-Encoding"), "gzip")
                    self.assertIn("Secure", r.headers.get("Set-Cookie", ""))
                    cookie = r.headers.get("Set-Cookie", "").split(";", 1)[0]
                    vista = json.loads(gzip.decompress(r.read()))

                # 3. POST aceptado con Origin HTTPS (Hostinger / proxy reverso) y bloqueado si es otro dominio
                body = json.dumps({"tipo": "iniciar", "payload": {"modalidad": "AGENTE", "retos": 1},
                                   "evento_id": uuid4().hex, "revision": vista["revision"],
                                   "sesion_id": vista["sesion_id"], "reto_id": vista["reto_id"]}).encode()
                req_https = Request(
                    f"{base}/api/accion",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "Cookie": cookie,
                        "Origin": f"https://127.0.0.1:{srv.server_port}",
                        "X-Forwarded-Proto": "https",
                    },
                )
                with urlopen(req_https) as r:
                    self.assertEqual(r.status, 200)
                    self.assertTrue(json.loads(r.read())["aceptada"])

                req_malo = Request(
                    f"{base}/api/accion",
                    data=body,
                    headers={"Content-Type": "application/json", "Origin": "https://malicioso.example"},
                )
                with self.assertRaises(HTTPError) as ctx:
                    urlopen(req_malo)
                self.assertEqual(ctx.exception.code, 403)

                # 4. ETag + 304 Not Modified en imágenes cacheadas
                with urlopen(f"{base}/habitats/H01.webp") as r:
                    etag = r.headers.get("ETag")
                    self.assertTrue(etag)
                    self.assertIn("max-age=604800", r.headers.get("Cache-Control", ""))
                req_304 = Request(f"{base}/habitats/H01.webp", headers={"If-None-Match": etag})
                with self.assertRaises(HTTPError) as ctx304:
                    urlopen(req_304)
                self.assertEqual(ctx304.exception.code, 304)

                # 5. Streaming Range 206 de video de portada
                req_range = Request(f"{base}/portada/bosque-de-luz.mp4", headers={"Range": "bytes=0-1023"})
                with urlopen(req_range) as r:
                    self.assertEqual(r.status, 206)
                    self.assertEqual(len(r.read()), 1024)
            finally:
                srv.shutdown()
                srv.server_close()

    def test_adaptador_wsgi_pythonanywhere_https_y_voz(self):
        import gzip
        import io
        from tempfile import TemporaryDirectory
        from codigo.interfaz.wsgi import crear_aplicacion

        with TemporaryDirectory() as carpeta:
            app = crear_aplicacion(registros=Path(carpeta), ampliado=True)

            def llamar(metodo, ruta, *, body=b"", headers=None, esquema="https"):
                env = {
                    "REQUEST_METHOD": metodo,
                    "PATH_INFO": ruta,
                    "QUERY_STRING": "",
                    "SERVER_NAME": "matadorrojo.pythonanywhere.com",
                    "SERVER_PORT": "443",
                    "wsgi.url_scheme": esquema,
                    "wsgi.input": io.BytesIO(body),
                    "CONTENT_LENGTH": str(len(body)),
                }
                for k, v in (headers or {}).items():
                    if k.lower() == "content-type":
                        env["CONTENT_TYPE"] = v
                    else:
                        env["HTTP_" + k.upper().replace("-", "_")] = v
                resp = {}
                def start(status, hdrs):
                    resp["status"] = status
                    resp["headers"] = dict(hdrs)
                datos = b"".join(app(env, start))
                return resp["status"], resp["headers"], datos

            st, _, raw = llamar("GET", "/healthz")
            self.assertTrue(st.startswith("200"))
            self.assertTrue(json.loads(raw)["ok"])

            st, hdrs, raw = llamar("GET", "/api/vista", headers={"Accept-Encoding": "gzip"})
            self.assertTrue(st.startswith("200"))
            self.assertEqual(hdrs.get("Content-Encoding"), "gzip")
            self.assertIn("Secure", hdrs.get("Set-Cookie", ""))
            cookie = hdrs["Set-Cookie"].split(";", 1)[0]
            vista = json.loads(gzip.decompress(raw))

            accion = json.dumps({
                "tipo": "iniciar", "payload": {"modalidad": "AGENTE", "retos": 1},
                "evento_id": uuid4().hex, "revision": vista["revision"],
                "sesion_id": vista["sesion_id"], "reto_id": vista["reto_id"],
            }).encode()
            st, _, raw = llamar(
                "POST", "/api/accion", body=accion,
                headers={
                    "Content-Type": "application/json",
                    "Cookie": cookie,
                    "Origin": "https://matadorrojo.pythonanywhere.com",
                },
            )
            self.assertTrue(st.startswith("200"))
            self.assertTrue(json.loads(raw)["aceptada"])

            st, hdrs, _ = llamar("GET", "/habitats/H01.webp")
            self.assertTrue(st.startswith("200"))
            st304, _, body304 = llamar("GET", "/habitats/H01.webp", headers={"If-None-Match": hdrs["ETag"]})
            self.assertTrue(st304.startswith("304"))
            self.assertEqual(body304, b"")

            st206, _, trozo = llamar("GET", "/portada/bosque-de-luz.mp4", headers={"Range": "bytes=0-511"})
            self.assertTrue(st206.startswith("206"))
            self.assertEqual(len(trozo), 512)


if __name__ == "__main__":
    unittest.main()
