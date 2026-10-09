"""Jugador sintético que envía acciones legales al mismo núcleo de la consola."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean

from codigo.entrenamiento.bayes import ModeloBayes
from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.estado import TERMINALES
from codigo.nucleo.gestor import GestorPartida


def uniforme(semilla: int, reto: int, ayuda: int, canal: str) -> float:
    """Flujo por evento: políticas distintas comparten los mismos sorteos exógenos."""
    entrada = json.dumps([semilla, reto, ayuda, canal], separators=(",", ":")).encode()
    entero = int.from_bytes(hashlib.blake2b(entrada, digest_size=8).digest(), "big")
    return (entero >> 11) / (1 << 53)


class RegistroExperimento:
    """Conserva cierres compactos y aplica aprendizaje solo en entrenamiento."""
    def __init__(self, condicion: dict, identificador: str, modelo: ModeloBayes | None = None,
                 archivo=None):
        self.condicion = condicion
        self.identificador = identificador
        self.modelo = modelo
        self.archivo = archivo
        self.abiertas: dict[str, dict] = {}
        self.resumen: dict[tuple, Counter] = {}
        self.totales = Counter()
        self.tiempos_ns: list[int] = []
        self.costes_variedad: list[float] = []
        self.brechas_elegibles: list[float] = []
        self.probabilidades_elegidas: list[float] = []
        self.ejemplos: list[dict] = []
        self.reto_planificado = 0

    def agregar(self, fila: dict) -> None:
        tipo = fila["tipo_registro"]
        if tipo == "AYUDA_PRESENTADA":
            traza = fila["decision"]
            z = fila["contexto"]
            probs = self.condicion["probabilidades"][f"b{z['repeticion_previa']}"]
            v = fila["variante_id"]
            max_elegible = max(probs[a] for a in fila["variantes_elegibles"])
            coste = max(probs.values()) - max_elegible
            brecha = max_elegible - probs[v]
            self.totales["ayudas"] += 1
            if traza["variante_anterior"] is not None:
                self.totales["oportunidades_repeticion_automatica"] += 1
                self.totales["repeticiones_automaticas"] += int(traza["variante_anterior"] == v)
            self.tiempos_ns.append(traza["tiempo_decision_ns"])
            self.costes_variedad.append(coste if traza["politica"] != "ID3" else 0.0)
            self.brechas_elegibles.append(brecha)
            self.probabilidades_elegidas.append(probs[v])
            self.abiertas[fila["observacion_id"]] = {
                "experimento_id": self.identificador, "condicion": self.condicion["id"],
                "reto_planificado": self.reto_planificado,
                "probabilidad_sintetica_elegida": probs[v],
                "probabilidades_sinteticas": probs,
                "decision": {k: traza[k] for k in ("metodo", "variante_anterior", "estimaciones",
                    "variantes_elegibles", "parametros_congelados", "modelo_version")},
                "coste_restriccion_variedad": coste if traza["politica"] != "ID3" else 0.0,
                "brecha_entre_elegibles": brecha}
        elif tipo == "OBSERVACION_CERRADA":
            detalle = self.abiertas.pop(fila["observacion_id"])
            actualizada = self.modelo.actualizar(fila) if self.modelo else False
            fila["modelo_actualizado"] = actualizada
            z = fila["contexto"]
            clave = (z["habitat_guia_id"], z["nivel"], z["repeticion_previa"], fila["variante_id"])
            conteos = self.resumen.setdefault(clave, Counter())
            y = fila["resultado"]
            etiqueta = "sin_etiqueta" if y is None else f"y{y}"
            conteos[etiqueta] += 1
            self.totales[etiqueta] += 1
            registro = {**fila, **detalle}
            if len(self.ejemplos) < 12:
                self.ejemplos.append(registro)
            if self.archivo:
                self.archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def por_contexto(self) -> list[dict]:
        return [{"habitat_guia_id": h, "nivel": l, "repeticion_previa": b, "variante_id": v,
                 "y0": c["y0"], "y1": c["y1"], "sin_etiqueta": c["sin_etiqueta"],
                 "etiquetadas": c["y0"] + c["y1"],
                 "total": c["y0"] + c["y1"] + c["sin_etiqueta"]}
                for (h, l, b, v), c in sorted(self.resumen.items())]


def simular(banco: BancoDatos, motor: MotorGuia, condicion: dict, *, retos: int,
            semilla: int, identificador: str, configuracion: dict,
            modelo: ModeloBayes | None = None, archivo=None) -> dict:
    if type(retos) is not int or retos < 1:
        raise ValueError("El número de retos de un experimento debe ser positivo.")
    origen = "SIMULACION_ENTRENAMIENTO" if modelo else "SIMULACION_EVALUACION"
    registro = RegistroExperimento(condicion, identificador, modelo, archivo)
    contador = Counter()
    ayudas_completados = []
    historia = []
    orden = banco.configuracion["orden_animales"]
    gestor = None
    numero_sesion = 0
    numero_evento = 0
    huella_antes = tuple(motor.parametros.items())
    max_ayudas = configuracion["max_ayudas_solo_simulador"]

    def enviar(tipo: str, *, interno: bool = False, **payload):
        nonlocal numero_evento
        numero_evento += 1
        salida = gestor.procesar(gestor.crear_evento(tipo, interno=interno,
                   evento_id=f"{identificador}-EV{numero_evento:08d}", **payload))
        if not salida.aceptada:
            raise AssertionError(f"El simulador emitió una acción inválida: {tipo}, {salida.motivo}.")
        return salida

    for trial in range(retos):
        registro.reto_planificado = trial
        if gestor is None or gestor.estado.fase in TERMINALES:
            numero_sesion += 1
            gestor = GestorPartida(banco, 48, motor.politica, origen=origen,
                sesion_id=f"{identificador}-S{numero_sesion:05d}", registro=registro,
                motor=motor, traza_completa=False)
            modalidad = "JUGADOR" if numero_sesion % 2 else "AGENTE"
            enviar("iniciar", modalidad=modalidad)
        animal_id = orden[trial % len(orden)]
        if gestor.estado.modalidad == "JUGADOR":
            enviar("elegir_animal", animal_id=animal_id)
        else:
            enviar("generar_reto", animal_id=animal_id, interno=True)
        enviar("presentar_reto", interno=True)
        contador[f"retos_{gestor.estado.modalidad}"] += 1
        if uniforme(semilla, trial, 0, "repetir_pregunta") < configuracion["prob_repetir_pregunta"]:
            enviar("repetir")
            contador["repeticiones_manuales"] += 1
        enviar("ayuda")
        ayudas_en_reto = 1
        while gestor.estado.fase == "ESPERANDO_RESPUESTA":
            indice = ayudas_en_reto
            if uniforme(semilla, trial, indice, "pausa") < configuracion["prob_pausa"]:
                enviar("pausar")
                enviar("reanudar")
                contador["pausas"] += 1
            if uniforme(semilla, trial, indice, "repetir_ayuda") < configuracion["prob_repetir_ayuda"]:
                enviar("repetir")
                contador["repeticiones_manuales"] += 1
            observacion = gestor.estado.observacion
            z = observacion["contexto"]
            v = observacion["variante_id"]
            probs = condicion["probabilidades"][f"b{z['repeticion_previa']}"]
            suerte_tipo = uniforme(semilla, trial, indice, "tipo_cierre")
            p_salida = configuracion["prob_salida"]
            p_pendiente = configuracion["prob_pendiente"]
            if suerte_tipo < p_salida:
                enviar("salir")
                contador["salidas_voluntarias"] += 1
                break
            if suerte_tipo < p_salida + p_pendiente:
                pendiente = next(h for h in banco.habitats if banco.evaluar(animal_id, h)["estado"] == "PENDIENTE")
                enviar("seleccionar_habitat", habitat_id=pendiente)
                contador["selecciones_pendientes"] += 1
                if ayudas_en_reto >= max_ayudas:
                    enviar("salir")
                    contador["cortes_simulador"] += 1
                    break
                enviar("ayuda")
                ayudas_en_reto += 1
                continue
            y = int(uniforme(semilla, trial, indice, "resultado_etiquetado") < probs[v])
            if y == 1:
                validos = banco.animales[animal_id]["habitats_confirmados"]
                indice_valido = int(uniforme(semilla, trial, indice, "habitat_valido") * len(validos))
                enviar("seleccionar_habitat", habitat_id=validos[indice_valido])
                contador["retos_completados"] += 1
                ayudas_completados.append(ayudas_en_reto)
                enviar("continuar")
                break
            if ayudas_en_reto >= max_ayudas:
                # Interrumpir sin nueva ayuda no puede producir la etiqueta y=0.
                enviar("salir")
                contador["cortes_simulador"] += 1
                break
            enviar("ayuda")
            ayudas_en_reto += 1
        if modelo and ((trial + 1) % configuracion["intervalo_historia"] == 0 or trial + 1 == retos):
            errores = []
            for (h, l, b, variante), beta in modelo.valores.items():
                errores.append(abs(beta.media - condicion["probabilidades"][f"b{b}"][variante]))
            historia.append({"retos_entrenados": trial + 1, "actualizaciones": modelo.actualizaciones,
                             "error_absoluto_medio_144_parametros": mean(errores)})
        # El gestor conserva los últimos cierres; el registro ya los procesó y guardó.
        gestor.observaciones_cerradas.clear()
    if gestor.estado.fase not in TERMINALES:
        enviar("salir")
    if registro.abiertas:
        raise AssertionError("Quedaron observaciones sin cerrar al terminar el experimento.")
    if modelo is None and tuple(motor.parametros.items()) != huella_antes:
        raise AssertionError("Los parámetros cambiaron durante la evaluación.")
    total = registro.totales["y0"] + registro.totales["y1"] + registro.totales["sin_etiqueta"]
    if total != registro.totales["ayudas"]:
        raise AssertionError("El total de ayudas y el total de cierres no coinciden.")
    etiquetadas = registro.totales["y0"] + registro.totales["y1"]
    oportunidades = registro.totales["oportunidades_repeticion_automatica"]
    return {"experimento_id": identificador, "origen": origen, "condicion": condicion["id"],
        "politica": motor.politica, "semilla_entorno": semilla, "retos_iniciados": retos,
        **dict(contador), **dict(registro.totales), "etiquetadas": etiquetadas,
        "tasa_y1_etiquetadas": registro.totales["y1"] / etiquetadas if etiquetadas else None,
        "proporcion_sin_etiqueta": registro.totales["sin_etiqueta"] / total if total else None,
        "proporcion_retos_completados": contador["retos_completados"] / retos,
        "ayudas_por_reto_completado": mean(ayudas_completados) if ayudas_completados else None,
        "ayudas_por_reto_iniciado": registro.totales["ayudas"] / retos,
        "tasa_repeticion_automatica": registro.totales["repeticiones_automaticas"] / oportunidades if oportunidades else None,
        "tiempo_decision_medio_us": mean(registro.tiempos_ns) / 1000,
        "probabilidad_configurada_media": mean(registro.probabilidades_elegidas),
        "coste_variedad_medio": mean(registro.costes_variedad),
        "brecha_elegibles_media": mean(registro.brechas_elegibles),
        "modelo_evaluacion_invariable": modelo is None,
        "por_contexto": registro.por_contexto(), "historia_entrenamiento": historia,
        "ejemplos": registro.ejemplos}

