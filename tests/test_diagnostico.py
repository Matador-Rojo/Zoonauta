"""El diagnóstico exige réplicas comparables y no presenta estabilidad como prueba."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from codigo.entrenamiento.diagnosticar import comparar


class Diagnostico(unittest.TestCase):
    def preparar(self, carpeta):
        a, b = Path(carpeta) / "antes", Path(carpeta) / "despues"
        historia = [{"retos_entrenados": (i + 1) * 320,
            "error_absoluto_medio_144_parametros": error,
            "cambio_medio_desde_control_anterior": cambio}
            for i, (error, cambio) in enumerate([(0.1, 0.03), (0.08, 0.008), (0.06, 0.006), (0.05, 0.004)])]
        for raiz, numero in ((a, 1), (b, 4)):
            (raiz / "modelos").mkdir(parents=True)
            modelo = raiz / "modelos/SIM_CONTEXTUAL_R01.json"
            modelo.write_text(json.dumps({"items": [
                {"contexto": {"nivel": 1}, "variante_id": "V1", "observaciones_etiquetadas": 5},
                {"contexto": {"nivel": 1}, "variante_id": "V2", "observaciones_etiquetadas": 20}]}), encoding="utf-8")
            d = {"condiciones": ["CONTROL_SINTETICO"], "semillas_entrenamiento": [1],
                "semillas_evaluacion": [2], "recursos_sha256": {}, "codigo_sha256": {},
                "configuracion": {"retos_entrenamiento_por_condicion_replica": numero * 320, "intervalo_historia": 320},
                "modelos": [{"ruta": "modelos/SIM_CONTEXTUAL_R01.json", "sha256": hashlib.sha256(modelo.read_bytes()).hexdigest()}],
                "curvas_entrenamiento": [{"modelo": "SIM_CONTEXTUAL_R01", "historia": historia[:numero]}]}
            (raiz / "evaluacion_demo.json").write_text(json.dumps(d), encoding="utf-8")
        return a, b

    def cambiar(self, raiz, cambio):
        p = raiz / "evaluacion_demo.json"
        d = json.loads(p.read_text("utf-8"))
        cambio(d)
        p.write_text(json.dumps(d), encoding="utf-8")

    def test_estabilidad_y_escasez_se_informan_sin_afirmar_convergencia(self):
        with TemporaryDirectory() as carpeta:
            a, b = self.preparar(carpeta)
            d = comparar(a, b)
            self.assertEqual(1, d["modelos_con_estabilidad_media_observada"])
            self.assertEqual(1, d["distribuciones_con_menos_de_10_etiquetas"])
            self.assertFalse(d["convergencia_general_demostrada"])
            self.assertAlmostEqual(0.5, d["reduccion_relativa_error_medio"])

    def test_modelo_modificado_se_rechaza(self):
        with TemporaryDirectory() as carpeta:
            a, b = self.preparar(carpeta)
            (b / "modelos/SIM_CONTEXTUAL_R01.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                comparar(a, b)

    def test_semillas_distintas_no_son_comparacion_pareada(self):
        with TemporaryDirectory() as carpeta:
            a, b = self.preparar(carpeta)
            self.cambiar(b, lambda d: d.update(semillas_evaluacion=[3]))
            with self.assertRaises(ValueError):
                comparar(a, b)

    def test_no_admite_un_prefijo_de_entrenamiento_distinto(self):
        with TemporaryDirectory() as carpeta:
            a, b = self.preparar(carpeta)
            self.cambiar(b, lambda d: d["curvas_entrenamiento"][0]["historia"][0].update(error_absoluto_medio_144_parametros=0.01))
            with self.assertRaises(ValueError):
                comparar(a, b)

    def test_mismo_presupuesto_no_es_ampliacion(self):
        with TemporaryDirectory() as carpeta:
            a, b = self.preparar(carpeta)
            self.cambiar(b, lambda d: d["configuracion"].update(retos_entrenamiento_por_condicion_replica=320))
            with self.assertRaises(ValueError):
                comparar(a, b)

    def test_umbral_invalido_se_rechaza(self):
        with TemporaryDirectory() as carpeta:
            a, b = self.preparar(carpeta)
            for umbral in (0, -1, float("nan")):
                with self.assertRaises(ValueError):
                    comparar(a, b, umbral)


if __name__ == "__main__":
    unittest.main()
