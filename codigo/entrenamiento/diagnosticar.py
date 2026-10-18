"""Comparar cobertura y estabilidad de dos presupuestos de entrenamiento sintético."""
from __future__ import annotations

import argparse
import hashlib
import json
from math import isfinite
from pathlib import Path
from statistics import mean


def leer(carpeta: Path) -> dict:
    documento = json.loads((carpeta / "evaluacion_demo.json").read_text("utf-8"))
    for modelo in documento["modelos"]:
        archivo = (carpeta / modelo["ruta"]).resolve()
        if not archivo.is_relative_to(carpeta.resolve()) or hashlib.sha256(archivo.read_bytes()).hexdigest() != modelo["sha256"]:
            raise ValueError("Un modelo no coincide con su huella o está fuera del paquete.")
    return documento


def comparar(antes: Path, despues: Path, umbral_cambio: float = 0.01) -> dict:
    if not isfinite(umbral_cambio) or umbral_cambio <= 0:
        raise ValueError("El umbral diagnóstico debe ser positivo y finito.")
    a, b = leer(antes), leer(despues)
    for clave in ("condiciones", "semillas_entrenamiento", "semillas_evaluacion", "recursos_sha256", "codigo_sha256"):
        if a[clave] != b[clave]:
            raise ValueError(f"La comparación cambió algo más que el presupuesto: {clave}.")
    clave_retos = "retos_entrenamiento_por_condicion_replica"
    if ({k: v for k, v in a["configuracion"].items() if k != clave_retos}
            != {k: v for k, v in b["configuracion"].items() if k != clave_retos}
            or b["configuracion"][clave_retos] <= a["configuracion"][clave_retos]):
        raise ValueError("Deben conservarse las condiciones y ampliar el entrenamiento.")
    anteriores = {c["modelo"]: c for c in a["curvas_entrenamiento"]}
    actuales = {c["modelo"]: c for c in b["curvas_entrenamiento"]}
    if not anteriores or set(anteriores) != set(actuales):
        raise ValueError("La comparación requiere las mismas réplicas.")
    modelos = {Path(m["ruta"]).stem: m for m in b["modelos"]}
    resultados = []
    for nombre, curva in actuales.items():
        historia = curva["historia"]
        prefijo = anteriores[nombre]["historia"]
        if historia[:len(prefijo)] != prefijo:
            raise ValueError(f"El entrenamiento ampliado no conserva su prefijo: {nombre}.")
        items = json.loads((despues / modelos[nombre]["ruta"]).read_text("utf-8"))["items"]
        conteos = [i["observaciones_etiquetadas"] for i in items]
        escasas = [{"contexto": i["contexto"], "variante_id": i["variante_id"],
                    "etiquetas": i["observaciones_etiquetadas"]} for i in items if i["observaciones_etiquetadas"] < 10]
        error_a = prefijo[-1]["error_absoluto_medio_144_parametros"]
        error_b = historia[-1]["error_absoluto_medio_144_parametros"]
        cambios = [p["cambio_medio_desde_control_anterior"] for p in historia[-3:]]
        resultados.append({"modelo": nombre, "error_anterior": error_a, "error_actual": error_b,
            "reduccion_relativa_error": (error_a - error_b) / error_a if error_a else None,
            "ultimos_tres_cambios_medios": cambios,
            "estabilidad_media_observada": len(historia) >= 3 and all(c <= umbral_cambio for c in cambios),
            "distribuciones": len(items), "sin_observaciones": sum(c == 0 for c in conteos),
            "etiquetas_minimas": min(conteos), "con_menos_de_10_etiquetas": escasas,
            "prefijo_entrenamiento_conservado": True})
    error_a = mean(r["error_anterior"] for r in resultados)
    error_b = mean(r["error_actual"] for r in resultados)
    return {"schema_version": "1.0.0", "origen": "DIAGNOSTICO_SINTETICO_ENTRENAMIENTO",
        "resumen_anterior_sha256": hashlib.sha256((antes / "evaluacion_demo.json").read_bytes()).hexdigest(),
        "resumen_actual_sha256": hashlib.sha256((despues / "evaluacion_demo.json").read_bytes()).hexdigest(),
        "presupuesto_anterior_por_replica": a["configuracion"][clave_retos],
        "presupuesto_actual_por_replica": b["configuracion"][clave_retos],
        "replicas_comparadas": len(resultados), "intervalo_controles": b["configuracion"]["intervalo_historia"],
        "umbral_operativo_cambio_medio": umbral_cambio,
        "error_medio_anterior": error_a, "error_medio_actual": error_b,
        "reduccion_relativa_error_medio": (error_a - error_b) / error_a if error_a else None,
        "modelos_con_estabilidad_media_observada": sum(r["estabilidad_media_observada"] for r in resultados),
        "distribuciones_sin_observaciones": sum(r["sin_observaciones"] for r in resultados),
        "distribuciones_con_menos_de_10_etiquetas": sum(len(r["con_menos_de_10_etiquetas"]) for r in resultados),
        "modelo_de_demo": "SIM_CONTEXTUAL_R01", "criterio_modelo_de_demo": "Primera réplica fijada; no se selecciona por resultados de evaluación.",
        "convergencia_general_demostrada": False, "modelos": resultados,
        "limites": "El umbral es un diagnóstico operativo en un horizonte finito. La estabilidad media no implica precisión de cada variante. Las distribuciones con pocas etiquetas conservan incertidumbre. Los datos no representan comprensión ni aprendizaje humano."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--antes", type=Path, required=True)
    parser.add_argument("--despues", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    resultado = comparar(args.antes, args.despues)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: resultado[k] for k in ("replicas_comparadas", "error_medio_anterior", "error_medio_actual",
        "modelos_con_estabilidad_media_observada", "distribuciones_sin_observaciones", "distribuciones_con_menos_de_10_etiquetas")}, indent=2))


if __name__ == "__main__":
    main()
