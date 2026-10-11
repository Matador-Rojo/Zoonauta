"""Contratos de la interfaz que podrían alterar el juego con clics reales."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import unittest
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
        for nivel in (1, 2, 3, 3):
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
                self.assertEqual(1, r["respuesta_emitida"]["nivel"])
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


if __name__ == "__main__":
    unittest.main()
