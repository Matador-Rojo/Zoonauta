"""Agente de la 6.0: elige la ayuda de cada reto del catálogo ampliado.

Qué sabe el agente (representación):
  * Los rasgos documentados de cada hábitat (``datos/expedicion/atributos_habitats.json``):
    cada valor cita la pista revisada que lo dice. Sin valor = desconocido.
  * Los conceptos (pictogramas) de las pistas 1 y 2 de cada hábitat.

Qué puede decir (candidatas): solo frases verdaderas del hábitat guía del animal:
  * sus pistas revisadas 1 y 2;
  * las ayudas breves por rasgo (una idea y un pictograma) de los rasgos documentados del
    hábitat guía, si su grabación existe (``solo_grabadas``);
  * su pista 3 («Señala el hábitat …»), el apoyo explícito, como último recurso.

Cómo compara una candidata con otra opción visible ``d``:
  * ``conflicto``: ``d`` documenta otro valor del mismo rasgo → la ayuda la distingue;
  * ``compartida``: todo lo que muestra la ayuda (sus pictogramas, o el único rasgo de una
    ayuda por rasgo) también consta en ``d`` → no sirve para separarlas;
  * ``parcial``: parte de lo que dice vale para ``d`` y el resto no consta en ``d``;
  * ``propia``: nada de lo que dice consta en ``d`` → probablemente la distingue, sin comprobar.
Nada de esto se muestra al jugador: las frases siempre describen el hábitat guía en
positivo. Un hábitat no confirmado para el animal es una relación desconocida, no
«incorrecta», y una ayuda nunca afirma algo de las otras opciones.

Dos políticas comparten esta representación:
  * ``ID3_OPCIONES`` (línea base): un árbol ID3 (``codigo.motores.id3``, entropía y
    ganancia de información) construido al empezar el reto con las opciones visibles;
    presenta las ayudas del camino del hábitat guía y no mira lo que hace el jugador.
  * ``AGENTE_ADAPTATIVO`` (modelo principal): decide en cada petición con el estado del
    reto (opciones que quedan, elecciones, ayudas ya vistas, Repetir) maximizando una
    utilidad esperada con parámetros fijos. No aprende durante la partida.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from time import perf_counter_ns

from codigo.motores.id3 import ArbolID3
from codigo.nucleo.datos import BancoDatos, ErrorDatos

POLITICA_AGENTE = "AGENTE_ADAPTATIVO"
POLITICA_ID3 = "ID3_OPCIONES"

# Parámetros del modelo de decisión, fijados a mano y documentados en
# docs/agente/agente_6.md. No se ajustan con datos de jugadores (no los hay).
PESO_PROPIA = 0.5          # una diferencia no comprobada cuenta la mitad que una documentada
COMPRENSION_POR_IDEA = 0.85  # probabilidad relativa de entender cada idea extra de la frase
COMPRENSION_CON_DIFICULTAD = 0.6  # tras Repetir o una elección que la ayuda anterior descartaba
BONO_ULTIMA_ELECCION = 1.0   # distinguir el hábitat que el jugador acaba de elegir
PESO_PARCIAL = 0.25        # comparte parte de lo que dice con la otra opción
PENALIZACION_VALIDA = 1.0    # alejar de otra respuesta válida visible
MAX_PISTAS_ANTES_DE_SENALAR = 3
ELECCIONES_ANTES_DE_SENALAR = 2


@dataclass(frozen=True)
class Candidata:
    plantilla: dict
    tipo: str                          # PISTA | RASGO | SENALAR
    rasgos: dict = field(default_factory=dict)   # atributo -> valor que afirma del guía
    conceptos: frozenset = frozenset()

    @property
    def id(self) -> str:
        return self.plantilla["id"]


class Representacion:
    def __init__(self, banco: BancoDatos, ayudas_activas: set[str] | None = None):
        if not banco.ampliado:
            raise ErrorDatos("El agente 6.0 requiere el catálogo ampliado.")
        self.banco = banco
        self.rasgos = banco.rasgos_habitat
        self.conceptos = {h: frozenset(t["id"] for n in (1, 2)
                                       for t in banco.pistas_progresivas[h, n]["pictogramas"])
                          for h in banco.habitats}
        self.ayuda_de = {(a["atributo"], a["valor"]): a for a in banco.ayudas_rasgo.values()}
        self.ayudas_activas = set(banco.ayudas_rasgo) if ayudas_activas is None else set(ayudas_activas)
        self._candidatas = {h: self._construir(h) for h in banco.habitats}

    def _construir(self, g: str) -> list[Candidata]:
        lista = []
        for nivel in (1, 2):
            pista = self.banco.pistas_progresivas[g, nivel]
            rasgos = {a: v for a, (v, evidencia) in self.rasgos[g].items() if evidencia == pista["id"]}
            lista.append(Candidata(pista, "PISTA", rasgos,
                                   frozenset(t["id"] for t in pista["pictogramas"])))
        textos_pistas = {c.plantilla["texto"] for c in lista}
        for atributo, (valor, evidencia) in sorted(self.rasgos[g].items()):
            ayuda = self.ayuda_de[atributo, valor]
            if ayuda["texto"] in textos_pistas:
                continue  # misma frase que una pista del hábitat: se usa la pista, no se repite
            plantilla = {"id": ayuda["id"], "texto": ayuda["texto"], "texto_pt": ayuda["texto_pt"],
                         "pictogramas": ayuda["pictogramas"], "habitat_guia_id": g,
                         "nivel": self.banco.variantes[evidencia]["nivel"], "variante_id": "RASGO",
                         "evidencia": evidencia}
            lista.append(Candidata(plantilla, "RASGO", {atributo: valor},
                                   frozenset(t["id"] for t in ayuda["pictogramas"])))
        return lista

    def candidatas(self, g: str) -> list[Candidata]:
        return [c for c in self._candidatas[g] if c.tipo == "PISTA" or c.id in self.ayudas_activas]

    def senalar(self, g: str) -> Candidata:
        pista = self.banco.pistas_progresivas[g, 3]
        return Candidata(pista, "SENALAR", {}, frozenset(t["id"] for t in pista["pictogramas"]))

    def relacion(self, c: Candidata, d: str) -> str:
        rd = self.rasgos[d]
        if any(a in rd and rd[a][0] != v for a, v in c.rasgos.items()):
            return "conflicto"
        # «compartida» solo si todo lo que la ayuda muestra (sus pictogramas) también aparece en
        # las pistas de d; si dice algo que d no documenta, eso es desconocido, no igual.
        if c.conceptos <= self.conceptos[d]:
            return "compartida"
        # Una ayuda por rasgo solo dice ese rasgo: si d lo documenta igual, dice lo mismo de d.
        if c.tipo == "RASGO" and all(a in rd and rd[a][0] == v for a, v in c.rasgos.items()):
            return "compartida"
        if any(a in rd and rd[a][0] == v for a, v in c.rasgos.items()):
            return "parcial"   # dice algo que también vale para d; el resto no consta en d
        return "propia"


def ayudas_con_grabacion(banco: BancoDatos) -> set[str]:
    """Ayudas por rasgo con grabación sola y tras «Vamos a buscar otro lugar.» (es-419)."""
    from codigo.interfaz import voz_grabada  # import tardío: el núcleo no depende de la interfaz
    apoyo = banco.mensajes["MSG_APOYO_AUTO"]["texto"]
    return {i for i, a in banco.ayudas_rasgo.items()
            if voz_grabada.buscar(a["texto"], "es", banco)
            and voz_grabada.buscar(f"{apoyo} {a['texto']}", "es", banco)}


class _MotorReto:
    """Base común: misma interfaz que el gestor espera de los motores (decidir_reto)."""
    politica = ""
    nodo_inicial = "INICIO_AGENTE"
    parametros_congelados = True

    def __init__(self, banco: BancoDatos, *, solo_grabadas: bool = True,
                 ayudas_activas: set[str] | None = None):
        if ayudas_activas is None and solo_grabadas:
            ayudas_activas = ayudas_con_grabacion(banco)
        self.banco = banco
        self.rep = Representacion(banco, ayudas_activas)
        self.modelo_version = (banco.huellas["expedicion/atributos_habitats.json"] + ":"
                               + banco.huellas["expedicion/pistas.json"])

    def _traza(self, contexto: dict, elegida: Candidata, regla: str, metodo: str,
               evaluaciones: list[dict], comienzo: int) -> dict:
        return {
            "politica": self.politica, "metodo": metodo, "regla": regla,
            "contexto": {"habitat_guia_id": contexto["habitat_guia_id"], "nivel": elegida.plantilla["nivel"],
                         "repeticion_previa": contexto["repeticion_previa"],
                         "cantidad_opciones": len(contexto["opciones"])},
            "variante_elegida": elegida.plantilla["variante_id"], "ayuda_elegida": elegida.id,
            "tipo_ayuda": elegida.tipo, "variante_anterior": None,
            "variantes_elegibles": [e["id"] for e in evaluaciones] or [elegida.id],
            "variantes_usadas_reto": list(contexto["mostradas"]),
            "candidatas": evaluaciones, "estimaciones": {},
            "nodo_id": f"{contexto['habitat_guia_id']}:{elegida.id}",
            "ayudas_por_rasgo_activas": len(self.rep.ayudas_activas),
            "modelo_estado": "REGLAS_Y_UTILIDAD_FIJAS" if self.politica == POLITICA_AGENTE else "ID3_SOBRE_OPCIONES",
            "modelo_version": self.modelo_version, "parametros_congelados": True,
            "tiempo_decision_ns": perf_counter_ns() - comienzo,
        }

    def _salida(self, contexto, elegida, regla, metodo, evaluaciones, comienzo):
        traza = self._traza(contexto, elegida, regla, metodo, evaluaciones, comienzo)
        return elegida.plantilla, traza["nodo_id"], traza

    def _editorial(self, g: str, mostradas: list[str]) -> Candidata | None:
        for c in self.rep.candidatas(g):
            if c.tipo == "PISTA" and c.id not in mostradas:
                return c
        return None


class MotorID3Opciones(_MotorReto):
    """Línea base: camino ID3 del hábitat guía entre las opciones visibles del reto."""
    politica = POLITICA_ID3

    def camino(self, g: str, opciones: list[str]) -> tuple[list[Candidata], list[dict]]:
        candidatas = self.rep.candidatas(g)
        filas = [{"clase": o, "atributos": {
                    c.id: ("descarta" if o != g and self.rep.relacion(c, o) == "conflicto" else "mantiene")
                    for c in candidatas}} for o in opciones]
        arbol = ArbolID3(filas, [c.id for c in candidatas])
        pasos = [p for p in arbol.ruta(filas[opciones.index(g)]["atributos"]) if p["ganancia"] > 1e-12]
        por_id = {c.id: c for c in candidatas}
        return [por_id[p["nombre"]] for p in pasos], pasos

    def decidir_reto(self, contexto: dict) -> tuple[dict, str, dict]:
        comienzo = perf_counter_ns()
        g, mostradas = contexto["habitat_guia_id"], contexto["mostradas"]
        camino, pasos = self.camino(g, list(contexto["opciones"]))
        evaluaciones = [{"id": c.id, "ganancia_bits": round(p["ganancia"], 6)} for c, p in zip(camino, pasos, strict=True)]
        for c in camino:
            if c.id not in mostradas:
                return self._salida(contexto, c, "CAMINO_ID3", "GANANCIA_DE_INFORMACION", evaluaciones, comienzo)
        siguiente = self._editorial(g, mostradas)
        if siguiente:
            return self._salida(contexto, siguiente, "SECUENCIA_TRAS_EL_ARBOL", "GANANCIA_DE_INFORMACION",
                                evaluaciones, comienzo)
        return self._salida(contexto, self.rep.senalar(g), "APOYO_EXPLICITO", "GANANCIA_DE_INFORMACION",
                            evaluaciones, comienzo)


class MotorAgente(_MotorReto):
    """Modelo principal: utilidad esperada de cada ayuda con el estado actual del reto."""
    politica = POLITICA_AGENTE

    def evaluar(self, c: Candidata, contexto: dict, restantes: list[str], distractores: list[str],
                validas: list[str], ultima: str | None, dificultad: bool,
                elegidas: list[str] = ()) -> dict:
        rel = {d: self.rep.relacion(c, d) for d in distractores}
        conflicto = sorted(d for d, r in rel.items() if r == "conflicto")
        propia = sorted(d for d, r in rel.items() if r == "propia")
        parcial = sorted(d for d, r in rel.items() if r == "parcial")
        aleja = sorted(t for t in validas if t != contexto["habitat_guia_id"]
                       and self.rep.relacion(c, t) == "conflicto")
        # Una ayuda que también describe (del todo o en parte) un hábitat ya elegido y no
        # confirmado parece señalarlo otra vez: confunde en lugar de ayudar a corregir.
        confunde = sorted(p for p in set(elegidas) if self.rep.relacion(c, p) in ("compartida", "parcial"))
        esperadas = len(conflicto) + PESO_PROPIA * len(propia) + PESO_PARCIAL * len(parcial)
        ganancia = log2(len(restantes) / max(len(restantes) - esperadas, 1.0)) if restantes else 0.0
        ideas = max(len(c.conceptos), 1)
        comprension = (COMPRENSION_CON_DIFICULTAD if dificultad else COMPRENSION_POR_IDEA) ** (ideas - 1)
        # La última elección ya no está entre las opciones que quedan: se compara aparte.
        con_ultima = self.rep.relacion(c, ultima) if ultima else None
        bono = {"conflicto": BONO_ULTIMA_ELECCION, "propia": BONO_ULTIMA_ELECCION / 2}.get(con_ultima, 0.0)
        utilidad = comprension * ganancia + bono - PENALIZACION_VALIDA * len(aleja)
        return {"id": c.id, "tipo": c.tipo, "ideas": ideas, "descarta_documentado": conflicto,
                "distingue_sin_comprobar": propia, "en_parte_compartida": parcial,
                "aleja_de_valida": aleja, "describe_eleccion_previa": confunde,
                "relacion_con_ultima_eleccion": con_ultima,
                "ganancia_bits": round(ganancia, 6), "comprension": round(comprension, 6),
                "bono_ultima_eleccion": bono, "utilidad": round(utilidad, 6),
                "informativa": bool(conflicto or propia or parcial) and not confunde}

    def decidir_reto(self, contexto: dict) -> tuple[dict, str, dict]:
        comienzo = perf_counter_ns()
        g = contexto["habitat_guia_id"]
        mostradas = list(contexto["mostradas"])
        confirmados = set(contexto["confirmados"])
        pendientes = [e["habitat_id"] for e in contexto["elecciones"] if e["resultado"] != "VALIDA"]
        restantes = [o for o in contexto["opciones"] if o not in pendientes]
        distractores = [o for o in restantes if o not in confirmados]
        validas = [o for o in restantes if o in confirmados]
        ultima = pendientes[-1] if pendientes and contexto["motivo"].startswith("SELECCION_") else None
        ya = [c for c in self.rep.candidatas(g) if c.id in mostradas]
        # Elegir una opción que una ayuda ya mostrada descartaba sugiere que no se entendió.
        no_entendida = bool(ultima and any(self.rep.relacion(c, ultima) == "conflicto" for c in ya))
        dificultad = bool(contexto["repeticion_previa"]) or no_entendida
        senalar = self.rep.senalar(g)

        def salida(c, regla, evaluaciones=()):
            _, nodo, traza = self._salida(contexto, c, regla, "UTILIDAD_ESPERADA", list(evaluaciones), comienzo)
            traza["estado_reto"] = {"restantes": restantes, "distractores": distractores, "validas": validas,
                                    "ultima_eleccion": ultima, "elecciones_pendientes": len(pendientes),
                                    "ayuda_no_entendida": no_entendida, "dificultad": dificultad}
            return c.plantilla, nodo, traza

        if senalar.id in mostradas:
            return salida(senalar, "MANTENER_APOYO_EXPLICITO")
        if len(set(pendientes)) >= ELECCIONES_ANTES_DE_SENALAR:
            return salida(senalar, "APOYO_EXPLICITO_TRAS_VARIAS_ELECCIONES")
        if len(mostradas) >= MAX_PISTAS_ANTES_DE_SENALAR:
            return salida(senalar, "APOYO_EXPLICITO_TRAS_VARIAS_PISTAS")
        nuevas = [c for c in self.rep.candidatas(g) if c.id not in mostradas]
        evaluaciones = [self.evaluar(c, contexto, restantes, distractores, validas, ultima, dificultad,
                                     pendientes) for c in nuevas]
        if not distractores:
            # Todo lo que queda es válido. Sin elecciones previas se sigue la secuencia editorial;
            # tras una elección, solo vale una ayuda que no describa lo elegido, y mejor si lo distingue.
            orden_rel = {"conflicto": 0, "propia": 1}
            aptas = [(c, e) for c, e in zip(nuevas, evaluaciones, strict=True)
                     if not e["describe_eleccion_previa"] and (c.tipo == "PISTA" or ultima)]
            if aptas:
                c, e = min(aptas, key=lambda par: (
                    bool(par[1]["aleja_de_valida"]),
                    orden_rel.get(self.rep.relacion(par[0], ultima), 2) if ultima else 0,
                    par[0].plantilla["nivel"], par[1]["ideas"], par[0].id))
                regla = ("DISTINGUE_LA_ULTIMA_ELECCION"
                         if ultima and self.rep.relacion(c, ultima) == "conflicto"
                         else "SECUENCIA_SIN_OPCIONES_QUE_DESCARTAR")
                return salida(c, regla, evaluaciones)
            return salida(senalar, "SIN_AYUDA_QUE_DISTINGA" if ultima else "APOYO_EXPLICITO", evaluaciones)
        utiles = [(c, e) for c, e in zip(nuevas, evaluaciones, strict=True)
                  if e["informativa"] and e["utilidad"] > 0]
        if not utiles:
            if not pendientes:
                # Sin errores previos no se revela la respuesta en la primera petición: se sigue
                # la secuencia editorial (de menos a más apoyo).
                siguiente = self._editorial(g, mostradas)
                if siguiente:
                    return salida(siguiente, "SECUENCIA_SIN_AYUDA_QUE_DISTINGA", evaluaciones)
            return salida(senalar, "SIN_AYUDA_QUE_DISTINGA", evaluaciones)
        orden_tipo = {"RASGO": 0, "PISTA": 1}
        c, e = max(utiles, key=lambda par: (par[1]["utilidad"], -par[1]["ideas"],
                                            -orden_tipo[par[0].tipo], -par[0].plantilla["nivel"]))
        regla = ("DISTINGUE_LA_ULTIMA_ELECCION" if e["relacion_con_ultima_eleccion"] == "conflicto"
                 else "MAYOR_UTILIDAD_ESPERADA")
        return salida(c, regla, evaluaciones)


MOTORES_6 = {POLITICA_AGENTE: MotorAgente, POLITICA_ID3: MotorID3Opciones}
