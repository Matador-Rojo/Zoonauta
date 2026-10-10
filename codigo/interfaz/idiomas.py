"""Traducción de presentación; conserva los identificadores y datos del agente."""
from __future__ import annotations

from copy import deepcopy
import json

from codigo.nucleo.datos import RAIZ_PROYECTO

IDIOMAS = {"es", "pt-BR"}
PORTUGUES = json.loads((RAIZ_PROYECTO / "datos/traducciones_pt_BR.json").read_text(encoding="utf-8"))
FRASES = sorted(PORTUGUES["textos"], key=len, reverse=True)


def validar_idioma(idioma: str) -> str:
    if not isinstance(idioma, str) or idioma not in IDIOMAS:
        raise ValueError("Selecciona un idioma válido.")
    return idioma


def texto(texto_es: str, idioma: str) -> str:
    if idioma == "es" or not texto_es:
        return texto_es
    restantes = texto_es.strip()
    traducidas = []
    while restantes:
        for frase in FRASES:
            if restantes == frase or restantes.startswith(frase + " "):
                traducidas.append(PORTUGUES["textos"][frase])
                restantes = restantes[len(frase):].strip()
                break
        else:
            raise ValueError("Falta una traducción del contenido educativo.")
    return " ".join(traducidas)


def respuesta(original: dict | None, idioma: str) -> dict | None:
    if original is None:
        return None
    copia = deepcopy(original)
    for clave in ("texto_apoyo", "texto_voz"):
        copia[clave] = texto(copia[clave], idioma)
    return copia


def vista(original: dict, idioma: str) -> dict:
    copia = deepcopy(original)
    copia["idioma"] = idioma
    if idioma == "es":
        return copia
    copia["respuesta"] = respuesta(copia["respuesta"], idioma)
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
    return PORTUGUES["errores"].get(mensaje, "Não foi possível concluir a operação.")


def saludo(idioma: str) -> str:
    return PORTUGUES["saludo"] if idioma == "pt-BR" else "Hola. Vamos a descubrir dónde viven los animales."
