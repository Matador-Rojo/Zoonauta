"""Opciones accesibles, decisiones explicables y evaluación sin contaminación."""
import copy
import contextlib
import io
import tempfile
from pathlib import Path
import unittest
from uuid import uuid4

from codigo.interfaz.servicio import SesionWeb
from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.gestor import GestorPartida
from codigo.entrenamiento.simulador import simular
from codigo.entrenamiento.evaluar_demo import evaluar, estabilidad
from codigo.nucleo.auditoria import auditar


class PruebasHito2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos()

    def preparar(self, opciones=8, politica="PROBABILISTICO", animal="A01"):
        self.g = GestorPartida(self.banco, 2, politica, ayuda_en_pendiente=True,
                              cantidad_opciones=opciones)
        self.enviar("iniciar", modalidad="JUGADOR")
        self.enviar("elegir_animal", animal_id=animal)
        self.g.avanzar_preparacion()
        return self.g

    def enviar(self, tipo, **payload):
        salida = self.g.procesar(self.g.crear_evento(tipo, **payload))
        self.assertTrue(salida.aceptada, salida.motivo)
        return salida

    def test_opciones_unicas_con_respuesta_y_contraste_para_48_animales(self):
        posiciones = set()
        for n in (2, 4, 8):
            for animal in self.banco.animales:
                with self.subTest(n=n, animal=animal):
                    g = self.preparar(n, animal=animal)
                    opciones = g.estado.opciones_habitat
                    self.assertEqual(n, len(set(opciones)))
                    self.assertIn(g.estado.habitat_guia_id, opciones)
                    self.assertTrue(any(self.banco.evaluar(animal, h)["estado"] == "PENDIENTE" for h in opciones))
                    self.assertEqual(opciones, [h["id"] for h in g.vista()["opciones_habitat"]])
                    if n == 2:
                        posiciones.add(opciones.index(g.estado.habitat_guia_id))
        self.assertEqual({0, 1}, posiciones)

    def test_opciones_no_cambian_con_pausa_ni_repeticion(self):
        for n in (2, 4):
            g = self.preparar(n)
            antes = copy.deepcopy(g.estado.opciones_habitat)
            self.enviar("ayuda")
            self.enviar("repetir")
            self.enviar("pausar")
            self.enviar("reanudar")
            self.assertEqual(antes, g.estado.opciones_habitat)
            ausente = next(h for h in self.banco.habitats if h not in antes)
            salida = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=ausente))
            self.assertEqual((False, "HABITAT_NO_VISIBLE"), (salida.aceptada, salida.motivo))
            self.assertFalse(g.estado.elecciones_reto)

    def test_primera_eleccion_busca_atributo_que_distingue(self):
        g = self.preparar(animal="A02")
        # Selva y bosque comparten entorno; cambia el segundo atributo (clima).
        r = self.enviar("seleccionar_habitat", habitat_id="H05")
        self.assertEqual(2, g.estado.nivel)
        self.assertEqual("ATRIBUTO_QUE_DISTINGUE_LA_ELECCION", r.traza["adaptacion_reto"]["regla"])
        self.assertEqual("temperatura", r.traza["atributo_guia"]["nombre"])
        self.assertEqual(0, g.estado.completados)

    def test_segunda_eleccion_pendiente_ofrece_apoyo_explicito(self):
        g = self.preparar()
        self.enviar("seleccionar_habitat", habitat_id="H03")
        r = self.enviar("seleccionar_habitat", habitat_id="H03")
        self.assertEqual(3, r.respuesta.nivel)
        self.assertEqual("APOYO_EXPLICITO_TRAS_VARIAS_ELECCIONES", r.traza["adaptacion_reto"]["regla"])
        self.assertIsNone(g.observaciones_cerradas[-1]["resultado"])

    def test_repetir_es_exacto_y_nueva_peticion_reformula_una_vez(self):
        g = self.preparar()
        primera = self.enviar("ayuda").respuesta
        self.assertEqual(primera, self.enviar("repetir").respuesta)
        segunda = self.enviar("ayuda")
        self.assertEqual(1, segunda.respuesta.nivel)
        self.assertNotEqual(primera.contenido_id, segunda.respuesta.contenido_id)
        self.assertEqual("REFORMULAR_TRAS_REPETICION", segunda.traza["adaptacion_reto"]["regla"])
        self.assertEqual(2, self.enviar("ayuda").respuesta.nivel)

    def test_tres_variantes_antes_de_reutilizar_y_sin_repeticion_inmediata(self):
        g = self.preparar()
        for _ in range(2):
            self.enviar("ayuda")
        variantes = [self.enviar("ayuda").respuesta.variante_id for _ in range(7)]
        self.assertEqual(3, len(set(variantes[:3])))
        self.assertTrue(all(a != b for a, b in zip(variantes, variantes[1:])))

    def test_historial_es_del_reto_y_se_limpia_al_continuar(self):
        g = self.preparar()
        self.enviar("seleccionar_habitat", habitat_id="H03")
        self.enviar("seleccionar_habitat", habitat_id=g.estado.habitat_guia_id)
        self.assertTrue(g.estado.elecciones_reto)
        self.enviar("continuar")
        self.assertEqual([], g.estado.elecciones_reto)
        self.assertEqual([], g.estado.ayudas_reto)
        self.enviar("elegir_animal", animal_id="A08")
        self.g.avanzar_preparacion()
        self.assertEqual(1, self.enviar("ayuda").respuesta.nivel)

    def test_recorrido_completo_para_tres_politicas_y_tres_dificultades(self):
        for politica in ("ID3", "ROTACION", "PROBABILISTICO"):
            for n in (2, 4, 8):
                with self.subTest(politica=politica, n=n):
                    s = SesionWeb(self.banco, politica=politica)
                    def actuar(tipo, **payload):
                        v = s.vista()
                        return s.actuar({"tipo": tipo, "payload": payload, "evento_id": uuid4().hex,
                            "sesion_id": v["sesion_id"], "reto_id": v["reto_id"], "revision": v["revision"]})
                    parametros = dict(s.gestor.motor.parametros)
                    actuar("iniciar", modalidad="AGENTE", retos=2, cantidad_opciones=n)
                    for _ in range(2):
                        opciones = s.vista()["opciones_habitat"]
                        self.assertEqual(n, len(opciones))
                        actuar("ayuda")
                        respuesta = s.vista()["respuesta"]
                        actuar("repetir")
                        self.assertEqual(respuesta, s.vista()["respuesta"])
                        actuar("pausar")
                        actuar("reanudar")
                        self.assertEqual(opciones, s.vista()["opciones_habitat"])
                        actuar("seleccionar_habitat", habitat_id=s.gestor.estado.habitat_guia_id)
                        actuar("continuar")
                    self.assertEqual("COMPLETADA", s.vista()["fase"])
                    self.assertEqual(parametros, dict(s.gestor.motor.parametros))

    def test_opciones_invalidas_no_alteran_inicio(self):
        for n in (True, "2", 0, 3, 9, None):
            s = SesionWeb(self.banco)
            v = s.vista()
            with self.assertRaises(ValueError):
                s.actuar({"tipo": "iniciar", "payload": {"modalidad": "AGENTE", "retos": 1, "cantidad_opciones": n},
                    "evento_id": uuid4().hex, "sesion_id": v["sesion_id"], "reto_id": None, "revision": 0})
            self.assertEqual("INICIO", s.gestor.estado.fase)
            self.assertEqual(8, s.gestor.N)

    def test_simulacion_usa_opciones_visibles_y_metricas_con_protocolo_web(self):
        condicion = self.banco.leer("configuracion_simulador.json")["items"][2]
        for n in (2, 4, 8):
            cfg = {**self.banco.leer("configuracion_experimentos.json"),
                   "cantidad_opciones": n, "ayuda_en_pendiente": True}
            r = simular(self.banco, MotorGuia(self.banco, "PROBABILISTICO"), condicion,
                        retos=48, semilla=90001, identificador=f"EVAL_{n}", configuracion=cfg)
            self.assertEqual(n, r["cantidad_opciones"])
            self.assertTrue(r["modelo_evaluacion_invariable"])
            self.assertGreaterEqual(r["turnos_decision_por_reto_completado"], 2)

    def test_semilla_de_opciones_independiente_de_politica(self):
        opciones = []
        for politica in ("ID3", "ROTACION", "PROBABILISTICO"):
            self.g = GestorPartida(self.banco, 1, politica, cantidad_opciones=4, semilla_opciones="CONTROL:0")
            self.enviar("iniciar", modalidad="JUGADOR")
            self.enviar("elegir_animal", animal_id="A02")
            opciones.append(self.g.estado.opciones_habitat)
        self.assertEqual(opciones[0], opciones[1])
        self.assertEqual(opciones[1], opciones[2])

    def test_auditoria_detecta_pictograma_de_otro_habitat(self):
        banco = copy.deepcopy(self.banco)
        self.assertTrue(auditar(banco)["correcto"])
        banco.variantes["AY_H01_L3_V1"]["pictogramas"].append({"tipo": "PICTOGRAMA", "id": "P_H08"})
        r = auditar(banco)
        self.assertFalse(r["correcto"])
        self.assertTrue(any("otro hábitat" in e for e in r["errores"]))

    def test_evaluacion_separa_tamanos_semillas_y_curvas(self):
        cfg = {**self.banco.leer("configuracion_experimentos.json"), "replicas": 1,
            "retos_entrenamiento_por_condicion_replica": 8,
            "retos_evaluacion_por_condicion_replica_politica": 8, "intervalo_historia": 4}
        with tempfile.TemporaryDirectory() as carpeta:
            with contextlib.redirect_stdout(io.StringIO()):
                r = evaluar(self.banco, Path(carpeta), cfg)
            self.assertEqual(24, r["total_retos_entrenamiento"])
            self.assertEqual(216, r["total_retos_evaluacion"])
            self.assertTrue(r["parametros_congelados_verificados"])
            self.assertFalse(set(r["semillas_entrenamiento"]) & set(r["semillas_evaluacion"]))
            self.assertEqual(3, len(r["curvas_entrenamiento"]))
            self.assertTrue(all(c["estabilidad"]["controles"] == 2 for c in r["curvas_entrenamiento"]))
            for n in ("2", "4", "8"):
                self.assertEqual(9, len(r["por_cantidad_opciones"][n]))
            with self.assertRaises(ValueError):
                evaluar(self.banco, Path(carpeta), cfg)
        self.assertFalse(estabilidad([])["convergencia_demostrada"])


if __name__ == "__main__":
    unittest.main()
