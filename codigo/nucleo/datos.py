"""Carga y comprueba el banco preconfigurado; no infiere relaciones biológicas."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DATOS_PREDETERMINADOS = RAIZ_PROYECTO / "datos"


class ErrorDatos(ValueError):
    """El banco no permite una ejecución coherente."""


class BancoDatos:
    def __init__(self, directorio: Path | str = DATOS_PREDETERMINADOS):
        self.directorio = Path(directorio).resolve()
        self.huellas: dict[str, str] = {}
        self.animales = self._indice("animales.json")
        self.habitats = self._indice("habitats.json")
        self.escenarios = self._indice("escenarios.json")
        self.variantes = self._indice("variantes_ayuda.json")
        self.pictogramas = self._indice("pictogramas.json")
        self.mensajes = self._indice("mensajes_sistema.json")
        filas = self.leer("asociaciones.json")["items"]
        self.asociaciones = {(r["animal_id"], r["habitat_id"]): r for r in filas}
        if len(filas) != len(self.asociaciones):
            raise ErrorDatos("Hay asociaciones duplicadas.")
        self.perfiles_documento = self.leer("perfiles_id3.json")
        self.perfiles = {r["clase"]: r for r in self.perfiles_documento["items"]}
        self.configuracion = self.leer("configuracion_poc.json")["configuracion"]
        self.escenario_por_animal = {r["animal_id"]: r for r in self.escenarios.values()}
        self.validar()

    def leer(self, nombre: str) -> dict:
        try:
            contenido = (self.directorio / nombre).read_bytes()
            documento = json.loads(contenido.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ErrorDatos(f"No se pudo cargar {nombre}: {exc}") from exc
        if not isinstance(documento, dict) or documento.get("schema_version") != "1.0.0":
            raise ErrorDatos(f"Versión o formato no compatible: {nombre}.")
        self.huellas[nombre] = hashlib.sha256(contenido).hexdigest()
        return documento

    def _indice(self, nombre: str) -> dict:
        filas = self.leer(nombre)["items"]
        indice = {r["id"]: r for r in filas}
        if len(filas) != len(indice):
            raise ErrorDatos(f"IDs duplicados en {nombre}.")
        return indice

    def validar(self) -> None:
        if len(self.animales) != 48 or len(self.habitats) != 8:
            raise ErrorDatos("Se requieren los 48 animales y los 8 hábitats acordados.")
        pares = {(a, h) for a in self.animales for h in self.habitats}
        if set(self.asociaciones) != pares:
            raise ErrorDatos("La matriz debe contener las 384 relaciones.")
        if set(self.perfiles) != set(self.habitats) or len(self.perfiles_documento["items"]) != 8:
            raise ErrorDatos("Debe existir un perfil único por hábitat.")
        if len(self.escenarios) != 48 or set(self.escenario_por_animal) != set(self.animales):
            raise ErrorDatos("Debe existir un escenario único por animal.")
        if set(self.configuracion["orden_animales"]) != set(self.animales):
            raise ErrorDatos("El orden del catálogo debe conservar los 48 animales.")
        if set(self.configuracion["orden_habitats"]) != set(self.habitats):
            raise ErrorDatos("El orden de opciones debe conservar los ocho hábitats.")
        for asociacion in self.asociaciones.values():
            if asociacion["estado"] not in {"VALIDA", "INCORRECTA", "PENDIENTE"}:
                raise ErrorDatos("Estado de asociación no reconocido.")
        for animal_id, animal in self.animales.items():
            validos = {h for (a, h), r in self.asociaciones.items()
                       if a == animal_id and r["estado"] == "VALIDA"}
            escenario = self.escenario_por_animal[animal_id]
            if set(animal["habitats_confirmados"]) != validos:
                raise ErrorDatos(f"Asociaciones inconsistentes para {animal_id}.")
            if animal["habitat_referencia_id"] not in validos:
                raise ErrorDatos(f"Guía no confirmada para {animal_id}.")
            if escenario["habitat_guia_id"] != animal["habitat_referencia_id"]:
                raise ErrorDatos(f"Guía inconsistente en {escenario['id']}.")
            if set(escenario["habitats_confirmados"]) != validos:
                raise ErrorDatos(f"Respuestas inconsistentes en {escenario['id']}.")
            if escenario["opciones_habitat"] != self.configuracion["orden_habitats"]:
                raise ErrorDatos("Cada reto debe conservar las ocho opciones.")
            if set(escenario["modalidades"]) != {"AGENTE", "JUGADOR"}:
                raise ErrorDatos("Cada reto debe admitir ambas modalidades.")
            for nivel, ayudas in escenario["ayudas"].items():
                for variante_id, contenido_id in ayudas.items():
                    ayuda = self.variantes.get(contenido_id)
                    if (not ayuda or ayuda["nivel"] != int(nivel)
                            or ayuda["variante_id"] != variante_id
                            or ayuda["habitat_guia_id"] != escenario["habitat_guia_id"]):
                        raise ErrorDatos(f"Ayuda inconsistente en {escenario['id']}.")
        for registro in [*self.animales.values(), *self.habitats.values()]:
            if registro["pictograma_id"] not in self.pictogramas:
                raise ErrorDatos("Un pictograma del catálogo no está definido.")

    def evaluar(self, animal_id: str, habitat_id: str) -> dict:
        """Las relaciones pendientes nunca se interpretan como incorrectas."""
        return self.asociaciones[(animal_id, habitat_id)]

