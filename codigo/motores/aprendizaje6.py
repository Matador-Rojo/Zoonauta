"""Agente 6.0 con un modelo aprendido fuera de la partida (sistema experto probabilístico).

Qué aprende: para cada *tipo* de ayuda, la probabilidad de que la siguiente acción del
jugador sea elegir un hábitat confirmado. El tipo es la clave de
``codigo.motores.agente.clave_aprendizaje``: pista revisada o ayuda por rasgo, una o varias
ideas, 2/4/8 opciones, señal de dificultad y si la ayuda distingue lo visible de forma
documentada, sin comprobar o nada. Cada tipo tiene una distribución Beta(α, β) que empieza
en Beta(1, 1) y se actualiza con resultados 1/0 (Beta-Bernoulli).

Recompensa (decidida el 2026-11-14): 1 si tras la ayuda se elige un hábitat confirmado;
0 si se pide otra pista o se elige un hábitat no confirmado («no llevó a una respuesta
confirmada»; no dice que ese hábitat sea incorrecto); sin dato si se sale.

Qué no cambia: el modelo solo elige entre las ayudas que el agente ya considera seguras e
informativas. Las reglas fijas (solo frases verdaderas del hábitat guía, solo con
grabación, la primera Pista nunca revela, nunca describir lo ya elegido, no alejar de otra
respuesta válida visible si hay alternativa, apoyo explícito tras dos elecciones o tres
pistas) quedan fuera del aprendizaje.

Al jugar, el modelo está congelado (media posterior): no aprende durante la partida. Solo
se entrena con ``codigo.entrenamiento.entrenar_agente6`` a partir de registros de partidas.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
from random import Random

from codigo.motores.agente import MotorAgente, clave_aprendizaje
from codigo.nucleo.datos import BancoDatos, ErrorDatos

POLITICA_APRENDIDA = "AGENTE_APRENDIDO"
ESQUEMA = "zoonauta-agente6-modelo/1"
CLAVES = tuple(clave_aprendizaje(t, i, k, d, inf)
               for t, i, k, d, inf in itertools.product(("PISTA", "RASGO"), (1, 2), (2, 4, 8), (False, True),
                                                       ("documentado", "sin_comprobar", "ninguno")))
RAIZ = Path(__file__).resolve().parents[2]
# Modelo de demostración: primera réplica de la condición IDEAS, entrenada con jugadores
# SIMULADOS (no personas); elegida por orden, no por sus resultados.
MODELO_DEMO = RAIZ / "docs/experimentos/agente6/aprendizaje/modelos/IDEAS_R01.json"


def huellas_requeridas(banco: BancoDatos) -> dict[str, str]:
    return {"atributos": banco.huellas["expedicion/atributos_habitats.json"],
            "pistas": banco.huellas["expedicion/pistas.json"]}


class ModeloAyudas:
    """Una Beta(α, β) por tipo de ayuda; se actualiza solo durante el entrenamiento."""

    def __init__(self, documento: dict):
        if documento.get("esquema") != ESQUEMA:
            raise ErrorDatos("Modelo del agente 6.0 con un esquema desconocido.")
        parametros = documento["parametros"]
        if set(parametros) != set(CLAVES):
            raise ErrorDatos("El modelo no contiene exactamente los tipos de ayuda esperados.")
        for clave, p in parametros.items():
            if not (p["alpha"] > 0 and p["beta"] > 0 and p["n"] >= 0):
                raise ErrorDatos(f"Parámetros no válidos para {clave}.")
        self.origen = documento["origen"]
        self.huellas = dict(documento["huellas"])
        self.metadatos = dict(documento.get("metadatos", {}))
        self.parametros = {c: dict(p) for c, p in parametros.items()}
        self.actualizaciones = sum(p["n"] for p in self.parametros.values())

    @classmethod
    def nuevo(cls, banco: BancoDatos, origen: str, metadatos: dict | None = None) -> "ModeloAyudas":
        return cls({"esquema": ESQUEMA, "origen": origen, "huellas": huellas_requeridas(banco),
                    "metadatos": metadatos or {},
                    "parametros": {c: {"alpha": 1.0, "beta": 1.0, "n": 0} for c in CLAVES}})

    @classmethod
    def cargar(cls, ruta: Path | str) -> "ModeloAyudas":
        return cls(json.loads(Path(ruta).read_text(encoding="utf-8")))

    def media(self, clave: str) -> float:
        p = self.parametros[clave]
        return p["alpha"] / (p["alpha"] + p["beta"])

    def muestra(self, clave: str, azar: Random) -> float:
        p = self.parametros[clave]
        return azar.betavariate(p["alpha"], p["beta"])

    def actualizar(self, clave: str, resultado: int) -> None:
        if resultado not in (0, 1):
            raise ValueError("El resultado debe ser 0 o 1.")
        p = self.parametros[clave]
        p["alpha" if resultado else "beta"] += 1
        p["n"] += 1
        self.actualizaciones += 1

    def documento(self) -> dict:
        return {"esquema": ESQUEMA, "origen": self.origen, "huellas": self.huellas,
                "metadatos": self.metadatos, "actualizaciones": self.actualizaciones,
                "parametros": self.parametros}

    def guardar(self, ruta: Path | str) -> None:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(self.documento(), ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8", newline="\n")

    def huella(self) -> str:
        texto = json.dumps(self.documento(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class MotorAgenteAprendido(MotorAgente):
    """El agente 6.0 que elige, entre las ayudas seguras, la de mayor probabilidad aprendida.

    Con ``azar`` (solo en entrenamiento) muestrea de cada Beta (Thompson sampling) para
    explorar; sin ``azar`` usa la media posterior y el modelo queda congelado.
    """
    politica = POLITICA_APRENDIDA

    def __init__(self, banco: BancoDatos, modelo: ModeloAyudas | Path | str | None = None, *,
                 azar: Random | None = None, solo_grabadas: bool = True,
                 ayudas_activas: set[str] | None = None):
        super().__init__(banco, solo_grabadas=solo_grabadas, ayudas_activas=ayudas_activas)
        modelo = ModeloAyudas.cargar(MODELO_DEMO if modelo is None else modelo) \
            if not isinstance(modelo, ModeloAyudas) else modelo
        if modelo.huellas != huellas_requeridas(banco):
            raise ErrorDatos("El modelo se entrenó con otros rasgos o pistas: vuelve a entrenarlo.")
        self.modelo = modelo
        self.azar = azar
        self.metodo = "THOMPSON_ENTRENAMIENTO" if azar else "MEDIA_POSTERIOR_CONGELADA"
        self.parametros_congelados = azar is None
        self.modelo_version = f"{self.modelo_version}:{modelo.huella()[:16]}"

    def _elegir(self, utiles):
        def valor(par):
            clave = par[1]["clave_aprendizaje"]
            return self.modelo.muestra(clave, self.azar) if self.azar else self.modelo.media(clave)
        # Regla fija antes de lo aprendido: si hay alguna ayuda que no aleja de otra respuesta
        # válida visible (p. ej. el bosque templado del jaguar), solo se elige entre esas.
        utiles = [par for par in utiles if not par[1]["aleja_de_valida"]] or utiles
        valores = {par[0].id: valor(par) for par in utiles}
        for _, e in utiles:
            e["probabilidad_aprendida"] = round(self.modelo.media(e["clave_aprendizaje"]), 6)
            e["valor_decision"] = round(valores[e["id"]], 6)
        orden_tipo = {"RASGO": 0, "PISTA": 1}
        c, e = max(utiles, key=lambda par: (valores[par[0].id], par[1]["utilidad"], -par[1]["ideas"],
                                            -orden_tipo[par[0].tipo], -par[0].plantilla["nivel"]))
        return c, e, "MAYOR_PROBABILIDAD_APRENDIDA"

    def decidir_reto(self, contexto: dict):
        plantilla, nodo, traza = super().decidir_reto(contexto)
        traza["modelo_estado"] = "ENTRENAMIENTO" if self.azar else "APRENDIDO_CONGELADO"
        traza["modelo_origen"] = self.modelo.origen
        traza["parametros_congelados"] = self.azar is None
        return plantilla, nodo, traza
