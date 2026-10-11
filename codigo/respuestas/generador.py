"""Resuelve slots a IDs simbólicos; no afirma que existan imágenes o audio."""
from __future__ import annotations

from codigo.nucleo.datos import BancoDatos, ErrorDatos
from codigo.nucleo.estado import Respuesta


class GeneradorRespuestas:
    def __init__(self, banco: BancoDatos):
        self.banco = banco

    def _pictogramas(self, plantilla: dict, animal_id: str | None,
                     habitat_id: str | None) -> tuple[str, ...]:
        salida = []
        for token in plantilla["pictogramas"]:
            if token["tipo"] == "PICTOGRAMA":
                pid = token["id"]
            elif token["nombre"] == "animal_actual" and animal_id:
                pid = self.banco.animales[animal_id]["pictograma_id"]
            elif token["nombre"] == "habitat_seleccionado" and habitat_id:
                pid = self.banco.habitats[habitat_id]["pictograma_id"]
            else:
                raise ErrorDatos("No se puede resolver un slot de la respuesta.")
            if pid not in self.banco.pictogramas:
                raise ErrorDatos(f"Pictograma desconocido: {pid}.")
            salida.append(pid)
        return tuple(salida)

    def mensaje(self, id: str, animal_id: str | None = None,
                habitat_id: str | None = None, contexto: str | None = None) -> Respuesta:
        plantilla = self.banco.mensajes[id]
        if "texto_plantilla" in plantilla:
            locativo = self.banco.habitats[habitat_id]["frase_locativa"]
            texto = plantilla["texto_plantilla"].format(habitat_locativo=locativo)
        else:
            texto = plantilla["texto"]
        if contexto:
            texto += " " + contexto
        return Respuesta(id, plantilla["tipo"], self._pictogramas(plantilla, animal_id, habitat_id),
                         texto, texto)

    def ayuda(self, plantilla: dict, animal_id: str, prefijo: Respuesta | None = None) -> Respuesta:
        texto = plantilla["texto"]
        simbolos = self._pictogramas(plantilla, animal_id, None)
        if prefijo:
            texto = prefijo.texto_apoyo + " " + texto
            simbolos = prefijo.pictogramas + simbolos
        tipo = "NEUTRAL" if prefijo and prefijo.tipo_respuesta == "NEUTRAL" else "AYUDA"
        return Respuesta(plantilla["id"], tipo, simbolos, texto, texto,
                         plantilla["nivel"], plantilla["variante_id"])

