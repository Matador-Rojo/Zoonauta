"""Banco de la expedición de 48 hábitats, independiente del banco experimental."""
from __future__ import annotations

from collections import Counter

from codigo.nucleo.datos import BancoDatos, ErrorDatos


def cargar_catalogo(banco: BancoDatos) -> None:
    habitats = banco._indice("expedicion/habitats.json")
    animales = banco._indice("expedicion/animales.json")
    fichas = banco._indice("expedicion/pictogramas.json")
    variantes = banco._indice("expedicion/pistas.json")
    controles = banco._indice("pictogramas.json")
    pictogramas = {i: p for i, p in controles.items() if p["tipo"] not in {"ANIMAL", "HABITAT"}}
    pictogramas.update(fichas)
    if len(habitats) != 48 or len(animales) != 288 or len(fichas) != 402:
        raise ErrorDatos("El catálogo ampliado requiere 48 hábitats, 288 animales y 402 pictogramas propios.")
    referencias = Counter(a["habitat_referencia_id"] for a in animales.values())
    if set(referencias) != set(habitats) or set(referencias.values()) != {6}:
        raise ErrorDatos("Cada hábitat debe tener seis animales de referencia.")
    for h in habitats.values():
        validar_opciones(h["id"], h["afines"], habitats)
    asociaciones, ordenes, escenarios = {}, {}, {}
    for a in animales.values():
        animal = a["id"]
        principal = a["habitat_referencia_id"]
        secundarios = a["secundarios"]
        confirmados = [principal, *secundarios]
        validar_opciones(animal, [*confirmados, *a["contrastes_preferentes"]], habitats)
        if len(confirmados) > 8 or any(not ficha["fuentes"] for ficha in secundarios.values()):
            raise ErrorDatos(f"Hay demasiadas asociaciones válidas o falta su fuente en {animal}.")
        a["habitats_confirmados"] = confirmados
        ordenes[animal] = tuple(dict.fromkeys([
            *confirmados, *a["contrastes_preferentes"], *habitats[principal]["afines"]]))
        escenarios[animal] = {"id": animal, "animal_id": animal, "habitat_guia_id": principal}
        for h in habitats:
            asociaciones[animal, h] = {
                "estado": "VALIDA" if h in confirmados else "PENDIENTE",
                "contexto": secundarios.get(h, {}).get("contexto"),
            }
    for ficha in (*animales.values(), *habitats.values()):
        if ficha["pictograma_id"] not in pictogramas:
            raise ErrorDatos(f"Falta el pictograma de {ficha['id']}.")
    pistas = {(p["habitat_guia_id"], p["nivel"]): p for p in variantes.values()}
    if len(variantes) != 144 or pistas.keys() != {(h, nivel) for h in habitats for nivel in (1, 2, 3)}:
        raise ErrorDatos("Cada hábitat necesita tres pistas progresivas.")
    for pista in pistas.values():
        if not all(token["id"] in pictogramas for token in pista["pictogramas"]):
            raise ErrorDatos(f"Hay pictogramas desconocidos en {pista['id']}.")
    banco.habitats, banco.animales = habitats, animales
    banco.pictogramas, banco.variantes, banco.pistas_progresivas = pictogramas, variantes, pistas
    banco.asociaciones, banco.opciones_ordenadas = asociaciones, ordenes
    banco.escenarios = banco.escenario_por_animal = escenarios
    banco.mensajes = banco._indice("mensajes_sistema.json")
    banco.configuracion = {"retos_por_partida": 8, "orden_demo_agente": list(escenarios),
                           "orden_animales": list(animales), "orden_habitats": list(habitats)}


def validar_opciones(referencia: str, opciones: list[str], habitats: dict) -> None:
    if len(opciones) != len(set(opciones)) or not set(opciones) <= habitats.keys():
        raise ErrorDatos(f"Hábitats duplicados o desconocidos para {referencia}.")
    if referencia in habitats and (len(opciones) < 7 or referencia in opciones):
        raise ErrorDatos(f"Faltan contrastes para {referencia} o incluye su propio hábitat.")
