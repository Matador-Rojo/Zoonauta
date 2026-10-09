"""Pruebas del aprendizaje, cierre de observaciones y aislamiento de evaluación."""
import contextlib
import copy
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path

from codigo.entrenamiento.bayes import ModeloBayes, MotorThompson
from codigo.entrenamiento.experimento import ejecutar
from codigo.entrenamiento.simulador import RegistroExperimento, simular, uniforme
from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.gestor import GestorPartida


class PruebasAprendizaje(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos()
        cls.priors = cls.banco.leer("parametros_iniciales.json")
        cls.cfg = cls.banco.leer("configuracion_experimentos.json")
        cls.condicion = cls.banco.leer("configuracion_simulador.json")["items"][1]

    def fila(self, id="O1", y=1):
        return {"origen": "SIMULACION_ENTRENAMIENTO", "observacion_id": id, "resultado": y,
                "contexto": {"habitat_guia_id": "H02", "nivel": 2, "repeticion_previa": 1},
                "variante_id": "V2"}

    def test_actualizacion_unica_y_sin_etiqueta(self):
        m = ModeloBayes(self.priors)
        self.assertTrue(m.actualizar(self.fila("O1", 1)))
        self.assertTrue(m.actualizar(self.fila("O2", 0)))
        self.assertFalse(m.actualizar(self.fila("O2", 0)))
        self.assertFalse(m.actualizar(self.fila("O3", None)))
        self.assertFalse(m.actualizar(self.fila("O3", None)))
        beta = m.valores[("H02", 2, 1, "V2")]
        self.assertEqual((beta.alpha, beta.beta, m.actualizaciones, m.sin_etiqueta), (2, 2, 2, 1))
        with self.assertRaises(ValueError): m.actualizar(self.fila("O3", 1))
        with self.assertRaises(ValueError): m.actualizar(self.fila("O1", 0))
        with self.assertRaises(ValueError): m.actualizar({**self.fila("OTRA", 1), "origen": "SIMULACION_EVALUACION"})
        self.assertEqual(m.actualizaciones, 2)

    def test_feedback_se_aplica_antes_de_nueva_decision(self):
        m = ModeloBayes(self.priors, "CONTROL")
        motor = MotorThompson(self.banco, m, 21)
        registro = RegistroExperimento(self.condicion, "CONTROL", m)
        g = GestorPartida(self.banco, 1, "PROBABILISTICO", origen="SIMULACION_ENTRENAMIENTO",
                           motor=motor, registro=registro)
        def enviar(tipo, **payload):
            interno = payload.pop("interno", False)
            s = g.procesar(g.crear_evento(tipo, interno=interno, **payload))
            self.assertTrue(s.aceptada)
            return s
        enviar("iniciar", modalidad="JUGADOR")
        enviar("elegir_animal", animal_id="A08")
        enviar("presentar_reto", interno=True)
        primera = enviar("ayuda")
        enviar("repetir")
        enviar("pausar")
        enviar("reanudar")
        self.assertEqual(m.actualizaciones, 0)
        segunda = enviar("ayuda")
        self.assertEqual(m.actualizaciones, 1)
        self.assertTrue(segunda.traza["modelo_version"].endswith("U1"))
        variante = primera.respuesta.variante_id
        self.assertEqual(m.valores[("H02", 1, 0, variante)].beta, 2)
        enviar("seleccionar_habitat", habitat_id="H02")
        self.assertEqual(m.actualizaciones, 2)
        self.assertEqual(registro.totales["y0"], 1)
        self.assertEqual(registro.totales["y1"], 1)
        self.assertTrue(all(o["modelo_actualizado"] for o in g.observaciones_cerradas))

    def test_thompson_excluye_ultima_y_es_reproducible(self):
        a = MotorThompson(self.banco, ModeloBayes(self.priors), 42)
        b = MotorThompson(self.banco, ModeloBayes(self.priors), 42)
        for i in range(20):
            ayuda, _, traza = a.decidir("H02", 3, i % 2, {"H02:3": "V1"})
            otra, _, otra_traza = b.decidir("H02", 3, i % 2, {"H02:3": "V1"})
            self.assertNotEqual(ayuda["variante_id"], "V1")
            self.assertEqual(ayuda["variante_id"], otra["variante_id"])
            self.assertEqual(traza["muestras_beta"], otra_traza["muestras_beta"])
            self.assertFalse(traza["parametros_congelados"])

    def test_exportacion_y_evaluacion_inmutable(self):
        with tempfile.TemporaryDirectory() as temporal:
            m = ModeloBayes(self.priors)
            m.actualizar(self.fila())
            ruta = Path(temporal) / "aprendido.json"
            m.guardar(ruta)
            motor = MotorGuia(self.banco, "PROBABILISTICO", ruta)
            self.assertEqual(motor.parametros[("H02", 2, 1, "V2")].alpha, 2)
            contenido = ruta.read_bytes()
            resultado = simular(self.banco, motor, self.condicion, retos=48, semilla=91001,
                        identificador="EVAL_CONTROL", configuracion=self.cfg)
            self.assertTrue(resultado["modelo_evaluacion_invariable"])
            self.assertEqual(ruta.read_bytes(), contenido)
            self.assertEqual(resultado["retos_iniciados"], 48)

    def test_cortes_de_simulacion_no_crean_etiquetas_cero(self):
        cfg = {**self.cfg, "prob_repetir_pregunta": 0, "prob_repetir_ayuda": 0,
               "prob_salida": 0, "prob_pendiente": 0, "prob_pausa": 0,
               "max_ayudas_solo_simulador": 1}
        condicion = {"id": "CONTROL_P0", "probabilidades": {"b0": {"V1": 0, "V2": 0, "V3": 0},
                       "b1": {"V1": 0, "V2": 0, "V3": 0}}}
        m = ModeloBayes(self.priors)
        resultado = simular(self.banco, MotorThompson(self.banco, m, 21), condicion, retos=4,
                             semilla=11001, identificador="TRAIN_CORTE", configuracion=cfg, modelo=m)
        self.assertEqual(resultado["cortes_simulador"], 4)
        self.assertEqual(resultado["sin_etiqueta"], 4)
        self.assertEqual(resultado["etiquetadas"], 0)
        self.assertEqual(m.actualizaciones, 0)

    def test_flujos_exogenos_no_dependen_de_politica(self):
        x = uniforme(91001, 31, 2, "resultado_etiquetado")
        self.assertEqual(x, uniforme(91001, 31, 2, "resultado_etiquetado"))
        self.assertNotEqual(x, uniforme(11001, 31, 2, "resultado_etiquetado"))
        self.assertNotEqual(x, uniforme(91001, 31, 2, "pausa"))
        self.assertTrue(0 <= x < 1)

    def test_experimento_completo_con_cierres_y_modelos(self):
        with tempfile.TemporaryDirectory() as temporal:
            cfg = {**self.cfg, "replicas": 2,
                   "retos_entrenamiento_por_condicion_replica": 48,
                   "retos_evaluacion_por_condicion_replica_politica": 48}
            destino = Path(temporal)
            with contextlib.redirect_stdout(io.StringIO()):
                resumen = ejecutar(self.banco, destino, cfg, [self.condicion])
            self.assertEqual(len(resumen["agregado"]), 3)
            self.assertEqual(len(resumen["modelos"]), 2)
            self.assertTrue(resumen["evaluacion_congelada_verificada"])
            self.assertFalse(set(resumen["semillas_entrenamiento"]) & set(resumen["semillas_evaluacion"]))
            for entrada in resumen["modelos"]:
                doc = json.loads((destino / entrada["ruta"]).read_text(encoding="utf-8"))
                self.assertEqual(sum(r["alpha"] + r["beta"] - 2 for r in doc["items"]), doc["actualizaciones"])
            for ruta in destino.glob("observaciones_*.jsonl.gz"):
                with gzip.open(ruta, "rt", encoding="utf-8") as f:
                    filas = [json.loads(l) for l in f]
                self.assertEqual(len(filas), len({r["observacion_id"] for r in filas}))
                if "EVAL" in ruta.name:
                    self.assertTrue(all(not r["modelo_actualizado"] for r in filas))
                else:
                    self.assertTrue(all(r["modelo_actualizado"] == (r["resultado"] is not None) for r in filas))
            with self.assertRaises(ValueError): ejecutar(self.banco, destino, cfg, [self.condicion])


if __name__ == "__main__":
    unittest.main()

