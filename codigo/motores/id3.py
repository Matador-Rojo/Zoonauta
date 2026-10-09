"""ID3 categórico construido mediante entropía y ganancia; no rutas manuales."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from math import log2


def entropia(filas: list[dict]) -> float:
    pesos: Counter = Counter()
    for fila in filas:
        pesos[fila["clase"]] += fila.get("peso", 1)
    total = sum(pesos.values())
    if total <= 0:
        raise ValueError("ID3 requiere ejemplos con peso positivo.")
    return -sum((p / total) * log2(p / total) for p in pesos.values() if p > 0)


def grupos(filas: list[dict], atributo: str) -> dict[str, list[dict]]:
    resultado: dict[str, list[dict]] = {}
    for fila in filas:
        resultado.setdefault(fila["atributos"][atributo], []).append(fila)
    return resultado


def ganancia(filas: list[dict], atributo: str) -> float:
    total = sum(r.get("peso", 1) for r in filas)
    residual = sum(sum(r.get("peso", 1) for r in sub) / total * entropia(sub)
                   for sub in grupos(filas, atributo).values())
    return entropia(filas) - residual


@dataclass
class Nodo:
    id: str
    clases: tuple[str, ...]
    entropia: float
    atributo: str | None = None
    clase: str | None = None
    ganancias: dict[str, float] = field(default_factory=dict)
    hijos: dict[str, "Nodo"] = field(default_factory=dict)


class ArbolID3:
    def __init__(self, filas: list[dict], orden_atributos: list[str]):
        if not filas or any(r.get("peso", 1) <= 0 for r in filas):
            raise ValueError("Los perfiles de ID3 deben tener pesos positivos.")
        if not orden_atributos or len(set(orden_atributos)) != len(orden_atributos):
            raise ValueError("El orden de atributos debe ser único y no vacío.")
        if any(set(r["atributos"]) != set(orden_atributos) for r in filas):
            raise ValueError("Los atributos de los perfiles son inconsistentes.")
        self.nodos: dict[str, Nodo] = {}
        self.raiz = self._construir(filas, list(orden_atributos))

    def _construir(self, filas: list[dict], atributos: list[str]) -> Nodo:
        clases = tuple(sorted({r["clase"] for r in filas}))
        nodo = Nodo(f"N{len(self.nodos):02d}", clases, entropia(filas))
        self.nodos[nodo.id] = nodo
        if len(clases) == 1:
            nodo.clase = clases[0]
            return nodo
        if not atributos:
            conteos: Counter = Counter()
            for fila in filas:
                conteos[fila["clase"]] += fila.get("peso", 1)
            nodo.clase = min(clases, key=lambda c: (-conteos[c], c))
            return nodo
        nodo.ganancias = {a: ganancia(filas, a) for a in atributos}
        # Una tolerancia evita que diferencias de redondeo rompan el empate fijo.
        mejor = atributos[0]
        for atributo in atributos[1:]:
            if nodo.ganancias[atributo] > nodo.ganancias[mejor] + 1e-12:
                mejor = atributo
        nodo.atributo = mejor
        restantes = [a for a in atributos if a != mejor]
        for valor, subconjunto in sorted(grupos(filas, mejor).items()):
            nodo.hijos[valor] = self._construir(subconjunto, restantes)
        return nodo

    def ruta(self, perfil: dict[str, str]) -> list[dict]:
        nodo = self.raiz
        pasos = []
        while nodo.atributo is not None:
            valor = perfil[nodo.atributo]
            if valor not in nodo.hijos:
                raise ValueError(f"Valor no conocido para {nodo.atributo}: {valor}.")
            hijo = nodo.hijos[valor]
            pasos.append({"nombre": nodo.atributo, "valor": valor,
                          "desde": nodo.id, "hacia": hijo.id,
                          "ganancia": nodo.ganancias[nodo.atributo]})
            nodo = hijo
        return pasos

    def predecir(self, perfil: dict[str, str]) -> str:
        ruta = self.ruta(perfil)
        nodo = self.nodos[ruta[-1]["hacia"]] if ruta else self.raiz
        return nodo.clase

    def serializar(self) -> dict:
        return {"algoritmo": "ID3", "origen": "OCHO_PERFILES_DIDACTICOS",
                "entropia_inicial": self.raiz.entropia,
                "ganancias_raiz": self.raiz.ganancias,
                "arbol": asdict(self.raiz)}

