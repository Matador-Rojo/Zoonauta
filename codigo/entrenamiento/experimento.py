"""Entrenar por Thompson, congelar y comparar tres políticas en nuevas simulaciones."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import io
import os
from contextlib import contextmanager
from pathlib import Path
from statistics import mean, stdev

from codigo.entrenamiento.bayes import ModeloBayes, MotorThompson
from codigo.entrenamiento.simulador import simular
from codigo.motores.guia import MotorGuia, POLITICAS
from codigo.nucleo.datos import BancoDatos, DATOS_PREDETERMINADOS


METRICAS = ("tasa_y1_etiquetadas", "proporcion_sin_etiqueta", "proporcion_retos_completados",
            "ayudas_por_reto_completado", "ayudas_por_reto_iniciado", "tasa_repeticion_automatica",
            "tiempo_decision_medio_us", "probabilidad_configurada_media", "coste_variedad_medio",
            "brecha_elegibles_media", "turnos_decision_por_reto_completado")


def guardar_json(ruta: Path, contenido: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


@contextmanager
def archivo_registro(ruta: Path):
    """Cerrar y sincronizar el gzip antes de sustituir el archivo de destino."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    try:
        with temporal.open("wb") as bruto:
            with gzip.GzipFile(filename="", mode="wb", fileobj=bruto, mtime=0) as comprimido:
                with io.TextIOWrapper(comprimido, encoding="utf-8") as texto:
                    yield texto
            bruto.flush()
            os.fsync(bruto.fileno())
        # Leer hasta EOF comprueba también el cierre y el CRC del flujo.
        with gzip.open(temporal, "rb") as comprobar:
            while comprobar.read(1024 * 1024):
                pass
        os.replace(temporal, ruta)
    finally:
        temporal.unlink(missing_ok=True)


def agregar_resultados(corridas: list[dict]) -> list[dict]:
    condiciones = list(dict.fromkeys(r["condicion"] for r in corridas))
    salida = []
    for condicion in condiciones:
        for politica in POLITICAS:
            filas = [r for r in corridas if r["condicion"] == condicion and r["politica"] == politica]
            resumen = {"condicion": condicion, "politica": politica, "replicas": len(filas)}
            for metrica in METRICAS:
                valores = [r[metrica] for r in filas if r[metrica] is not None]
                resumen[metrica] = {"media": mean(valores) if valores else None,
                                    "desviacion_entre_semillas": stdev(valores) if len(valores) > 1 else 0.0}
            for conteo in ("retos_iniciados", "retos_completados", "etiquetadas", "y0", "y1",
                           "sin_etiqueta", "ayudas", "salidas_voluntarias", "selecciones_pendientes",
                           "cortes_simulador"):
                resumen[conteo] = sum(r.get(conteo, 0) for r in filas)
            salida.append(resumen)
    return salida


def diferencias_pareadas(corridas: list[dict]) -> list[dict]:
    resultados = []
    for condicion in dict.fromkeys(r["condicion"] for r in corridas):
        principal = {r["replica"]: r for r in corridas if r["condicion"] == condicion and r["politica"] == "PROBABILISTICO"}
        for comparador in ("ID3", "ROTACION"):
            base = {r["replica"]: r for r in corridas if r["condicion"] == condicion and r["politica"] == comparador}
            delta = [principal[i]["tasa_y1_etiquetadas"] - base[i]["tasa_y1_etiquetadas"] for i in principal]
            resultados.append({"condicion": condicion, "comparador": comparador,
                               "diferencia_media_puntos_porcentuales": 100 * mean(delta),
                               "desviacion_diferencias_puntos_porcentuales": 100 * stdev(delta) if len(delta) > 1 else 0.0,
                               "diferencias_por_semilla": delta})
    return resultados


def crear_informe(resumen: dict, grafico: bool = False) -> str:
    cfg = resumen["configuracion"]
    n = cfg["replicas"]
    t = ["# Animales y hábitats: aprendizaje y comparación sintética", "",
         "Ejecución reproducible del selector de ayudas.", "",
         "Se ejecutó el aprendizaje del selector de ayudas con Thompson Sampling y se evaluó el modelo congelado frente a ID3 y rotación. Los resultados proceden exclusivamente del jugador sintético configurado.", "",
         "## 1. Diseño del experimento", "",
         f"Cada condición utilizó {n} réplicas. Por condición y réplica se simularon {cfg['retos_entrenamiento_por_condicion_replica']:,} retos de entrenamiento y {cfg['retos_evaluacion_por_condicion_replica_politica']:,} retos de evaluación por política. Cada réplica entrenó su propio modelo; ninguno utilizó las etiquetas de evaluación.", "",
         "El mismo catálogo y las mismas reglas se ejecutaron con el gestor compartido. Los 48 animales se programaron por igual. Las modalidades de inicio se alternaron al comenzar nuevas sesiones. Las opciones se mantuvieron estables durante cada reto.", "",
         "Los sorteos de evaluación se indexaron por semilla, reto, número de ayuda y tipo de evento. Así, las políticas compartieron los sorteos exógenos correspondientes. Cuando sus respuestas difieren, también pueden diferir las ayudas y contextos alcanzados: el indicador agregado describe cada política completa y no un efecto aislado de una variante.", "",
         "| Condición | b = 0: V1 / V2 / V3 | b = 1: V1 / V2 / V3 |", "|---|---|---|"]
    for c in resumen["condiciones"]:
        row = [c["id"]]
        for b in (0, 1):
            row.append(" / ".join(f"{c['probabilidades'][f'b{b}'][v]:.0%}" for v in ("V1", "V2", "V3")))
        t.append("| " + " | ".join(row) + " |")
    t += ["", "Estas probabilidades son parámetros artificiales de la señal y entre cierres etiquetados. No se extrajeron de personas. El uso de Repetir antes de la pista determina b; repetir después conserva el contexto original de esa pista y afecta a ayudas posteriores.", "",
          f"Se configuró {cfg['prob_repetir_pregunta']:.0%} de repetición de la pregunta, {cfg['prob_repetir_ayuda']:.0%} de repetición de una ayuda, {cfg['prob_pausa']:.0%} de pausa, {cfg['prob_salida']:.0%} de salida y {cfg['prob_pendiente']:.0%} de selección pendiente por oportunidad correspondiente. Los cierres pendientes y las salidas son independientes de la variante en este simulador.", "",
          f"El tope de {cfg['max_ayudas_solo_simulador']} ayudas protege la ejecución sintética. Un corte cierra sin etiqueta; este tope no se aplica al jugador en la consola. Se observaron {sum(r['cortes_simulador'] for r in resumen['agregado'])} cortes en evaluación.", "",
          "## 2. Resultados de evaluación", "",
          f"Los porcentajes siguientes son medias de {n} réplicas. La variación presentada es la desviación estándar entre semillas, no un intervalo de confianza.", "",
          "| Condición | Política | y = 1 entre etiquetadas | Sin etiqueta | Retos completados | Ayudas por reto completado |", "|---|---|---:|---:|---:|---:|"]
    for r in resumen["agregado"]:
        tasa = r["tasa_y1_etiquetadas"]
        t.append(f"| {r['condicion']} | {r['politica']} | {100*tasa['media']:.2f}% ± {100*tasa['desviacion_entre_semillas']:.2f} pp | "
                 f"{100*r['proporcion_sin_etiqueta']['media']:.2f}% | {100*r['proporcion_retos_completados']['media']:.2f}% | "
                 f"{r['ayudas_por_reto_completado']['media']:.2f} |")
    if grafico:
        t += ["", "![Comparación sintética de las políticas](comparacion_politicas_animales_habitats.png)", "",
              "Figura 1. Porcentaje de y = 1 entre cierres etiquetados. Barras: media entre réplicas; líneas: una desviación estándar entre semillas. Fuente: ejecuciones registradas en resumen_experimentos.json. Datos sintéticos."]
    t += ["", "### Diferencias pareadas del modelo probabilístico", "",
          "| Condición | Comparador | Diferencia media | Desviación entre diferencias |", "|---|---|---:|---:|"]
    for r in resumen["diferencias_pareadas"]:
        t.append(f"| {r['condicion']} | {r['comparador']} | {r['diferencia_media_puntos_porcentuales']:+.2f} pp | {r['desviacion_diferencias_puntos_porcentuales']:.2f} pp |")
    t += ["", "Estas diferencias son descriptivas para las semillas ejecutadas; no se realizó una prueba de significación ni una evaluación pedagógica.", "",
          "## 3. Cómo interpretar las condiciones", "",
          "- Uniforme: todas las variantes tienen la misma probabilidad configurada. Las diferencias observadas pueden proceder de los sorteos; aprender una preferencia no crea una ventaja real en esta condición.",
          "- Diferencias constantes: V1 es la mejor variante configurada en ambos valores de b. ID3 conserva V1, mientras que el modelo probabilístico excluye la última forma cuando existen alternativas. Esta restricción puede reducir su resultado frente al baseline.",
          "- Contextual: la variante más favorable cambia de V1 a V2 al cambiar b. La comparación permite revisar si el selector aprendido responde a esa diferencia, dentro de la restricción de variedad.", "",
          "El diagnóstico también guarda la brecha frente a la mejor variante elegible y el coste de excluir la mejor variante global. Son cálculos sobre probabilidades conocidas del simulador, no medidas de comprensión. La variedad por sí sola no demuestra una mejora.", "",
          "## 4. Cobertura y denominadores", "",
          "| Condición | Política | Retos iniciados | Cierres etiquetados | Cierres sin etiqueta | Nuevas ayudas |", "|---|---|---:|---:|---:|---:|"]
    for r in resumen["agregado"]:
        t.append(f"| {r['condicion']} | {r['politica']} | {r['retos_iniciados']} | {r['etiquetadas']} | {r['sin_etiqueta']} | {r['ayudas']} |")
    t += ["", "La tasa principal es y1 / (y0 + y1). La proporción sin etiqueta usa (y0 + y1 + sin_etiqueta) como denominador. La proporción de retos completados utiliza todos los retos iniciados. La media de ayudas por reto completado excluye los retos abandonados; ayudas por reto iniciado se conserva por separado en el JSON.", "",
          "Las medias por semilla dan el mismo peso a cada réplica. Los conteos de la tabla se suman entre réplicas. El desglose por hábitat, nivel, b y variante se guarda en las corridas individuales. Los contextos de nivel alto pueden recibir menos observaciones porque una selección válida termina antes el reto.", "",
          "## 5. Comprobaciones de aprendizaje", "",
          f"Se guardaron {len(resumen['modelos'])} modelos entrenados. Cada modelo conserva sus 144 distribuciones, conteos de etiquetas, semillas y procedencia. Las actualizaciones de α y β suman únicamente cierres etiquetados de entrenamiento.", "",
          f"El menor número de distribuciones con alguna etiqueta por modelo fue {min(r['distribuciones_con_etiquetas'] for r in resumen['modelos'])} de 144. El mínimo de etiquetas en una distribución fue {min(r['etiquetas_minimas_por_distribucion'] for r in resumen['modelos'])}. Tener cobertura no implica tener estimaciones precisas: algunas variantes de niveles altos recibieron pocos resultados.", "",
          "El registro distingue entrenamiento y evaluación. Las selecciones pendientes, las salidas, las pausas y Repetir no se utilizan como errores. Una observación duplicada no produce otra actualización y un cierre sin etiqueta no puede recibir una etiqueta retroactiva.", "",
          "Los modelos de evaluación se cargan como tablas de parámetros inmutables. Se comprobó que su contenido no cambia durante cada corrida. Los resultados de la evaluación no se incorporan al entrenamiento ni se utilizan para elegir una semilla ganadora.", "",
          "## 6. Archivos de evidencia", "",
          "- resumen_experimentos.json: configuración, resultados agregados, diferencias pareadas y huellas de modelos.",
          "- corridas/: métricas y cobertura por contexto de cada ejecución.",
          "- modelos/: posteriores aprendidas por condición y réplica.",
          "- observaciones_*.jsonl.gz: cierres, decisiones y procedencia; pueden leerse con gzip de Python.",
          "- Las historias de entrenamiento y los ejemplos de decisiones se conservan en las corridas.", "",
          "## 7. Límites y continuidad", "",
          "Las probabilidades artificiales no varían por animal ni por nivel, aunque el modelo mantenga esos contextos separados. El simulador no representa comprensión, fatiga, accesibilidad ni aprendizaje duradero. La generalización que se comprueba es a nuevos sorteos del mismo entorno sintético.", "",
          "La interfaz de Zoonauta ya integra selección por clic o toque, pictogramas y voz. Esta ejecución comprueba el núcleo compartido con un jugador sintético; no evalúa comprensión CAA ni aprendizaje humano.", "",
          "## 8. Redacción para el documento técnico", "",
          f"Se implementó un simulador de interacciones sintéticas sobre el núcleo compartido del juego. El entrenamiento utilizó Thompson Sampling para explorar variantes elegibles y actualizó distribuciones Beta–Bernoulli exclusivamente con observaciones etiquetadas. Se ejecutaron {resumen['total_retos_entrenamiento']:,} retos de entrenamiento y {resumen['total_retos_evaluacion']:,} de evaluación, distribuidos en {len(resumen['condiciones'])} condiciones y {n} réplicas. La evaluación se realizó con parámetros congelados y semillas separadas.", "",
          "La comparación conservó ID3 con presentación fija, rotación de variantes y selección probabilística. El indicador principal fue la proporción de selecciones válidas antes de una nueva ayuda entre los cierres etiquetados. Los cierres pendientes y las salidas se informaron por separado. Las condiciones permiten observar igualdad de resultados, ventajas de una presentación fija y ventajas del selector contextual, sin asumir superioridad universal del modelo adaptativo.", "",
          "Las conclusiones se limitan a las probabilidades artificiales del simulador. La cobertura por contexto, los parámetros aprendidos y los registros se conservaron para revisar la procedencia de cada decisión. La efectividad de las secuencias de pictogramas y la interacción accesible requieren una evaluación posterior con usuarios.", ""]
    return "\n".join(t)


def ejecutar(banco: BancoDatos, destino: Path, cfg: dict, condiciones: list[dict],
             *, registros: bool = True, grafico: bool = False) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    if (destino / "resumen_experimentos.json").exists():
        raise ValueError("La carpeta ya contiene un experimento. Elige otra salida para conservarlo.")
    if cfg["replicas"] < 1 or cfg["prob_salida"] + cfg["prob_pendiente"] > 1:
        raise ValueError("Configuración de experimentos inválida.")
    train_seeds = [cfg["semilla_entrenamiento_base"] + i * cfg["paso_entre_semillas"] for i in range(cfg["replicas"])]
    eval_seeds = [cfg["semilla_evaluacion_base"] + i * cfg["paso_entre_semillas"] for i in range(cfg["replicas"])]
    if set(train_seeds) & set(eval_seeds):
        raise ValueError("Las semillas de entrenamiento y evaluación se solapan.")
    corridas = []
    modelos = []
    for condicion in condiciones:
        for i in range(cfg["replicas"]):
            etiqueta = f"{condicion['id']}_R{i+1:02d}"
            modelo = ModeloBayes(banco.leer("parametros_iniciales.json"), etiqueta)
            semilla_ts = cfg["semilla_thompson_base"] + i * cfg["paso_entre_semillas"]
            motor_train = MotorThompson(banco, modelo, semilla_ts)
            ruta_train = destino / f"observaciones_TRAIN_{etiqueta}.jsonl.gz"
            if registros:
                with archivo_registro(ruta_train) as f:
                    train = simular(banco, motor_train, condicion,
                        retos=cfg["retos_entrenamiento_por_condicion_replica"], semilla=train_seeds[i],
                        identificador=f"TRAIN_{etiqueta}", configuracion=cfg, modelo=modelo, archivo=f)
            else:
                train = simular(banco, motor_train, condicion,
                    retos=cfg["retos_entrenamiento_por_condicion_replica"], semilla=train_seeds[i],
                    identificador=f"TRAIN_{etiqueta}", configuracion=cfg, modelo=modelo)
            if modelo.actualizaciones != train["etiquetadas"] or modelo.sin_etiqueta != train.get("sin_etiqueta", 0):
                raise AssertionError("Las actualizaciones no coinciden con los cierres de entrenamiento.")
            guardar_json(destino / "corridas" / f"TRAIN_{etiqueta}.json", train)
            ruta_modelo = destino / "modelos" / f"{etiqueta}.json"
            modelo.guardar(ruta_modelo, {"condicion": condicion, "semilla_entorno": train_seeds[i],
                "semilla_thompson": semilla_ts, "retos_entrenados": cfg["retos_entrenamiento_por_condicion_replica"]})
            modelos.append({"condicion": condicion["id"], "replica": i + 1,
                "ruta": str(ruta_modelo.relative_to(destino)),
                "sha256": hashlib.sha256(ruta_modelo.read_bytes()).hexdigest(),
                "actualizaciones": modelo.actualizaciones,
                "distribuciones_con_etiquetas": sum(sum(c) > 0 for c in modelo.conteos.values()),
                "etiquetas_minimas_por_distribucion": min(sum(c) for c in modelo.conteos.values())})
            for politica in POLITICAS:
                motor = MotorGuia(banco, politica, ruta_modelo if politica == "PROBABILISTICO" else None)
                id_eval = f"EVAL_{etiqueta}_{politica}"
                kwargs = dict(retos=cfg["retos_evaluacion_por_condicion_replica_politica"],
                              semilla=eval_seeds[i], identificador=id_eval, configuracion=cfg)
                if registros:
                    with archivo_registro(destino / f"observaciones_{id_eval}.jsonl.gz") as f:
                        evaluacion = simular(banco, motor, condicion, archivo=f, **kwargs)
                else:
                    evaluacion = simular(banco, motor, condicion, **kwargs)
                evaluacion["replica"] = i + 1
                guardar_json(destino / "corridas" / f"{id_eval}.json", evaluacion)
                corridas.append(evaluacion)
            print(f"{etiqueta}: entrenamiento y evaluación de las tres políticas completos.", flush=True)
    resumen = {"schema_version": "1.0.0", "origen": "EXPERIMENTOS_SINTETICOS",
        "configuracion": cfg, "condiciones": condiciones,
        "semillas_entrenamiento": train_seeds, "semillas_evaluacion": eval_seeds,
        "recursos_sha256": dict(banco.huellas), "modelos": modelos,
        "agregado": agregar_resultados(corridas), "diferencias_pareadas": diferencias_pareadas(corridas),
        "evaluacion_congelada_verificada": all(r["modelo_evaluacion_invariable"] for r in corridas),
        "total_retos_entrenamiento": len(condiciones) * cfg["replicas"] * cfg["retos_entrenamiento_por_condicion_replica"],
        "total_retos_evaluacion": sum(r["retos_iniciados"] for r in corridas)}
    guardar_json(destino / "resumen_experimentos.json", resumen)
    if grafico:
        from codigo.entrenamiento.grafico import crear_grafico
        crear_grafico(resumen, destino / "comparacion_politicas_animales_habitats.png")
    (destino / "informe_comparacion.md").write_text(crear_informe(resumen, grafico), encoding="utf-8")
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=DATOS_PREDETERMINADOS)
    parser.add_argument("--salida", type=Path, default=Path("resultados_aprendizaje"))
    parser.add_argument("--replicas", type=int)
    parser.add_argument("--entrenamiento", type=int)
    parser.add_argument("--evaluacion", type=int)
    parser.add_argument("--condicion", choices=("SIM_UNIFORME", "SIM_DIFERENCIAS", "SIM_CONTEXTUAL"))
    parser.add_argument("--sin-registros", action="store_true", help="Omitir los cierres JSONL completos.")
    parser.add_argument("--grafico", action="store_true", help="Exportar PNG; requiere matplotlib.")
    parser.add_argument("--opciones", type=int, choices=(2, 4, 8), default=8)
    parser.add_argument("--ayuda-automatica", action="store_true", help="Usar el protocolo de la interfaz ante selecciones pendientes.")
    args = parser.parse_args()
    banco = BancoDatos(args.datos)
    cfg = banco.leer("configuracion_experimentos.json")
    cfg["cantidad_opciones"] = args.opciones
    cfg["ayuda_en_pendiente"] = args.ayuda_automatica
    for arg, key in ((args.replicas, "replicas"), (args.entrenamiento, "retos_entrenamiento_por_condicion_replica"),
                     (args.evaluacion, "retos_evaluacion_por_condicion_replica_politica")):
        if arg is not None:
            if arg < 1: parser.error("Las cantidades deben ser positivas.")
            cfg[key] = arg
    condiciones = banco.leer("configuracion_simulador.json")["items"]
    if args.condicion:
        condiciones = [c for c in condiciones if c["id"] == args.condicion]
    resumen = ejecutar(banco, args.salida, cfg, condiciones,
                        registros=not args.sin_registros, grafico=args.grafico)
    print("\nEvaluación: y=1 entre cierres etiquetados (media entre semillas).")
    for r in resumen["agregado"]:
        print(f"{r['condicion']:16s} {r['politica']:15s} {r['tasa_y1_etiquetadas']['media']:.2%}")
    print(f"\nInforme guardado en {args.salida / 'informe_comparacion.md'}")


if __name__ == "__main__":
    main()

