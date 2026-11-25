"""Sesiones web: cada clic se procesa una sola vez con el gestor existente."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from random import Random, SystemRandom
from threading import RLock
from uuid import uuid4

from codigo.interfaz import idiomas
from codigo.motores.agente import MOTORES_6, POLITICA_AGENTE
from codigo.motores.aprendizaje6 import POLITICA_APRENDIDA, MotorAgenteAprendido
from codigo.motores.guia import MotorGuia, MotorPistas
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO
from codigo.nucleo.estado import Evento, TERMINALES
from codigo.nucleo.gestor import GestorPartida
from codigo.nucleo.registro import Registro


POLITICAS_6 = (*MOTORES_6, POLITICA_APRENDIDA, MotorPistas.politica)
MODELO_DEMO = RAIZ_PROYECTO / "docs/experimentos/hito2/entrenamiento/modelos/SIM_CONTEXTUAL_R01.json"


class ConflictoVista(ValueError):
    """La acción procede de una pantalla anterior."""


class SesionWeb:
    def __init__(self, banco: BancoDatos, registros: Path | None = None,
                 politica: str = "PROBABILISTICO", parametros: Path | None = MODELO_DEMO,
                 aleatorio: Random | None = None, agente: str = POLITICA_AGENTE,
                 modelo_agente: Path | None = None):
        self.banco = banco
        self.registros = registros
        # Catálogo ampliado (6.0 y 5.0 en /v5/): el agente elige las pistas; ID3_OPCIONES y
        # PISTAS_PROGRESIVAS quedan como comparación. El original conserva sus tres políticas.
        if banco.ampliado and agente not in POLITICAS_6:
            raise ValueError(f"Agente no reconocido: {agente}.")
        self.politica = agente if banco.ampliado else politica
        self.modelo_agente = modelo_agente
        self.parametros = parametros
        self.aleatorio = aleatorio if aleatorio is not None else SystemRandom()
        self.lock = RLock()
        self.revision = 0
        self.idioma = "es"
        self._recibos: dict[str, str] = {}
        self.gestor = self._nuevo(8)
        self.respuesta = asdict(self.gestor.generador.mensaje("MSG_INICIO"))

    def _nuevo(self, retos: int) -> GestorPartida:
        sid = "WEB-" + uuid4().hex
        registro = Registro(self.registros / f"{sid}.jsonl" if self.registros else None)
        if not self.banco.ampliado:
            motor = MotorGuia(self.banco, self.politica, parametros=self.parametros)
        elif self.politica == POLITICA_APRENDIDA:
            # Modelo aprendido fuera de la partida y congelado (por defecto, el de demostración
            # entrenado con jugadores simulados). No aprende mientras se juega.
            motor = MotorAgenteAprendido(self.banco, self.modelo_agente, solo_grabadas=True)
        elif self.politica in MOTORES_6:
            # Solo ayudas con grabación: la 6.0 nunca muestra una ayuda que la voz no puede leer.
            motor = MOTORES_6[self.politica](self.banco, solo_grabadas=True)
        else:
            motor = MotorPistas(self.banco)
        # Una permutación completa por partida: todos los animales pueden aparecer
        # y ninguno se repite. La consola y los experimentos conservan su orden.
        orden = self.aleatorio.sample(list(self.banco.escenarios), len(self.banco.escenarios))
        anterior = getattr(self, "gestor", None)
        if anterior and orden[0] == anterior.orden_escenarios[0]:
            orden[0], orden[1] = orden[1], orden[0]
        return GestorPartida(self.banco, retos, self.politica, origen="INTERFAZ_MANUAL",
                             sesion_id=sid, registro=registro, motor=motor,
                             ayuda_en_pendiente=True, orden_escenarios=orden,
                             modo_opciones="aleatorio_facil" if self.banco.ampliado else "afinidad")

    def vista(self) -> dict:
        with self.lock:
            vista = self.gestor.vista()
            # La navegación (pausa, inicio o salida) puede tener una respuesta
            # distinta de u; Repetir seguirá recuperando u desde el gestor.
            vista.pop("respuesta_educativa")
            vista["respuesta"] = self.respuesta
            vista["sesion_id"] = self.gestor.sesion_id
            vista["reto_id"] = self.gestor.estado.reto_id
            vista["revision"] = self.revision
            vista["catalogo_ampliado"] = self.banco.ampliado
            vista["pictogramas"] = {k: {"etiqueta": v["etiqueta"],
                "imagen": f"/media/{k}"} for k, v in self.banco.pictogramas.items()}
            return idiomas.vista(vista, self.idioma, self.banco)

    def cambiar_idioma(self, entrada: dict) -> dict:
        with self.lock:
            self._comprobar_vista(entrada)
            self.idioma = idiomas.validar_idioma(entrada.get("idioma"))
            return self.vista()

    def _comprobar_vista(self, entrada: dict) -> None:
        if (type(entrada.get("revision")) is not int or entrada["revision"] != self.revision
                or entrada.get("sesion_id") != self.gestor.sesion_id
                or entrada.get("reto_id") != self.gestor.estado.reto_id):
            raise ConflictoVista("La pantalla ha cambiado. Se recuperó la vista actual.")

    def texto_voz(self, entrada: dict) -> str:
        with self.lock:
            self._comprobar_vista(entrada)
            if entrada.get("idioma") != self.idioma:
                raise ConflictoVista("La pantalla ha cambiado. Se recuperó la vista actual.")
            if type(entrada.get("prueba", False)) is not bool:
                raise ValueError("La entrada debe ser un objeto JSON.")
            contexto = entrada.get("contexto", "respuesta")
            if contexto not in ("respuesta", "modalidad"):
                raise ValueError("Contexto de lectura no válido.")
            if contexto == "modalidad":
                if entrada.get("prueba") or self.gestor.estado.fase != "INICIO":
                    raise ConflictoVista("La pantalla ha cambiado. Se recuperó la vista actual.")
                pregunta = "¿Quién elige el animal?"
                return idiomas.interfaz(pregunta, self.idioma)
            return (idiomas.saludo(self.idioma) if entrada.get("prueba")
                    else idiomas.texto(self.respuesta["texto_voz"], self.idioma, self.banco))

    def actuar(self, entrada: dict) -> dict:
        with self.lock:
            if not isinstance(entrada, dict):
                raise ValueError("La acción debe ser un objeto.")
            eid = entrada.get("evento_id")
            if not isinstance(eid, str) or not 1 <= len(eid) <= 120:
                raise ValueError("Falta un identificador de evento válido.")
            firma = json.dumps(entrada, sort_keys=True, ensure_ascii=False)
            if eid in self._recibos:
                anterior = self._recibos[eid]
                if firma != anterior:
                    raise ValueError("El identificador ya pertenece a otra acción.")
                return {"aceptada": False, "motivo": "EVENTO_DUPLICADO",
                        "vista": self.vista(), "respuesta_emitida": None}
            self._comprobar_vista(entrada)
            tipo = entrada.get("tipo")
            payload = entrada.get("payload", {})
            if not isinstance(payload, dict):
                raise ValueError("Los datos de la acción deben ser un objeto.")
            if tipo == "nueva_partida":
                if self.gestor.estado.fase not in TERMINALES:
                    raise ValueError("Termina la partida antes de comenzar otra.")
                self.gestor = self._nuevo(8)
                emitida = self.gestor.generador.mensaje("MSG_INICIO")
                aceptada, motivo = True, "NUEVA_PARTIDA"
            else:
                if tipo == "iniciar":
                    if self.gestor.estado.fase != "INICIO":
                        raise ValueError("La partida ya está iniciada.")
                    retos = payload.get("retos", 8)
                    if type(retos) is not int or not 1 <= retos <= 48:
                        raise ValueError("Selecciona entre 1 y 48 retos.")
                    if payload.get("modalidad") not in {"AGENTE", "JUGADOR"}:
                        raise ValueError("Selecciona una modalidad válida.")
                    opciones = payload.get("cantidad_opciones", 8)
                    if type(opciones) is not int or opciones not in (2, 4, 8):
                        raise ValueError("Selecciona 2, 4 u 8 hábitats.")
                    self.gestor.N = retos
                    # Prioriza animales aún no descubiertos en «Mi álbum»; al completarse
                    # los 288, continúa de forma fluida con todo el catálogo barajado.
                    descubiertos = payload.get("animales_descubiertos")
                    if isinstance(descubiertos, list):
                        vistos_ids = {x for x in descubiertos if isinstance(x, str)}
                        if vistos_ids:
                            todos = list(self.banco.escenarios)
                            pendientes = [e for e in todos if self.banco.escenarios[e]["animal_id"] not in vistos_ids]
                            ya_vistos = [e for e in todos if self.banco.escenarios[e]["animal_id"] in vistos_ids]
                            orden_nuevo = (
                                self.aleatorio.sample(pendientes, len(pendientes))
                                + self.aleatorio.sample(ya_vistos, len(ya_vistos))
                            )
                            self.gestor.orden_escenarios = tuple(orden_nuevo)
                payload_evento = {k: v for k, v in payload.items() if k != "animales_descubiertos"}
                # El cliente nunca puede crear eventos internos ni pasar
                # acciones directamente al motor de guía.
                evento = Evento(tipo, eid, self.gestor.sesion_id,
                                self.gestor.estado.reto_id, payload_evento, False)
                salida = self.gestor.procesar(evento)
                aceptada, motivo, emitida = salida.aceptada, salida.motivo, salida.respuesta
                if aceptada:
                    for paso in self.gestor.avanzar_preparacion():
                        if paso.respuesta:
                            emitida = paso.respuesta
            if emitida:
                self.respuesta = asdict(emitida)
            self.revision += 1
            resultado = {"aceptada": aceptada, "motivo": motivo,
                "vista": self.vista(), "respuesta_emitida": idiomas.respuesta(
                    asdict(emitida) if emitida else None, self.idioma, self.banco)}
            self._recibos[eid] = firma
            return resultado

    def revision_tecnica(self) -> dict:
        with self.lock:
            return {"sesion_id": self.gestor.sesion_id, "idioma": self.idioma, "origen": "INTERFAZ_MANUAL",
                "politica": self.politica, "modelo_version": self.gestor.motor.modelo_version,
                "parametros_congelados": self.gestor.motor.parametros_congelados,
                "estado": self.gestor.estado.serializar(),
                "registro": self.gestor.registro.filas,
                "observaciones_cerradas": self.gestor.observaciones_cerradas}
