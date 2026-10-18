"""Entrenar y evaluar el protocolo del demo en 2, 4 y 8 opciones; datos sintéticos."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from codigo.entrenamiento.experimento import ejecutar, guardar_json, agregar_resultados
from codigo.entrenamiento.simulador import simular
from codigo.motores.guia import MotorGuia, POLITICAS
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO


def estabilidad(historia: list[dict]) -> dict:
    """Diagnóstico descriptivo; una curva corta o plana no prueba convergencia."""
    if not historia:
        return {"controles": 0, "convergencia_demostrada": False}
    primero, ultimo = historia[0], historia[-1]
    return {"controles": len(historia),
        "error_medio_primer_control": primero["error_absoluto_medio_144_parametros"],
        "error_medio_ultimo_control": ultimo["error_absoluto_medio_144_parametros"],
        "ultimo_cambio_medio": ultimo["cambio_medio_desde_control_anterior"],
        "ultimo_cambio_maximo": ultimo["cambio_maximo_desde_control_anterior"],
        "distribuciones_con_10_etiquetas": ultimo["distribuciones_con_10_etiquetas"],
        "convergencia_demostrada": False,
        "interpretacion": "Evolución y cobertura observadas en un horizonte finito; no constituyen una prueba de convergencia."}


def evaluar(banco: BancoDatos, destino: Path, configuracion: dict | None = None) -> dict:
    cfg = {**(configuracion or banco.leer("configuracion_experimentos.json")),
           "cantidad_opciones": 8, "ayuda_en_pendiente": True}
    if destino.exists() and any(destino.iterdir()):
        raise ValueError("La salida ya contiene archivos. Usa una carpeta nueva.")
    condiciones = banco.leer("configuracion_simulador.json")["items"]
    # Se entrena una vez por condición y semilla. El tamaño del panel cambia
    # solo en evaluación; todas las políticas comparten los mismos sorteos.
    base = ejecutar(banco, destino / "entrenamiento", cfg, condiciones, registros=False)
    corridas = []
    curvas = []
    for modelo in base["modelos"]:
        nombre = Path(modelo["ruta"]).stem
        train = json.loads((destino / "entrenamiento/corridas" / f"TRAIN_{nombre}.json").read_text("utf-8"))
        curvas.append({"modelo": nombre, "historia": train["historia_entrenamiento"],
                       "estabilidad": estabilidad(train["historia_entrenamiento"])})
        condicion = next(c for c in condiciones if c["id"] == modelo["condicion"])
        semilla = base["semillas_evaluacion"][modelo["replica"] - 1]
        ruta_modelo = destino / "entrenamiento" / modelo["ruta"]
        for n in (2, 4, 8):
            for politica in POLITICAS:
                if n == 8:
                    ruta = destino / "entrenamiento/corridas" / f"EVAL_{nombre}_{politica}.json"
                    resultado = json.loads(ruta.read_text("utf-8"))
                else:
                    motor = MotorGuia(banco, politica, ruta_modelo if politica == "PROBABILISTICO" else None)
                    resultado = simular(banco, motor, condicion,
                        retos=cfg["retos_evaluacion_por_condicion_replica_politica"], semilla=semilla,
                        identificador=f"EVAL_{nombre}_{politica}_O{n}",
                        configuracion={**cfg, "cantidad_opciones": n})
                    resultado["replica"] = modelo["replica"]
                    guardar_json(destino / "corridas" / f"{resultado['experimento_id']}.json", resultado)
                corridas.append(resultado)
    resumen = {"schema_version": "1.0.0", "origen": "EVALUACION_SINTETICA_PROTOCOLO_DEMO",
        "configuracion": cfg, "condiciones": condiciones,
        "semillas_entrenamiento": base["semillas_entrenamiento"],
        "semillas_evaluacion": base["semillas_evaluacion"],
        "parametros_congelados_verificados": all(r["modelo_evaluacion_invariable"] for r in corridas),
        "total_retos_entrenamiento": base["total_retos_entrenamiento"],
        "total_retos_evaluacion": sum(r["retos_iniciados"] for r in corridas),
        "por_cantidad_opciones": {str(n): agregar_resultados([r for r in corridas if r["cantidad_opciones"] == n]) for n in (2, 4, 8)},
        "curvas_entrenamiento": curvas,
        "modelos": [{**m, "ruta": "entrenamiento/" + m["ruta"].replace("\\", "/")} for m in base["modelos"]],
        "recursos_sha256": dict(banco.huellas),
        "codigo_sha256": {p: hashlib.sha256((RAIZ_PROYECTO / p).read_bytes()).hexdigest() for p in (
            "codigo/nucleo/gestor.py", "codigo/nucleo/estado.py", "codigo/motores/guia.py",
            "codigo/entrenamiento/bayes.py", "codigo/entrenamiento/simulador.py",
            "codigo/entrenamiento/experimento.py", "codigo/entrenamiento/evaluar_demo.py")},
        "nota": "Las probabilidades artificiales no modelan comprensión ni efecto del número de opciones. La comparación prueba integración y políticas dentro del simulador; no demuestra una mejora educativa ni superioridad universal."}
    for m in resumen["modelos"]:
        if hashlib.sha256((destino / m["ruta"]).read_bytes()).hexdigest() != m["sha256"]:
            raise AssertionError("Cambió un modelo durante la evaluación.")
    guardar_json(destino / "evaluacion_demo.json", resumen)
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--replicas", type=int)
    parser.add_argument("--entrenamiento", type=int)
    parser.add_argument("--evaluacion", type=int)
    args = parser.parse_args()
    banco = BancoDatos()
    cfg = banco.leer("configuracion_experimentos.json")
    for argumento, clave in ((args.replicas, "replicas"), (args.entrenamiento, "retos_entrenamiento_por_condicion_replica"),
                            (args.evaluacion, "retos_evaluacion_por_condicion_replica_politica")):
        if argumento is not None:
            if argumento < 1:
                parser.error("Las cantidades deben ser positivas.")
            cfg[clave] = argumento
    resultado = evaluar(banco, args.salida, cfg)
    print(json.dumps({k: resultado[k] for k in ("total_retos_entrenamiento", "total_retos_evaluacion", "parametros_congelados_verificados")}, indent=2))


if __name__ == "__main__":
    main()
