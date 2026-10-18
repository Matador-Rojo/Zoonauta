"""Aprendizaje externo Beta–Bernoulli, con actualizaciones únicas y procedencia."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from types import MappingProxyType

from codigo.motores.guia import BetaFija, MotorGuia
from codigo.nucleo.datos import BancoDatos


class ModeloBayes:
    def __init__(self, documento: dict, identificador: str = "APRENDIZAJE_SINTETICO"):
        self.identificador = identificador
        self.valores: dict[tuple, BetaFija] = {}
        self.conteos: dict[tuple, list[int]] = {}
        self.vistos: dict[str, tuple] = {}
        self.actualizaciones = 0
        self.sin_etiqueta = 0
        for r in documento["items"]:
            z = r["contexto"]
            clave = (z["habitat_guia_id"], z["nivel"], z["repeticion_previa"], r["variante_id"])
            if r["alpha"] != 1 or r["beta"] != 1 or clave in self.valores:
                raise ValueError("Esta fase de entrenamiento comienza con priors únicos Beta(1,1).")
            self.valores[clave] = BetaFija(1, 1)
            self.conteos[clave] = [0, 0]

    def actualizar(self, observacion: dict) -> bool:
        if observacion["origen"] != "SIMULACION_ENTRENAMIENTO":
            raise ValueError("Este aprendiz solo admite resultados sintéticos de entrenamiento.")
        z = observacion["contexto"]
        clave = (z["habitat_guia_id"], z["nivel"], z["repeticion_previa"], observacion["variante_id"])
        if clave not in self.valores:
            raise ValueError("Contexto o variante desconocidos.")
        y = observacion["resultado"]
        if y is not None and (type(y) is not int or y not in (0, 1)):
            raise ValueError("Una etiqueta debe ser 0, 1 o null.")
        id = observacion["observacion_id"]
        firma = (clave, y)
        if id in self.vistos:
            if self.vistos[id] != firma:
                raise ValueError("No se puede cambiar retrospectivamente una observación cerrada.")
            return False
        self.vistos[id] = firma
        if y is None:
            self.sin_etiqueta += 1
            return False
        beta = self.valores[clave]
        self.valores[clave] = BetaFija(beta.alpha + y, beta.beta + (1 - y))
        self.conteos[clave][y] += 1
        self.actualizaciones += 1
        return True

    def documento(self, metadata: dict | None = None) -> dict:
        items = []
        for (h, l, b, v), valor in sorted(self.valores.items()):
            c0, c1 = self.conteos[(h, l, b, v)]
            items.append({"contexto": {"habitat_guia_id": h, "nivel": l, "repeticion_previa": b},
                          "variante_id": v, "alpha": valor.alpha, "beta": valor.beta,
                          "resultados_0": c0, "resultados_1": c1,
                          "observaciones_etiquetadas": c0 + c1})
        return {"schema_version": "1.0.0", "estado_modelo": "ENTRENADO_CON_INTERACCIONES_SINTETICAS",
                "origen": "SIMULACION_ENTRENAMIENTO", "identificador": self.identificador,
                "modo_evaluacion": "PARAMETROS_CONGELADOS", "items": items,
                "actualizaciones": self.actualizaciones, "cierres_sin_etiqueta": self.sin_etiqueta,
                "metadata": metadata or {}}

    def guardar(self, ruta: Path, metadata: dict | None = None) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(self.documento(metadata), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    def huella(self) -> str:
        contenido = [(clave, v.alpha, v.beta) for clave, v in sorted(self.valores.items())]
        return hashlib.sha256(json.dumps(contenido).encode()).hexdigest()


class MotorThompson(MotorGuia):
    def __init__(self, banco: BancoDatos, modelo: ModeloBayes, semilla: int):
        super().__init__(banco, "PROBABILISTICO")
        if set(modelo.valores) != set(self.parametros):
            raise ValueError("El modelo de aprendizaje no tiene los mismos contextos.")
        self.modelo = modelo
        self.parametros = MappingProxyType(modelo.valores)
        self.rng = random.Random(semilla)
        self.modelo_estado = "EXPLORACION_SINTETICA_THOMPSON"
        self.parametros_congelados = False

    def _seleccionar(self, habitat_id, nivel, repeticion, orden, elegibles, anterior, probabilidades):
        muestras = {}
        for v in elegibles:
            beta = self.parametros[(habitat_id, nivel, repeticion, v)]
            muestras[v] = self.rng.betavariate(beta.alpha, beta.beta)
        self.modelo_version = f"{self.modelo.identificador}-U{self.modelo.actualizaciones}"
        elegida = min(elegibles, key=lambda v: (-muestras[v], v))
        return elegida, {"metodo": "THOMPSON_SAMPLING", "muestras_beta": muestras}

