"""Ejecuta los ocho recorridos especificados en el paquete de datos."""
from __future__ import annotations

import argparse
import copy
import json
from dataclasses import asdict
from pathlib import Path

from codigo.nucleo.datos import BancoDatos, DATOS_PREDETERMINADOS
from codigo.nucleo.gestor import GestorPartida
from codigo.nucleo.registro import Registro


def comprobar_esperado(gestor: GestorPartida, salida, esperado: dict,
                       antes: dict, cerradas_antes: int) -> None:
    s = gestor.estado
    valores = {"fase": s.fase, "animal_id": s.animal_id, "nivel": s.nivel,
               "completados": s.completados, "resultado": s.resultado,
               "repeticion_previa": s.repeticion_previa,
               "variante": s.respuesta_educativa.variante_id if s.respuesta_educativa else None,
               "accion_ignorada": not salida.aceptada,
               "actualizaciones_modelo": sum(r["modelo_actualizado"] for r in gestor.observaciones_cerradas)}
    for campo, objetivo in esperado.items():
        if campo == "conservar_u":
            real = s.u == antes["u"] and asdict(s.respuesta_educativa) == antes["respuesta_educativa"]
        elif campo == "conservar_observacion":
            real = s.observacion == antes["observacion"]
        elif campo == "etiqueta_cierre_observacion":
            if len(gestor.observaciones_cerradas) != cerradas_antes + 1:
                raise AssertionError("Se esperaba cerrar exactamente una observación.")
            real = gestor.observaciones_cerradas[-1]["resultado"]
        else:
            if campo not in valores:
                raise AssertionError(f"Expectativa no implementada: {campo}.")
            real = valores[campo]
        if real != objetivo:
            raise AssertionError(f"{campo}: esperado {objetivo!r}; obtenido {real!r}.")


def ejecutar_caso(banco: BancoDatos, caso: dict, registro: Registro | None = None) -> tuple[dict, GestorPartida]:
    cfg = caso["configuracion"]
    gestor = GestorPartida(banco, cfg["retos_por_partida"], cfg["politica"],
                           caso.get("orden_escenarios"), origen="PRUEBA_DE_CONTROL_SINTETICA",
                           sesion_id=f"ACEPTACION-{caso['id']}", registro=registro)
    pasos = []
    for indice, accion in enumerate(caso["acciones"], 1):
        payload = dict(accion.get("payload", {}))
        interno = payload.pop("interno", False)
        antes = copy.deepcopy(gestor.estado.serializar())
        cerradas = len(gestor.observaciones_cerradas)
        evento = gestor.crear_evento(accion["tipo"], interno=interno,
                                     evento_id=f"{caso['id']}-EV{indice:02d}", **payload)
        salida = gestor.procesar(evento)
        if not salida.aceptada and not accion.get("esperado", {}).get("accion_ignorada", False):
            raise AssertionError(f"{caso['id']}, paso {indice}: {salida.motivo}.")
        comprobar_esperado(gestor, salida, accion.get("esperado", {}), antes, cerradas)
        if len(gestor.vista()["opciones_habitat"]) != 8:
            raise AssertionError("Se perdió alguna opción de hábitat.")
        gestor.validar_estado()
        pasos.append({"paso": indice, "accion": accion["tipo"], "estado": gestor.estado.serializar(),
                      "salida": asdict(salida)})
    return {"caso_id": caso["id"], "descripcion": caso["descripcion"], "resultado": "CORRECTO",
            "pasos": pasos}, gestor


def ejecutar_todos(banco: BancoDatos, registro: Registro | None = None) -> list[dict]:
    return [ejecutar_caso(banco, caso, registro)[0]
            for caso in banco.leer("casos_aceptacion.json")["items"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=DATOS_PREDETERMINADOS)
    parser.add_argument("--salida", type=Path, help="Guardar los resultados ejecutados en JSON.")
    args = parser.parse_args()
    casos = ejecutar_todos(BancoDatos(args.datos))
    for caso in casos:
        print(f"{caso['caso_id']}: CORRECTO. {caso['descripcion']}")
    print(f"Resultado: {len(casos)}/{len(casos)} casos correctos.")
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(json.dumps({"origen": "PRUEBAS_DE_CONTROL_SINTETICAS", "casos": casos},
                                          ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

