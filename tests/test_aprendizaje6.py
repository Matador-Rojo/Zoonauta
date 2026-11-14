"""Agente 6.0 aprendido fuera de la partida: etiquetas, modelo Beta-Bernoulli, seguridad y simulación.

Pruebas automáticas con datos simulados; no validan nada sobre personas reales.
"""
import json
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest

from codigo.entrenamiento import entrenar_agente6 as ent
from codigo.motores.agente import MotorAgente
from codigo.motores.aprendizaje6 import (CLAVES, MODELO_DEMO, ModeloAyudas, MotorAgenteAprendido)
from codigo.nucleo.datos import BancoDatos, ErrorDatos
from codigo.nucleo.gestor import GestorPartida
from codigo.nucleo.registro import Registro


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos(ampliado=True)

    def reto(self, motor, animal="A01", k=8, registro=None):
        g = GestorPartida(self.banco, 1, motor=motor, ayuda_en_pendiente=True, semilla_opciones=7,
                          traza_completa=False, registro=registro or Registro())
        g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=k))
        g.procesar(g.crear_evento("elegir_animal", animal_id=animal))
        g.avanzar_preparacion()
        return g


class Etiquetas(Base):
    def test_recompensa_desde_el_registro_de_la_partida(self):
        registro = Registro()
        g = self.reto(MotorAgente(self.banco, solo_grabadas=False), registro=registro)
        confirmados = self.banco.animales["A01"]["habitats_confirmados"]
        pendiente = next(o for o in g.estado.opciones_habitat if o not in confirmados)
        g.procesar(g.crear_evento("ayuda"))
        g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=pendiente))
        g.procesar(g.crear_evento("ayuda"))
        g.procesar(g.crear_evento("seleccionar_habitat", habitat_id="H01"))
        cierres = [f["evento_cierre"] for f in registro.filas if f["tipo_registro"] == "OBSERVACION_CERRADA"]
        self.assertEqual(["SELECCION_PENDIENTE", "NUEVA_AYUDA", "SELECCION_VALIDA"], cierres)
        lista = ent.etiquetas(registro.filas)
        self.assertEqual([0, 0, 1], [x["resultado"] for x in lista])
        self.assertTrue(all(x["clave"] in CLAVES for x in lista))

    def test_salir_no_da_etiqueta_y_senalar_no_se_aprende(self):
        registro = Registro()
        g = self.reto(MotorAgente(self.banco), registro=registro)
        g.procesar(g.crear_evento("ayuda"))
        g.procesar(g.crear_evento("salir"))
        self.assertEqual([], ent.etiquetas(registro.filas))
        filas = [{"tipo_registro": "AYUDA_PRESENTADA", "observacion_id": "O1", "decision": {"clave_aprendizaje": None}},
                 {"tipo_registro": "OBSERVACION_CERRADA", "observacion_id": "O1", "evento_cierre": "SELECCION_VALIDA"}]
        self.assertEqual([], ent.etiquetas(filas))

    def test_la_clave_del_simulador_coincide_con_la_del_agente(self):
        motor = MotorAgente(self.banco, solo_grabadas=False)
        for animal in list(self.banco.animales)[::29]:
            g = self.reto(motor, animal, 8)
            salida = g.procesar(g.crear_evento("ayuda"))
            if salida.respuesta.nivel < 3:
                self.assertEqual(salida.traza["clave_aprendizaje"],
                                 ent.clave_mostrada(motor, self.banco, g.estado, False))


class Modelo(Base):
    def test_beta_bernoulli_guardar_y_cargar(self):
        m = ModeloAyudas.nuevo(self.banco, "PRUEBA")
        clave = CLAVES[0]
        self.assertEqual(0.5, m.media(clave))
        for y in (1, 1, 0):
            m.actualizar(clave, y)
        self.assertAlmostEqual(3 / 5, m.media(clave))
        with TemporaryDirectory() as tmp:
            m.guardar(Path(tmp) / "m.json")
            otro = ModeloAyudas.cargar(Path(tmp) / "m.json")
        self.assertEqual(m.parametros, otro.parametros)
        with self.assertRaises(ValueError):
            m.actualizar(clave, 2)

    def test_rechaza_un_modelo_de_otros_rasgos(self):
        m = ModeloAyudas.nuevo(self.banco, "PRUEBA")
        m.huellas["atributos"] = "0" * 64
        with self.assertRaises(ErrorDatos):
            MotorAgenteAprendido(self.banco, m)
        documento = m.documento()
        documento["esquema"] = "otro"
        with self.assertRaises(ErrorDatos):
            ModeloAyudas(documento)

    def test_modelo_de_demostracion_congelado(self):
        self.assertTrue(MODELO_DEMO.is_file())
        modelo = ModeloAyudas.cargar(MODELO_DEMO)
        self.assertEqual(ent.ORIGEN_SIMULADO, modelo.origen)
        antes = json.dumps(modelo.parametros, sort_keys=True)
        motor = MotorAgenteAprendido(self.banco)  # el de demostración
        self.assertTrue(motor.parametros_congelados)
        decisiones = []
        for _ in range(2):
            g = self.reto(motor)
            decisiones.append([g.procesar(g.crear_evento("ayuda")).respuesta.contenido_id for _ in range(3)])
        self.assertEqual(decisiones[0], decisiones[1])
        self.assertEqual(antes, json.dumps(motor.modelo.parametros, sort_keys=True))
        g = self.reto(motor)
        self.assertEqual("APRENDIDO_CONGELADO", g.procesar(g.crear_evento("ayuda")).traza["modelo_estado"])


class Seguridad(Base):
    def modelos_adversarios(self):
        """Modelos aleatorios con preferencias extremas: el aprendizaje puede ser cualquier cosa."""
        for semilla in range(4):
            azar = Random(semilla)
            m = ModeloAyudas.nuevo(self.banco, "PRUEBA")
            for clave in CLAVES:
                m.parametros[clave].update(alpha=azar.choice((1.0, 1000.0)), beta=azar.choice((1.0, 1000.0)))
            yield m

    def test_el_modelo_solo_reordena_dentro_de_las_ayudas_seguras(self):
        for m in self.modelos_adversarios():
            for solo_grabadas in (True, False):
                motor = MotorAgenteAprendido(self.banco, m, solo_grabadas=solo_grabadas)
                rep = motor.rep
                for animal, ficha in list(self.banco.animales.items())[::7]:
                    for k in (2, 4, 8):
                        g = self.reto(motor, animal, k)
                        self.assertNotEqual(3, g.procesar(g.crear_evento("ayuda")).respuesta.nivel)
                        distractores = [o for o in g.estado.opciones_habitat if o not in ficha["habitats_confirmados"]]
                        if not distractores:
                            continue
                        g = self.reto(motor, animal, k)
                        salida = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=distractores[0]))
                        r = salida.respuesta
                        if solo_grabadas and r.contenido_id.startswith("AY_ATR_"):
                            self.assertIn(r.contenido_id, motor.rep.ayudas_activas)  # solo con grabación
                        c = next((c for c in rep._candidatas[g.estado.habitat_guia_id] if c.id == r.contenido_id), None)
                        if c is None:
                            continue
                        self.assertNotIn(rep.relacion(c, distractores[0]), ("compartida", "parcial"))
                        elegida = next(e for e in salida.traza["candidatas"] if e["id"] == c.id)
                        if elegida["aleja_de_valida"]:
                            # Solo si ninguna otra ayuda útil evitaba alejar de una respuesta válida.
                            utiles = [e for e in salida.traza["candidatas"] if e["informativa"] and e["utilidad"] > 0]
                            self.assertTrue(all(e["aleja_de_valida"] for e in utiles))

    def test_jaguar_no_se_aleja_del_bosque_templado(self):
        # Caso encontrado en la revisión: tras elegir H14, el modelo de demostración daba
        # «Busca un bosque cálido y húmedo.», que aleja de H04 (válido para el jaguar).
        for motor in (MotorAgenteAprendido(self.banco), *(MotorAgenteAprendido(self.banco, m)
                                                          for m in self.modelos_adversarios())):
            g = GestorPartida(self.banco, 1, motor=motor, ayuda_en_pendiente=True, semilla_opciones=0,
                              traza_completa=False)
            g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=8))
            g.procesar(g.crear_evento("elegir_animal", animal_id="A01"))
            g.avanzar_preparacion()
            self.assertIn("H04", g.estado.opciones_habitat)
            salida = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id="H14"))
            c = next((c for c in motor.rep._candidatas["H01"] if c.id == salida.respuesta.contenido_id), None)
            if c is not None:
                self.assertNotEqual("conflicto", motor.rep.relacion(c, "H04"))


class Simulacion(Base):
    def test_recupera_las_probabilidades_plantadas(self):
        modelo, curva = ent.entrenar_simulado(self.banco, "IDEAS", 9, pasadas=1, cada=432)
        self.assertEqual(ent.ORIGEN_SIMULADO, modelo.origen)
        self.assertLess(curva[-1]["error_medio_ponderado"], 0.08)
        self.assertGreater(curva[-1]["observaciones"], 500)

    def test_entrenar_desde_archivos_de_registro(self):
        with TemporaryDirectory() as tmp:
            registro = Registro(Path(tmp) / "S1.jsonl")
            g = self.reto(MotorAgente(self.banco), registro=registro)
            g.procesar(g.crear_evento("ayuda"))
            g.procesar(g.crear_evento("seleccionar_habitat", habitat_id="H01"))
            lista = ent.etiquetas(ent.leer_registros(Path(tmp)))
        self.assertEqual(1, len(lista))
        self.assertEqual(1, lista[0]["resultado"])

    def test_entrenar_descarta_otra_version_de_los_datos(self):
        registro = Registro()
        g = self.reto(MotorAgente(self.banco), registro=registro)
        g.procesar(g.crear_evento("ayuda"))
        g.procesar(g.crear_evento("seleccionar_habitat", habitat_id="H01"))
        h = self.banco.huellas
        version = f"{h['expedicion/atributos_habitats.json']}:{h['expedicion/pistas.json']}"
        self.assertEqual(1, len(ent.etiquetas(registro.filas, version)))
        viejas = [{**f, "modelo_version": "otra:version"} if f["tipo_registro"] == "AYUDA_PRESENTADA" else f
                  for f in registro.filas]
        self.assertEqual([], ent.etiquetas(viejas, version))

    def test_probabilidades_plantadas_validas(self):
        azar = Random(1)
        for condicion in ent.CONDICIONES:
            for clave in azar.sample(CLAVES, 20):
                self.assertTrue(0.05 <= ent.probabilidad_plantada(condicion, clave) <= 0.95)


if __name__ == "__main__":
    unittest.main()
