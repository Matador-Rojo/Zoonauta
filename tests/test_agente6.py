"""Agente de la 6.0 con el catálogo ampliado: datos, decisiones, controles y voz.

Pruebas automáticas, sin personas: comprueban que las decisiones son coherentes con los
datos documentados, no que ayuden a un jugador real (eso requiere validación con usuarios).
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from codigo.interfaz import idiomas, voz_grabada
from codigo.motores.agente import (MotorAgente, MotorID3Opciones, Representacion,
                                   ayudas_con_grabacion)
from codigo.motores.id3 import ganancia
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.gestor import GestorPartida


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos(ampliado=True)
        cls.rep = Representacion(cls.banco)
        cls.agente = MotorAgente(cls.banco, solo_grabadas=False)
        cls.agente_grabadas = MotorAgente(cls.banco)
        cls.id3 = MotorID3Opciones(cls.banco, solo_grabadas=False)

    def reto(self, animal, k, motor=None):
        g = GestorPartida(self.banco, 1, motor=motor or self.agente, ayuda_en_pendiente=True,
                          semilla_opciones=7, traza_completa=False)
        g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=k))
        g.procesar(g.crear_evento("elegir_animal", animal_id=animal))
        g.avanzar_preparacion()
        return g

    def pista(self, g):
        return g.procesar(g.crear_evento("ayuda"))

    def elegir(self, g, h):
        return g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=h))

    def candidata(self, guia, contenido_id):
        return next(c for c in [*self.rep._candidatas[guia], self.rep.senalar(guia)] if c.id == contenido_id)

    def animal(self, guia, visible, k=8):
        return next(a for a, f in self.banco.animales.items() if f["habitat_referencia_id"] == guia
                    and visible in self.banco.opciones_ordenadas[a][:k])


class DatosRasgos(Base):
    def test_cada_valor_cita_una_pista_revisada_del_mismo_habitat(self):
        total = 0
        for h, rasgos in self.banco.rasgos_habitat.items():
            for _atributo, (_valor, pista_id) in rasgos.items():
                pista = self.banco.variantes[pista_id]
                self.assertEqual(h, pista["habitat_guia_id"])
                self.assertIn(pista["nivel"], (1, 2))
                total += 1
        self.assertEqual(111, total)
        # Sin datos no se inventan: dos hábitats quedan sin rasgos (pendiente de revisión).
        self.assertEqual({"H28", "H30"}, {h for h, r in self.banco.rasgos_habitat.items() if not r})
        # «Hay mucho pasto y pocos árboles en altura.» es la pista 2 de H16, no la 1.
        self.assertEqual(("pasto", "AY_H16_L2"), self.banco.rasgos_habitat["H16"]["vegetacion"])

    def test_ayudas_por_rasgo_breves_con_pictogramas_y_traduccion(self):
        apoyo = self.banco.mensajes["MSG_APOYO_AUTO"]["texto"]
        self.assertEqual(32, len(self.banco.ayudas_rasgo))
        for ayuda in self.banco.ayudas_rasgo.values():
            with self.subTest(ayuda=ayuda["id"]):
                self.assertTrue(ayuda["texto"].startswith("Busca ") and ayuda["texto"].endswith("."))
                self.assertLessEqual(len(ayuda["texto"]), 60)
                self.assertTrue(1 <= len(ayuda["pictogramas"]) <= 2)
                for t in ayuda["pictogramas"]:
                    self.assertIn(t["id"], self.banco.pictogramas)
                self.assertEqual(ayuda["texto_pt"], idiomas.texto(ayuda["texto"], "pt-BR", self.banco))
                self.assertTrue(idiomas.texto(f"{apoyo} {ayuda['texto']}", "pt-BR", self.banco))

    def test_desconocido_nunca_descarta(self):
        # H28 (turbera) no documenta rasgos: ninguna ayuda puede descartarla.
        for g in self.banco.habitats:
            for c in self.rep.candidatas(g):
                self.assertNotEqual("conflicto", self.rep.relacion(c, "H28"))

    def test_relaciones(self):
        def cand(g, i):
            return next(c for c in self.rep._candidatas[g] if c.id == i)
        # Una ayuda por rasgo dice lo mismo de otro hábitat que documenta ese rasgo igual.
        for g, i, d in (("H01", "AY_ATR_ARBOLES", "H08"), ("H07", "AY_ATR_COSTA", "H41"),
                        ("H44", "AY_ATR_ROCAS", "H20"), ("H21", "AY_ATR_POCA_LUZ", "H35")):
            self.assertEqual("compartida", self.rep.relacion(cand(g, i), d))
        # Una pista que añade algo no documentado en d no es «igual» (desconocido ≠ igual).
        self.assertEqual("parcial", self.rep.relacion(cand("H37", "AY_H37_L2"), "H40"))
        self.assertEqual("parcial", self.rep.relacion(cand("H01", "AY_H01_L1"), "H08"))
        self.assertEqual("conflicto", self.rep.relacion(cand("H06", "AY_ATR_FRIO"), "H05"))


class Decisiones(Base):
    def comprobar_compatible(self, g, salida):
        s = g.estado
        c = self.candidata(s.habitat_guia_id, salida.respuesta.contenido_id)
        self.assertIn(s.habitat_guia_id, s.opciones_habitat)
        documentados = {a: v for a, (v, _) in self.banco.rasgos_habitat[s.habitat_guia_id].items()}
        for atributo, valor in c.rasgos.items():
            self.assertEqual(documentados[atributo], valor)
        if c.tipo == "SENALAR":
            self.assertEqual(f"P_{s.habitat_guia_id}", c.plantilla["pictogramas"][-1]["id"])
        self.assertIn(salida.respuesta.nivel, (1, 2, 3))
        return c

    def test_exhaustivo_ayudas_compatibles_con_2_4_y_8_opciones(self):
        for motor in (self.agente, self.agente_grabadas, self.id3):
            for animal, ficha in self.banco.animales.items():
                for k in (2, 4, 8):
                    with self.subTest(politica=motor.politica, animal=animal, k=k):
                        g = self.reto(animal, k, motor)
                        opciones = g.estado.opciones_habitat
                        self.assertEqual(k, len(set(opciones)))
                        self.assertTrue(set(ficha["habitats_confirmados"][:k]) <= set(opciones))
                        self.comprobar_compatible(g, self.pista(g))
                        distractores = [o for o in opciones if o not in ficha["habitats_confirmados"]]
                        for d in distractores[:2]:
                            g = self.reto(animal, k, motor)
                            salida = self.elegir(g, d)
                            self.assertEqual("NEUTRAL", salida.respuesta.tipo_respuesta)
                            c = self.comprobar_compatible(g, salida)
                            if motor is not self.id3 and c.tipo != "SENALAR":
                                # El agente nunca repite algo que también describe lo elegido.
                                self.assertNotIn(self.rep.relacion(c, d), ("compartida", "parcial"))

    def test_primera_pista_nunca_revela_y_ninguna_frase_se_repite(self):
        for motor in (self.agente, self.agente_grabadas):
            for animal in self.banco.animales:
                for k in (2, 4, 8):
                    with self.subTest(politica=motor.politica, animal=animal, k=k):
                        g = self.reto(animal, k, motor)
                        # Sin errores previos, la primera Pista no es «Señala el hábitat …».
                        self.assertNotEqual(3, self.pista(g).respuesta.nivel)
                        textos = [g.estado.respuesta_educativa.texto_voz]
                        for _ in range(3):
                            r = self.pista(g).respuesta
                            if r.nivel == 3:
                                break
                            textos.append(r.texto_voz)
                        self.assertEqual(len(textos), len(set(textos)))

    def test_salta_la_pista_identica_al_habitat_parecido(self):
        # H04 y H05 comparten la pista 1 («Busca un bosque de clima templado.»).
        animal = self.animal("H04", "H05", 4)
        g = self.reto(animal, 4, self.agente_grabadas)
        self.assertIn("H05", g.estado.opciones_habitat)
        salida = self.pista(g)
        self.assertEqual("AY_H04_L2", salida.respuesta.contenido_id)
        self.assertEqual("conflicto", self.rep.relacion(self.candidata("H04", "AY_H04_L2"), "H05"))
        # Sin motor explícito, la partida del catálogo ampliado usa el agente.
        self.assertEqual("AGENTE_ADAPTATIVO", GestorPartida(self.banco, 1).motor.politica)

    def test_distingue_la_ultima_eleccion_con_un_rasgo_documentado(self):
        animal = self.animal("H06", "H05")  # lobo gris: taiga frente a coníferas templadas
        g = self.reto(animal, 8)
        salida = self.elegir(g, "H05")
        c = self.candidata("H06", salida.respuesta.contenido_id)
        self.assertEqual("conflicto", self.rep.relacion(c, "H05"))
        self.assertEqual("DISTINGUE_LA_ULTIMA_ELECCION", salida.traza["regla"])
        self.assertTrue(salida.respuesta.texto_voz.startswith("Vamos a buscar otro lugar. "))

    def test_no_aleja_de_un_secundario_documentado_visible(self):
        # Jaguar: selva (principal) y bosque templado (secundario con fuente) son válidos.
        for motor in (self.agente, self.agente_grabadas):
            g = self.reto("A01", 8, motor)
            self.assertIn("H04", g.estado.opciones_habitat)
            c = self.candidata("H01", self.pista(g).respuesta.contenido_id)
            self.assertNotEqual("conflicto", self.rep.relacion(c, "H04"))
            self.elegir(g, "H04")
            self.assertEqual("RETO_RESUELTO", g.estado.fase)

    def test_apoyo_explicito_tras_dos_elecciones_o_tres_pistas(self):
        animal = self.animal("H06", "H05")
        g = self.reto(animal, 8)
        pendientes = [o for o in g.estado.opciones_habitat
                      if o not in self.banco.animales[animal]["habitats_confirmados"]]
        self.elegir(g, pendientes[0])
        salida = self.elegir(g, pendientes[1])
        self.assertEqual(3, salida.respuesta.nivel)
        self.assertEqual("APOYO_EXPLICITO_TRAS_VARIAS_ELECCIONES", salida.traza["regla"])
        g = self.reto("A01", 8)
        reglas = [self.pista(g).traza["regla"] for _ in range(4)]
        self.assertEqual(3, g.estado.nivel)
        self.assertIn(reglas[3], ("APOYO_EXPLICITO_TRAS_VARIAS_PISTAS", "MANTENER_APOYO_EXPLICITO"))


class Controles(Base):
    def test_repetir_conserva_el_mensaje_exacto_y_marca_dificultad(self):
        g = self.reto("A01", 8)
        primera = self.pista(g).respuesta
        ayudas = list(g.estado.ayudas_reto)
        repetida = g.procesar(g.crear_evento("repetir")).respuesta
        self.assertEqual(primera, repetida)
        self.assertEqual(ayudas, g.estado.ayudas_reto)
        siguiente = self.pista(g)
        self.assertNotEqual(primera.contenido_id, siguiente.respuesta.contenido_id)
        self.assertTrue(siguiente.traza["estado_reto"]["dificultad"])

    def test_pausar_y_reanudar_no_cambian_la_decision(self):
        a, b = self.reto("A01", 4), self.reto("A01", 4)
        self.pista(a), self.pista(b)
        b.procesar(b.crear_evento("pausar"))
        reanudada = b.procesar(b.crear_evento("reanudar")).respuesta
        self.assertEqual(a.estado.respuesta_educativa, reanudada)
        self.assertEqual(self.pista(a).respuesta, self.pista(b).respuesta)


class VozYBaseline(Base):
    def test_sin_grabacion_no_se_usa_la_ayuda_por_rasgo(self):
        activas = ayudas_con_grabacion(self.banco)
        # Hoy solo «Busca un lugar con arbustos.» tiene grabación (es idéntica a AY_H13_L1).
        self.assertEqual({"AY_ATR_ARBUSTOS"}, activas)
        for animal in list(self.banco.animales)[::7]:
            g = self.reto(animal, 8, self.agente_grabadas)
            for _ in range(3):
                contenido = self.pista(g).respuesta.contenido_id
                self.assertTrue(not contenido.startswith("AY_ATR_") or contenido in activas)

    def test_al_llegar_las_grabaciones_el_agente_las_usa(self):
        with TemporaryDirectory() as tmp, patch.object(voz_grabada, "CARPETA_AUDIO", Path(tmp)):
            (Path(tmp) / "es-419").mkdir()
            for nombre in ("AY_ATR_FRIO", "MSG_APOYO_AUTO__AY_ATR_FRIO"):
                (Path(tmp) / f"es-419/{nombre}.mp3").write_bytes(b"ID3" + b"x" * 2048)
            motor = MotorAgente(self.banco)
            self.assertEqual({"AY_ATR_FRIO"}, motor.rep.ayudas_activas)
            g = self.reto(self.animal("H06", "H05"), 8, motor)
            self.assertEqual("AY_ATR_FRIO", self.pista(g).respuesta.contenido_id)

    def test_id3_elige_la_mayor_ganancia_de_informacion(self):
        for animal in list(self.banco.animales)[::11]:
            g = self.reto(animal, 8, self.id3)
            guia, opciones = g.estado.habitat_guia_id, list(g.estado.opciones_habitat)
            camino, pasos = self.id3.camino(guia, opciones)
            if not camino:
                continue
            candidatas = self.id3.rep.candidatas(guia)
            filas = [{"clase": o, "atributos": {c.id: ("descarta" if o != guia and self.rep.relacion(c, o) == "conflicto"
                                                      else "mantiene") for c in candidatas}} for o in opciones]
            mejor = max(ganancia(filas, c.id) for c in candidatas)
            self.assertAlmostEqual(mejor, pasos[0]["ganancia"])
            self.assertEqual(camino[0].id, self.pista(g).respuesta.contenido_id)


if __name__ == "__main__":
    unittest.main()
