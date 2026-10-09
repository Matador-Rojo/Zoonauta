"""Estado formal y contratos compartidos entre consola y futura interfaz."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


TERMINALES = {"COMPLETADA", "ABANDONADA"}
PAUSABLES = {"SELECCION_ANIMAL", "PRESENTACION", "ESPERANDO_RESPUESTA", "RETO_RESUELTO"}


@dataclass(frozen=True)
class Respuesta:
    contenido_id: str
    tipo_respuesta: str
    pictogramas: tuple[str, ...]
    texto_apoyo: str
    texto_voz: str
    nivel: int | None = None
    variante_id: str | None = None


@dataclass(frozen=True)
class Evento:
    tipo: str
    evento_id: str
    sesion_id: str
    reto_id: str | None
    payload: dict[str, Any] = field(default_factory=dict)
    interno: bool = False


@dataclass
class Estado:
    modalidad: str | None = None
    fase: str = "INICIO"
    animal_id: str | None = None
    habitat_guia_id: str | None = None
    nivel: int = 0
    habitat_seleccionado_id: str | None = None
    resultado: str = "SIN_RESPUESTA"
    completados: int = 0
    fase_previa: str | None = None
    u: str | None = None
    nodo_id: str | None = None
    repeticion_previa: int = 0
    observacion: dict | None = None
    variantes_anteriores: dict[str, str] = field(default_factory=dict)
    respuesta_educativa: Respuesta | None = None
    reto_id: str | None = None
    numero_reto: int = 0

    def serializar(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Salida:
    aceptada: bool
    motivo: str
    respuesta: Respuesta | None
    controles_disponibles: tuple[str, ...]
    traza: dict | None = None

