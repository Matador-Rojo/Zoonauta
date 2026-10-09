"""Pruebas de reglas, atribución de observaciones y protección de eventos."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO
from codigo.nucleo.gestor import GestorPartida
from codigo.nucleo.registro import Registro
from codigo.poc.aceptacion import ejecutar_todos


class PruebasNucleo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos()

    def partida(self, animal="A08", politica="PROBABILISTICO", retos=1):
        g = GestorPartida(self.banco, retos, politica, origen="PRUEBA_DE_CONTROL_SINTETICA")
        self.enviar(g, "iniciar", modalidad="JUGADOR")
        self.enviar(g, "elegir_animal", animal_id=animal)
        self.enviar(g, "presentar_reto", interno=True)
        return g

    def enviar(self, g, tipo, **payload):
        interno = payload.pop("interno", False)
        salida = g.procesar(g.crear_evento(tipo, interno=interno, **payload))
        self.assertTrue(salida.aceptada, salida.motivo)
        return salida

    def test_ocho_casos_especificados(self):
        resultados = ejecutar_todos(self.banco)
        self.assertEqual(len(resultados), 8)
        self.assertTrue(all(r["resultado"] == "CORRECTO" for r in resultados))

    def test_id3_calcula_arbol_y_rutas(self):
        motor = MotorGuia(self.banco)
        raiz = motor.arbol.raiz
        self.assertAlmostEqual(raiz.entropia, 3.0)
        self.assertEqual(raiz.atributo, "entorno")
        self.assertAlmostEqual(raiz.ganancias["entorno"], 2.0)
        self.assertAlmostEqual(raiz.ganancias["temperatura"], 1.9056390622295665)
        secundarias = {"ARBOLADO": "temperatura", "LLANURA_CALIDA": "vegetacion",
                       "ACUATICO": "agua", "PAISAJE_FRIO": "ubicacion"}
        for valor, hijo in raiz.hijos.items():
            self.assertEqual(hijo.atributo, secundarias[valor])
            self.assertAlmostEqual(hijo.ganancias[hijo.atributo], 1.0)
        for habitat, perfil in self.banco.perfiles.items():
            self.assertEqual(motor.arbol.predecir(perfil["atributos"]), habitat)
            self.assertEqual(len(motor.rutas[habitat]), 2)

    def test_todas_las_asociaciones_confirmadas_resuelven(self):
        for (animal, habitat), fila in self.banco.asociaciones.items():
            if fila["estado"] == "VALIDA":
                with self.subTest(animal=animal, habitat=habitat):
                    g = self.partida(animal)
                    self.enviar(g, "seleccionar_habitat", habitat_id=habitat)
                    self.assertEqual(g.estado.fase, "RETO_RESUELTO")
                    self.assertEqual(g.estado.completados, 1)
                    self.assertIn(self.banco.habitats[habitat]["pictograma_id"],
                                  g.estado.respuesta_educativa.pictogramas)

    def test_pendientes_conservan_ruta_y_no_son_errores(self):
        # Recorre las celdas pendientes para impedir que el catálogo se reduzca a una respuesta única.
        for (animal, habitat), fila in self.banco.asociaciones.items():
            if fila["estado"] == "PENDIENTE":
                with self.subTest(animal=animal, habitat=habitat):
                    g = self.partida(animal)
                    self.enviar(g, "ayuda")
                    nodo = g.estado.nodo_id
                    self.enviar(g, "seleccionar_habitat", habitat_id=habitat)
                    self.assertEqual(g.estado.resultado, "PENDIENTE")
                    self.assertEqual(g.estado.fase, "ESPERANDO_RESPUESTA")
                    self.assertEqual((g.estado.nivel, g.estado.nodo_id, g.estado.completados), (1, nodo, 0))
                    self.assertIsNone(g.observaciones_cerradas[-1]["resultado"])

    def test_repetir_preserva_contenido_y_contexto_de_observacion(self):
        g = self.partida()
        self.enviar(g, "ayuda")
        respuesta = g.estado.respuesta_educativa
        d = copy.deepcopy(g.estado.observacion)
        salida = self.enviar(g, "repetir")
        self.assertIs(salida.respuesta, respuesta)
        self.assertEqual(g.estado.observacion, d)
        self.assertEqual(g.estado.repeticion_previa, 1)
        self.enviar(g, "seleccionar_habitat", habitat_id="H02")
        self.assertEqual(g.observaciones_cerradas[-1]["resultado"], 1)
        self.assertEqual(g.observaciones_cerradas[-1]["contexto"]["repeticion_previa"], 0)
        s = g.estado.serializar()
        self.enviar(g, "repetir")
        self.assertEqual(g.estado.serializar(), s)
        self.assertEqual(len(g.observaciones_cerradas), 1)

    def test_nueva_ayuda_cierra_un_resultado_y_usa_b_actual(self):
        g = self.partida()
        self.enviar(g, "ayuda")
        self.enviar(g, "repetir")
        self.enviar(g, "ayuda")
        self.assertEqual(len(g.observaciones_cerradas), 1)
        self.assertEqual(g.observaciones_cerradas[0]["resultado"], 0)
        self.assertEqual(g.observaciones_cerradas[0]["contexto"]["repeticion_previa"], 0)
        self.assertEqual(g.estado.observacion["contexto"]["repeticion_previa"], 1)

    def test_pausa_y_entrada_durante_pausa(self):
        g = self.partida()
        self.enviar(g, "ayuda")
        self.enviar(g, "ayuda")
        antes = g.estado.serializar()
        self.enviar(g, "pausar")
        pausado = g.estado.serializar()
        salida = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id="H02"))
        self.assertFalse(salida.aceptada)
        self.assertEqual(g.estado.serializar(), pausado)
        self.enviar(g, "reanudar")
        self.assertEqual(g.estado.serializar(), antes)

    def test_salir_cierra_sin_etiqueta_y_terminal_no_cambia(self):
        g = self.partida()
        self.enviar(g, "ayuda")
        self.enviar(g, "pausar")
        self.enviar(g, "salir")
        self.assertEqual(g.estado.fase, "ABANDONADA")
        self.assertIsNone(g.estado.fase_previa)
        self.assertIsNone(g.observaciones_cerradas[-1]["resultado"])
        antes = g.estado.serializar()
        salida = g.procesar(g.crear_evento("reanudar"))
        self.assertFalse(salida.aceptada)
        self.assertEqual(g.estado.serializar(), antes)

    def test_evento_duplicado_y_clic_tardio(self):
        g = self.partida(retos=2)
        evento = g.crear_evento("ayuda", evento_id="MISMA-AYUDA")
        self.assertTrue(g.procesar(evento).aceptada)
        antes = g.estado.serializar()
        self.assertEqual(g.procesar(evento).motivo, "EVENTO_DUPLICADO")
        self.assertEqual(g.estado.serializar(), antes)
        tardio = g.crear_evento("seleccionar_habitat", habitat_id="H02")
        self.enviar(g, "seleccionar_habitat", habitat_id="H02")
        self.enviar(g, "continuar")
        self.enviar(g, "elegir_animal", animal_id="A08")
        self.enviar(g, "presentar_reto", interno=True)
        antes = g.estado.serializar()
        self.assertEqual(g.procesar(tardio).motivo, "RETO_DISTINTO")
        self.assertEqual(g.estado.serializar(), antes)

    def test_evento_ignorado_no_se_reactiva_en_otra_fase(self):
        g = self.partida()
        temprano = g.crear_evento("continuar")
        self.assertFalse(g.procesar(temprano).aceptada)
        self.enviar(g, "seleccionar_habitat", habitat_id="H02")
        antes = g.estado.serializar()
        self.assertEqual(g.procesar(temprano).motivo, "EVENTO_DUPLICADO")
        self.assertEqual(g.estado.serializar(), antes)

    def test_entrada_desconocida_y_sesion_distinta(self):
        g = self.partida()
        antes = g.estado.serializar()
        evento = g.crear_evento("seleccionar_habitat", habitat_id="H99")
        self.assertEqual(g.procesar(evento).motivo, "HABITAT_DESCONOCIDO")
        ajeno = replace(g.crear_evento("ayuda"), sesion_id="OTRA")
        self.assertEqual(g.procesar(ajeno).motivo, "SESION_DISTINTA")
        self.assertEqual(g.estado.serializar(), antes)

    def test_politicas_y_parametros_congelados(self):
        for politica, esperado in [("ID3", ["V1", "V1", "V1", "V1"]),
                                   ("ROTACION", ["V1", "V2", "V3", "V1"]),
                                   ("PROBABILISTICO", ["V1", "V2", "V1", "V2"])]:
            with self.subTest(politica=politica):
                g = self.partida(politica=politica)
                iniciales = dict(g.motor.parametros)
                self.enviar(g, "ayuda")
                self.enviar(g, "ayuda")
                variantes = [self.enviar(g, "ayuda").respuesta.variante_id for _ in range(4)]
                self.assertEqual(variantes, esperado)
                self.enviar(g, "seleccionar_habitat", habitat_id="H02")
                self.assertEqual(dict(g.motor.parametros), iniciales)
                self.assertTrue(all(not o["modelo_actualizado"] for o in g.observaciones_cerradas))
                with self.assertRaises(TypeError):
                    g.motor.parametros[("H02", 3, 0, "V1")] = None

    def test_argmax_probabilistico_respeta_exclusion(self):
        # Valores artificiales de control, sin ejecutar un entrenamiento.
        with tempfile.TemporaryDirectory() as temporal:
            destino = Path(temporal)
            for fuente in self.banco.directorio.glob("*.json"):
                (destino / fuente.name).write_bytes(fuente.read_bytes())
            ruta = destino / "parametros_iniciales.json"
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            datos["estado_modelo"] = "PARAMETROS_ARTIFICIALES_DE_PRUEBA"
            valores = {"V1": (7, 5), "V2": (9, 3), "V3": (10, 2)}
            for r in datos["items"]:
                if r["contexto"] == {"habitat_guia_id": "H02", "nivel": 2, "repeticion_previa": 1}:
                    r["alpha"], r["beta"] = valores[r["variante_id"]]
            ruta.write_text(json.dumps(datos), encoding="utf-8")
            motor = MotorGuia(BancoDatos(destino), "PROBABILISTICO")
            ayuda, _, traza = motor.decidir("H02", 2, 1, {"H02:2": "V3"})
            self.assertEqual(ayuda["variante_id"], "V2")
            self.assertEqual(traza["variantes_elegibles"], ["V1", "V2"])
            self.assertAlmostEqual(traza["estimaciones"]["V2"], 0.75)

    def test_48_retos_automaticos_y_reinicio_local(self):
        g = GestorPartida(self.banco, 48, "PROBABILISTICO", origen="PRUEBA_DE_CONTROL_SINTETICA")
        self.enviar(g, "iniciar", modalidad="AGENTE")
        vistos = []
        for indice in range(48):
            g.avanzar_preparacion()
            vistos.append(g.estado.animal_id)
            self.assertEqual((g.estado.nivel, g.estado.repeticion_previa, g.estado.observacion), (0, 0, None))
            self.assertEqual(len(g.vista()["opciones_habitat"]), 8)
            self.enviar(g, "ayuda")
            self.enviar(g, "repetir")
            self.enviar(g, "seleccionar_habitat", habitat_id=g.estado.habitat_guia_id)
            self.enviar(g, "continuar")
            self.assertEqual(g.estado.completados, indice + 1)
        self.assertEqual(set(vistos), set(self.banco.animales))
        self.assertEqual(g.estado.fase, "COMPLETADA")
        self.assertEqual(g.avanzar_preparacion(), [])
        nueva = GestorPartida(self.banco)
        self.assertEqual(nueva.estado.fase, "INICIO")
        self.assertEqual(nueva.estado.variantes_anteriores, {})

    def test_ocho_opciones_y_catalogo_sin_datos_tecnicos(self):
        g = self.partida(animal="A31")
        for _ in range(4):
            self.enviar(g, "ayuda")
            vista = g.vista()
            self.assertEqual(len(vista["opciones_habitat"]), 8)
            self.assertEqual(len(vista["catalogo_animales"]), 48)
            self.assertNotIn("habitats_confirmados", vista["animal"])
            self.assertNotIn("K", vista)
        self.assertNotIn("H01", g.motor.arbol.nodos[g.estado.nodo_id].clases)
        self.enviar(g, "seleccionar_habitat", habitat_id="H01")
        self.assertEqual(g.estado.resultado, "VALIDA")

    def test_limites_y_eventos_internos(self):
        for n in (0, 49, True, 1.5):
            with self.assertRaises(ValueError):
                GestorPartida(self.banco, n)
        g = GestorPartida(self.banco, 1)
        self.enviar(g, "iniciar", modalidad="AGENTE")
        self.assertFalse(g.procesar(g.crear_evento("elegir_animal", animal_id="A08")).aceptada)
        self.assertFalse(g.procesar(g.crear_evento("generar_reto")).aceptada)
        self.enviar(g, "generar_reto", interno=True)
        self.assertFalse(g.procesar(g.crear_evento("presentar_reto")).aceptada)
        self.enviar(g, "presentar_reto", interno=True)

    def test_registro_jsonl_preserva_resultados_sin_etiqueta(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "registro.jsonl"
            g = GestorPartida(self.banco, 1, registro=Registro(ruta))
            self.enviar(g, "iniciar", modalidad="JUGADOR")
            self.enviar(g, "elegir_animal", animal_id="A31")
            self.enviar(g, "presentar_reto", interno=True)
            self.enviar(g, "ayuda")
            self.enviar(g, "seleccionar_habitat", habitat_id="H03")
            self.enviar(g, "seleccionar_habitat", habitat_id="H06")
            filas = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines()]
            cierres = [f for f in filas if f["tipo_registro"] == "OBSERVACION_CERRADA"]
            self.assertEqual(len(cierres), 1)
            self.assertIsNone(cierres[0]["resultado"])
            self.assertFalse(cierres[0]["etiqueta_disponible"])
            self.assertFalse(cierres[0]["modelo_actualizado"])

    def test_consola_jugador_recorrido_completo(self):
        with tempfile.TemporaryDirectory() as temporal:
            r = subprocess.run([sys.executable, "-m", "codigo.poc.consola", "--modalidad", "JUGADOR",
                                "--retos", "1", "--registro", str(Path(temporal) / "eventos.jsonl")],
                               input="31\nayuda\nrepetir\npausar\nreanudar\n3\n1\ncontinuar\n",
                               cwd=RAIZ_PROYECTO, text=True, encoding="utf-8", capture_output=True, timeout=20)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Puedes pedir una pista.", r.stdout)
            self.assertIn("Terminamos esta partida.", r.stdout)
            filas = [json.loads(l) for l in (Path(temporal) / "eventos.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(filas[-1]["estado_despues"]["fase"], "COMPLETADA")

    def test_consola_agente_y_fin_de_entrada(self):
        with tempfile.TemporaryDirectory() as temporal:
            for entrada, fase in [("ayuda\n1\ncontinuar\n", "COMPLETADA"), ("ayuda\n", "ABANDONADA")]:
                ruta = Path(temporal) / f"{fase}.jsonl"
                r = subprocess.run([sys.executable, "-m", "codigo.poc.consola", "--modalidad", "AGENTE",
                                    "--retos", "1", "--registro", str(ruta)], input=entrada,
                                   cwd=RAIZ_PROYECTO, text=True, encoding="utf-8", capture_output=True, timeout=20)
                self.assertEqual(r.returncode, 0, r.stderr)
                filas = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(filas[-1]["estado_despues"]["fase"], fase)
                if fase == "ABANDONADA":
                    cierre = next(f for f in filas if f["tipo_registro"] == "OBSERVACION_CERRADA")
                    self.assertIsNone(cierre["resultado"])


if __name__ == "__main__":
    unittest.main()

