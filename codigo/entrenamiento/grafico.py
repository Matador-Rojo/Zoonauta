"""Figura exportable del experimento; matplotlib es una dependencia opcional."""
from pathlib import Path


def crear_grafico(resumen: dict, destino: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    politica_etiquetas = {"ID3": "ID3 · V1 fija", "ROTACION": "Rotación", "PROBABILISTICO": "Probabilístico"}
    etiquetas = {"SIM_UNIFORME": "Probabilidades\niguales", "SIM_DIFERENCIAS": "V1 siempre\nmás favorable",
                 "SIM_CONTEXTUAL": "La variante favorable\ncambia con Repetir"}
    colores = {"ID3": "#245A81", "ROTACION": "#C1923C", "PROBABILISTICO": "#8C4C76"}
    tramas = {"ID3": "", "ROTACION": "//", "PROBABILISTICO": ".."}
    condiciones = [c["id"] for c in resumen["condiciones"]]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
    fig, ax = plt.subplots(figsize=(12.4, 7.4))
    fig.patch.set_facecolor("white")
    ancho = 0.24
    for j, politica in enumerate(politica_etiquetas):
        filas = [next(r for r in resumen["agregado"] if r["condicion"] == c and r["politica"] == politica)
                 for c in condiciones]
        valores = [100 * r["tasa_y1_etiquetadas"]["media"] for r in filas]
        errores = [100 * r["tasa_y1_etiquetadas"]["desviacion_entre_semillas"] for r in filas]
        x = [i + (j - 1) * ancho for i in range(len(condiciones))]
        barras = ax.bar(x, valores, ancho, yerr=errores, capsize=4, color=colores[politica],
                        edgecolor="#333333", linewidth=0.7, hatch=tramas[politica],
                        label=politica_etiquetas[politica], error_kw={"elinewidth": 1.0})
        for barra, valor, error in zip(barras, valores, errores):
            ax.text(barra.get_x() + barra.get_width()/2, valor + error + 2,
                    f"{valor:.1f}%", ha="center", fontsize=11)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.set_ylabel("Selección válida antes de una nueva ayuda\nentre cierres etiquetados")
    ax.set_xticks(range(len(condiciones)), [etiquetas[c] for c in condiciones])
    ax.grid(axis="y", color="#DCE1E5", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#6E7478")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.14), ncol=3, frameon=False)
    fig.suptitle("Animales y hábitats: comparación con interacciones sintéticas",
                 x=0.06, y=0.96, ha="left", fontsize=17, fontweight="bold")
    n = resumen["configuracion"]["replicas"]
    retos = resumen["configuracion"]["retos_evaluacion_por_condicion_replica_politica"]
    fig.text(0.06, 0.07, f"Media de {n} semillas; {retos:,} retos por política, condición y semilla. Líneas: ±1 desviación estándar.", fontsize=11)
    fig.text(0.06, 0.035, "Fuente: resumen_experimentos.json. Probabilidades artificiales; no es una evaluación con jugadores.", fontsize=10, color="#555B60")
    fig.subplots_adjust(left=0.12, right=0.98, top=0.76, bottom=0.23)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=220, facecolor="white")
    plt.close(fig)

