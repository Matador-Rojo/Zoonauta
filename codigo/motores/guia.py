"""Ruta ID3 y elección de variantes con parámetros congelados."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from pathlib import Path
import hashlib
import json
from time import perf_counter_ns

from codigo.nucleo.datos import BancoDatos, ErrorDatos
from codigo.motores.id3 import ArbolID3


POLITICAS = ("ID3", "ROTACION", "PROBABILISTICO")


@dataclass(frozen=True)
class BetaFija:
    alpha: float
    beta: float

    @property
    def media(self) -> float:
        return self.alpha / (self.alpha + self.beta)


class MotorGuia:
    def __init__(self, banco: BancoDatos, politica: str = "ID3", parametros: Path | str | None = None):
        if politica not in POLITICAS:
            raise ValueError(f"Política no reconocida: {politica}.")
        self.banco = banco
        self.politica = politica
        self.arbol = ArbolID3(banco.perfiles_documento["items"],
                              banco.perfiles_documento["orden_desempate"])
        self.rutas = {h: self.arbol.ruta(p["atributos"]) for h, p in banco.perfiles.items()}
        for h, pasos in self.rutas.items():
            if len(pasos) != 2 or self.arbol.predecir(banco.perfiles[h]["atributos"]) != h:
                raise ErrorDatos("El banco de ayudas requiere rutas de dos atributos y hojas puras.")
        if parametros is None:
            documento = banco.leer("parametros_iniciales.json")
            self.modelo_version = banco.huellas["parametros_iniciales.json"]
        else:
            contenido = Path(parametros).read_bytes()
            documento = json.loads(contenido.decode("utf-8"))
            if documento.get("schema_version") != "1.0.0":
                raise ErrorDatos("Versión no compatible del modelo aprendido.")
            self.modelo_version = hashlib.sha256(contenido).hexdigest()
        self.modelo_estado = documento["estado_modelo"]
        self.parametros_congelados = True
        valores = {}
        for fila in documento["items"]:
            z = fila["contexto"]
            clave = (z["habitat_guia_id"], z["nivel"], z["repeticion_previa"], fila["variante_id"])
            alpha, beta = fila["alpha"], fila["beta"]
            if clave in valores or not all(isfinite(v) and v > 0 for v in (alpha, beta)):
                raise ErrorDatos("Parámetros bayesianos duplicados o inválidos.")
            valores[clave] = BetaFija(alpha, beta)
        esperadas = {(h, l, b, v) for h in banco.habitats for l in (1, 2, 3)
                     for b in (0, 1) for v in ("V1", "V2", "V3")}
        if set(valores) != esperadas:
            raise ErrorDatos("Faltan contextos o variantes en los parámetros.")
        self.parametros = MappingProxyType(valores)
        self._validar_ayudas()

    def _validar_ayudas(self) -> None:
        for h, ruta in self.rutas.items():
            for nivel in (1, 2, 3):
                disponibles = self.disponibles(h, nivel)
                if "V1" not in disponibles:
                    raise ErrorDatos(f"Falta la pista base V1 para {h}, nivel {nivel}.")
                for ayuda in disponibles.values():
                    esperado = ({k: ruta[nivel - 1][k] for k in ("nombre", "valor")}
                                if nivel < 3 else None)
                    if ayuda["atributo_guia"] != esperado:
                        raise ErrorDatos(f"La ayuda {ayuda['id']} no coincide con la ruta ID3.")

    def disponibles(self, habitat_id: str, nivel: int) -> dict[str, dict]:
        return {r["variante_id"]: r for r in self.banco.variantes.values()
                if r["habitat_guia_id"] == habitat_id and r["nivel"] == nivel
                and r["habilitada_poc_texto"]}

    def decidir(self, habitat_id: str, nivel: int, repeticion: int,
                anteriores: dict[str, str], *, usadas: list[str] | None = None) -> tuple[dict, str, dict]:
        comienzo = perf_counter_ns()
        disponibles = self.disponibles(habitat_id, nivel)
        orden = sorted(disponibles)
        anterior = anteriores.get(f"{habitat_id}:{nivel}")
        elegibles = ([v for v in orden if v != anterior]
                     if len(orden) > 1 and anterior in orden and self.politica != "ID3"
                     else orden)
        no_vistas = [v for v in elegibles if v not in (usadas or [])]
        if self.politica == "PROBABILISTICO" and no_vistas:
            elegibles = no_vistas
        probabilidades = {v: self.parametros[(habitat_id, nivel, repeticion, v)].media
                          for v in elegibles}
        if self.politica == "ID3":
            elegibles = ["V1"]
            probabilidades = {"V1": self.parametros[(habitat_id, nivel, repeticion, "V1")].media}
        elegida, detalle = self._seleccionar(habitat_id, nivel, repeticion, orden,
                                            elegibles, anterior, probabilidades)
        ruta = self.rutas[habitat_id]
        nodo_id = ruta[min(nivel, 2) - 1]["hacia"]
        traza = {"politica": self.politica,
                 "contexto": {"habitat_guia_id": habitat_id, "nivel": nivel,
                              "repeticion_previa": repeticion},
                 "variante_elegida": elegida, "variante_anterior": anterior,
                 "variantes_usadas_reto": list(usadas or []),
                 "variantes_elegibles": elegibles, "estimaciones": probabilidades,
                 "exclusion_por_variedad": anterior if anterior in orden and anterior not in elegibles
                                          and self.politica != "ID3" else None,
                 "atributo_guia": disponibles[elegida]["atributo_guia"],
                 "nodo_id": nodo_id, "K": list(self.arbol.nodos[nodo_id].clases),
                 "modelo_estado": self.modelo_estado, "modelo_version": self.modelo_version,
                 "parametros_congelados": self.parametros_congelados, **detalle}
        traza["tiempo_decision_ns"] = perf_counter_ns() - comienzo
        return disponibles[elegida], nodo_id, traza

    def _seleccionar(self, habitat_id, nivel, repeticion, orden, elegibles, anterior, probabilidades):
        if self.politica == "ID3":
            return "V1", {"metodo": "PRESENTACION_FIJA"}
        if self.politica == "ROTACION":
            inicio = (orden.index(anterior) + 1) % len(orden) if anterior in orden else 0
            ciclo = orden[inicio:] + orden[:inicio]
            return next(v for v in ciclo if v in elegibles), {"metodo": "ROTACION"}
        return min(elegibles, key=lambda v: (-probabilidades[v], v)), {"metodo": "MEDIA_POSTERIOR"}

