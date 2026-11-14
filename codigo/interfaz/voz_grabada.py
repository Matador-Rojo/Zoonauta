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

TIPOS = {".mp3": "audio/mpeg", ".wav": "audio/wav"}


@lru_cache(maxsize=4)
def indice(banco: BancoDatos) -> dict[tuple[str, str], str]:
    """(idioma del juego, texto exacto) -> nombre base del archivo."""
    if not banco.ampliado:
        return {}
    idioma_juego = {v: k for k, v in IDIOMAS_GRABACION.items()}
    return {(idioma_juego[f["idioma"]], f["texto"]): f["archivo"].rsplit(".", 1)[0]
            for f in filas(extraer(banco))}


def buscar(texto: str, idioma: str, banco: BancoDatos, carpeta: Path | None = None) -> Path | None:
    carpeta = carpeta or CARPETA_AUDIO
    base = indice(banco).get((idioma, texto))
    if base is None:
        return None
    for extension in EXTENSIONES:
        ruta = carpeta / (base + extension)
        if ruta.is_file() and ruta.stat().st_size > 0:
            return ruta
    return None


def disponibles(banco: BancoDatos, carpeta: Path | None = None) -> dict[str, int]:
    """Cuántos mensajes tienen grabación por idioma (el cliente evita pedirlas si hay 0)."""
    conteo = {idioma: 0 for idioma in IDIOMAS_GRABACION}
    for (idioma, texto) in indice(banco):
        if buscar(texto, idioma, banco, carpeta):
            conteo[idioma] += 1
    return conteo
