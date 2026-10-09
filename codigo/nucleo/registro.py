"""Eventos y observaciones separados de los parámetros congelados."""
from __future__ import annotations

import copy
import json
from pathlib import Path


class Registro:
    def __init__(self, destino: Path | str | None = None):
        self.destino = Path(destino) if destino is not None else None
        self.filas: list[dict] = []
        if self.destino:
            self.destino.parent.mkdir(parents=True, exist_ok=True)

    def agregar(self, fila: dict) -> None:
        fila = copy.deepcopy(fila)
        self.filas.append(fila)
        if self.destino:
            with self.destino.open("a", encoding="utf-8") as archivo:
                archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")

