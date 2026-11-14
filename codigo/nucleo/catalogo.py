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
    rasgos, ayudas_rasgo = cargar_rasgos(banco, habitats, variantes, pictogramas)
    banco.habitats, banco.animales = habitats, animales
    banco.rasgos_habitat, banco.ayudas_rasgo = rasgos, ayudas_rasgo
    banco.pictogramas, banco.variantes, banco.pistas_progresivas = pictogramas, variantes, pistas
    banco.asociaciones, banco.opciones_ordenadas = asociaciones, ordenes
    banco.escenarios = banco.escenario_por_animal = escenarios
    banco.mensajes = banco._indice("mensajes_sistema.json")
    banco.configuracion = {"retos_por_partida": 8, "orden_demo_agente": list(escenarios),
                           "orden_animales": list(animales), "orden_habitats": list(habitats)}


def cargar_rasgos(banco: BancoDatos, habitats: dict, variantes: dict,
                  pictogramas: dict) -> tuple[dict, dict]:
    """Rasgos documentados de cada hábitat y ayudas breves por rasgo (agente 6.0).

    Cada valor cita la pista revisada del mismo hábitat que lo dice; un hábitat sin valor
    en un atributo es desconocido (nunca se interpreta como «no»).
    Devuelve ``{hábitat: {atributo: (valor, pista)}}`` y ``{ayuda_id: ayuda}``.
    """
    documento = banco.leer("expedicion/atributos_habitats.json")
    rasgos: dict[str, dict[str, tuple[str, str]]] = {h: {} for h in habitats}
    ayudas: dict[str, dict] = {}
    textos: set[str] = set()
    for atributo in documento["atributos"]:
        nombre = atributo["id"]
        if len({v["id"] for v in atributo["valores"]}) != len(atributo["valores"]) or len(atributo["valores"]) < 2:
            raise ErrorDatos(f"El atributo {nombre} necesita al menos dos valores distintos.")
        for valor in atributo["valores"]:
            ayuda = valor["ayuda"]
            if ayuda["id"] in ayudas or ayuda["texto"] in textos or not ayuda["texto_pt"]:
                raise ErrorDatos(f"Ayuda por rasgo duplicada o sin traducción: {ayuda['id']}.")
            if not 1 <= len(ayuda["pictogramas"]) <= 3 or any(
                    t["tipo"] != "PICTOGRAMA" or t["id"] not in pictogramas for t in ayuda["pictogramas"]):
                raise ErrorDatos(f"Pictogramas no válidos en {ayuda['id']}.")
            textos.add(ayuda["texto"])
            ayudas[ayuda["id"]] = {**ayuda, "atributo": nombre, "valor": valor["id"]}
            for h, pista_id in valor["habitats"].items():
                pista = variantes.get(pista_id)
                if h not in habitats or not pista or pista["habitat_guia_id"] != h or pista["nivel"] not in (1, 2):
                    raise ErrorDatos(f"La evidencia {pista_id} no es una pista 1 o 2 de {h}.")
                if nombre in rasgos[h]:
                    raise ErrorDatos(f"{h} tiene dos valores para {nombre}.")
                rasgos[h][nombre] = (valor["id"], pista_id)
    return rasgos, ayudas


def validar_opciones(referencia: str, opciones: list[str], habitats: dict) -> None:
    if len(opciones) != len(set(opciones)) or not set(opciones) <= habitats.keys():
        raise ErrorDatos(f"Hábitats duplicados o desconocidos para {referencia}.")
    if referencia in habitats and (len(opciones) < 7 or referencia in opciones):
        raise ErrorDatos(f"Faltan contrastes para {referencia} o incluye su propio hábitat.")
