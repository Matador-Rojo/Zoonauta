"""Grabaciones completas (ElevenLabs) como fuente principal de voz.

Solo se reproduce una grabación cuando su texto es exactamente el mensaje que la
partida va a leer. Nunca se unen archivos: si no hay grabación para el mensaje
completo, ``buscar`` devuelve ``None``. En la 6.0 (solo voz grabada) el cliente no
lo lee entonces con otra voz; la 5.0 lo lee con una voz del navegador si la hay (desde el
2026-11-14 no existen voces locales Piper ni Kokoro). ``tests/test_voz_grabada_cobertura.py`` comprueba que no falte ninguna.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from codigo.interfaz.catalogo_voz import CARPETA_AUDIO, EXTENSIONES, IDIOMAS_GRABACION, extraer, filas
from codigo.nucleo.datos import BancoDatos

TIPOS = {".m4a": "audio/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav"}

# Voces grabadas completas (ElevenLabs). Cada voz guarda sus 412 archivos
# con los mismos nombres exactos en su propia subcarpeta bajo assets/voz/grabada/.
VOCES_GRABADAS: dict[str, tuple[dict[str, str], ...]] = {
    "es": (
        {"id": "marcela", "etiqueta": "Marcela · ElevenLabs", "subcarpeta": "es-419"},
        {"id": "valeria", "etiqueta": "Valeria · ElevenLabs", "subcarpeta": "es-419-valeria"},
        {"id": "gaby", "etiqueta": "Gaby · ElevenLabs", "subcarpeta": "es-419-gaby"},
        {"id": "diego", "etiqueta": "Diego · ElevenLabs", "subcarpeta": "es-419-diego"},
    ),
    "pt-BR": (
        {"id": "roberta", "etiqueta": "Roberta · ElevenLabs", "subcarpeta": "pt-BR"},
        {"id": "will", "etiqueta": "Will · ElevenLabs", "subcarpeta": "pt-BR-will"},
    ),
    "en": (
        {"id": "mark", "etiqueta": "Mark · ElevenLabs", "subcarpeta": "en"},
        {"id": "jessica", "etiqueta": "Jessica · ElevenLabs", "subcarpeta": "en-jessica"},
    ),
}


@lru_cache(maxsize=4)
def indice(banco: BancoDatos) -> dict[tuple[str, str], str]:
    """(idioma del juego, texto exacto) -> nombre base del archivo."""
    if not banco.ampliado:
        return {}
    idioma_juego = {v: k for k, v in IDIOMAS_GRABACION.items()}
    return {(idioma_juego[f["idioma"]], f["texto"]): f["archivo"].rsplit(".", 1)[0]
            for f in filas(extraer(banco))}


def _subcarpeta_voz(idioma: str, voz: str | None) -> str | None:
    if not voz:
        return None
    for ficha in VOCES_GRABADAS.get(idioma, ()):
        if ficha["id"] == voz:
            return ficha["subcarpeta"]
    return None


def buscar(
    texto: str,
    idioma: str,
    banco: BancoDatos,
    carpeta: Path | None = None,
    voz: str | None = None,
) -> Path | None:
    carpeta = carpeta or CARPETA_AUDIO
    base = indice(banco).get((idioma, texto))
    if base is None:
        return None
    subcarpeta = _subcarpeta_voz(idioma, voz)
    if subcarpeta is not None:
        nombre = base.split("/", 1)[-1]
        base = f"{subcarpeta}/{nombre}"
    for extension in EXTENSIONES:
        ruta = carpeta / (base + extension)
        if ruta.is_file() and ruta.stat().st_size > 0:
            return ruta
    return None


def disponibles(banco: BancoDatos, carpeta: Path | None = None, voz: str | None = None) -> dict[str, int]:
    """Cuántos mensajes tienen grabación por idioma (el cliente evita pedirlas si hay 0)."""
    conteo = {idioma: 0 for idioma in IDIOMAS_GRABACION}
    for (idioma, texto) in indice(banco):
        if buscar(texto, idioma, banco, carpeta, voz=voz):
            conteo[idioma] += 1
    return conteo


def voces_disponibles(banco: BancoDatos, carpeta: Path | None = None) -> dict[str, list[dict[str, object]]]:
    """Lista las voces grabadas con al menos un audio presente por idioma."""
    resultado: dict[str, list[dict[str, object]]] = {}
    for idioma, fichas in VOCES_GRABADAS.items():
        activas: list[dict[str, object]] = []
        for ficha in fichas:
            cantidad = sum(
                1
                for (idi, texto) in indice(banco)
                if idi == idioma and buscar(texto, idioma, banco, carpeta, voz=ficha["id"])
            )
            if cantidad > 0:
                activas.append({"id": ficha["id"], "etiqueta": ficha["etiqueta"], "cantidad": cantidad})
        resultado[idioma] = activas
    return resultado
