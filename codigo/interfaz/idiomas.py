"""Traducción de presentación; conserva los identificadores y datos del agente."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json

from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO

IDIOMAS = {"es", "pt-BR", "en"}
PORTUGUES = json.loads((RAIZ_PROYECTO / "datos/traducciones_pt_BR.json").read_text(encoding="utf-8"))
INGLES = json.loads((RAIZ_PROYECTO / "datos/traducciones_en.json").read_text(encoding="utf-8"))
FRASES_PT = sorted(PORTUGUES["textos"], key=len, reverse=True)
FRASES_EN = sorted(INGLES["textos"], key=len, reverse=True)
FRASES_EN_AMPLIADO = sorted(INGLES["textos_ampliado"], key=len, reverse=True)
# Alias conservado por compatibilidad con utilidades externas.
FRASES = FRASES_PT


@lru_cache(maxsize=8)
def _textos_catalogo(banco: BancoDatos, idioma: str = "pt-BR") -> tuple[dict, list[str]]:
    if idioma == "en":
        return INGLES["textos_ampliado"], FRASES_EN_AMPLIADO
    textos = dict(PORTUGUES["textos"])
    for habitat in banco.habitats.values():
        textos[f"¡Sí! Este animal puede vivir {habitat['frase_locativa']}."] = (
            f"Sim! Este animal pode viver {habitat['frase_locativa_pt']}.")
    for pista in banco.variantes.values():
        textos[pista["texto"]] = pista["texto_pt"]
    # Ayudas breves por rasgo del agente 6.0 (traducción pendiente de revisión humana).
    for ayuda in banco.ayudas_rasgo.values():
        textos.setdefault(ayuda["texto"], ayuda["texto_pt"])
    for animal in banco.animales.values():
        for secundario in animal["secundarios"].values():
            if secundario.get("contexto"):
                textos[secundario["contexto"]] = secundario["contexto_pt"]
    return textos, sorted(textos, key=len, reverse=True)


def validar_idioma(idioma: str) -> str:
    if not isinstance(idioma, str) or idioma not in IDIOMAS:
        raise ValueError("Selecciona un idioma válido.")
    return idioma


def interfaz(texto_es: str, idioma: str) -> str:
    if idioma == "es":
        return texto_es
    if idioma == "en":
        return INGLES["interfaz"].get(texto_es, texto_es)
    return PORTUGUES["interfaz"].get(texto_es, texto_es)


def texto(texto_es: str, idioma: str, banco: BancoDatos | None = None) -> str:
    if idioma == "es" or not texto_es:
        return texto_es
    restantes = texto_es.strip()
    traducidas = []
    if banco is not None and banco.ampliado:
        textos, frases = _textos_catalogo(banco, idioma)
    elif idioma == "en":
        textos, frases = INGLES["textos"], FRASES_EN
    else:
        textos, frases = PORTUGUES["textos"], FRASES_PT
    while restantes:
        for frase in frases:
            if restantes == frase or restantes.startswith(frase + " "):
                traducidas.append(textos[frase])
                restantes = restantes[len(frase):].strip()
                break
        else:
            raise ValueError("Falta una traducción del contenido educativo.")
    return " ".join(traducidas)


def respuesta(original: dict | None, idioma: str, banco: BancoDatos | None = None) -> dict | None:
    if original is None:
        return None
    copia = deepcopy(original)
    for clave in ("texto_apoyo", "texto_voz"):
        copia[clave] = texto(copia[clave], idioma, banco)
    return copia


def vista(original: dict, idioma: str, banco: BancoDatos | None = None) -> dict:
    copia = deepcopy(original)
    copia["idioma"] = idioma
    if idioma == "es":
        return copia
    copia["respuesta"] = respuesta(copia["respuesta"], idioma, banco)
    if idioma == "en":
        es_ampliado = banco is not None and banco.ampliado
        habitats_map = INGLES["habitats_ampliado"] if es_ampliado else INGLES["habitats"]
        pictos_map = INGLES["pictogramas_ampliado"] if es_ampliado else INGLES["pictogramas"]
        for animal in copia.get("catalogo_animales", []):
            animal["nombre"] = INGLES["animales"][animal["id"]]
        if copia.get("animal"):
            copia["animal"]["nombre"] = INGLES["animales"][copia["animal"]["id"]]
        for habitat in copia["opciones_habitat"]:
            habitat["nombre"] = habitats_map[habitat["id"]]
        for identificador, pictograma in copia["pictogramas"].items():
            pictograma["etiqueta"] = pictos_map[identificador]
        return copia
    if banco is not None and banco.ampliado:
        animales = list(copia["catalogo_animales"])
        if copia["animal"]:
            animales.append(copia["animal"])
        for animal in animales:
            animal["nombre"] = banco.animales[animal["id"]]["nombre_pt"]
        for habitat in copia["opciones_habitat"]:
            habitat["nombre"] = banco.habitats[habitat["id"]]["nombre_pt"]
        for identificador, pictograma in copia["pictogramas"].items():
            pictograma["etiqueta"] = banco.pictogramas[identificador].get("etiqueta_pt") or PORTUGUES["pictogramas"][identificador]
        return copia
    for animal in copia.get("catalogo_animales", []):
        animal["nombre"] = PORTUGUES["animales"][animal["id"]]
    if copia.get("animal"):
        copia["animal"]["nombre"] = PORTUGUES["animales"][copia["animal"]["id"]]
    for habitat in copia["opciones_habitat"]:
        habitat["nombre"] = PORTUGUES["habitats"][habitat["id"]]
    for identificador, pictograma in copia["pictogramas"].items():
        pictograma["etiqueta"] = PORTUGUES["pictogramas"][identificador]
    return copia


def error(mensaje: str, idioma: str) -> str:
    if idioma == "es":
        return mensaje
    if idioma == "en":
        return INGLES["errores"].get(mensaje, "Couldn't complete the operation.")
    return PORTUGUES["errores"].get(mensaje, "Não foi possível concluir a operação.")


def saludo(idioma: str) -> str:
    if idioma == "en":
        return INGLES["saludo"]
    if idioma == "pt-BR":
        return PORTUGUES["saludo"]
    return "Hola. Vamos a descubrir dónde viven los animales."
