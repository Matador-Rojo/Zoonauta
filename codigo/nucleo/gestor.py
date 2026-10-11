"""Único coordinador de las transiciones y del incremento de progreso."""
from __future__ import annotations

import copy
from dataclasses import asdict
from uuid import uuid4

from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.estado import Estado, Evento, PAUSABLES, Respuesta, Salida, TERMINALES
from codigo.nucleo.registro import Registro
from codigo.respuestas.generador import GeneradorRespuestas


class GestorPartida:
    def __init__(self, banco: BancoDatos, retos: int | None = None, politica: str = "ID3",
                 orden_escenarios: list[str] | None = None, origen: str = "CONSOLA_MANUAL",
                 sesion_id: str | None = None, registro: Registro | None = None,
                 motor: MotorGuia | None = None, traza_completa: bool = True,
                 ayuda_en_pendiente: bool = False):
        self.banco = banco
        self.N = banco.configuracion["retos_por_partida"] if retos is None else retos
        if type(self.N) is not int or not 1 <= self.N <= 48:
            raise ValueError("La cantidad de retos debe ser un entero entre 1 y 48.")
        if orden_escenarios is None:
            # Ocho referencias primero; después los restantes. N=48 usa todo el banco.
            primero = banco.configuracion["orden_demo_agente"]
            orden_escenarios = primero + [e for e in banco.escenarios if e not in primero]
        if not orden_escenarios or any(e not in banco.escenarios for e in orden_escenarios):
            raise ValueError("El orden automático contiene escenarios desconocidos o está vacío.")
        self.orden_escenarios = tuple(orden_escenarios)
        self.origen = origen
        self.traza_completa = traza_completa
        # La interfaz activa el acompañamiento automático; las simulaciones
        # conservan su protocolo original de solicitud explícita de ayuda.
        self.ayuda_en_pendiente = ayuda_en_pendiente
        self.sesion_id = sesion_id or f"S-{uuid4().hex}"
        self.estado = Estado()
        self.motor = motor if motor is not None else MotorGuia(banco, politica)
        if self.motor.banco is not banco or self.motor.politica != politica:
            raise ValueError("El motor debe compartir el banco y la política del gestor.")
        self.generador = GeneradorRespuestas(banco)
        self.registro = registro if registro is not None else Registro()
        self.observaciones_cerradas: list[dict] = []
        self._eventos_vistos: set[str] = set()
        self._numero_observacion = 0

    def crear_evento(self, tipo: str, *, interno: bool = False,
                     evento_id: str | None = None, **payload) -> Evento:
        return Evento(tipo, evento_id or f"EV-{uuid4().hex}", self.sesion_id,
                      self.estado.reto_id, payload, interno)

    def controles(self) -> tuple[str, ...]:
        fase = self.estado.fase
        if fase == "INICIO":
            return ("iniciar", "salir")
        if fase == "SELECCION_ANIMAL":
            return (("elegir_animal", "pausar", "salir")
                    if self.estado.modalidad == "JUGADOR" else ("pausar", "salir"))
        if fase == "PRESENTACION":
            return ("pausar", "salir")
        if fase == "ESPERANDO_RESPUESTA":
            return ("seleccionar_habitat", "ayuda", "repetir", "pausar", "salir")
        if fase == "RETO_RESUELTO":
            return ("repetir", "continuar", "pausar", "salir")
        if fase == "PAUSADA":
            return ("reanudar", "salir")
        return ()

    def _permiso(self, evento: Evento) -> str | None:
        if not evento.evento_id:
            return "EVENTO_SIN_ID"
        if evento.sesion_id != self.sesion_id:
            return "SESION_DISTINTA"
        if evento.evento_id in self._eventos_vistos:
            return "EVENTO_DUPLICADO"
        if evento.reto_id != self.estado.reto_id:
            return "RETO_DISTINTO"
        if self.estado.fase in TERMINALES:
            return "PARTIDA_TERMINAL"
        tipo = evento.tipo
        if tipo == "generar_reto":
            permitido = (evento.interno and self.estado.fase == "SELECCION_ANIMAL"
                         and self.estado.modalidad == "AGENTE")
        elif tipo == "presentar_reto":
            permitido = evento.interno and self.estado.fase == "PRESENTACION"
        else:
            permitido = tipo in self.controles() and not evento.interno
        if not permitido:
            return "ACCION_NO_PERMITIDA"
        if tipo == "iniciar" and evento.payload.get("modalidad") not in {"AGENTE", "JUGADOR"}:
            return "MODALIDAD_DESCONOCIDA"
        if tipo == "elegir_animal" and evento.payload.get("animal_id") not in self.banco.animales:
            return "ANIMAL_DESCONOCIDO"
        if tipo == "generar_reto":
            animal_id = evento.payload.get("animal_id")
            if animal_id is not None and animal_id not in self.banco.animales:
                return "ANIMAL_DESCONOCIDO"
        if tipo == "seleccionar_habitat" and evento.payload.get("habitat_id") not in self.banco.habitats:
            return "HABITAT_DESCONOCIDO"
        return None

    def procesar(self, evento: Evento) -> Salida:
        antes = self.estado.serializar() if self.traza_completa else {}
        motivo = self._permiso(evento)
        if evento.evento_id and evento.sesion_id == self.sesion_id:
            self._eventos_vistos.add(evento.evento_id)
        if motivo:
            salida = Salida(False, motivo, None, self.controles())
            self._registrar_evento(evento, antes, salida)
            return salida
        s = self.estado
        tipo = evento.tipo
        respuesta = None
        traza = None
        if tipo == "iniciar":
            s.modalidad = evento.payload["modalidad"]
            s.fase = "SELECCION_ANIMAL"
            if s.modalidad == "JUGADOR":
                respuesta = self.generador.mensaje("MSG_ELEGIR_ANIMAL")
        elif tipo in {"elegir_animal", "generar_reto"}:
            animal_id = evento.payload.get("animal_id")
            if animal_id is None:
                escenario_id = self.orden_escenarios[s.completados % len(self.orden_escenarios)]
                animal_id = self.banco.escenarios[escenario_id]["animal_id"]
            self._preparar(animal_id)
        elif tipo == "presentar_reto":
            respuesta = self.generador.mensaje("MSG_PREGUNTA", s.animal_id)
            s.fase = "ESPERANDO_RESPUESTA"
            self._guardar_contenido(respuesta)
        elif tipo == "seleccionar_habitat":
            habitat_id = evento.payload["habitat_id"]
            asociacion = self.banco.evaluar(s.animal_id, habitat_id)
            resultado = asociacion["estado"]
            if resultado == "VALIDA":
                respuesta = self.generador.mensaje("MSG_VALIDA", s.animal_id, habitat_id,
                                                   asociacion["contexto"])
                self._cerrar_observacion(1, "SELECCION_VALIDA", evento)
                s.completados += 1
                s.fase = "RETO_RESUELTO"
                self._guardar_contenido(respuesta)
            elif resultado == "PENDIENTE":
                if self.ayuda_en_pendiente:
                    prefijo = self.generador.mensaje("MSG_APOYO_AUTO")
                    respuesta, traza = self._ayuda(evento, "SELECCION_PENDIENTE", prefijo,
                                                   resultado_cierre=None)
                else:
                    respuesta = self.generador.mensaje("MSG_PENDIENTE", s.animal_id)
                    self._cerrar_observacion(None, "SELECCION_PENDIENTE", evento)
                    self._guardar_contenido(respuesta)
            else:
                prefijo = self.generador.mensaje("MSG_INCORRECTA_VALIDADA")
                respuesta, traza = self._ayuda(evento, "SELECCION_INCORRECTA_VALIDADA", prefijo)
            s.habitat_seleccionado_id = habitat_id
            s.resultado = resultado
        elif tipo == "ayuda":
            respuesta, traza = self._ayuda(evento, "NUEVA_AYUDA")
        elif tipo == "repetir":
            respuesta = s.respuesta_educativa
            if s.fase == "ESPERANDO_RESPUESTA":
                s.repeticion_previa = 1
        elif tipo == "pausar":
            s.fase_previa = s.fase
            s.fase = "PAUSADA"
            respuesta = self.generador.mensaje("MSG_PAUSA")
        elif tipo == "reanudar":
            s.fase = s.fase_previa
            s.fase_previa = None
            respuesta = s.respuesta_educativa
        elif tipo == "continuar":
            if s.completados == self.N:
                s.fase = "COMPLETADA"
                respuesta = self.generador.mensaje("MSG_CIERRE")
                self._guardar_contenido(respuesta)
            else:
                self._limpiar_reto()
                s.fase = "SELECCION_ANIMAL"
                if s.modalidad == "JUGADOR":
                    respuesta = self.generador.mensaje("MSG_ELEGIR_ANIMAL")
        elif tipo == "salir":
            self._cerrar_observacion(None, "SALIDA", evento)
            s.fase = "ABANDONADA"
            s.fase_previa = None
            respuesta = self.generador.mensaje("MSG_SALIDA")
        self.validar_estado()
        salida = Salida(True, "ACEPTADA", respuesta, self.controles(), traza)
        self._registrar_evento(evento, antes, salida)
        return salida

    def _guardar_contenido(self, respuesta: Respuesta) -> None:
        self.estado.u = respuesta.contenido_id
        self.estado.respuesta_educativa = respuesta

    def _limpiar_reto(self) -> None:
        s = self.estado
        s.animal_id = s.habitat_guia_id = s.habitat_seleccionado_id = None
        s.nivel = 0
        s.resultado = "SIN_RESPUESTA"
        s.u = s.respuesta_educativa = None
        s.nodo_id = None
        s.repeticion_previa = 0
        s.observacion = None
        s.reto_id = None

    def _preparar(self, animal_id: str) -> None:
        s = self.estado
        self._limpiar_reto()
        escenario = self.banco.escenario_por_animal[animal_id]
        s.animal_id = animal_id
        s.habitat_guia_id = escenario["habitat_guia_id"]
        s.nodo_id = self.motor.arbol.raiz.id
        s.numero_reto += 1
        s.reto_id = f"{self.sesion_id}-R{s.numero_reto:02d}"
        s.fase = "PRESENTACION"

    def _ayuda(self, evento: Evento, motivo_cierre: str,
               prefijo: Respuesta | None = None,
               resultado_cierre: int | None = 0) -> tuple[Respuesta, dict]:
        s = self.estado
        nivel = min(s.nivel + 1, 3)
        # Cerrar primero permite que el entrenamiento externo incorpore y=0
        # antes de elegir la nueva variante. La evaluación no actualiza parámetros.
        self._cerrar_observacion(resultado_cierre, motivo_cierre, evento)
        plantilla, nodo_id, traza = self.motor.decidir(s.habitat_guia_id, nivel,
                                                       s.repeticion_previa, s.variantes_anteriores)
        respuesta = self.generador.ayuda(plantilla, s.animal_id, prefijo)
        s.nivel = nivel
        s.nodo_id = nodo_id
        self._guardar_contenido(respuesta)
        s.variantes_anteriores[f"{s.habitat_guia_id}:{nivel}"] = plantilla["variante_id"]
        self._numero_observacion += 1
        s.observacion = {
            "observacion_id": f"{self.sesion_id}-O{self._numero_observacion:03d}",
            "sesion_id": self.sesion_id, "reto_id": s.reto_id, "origen": self.origen,
            "animal_id": s.animal_id, "habitat_guia_id": s.habitat_guia_id,
            "contexto": copy.deepcopy(traza["contexto"]),
            "variante_id": plantilla["variante_id"], "contenido_id": plantilla["id"],
            "variantes_elegibles": list(traza["variantes_elegibles"]),
            "variante_anterior": traza["variante_anterior"],
            "modelo_version": self.motor.modelo_version, "politica": self.motor.politica,
            "evento_apertura": evento.evento_id}
        self.registro.agregar({"tipo_registro": "AYUDA_PRESENTADA", **s.observacion,
                                "respuesta": asdict(respuesta), "decision": traza})
        return respuesta, traza

    def _cerrar_observacion(self, resultado: int | None, motivo: str, evento: Evento) -> None:
        if self.estado.observacion is None:
            return
        fila = {**copy.deepcopy(self.estado.observacion), "resultado": resultado,
                "etiqueta_disponible": resultado is not None, "evento_cierre": motivo,
                "evento_cierre_id": evento.evento_id, "modelo_actualizado": False}
        self.observaciones_cerradas.append(fila)
        registro_cierre = {"tipo_registro": "OBSERVACION_CERRADA", **fila}
        self.registro.agregar(registro_cierre)
        # El registro de entrenamiento confirma si aplicó una actualización.
        # Los registros de consola y evaluación conservan el valor False.
        fila["modelo_actualizado"] = registro_cierre["modelo_actualizado"]
        self.estado.observacion = None

    def _registrar_evento(self, evento: Evento, antes: dict, salida: Salida) -> None:
        if not self.traza_completa:
            # El simulador conserva observaciones y decisiones; omite copias de
            # todas las pantallas para mantener acotado el registro por ejecución.
            return
        self.registro.agregar({"tipo_registro": "EVENTO", "sesion_id": self.sesion_id,
            "origen": self.origen, "evento": asdict(evento), "aceptada": salida.aceptada,
            "motivo": salida.motivo, "estado_antes": antes,
            "estado_despues": self.estado.serializar(),
            "respuesta_emitida": asdict(salida.respuesta) if salida.respuesta else None,
            "decision": salida.traza, "recursos_sha256": dict(self.banco.huellas)})

    def validar_estado(self) -> None:
        s = self.estado
        def exigir(condicion: bool, mensaje: str) -> None:
            if not condicion:
                raise AssertionError(mensaje)
        exigir(0 <= s.nivel <= 3 and 0 <= s.completados <= self.N, "Nivel o progreso fuera de rango.")
        exigir(s.repeticion_previa in (0, 1), "Señal de repetición inválida.")
        if s.fase == "PAUSADA":
            exigir(s.fase_previa in PAUSABLES, "Fase previa de pausa inválida.")
        else:
            exigir(s.fase_previa is None, "Fase previa fuera de una pausa.")
        efectiva = s.fase_previa if s.fase == "PAUSADA" else s.fase
        if efectiva == "INICIO":
            exigir(s.modalidad is None and s.animal_id is None and s.completados == 0, "Inicio incoherente.")
        if efectiva == "SELECCION_ANIMAL":
            exigir(s.animal_id is None and s.habitat_guia_id is None and s.nivel == 0
                   and s.habitat_seleccionado_id is None and s.u is None and s.reto_id is None,
                   "Selección contiene datos de un reto anterior.")
        if efectiva in {"PRESENTACION", "ESPERANDO_RESPUESTA", "RETO_RESUELTO"}:
            exigir(s.animal_id in self.banco.animales and s.reto_id is not None, "Reto sin animal o ID.")
            exigir(s.habitat_guia_id == self.banco.animales[s.animal_id]["habitat_referencia_id"],
                   "Guía no corresponde al animal.")
        if efectiva in {"SELECCION_ANIMAL", "PRESENTACION", "ESPERANDO_RESPUESTA"}:
            exigir(s.completados < self.N, "Se abrió otro reto después de completar N.")
        if efectiva == "RETO_RESUELTO":
            exigir(s.resultado == "VALIDA" and 1 <= s.completados <= self.N
                   and s.habitat_seleccionado_id in self.banco.animales[s.animal_id]["habitats_confirmados"],
                   "Un reto resuelto requiere una selección confirmada.")
        if s.fase == "COMPLETADA":
            exigir(s.completados == self.N, "Cierre prematuro.")
        if s.u is not None:
            exigir(s.respuesta_educativa is not None and s.u == s.respuesta_educativa.contenido_id,
                   "El contenido educativo y su ID no coinciden.")
        if s.observacion:
            exigir(efectiva == "ESPERANDO_RESPUESTA" and s.nivel > 0,
                   "Observación de ayuda fuera de un reto activo.")

    def vista(self) -> dict:
        """Solo información de interacción; las estimaciones permanecen en la traza."""
        s = self.estado
        return {"fase": s.fase, "modalidad": s.modalidad,
                "animal": {k: self.banco.animales[s.animal_id][k]
                           for k in ("id", "nombre", "pictograma_id")} if s.animal_id else None,
                "catalogo_animales": [{"id": a, "nombre": self.banco.animales[a]["nombre"],
                                       "pictograma_id": self.banco.animales[a]["pictograma_id"]}
                                      for a in self.banco.configuracion["orden_animales"]],
                "opciones_habitat": [{"id": h, "nombre": self.banco.habitats[h]["nombre"],
                                      "pictograma_id": self.banco.habitats[h]["pictograma_id"]}
                                     for h in self.banco.configuracion["orden_habitats"]],
                "seleccion_habilitada": s.fase == "ESPERANDO_RESPUESTA",
                "progreso": {"completados": s.completados, "total": self.N},
                "controles_disponibles": self.controles(),
                "respuesta_educativa": asdict(s.respuesta_educativa) if s.respuesta_educativa else None}

    def avanzar_preparacion(self) -> list[Salida]:
        """Adaptador común: ejecuta los eventos internos sin saltarse sus fases."""
        salidas = []
        if self.estado.fase == "SELECCION_ANIMAL" and self.estado.modalidad == "AGENTE":
            salidas.append(self.procesar(self.crear_evento("generar_reto", interno=True)))
        if self.estado.fase == "PRESENTACION":
            salidas.append(self.procesar(self.crear_evento("presentar_reto", interno=True)))
        return salidas

