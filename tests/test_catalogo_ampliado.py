"""Regresión de selección por afinidad y pistas del catálogo web ampliado."""
from collections import Counter
from random import Random
import unittest
from uuid import uuid4

from codigo.interfaz import idiomas
from codigo.interfaz.servicio import SesionWeb
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO
from codigo.nucleo.gestor import GestorPartida


class CatalogoAmpliado(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banco = BancoDatos(ampliado=True)

    def test_inventario_y_recursos(self):
        banco = self.banco
        self.assertEqual({6}, set(Counter(a["habitat_referencia_id"]
                                         for a in banco.animales.values()).values()))
        self.assertEqual(441, len(banco.pictogramas))
        self.assertEqual(144, len(banco.variantes))
        for ruta in [*(p["archivo_imagen"] for p in banco.pictogramas.values()),
                     *(h["paisaje"] for h in banco.habitats.values())]:
            self.assertTrue((RAIZ_PROYECTO / ruta).is_file(), ruta)
        for pista in banco.variantes.values():
            self.assertEqual(pista["texto_pt"], idiomas.texto(pista["texto"], "pt-BR", banco))

    def test_todos_los_animales_con_los_tres_tamanos(self):
        for animal, ficha in self.banco.animales.items():
            anterior = set()
            for cantidad in (2, 4, 8):
                with self.subTest(animal=animal, cantidad=cantidad):
                    conjuntos = []
                    for semilla in (7, 41):
                        gestor = GestorPartida(self.banco, 1, semilla_opciones=semilla,
                                                traza_completa=False)
                        gestor.procesar(gestor.crear_evento("iniciar", modalidad="JUGADOR",
                                                           cantidad_opciones=cantidad))
                        gestor.procesar(gestor.crear_evento("elegir_animal", animal_id=animal))
                        gestor.avanzar_preparacion()
                        opciones = set(gestor.estado.opciones_habitat)
                        self.assertEqual(cantidad, len(opciones))
                        self.assertTrue(set(ficha["habitats_confirmados"][:cantidad]) <= opciones)
                        self.assertTrue(anterior <= opciones)
                        conjuntos.append(opciones)
                    self.assertEqual(*conjuntos)
                    anterior = conjuntos[0]

    def test_secundario_del_delfin_y_reto_estable(self):
        sesion = SesionWeb(self.banco, aleatorio=Random(8))

        def actuar(tipo, **payload):
            entrada = {k: sesion.vista()[k] for k in ("sesion_id", "reto_id", "revision")}
            return sesion.actuar({**entrada, "tipo": tipo, "evento_id": uuid4().hex,
                                 "payload": payload})["vista"]

        actuar("iniciar", modalidad="JUGADOR", cantidad_opciones=2, retos=1)
        inicio = actuar("elegir_animal", animal_id="A33")
        self.assertEqual({"H23", "H08"}, {h["id"] for h in inicio["opciones_habitat"]})
        self.assertEqual(("H23", "H08", "H25", "H27", "H30", "H24", "H41", "H33"),
                         self.banco.opciones_ordenadas["A33"][:8])
        for tipo in ("ayuda", "repetir", "pausar", "reanudar"):
            self.assertEqual(inicio["opciones_habitat"], actuar(tipo)["opciones_habitat"])
        self.assertEqual(inicio["opciones_habitat"], sesion.vista()["opciones_habitat"])
        sesion.cambiar_idioma({**sesion.vista(), "idioma": "pt-BR"})
        valido = actuar("seleccionar_habitat", habitat_id="H08")
        self.assertEqual("RETO_RESUELTO", valido["fase"])
        self.assertEqual(1, valido["progreso"]["completados"])
        self.assertIn("quando o rio transborda", valido["respuesta"]["texto_voz"])

    def test_contraste_pendiente_activa_ayuda_y_revela_habitat(self):
        gestor = GestorPartida(self.banco, 1, ayuda_en_pendiente=True)
        gestor.procesar(gestor.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=2))
        gestor.procesar(gestor.crear_evento("elegir_animal", animal_id="N144"))
        gestor.avanzar_preparacion()
        self.assertEqual({"H31", "H24"}, set(gestor.estado.opciones_habitat))
        salida = gestor.procesar(gestor.crear_evento("seleccionar_habitat", habitat_id="H24"))
        self.assertEqual("NEUTRAL", salida.respuesta.tipo_respuesta)
        self.assertEqual(0, gestor.estado.completados)
        self.assertEqual(1, salida.respuesta.nivel)
        gestor.procesar(gestor.crear_evento("ayuda"))
        salida = gestor.procesar(gestor.crear_evento("ayuda"))
        self.assertEqual(("P_SENALAR", "P_H31"), salida.respuesta.pictogramas)

    def test_modo_aleatorio_facil_evita_habitats_afines_y_varia(self):
        from codigo.nucleo.gestor import FAMILIA_HABITAT, FAMILIAS_ACUATICAS
        # En la interfaz web (Hito 3), las opciones no confirmadas son aleatorias,
        # de familias visuales distintas al objetivo y distintas entre sí.
        for animal in ("A01", "A05", "N012", "N144"):
            ficha = self.banco.animales[animal]
            confirmados = set(ficha["habitats_confirmados"])
            familias_obj = {FAMILIA_HABITAT[h] for h in confirmados}
            evitar = set(ficha["contrastes_preferentes"])
            for h_id in confirmados:
                evitar.update(self.banco.habitats[h_id]["afines"])
            evitar -= confirmados
            vistos = []
            for semilla in (1, 2, 3):
                g = GestorPartida(self.banco, 1, semilla_opciones=semilla,
                                  modo_opciones="aleatorio_facil", traza_completa=False)
                g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=8))
                g.procesar(g.crear_evento("elegir_animal", animal_id=animal))
                g.avanzar_preparacion()
                opciones = set(g.estado.opciones_habitat)
                self.assertEqual(8, len(opciones))
                self.assertTrue(confirmados <= opciones)
                distractores = opciones - confirmados
                self.assertEqual(set(), distractores & evitar)
                self.assertEqual(set(), {FAMILIA_HABITAT[h] for h in distractores} & familias_obj)
                if len(confirmados) == 1:
                    self.assertEqual(len(distractores), len({FAMILIA_HABITAT[h] for h in distractores}))
                vistos.append(frozenset(opciones))
            self.assertGreater(len(set(vistos)), 1)

        # En tableros de 2 y 4 opciones para animales acuáticos, ningún distractor es acuático.
        for animal in self.banco.animales:
            ficha = self.banco.animales[animal]
            confirmados = set(ficha["habitats_confirmados"])
            familias_obj = {FAMILIA_HABITAT[h] for h in confirmados}
            g = GestorPartida(self.banco, 1, semilla_opciones=42,
                              modo_opciones="aleatorio_facil", traza_completa=False)
            g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=4))
            g.procesar(g.crear_evento("elegir_animal", animal_id=animal))
            g.avanzar_preparacion()
            distractores = set(g.estado.opciones_habitat) - confirmados
            self.assertEqual(set(), {FAMILIA_HABITAT[h] for h in distractores} & familias_obj, animal)
            self.assertEqual(len(distractores), len({FAMILIA_HABITAT[h] for h in distractores}), animal)
            if familias_obj <= FAMILIAS_ACUATICAS:
                self.assertEqual(set(), {FAMILIA_HABITAT[h] for h in distractores} & FAMILIAS_ACUATICAS, animal)
