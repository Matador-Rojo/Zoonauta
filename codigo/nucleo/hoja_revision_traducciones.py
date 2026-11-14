"""Genera la hoja de revisión humana español / portugués de Brasil.

Reúne todo lo que el juego muestra o lee en voz alta: interfaz, mensajes del sistema,
errores, animales (con nombre científico), hábitats, pistas, contextos educativos y
etiquetas de pictogramas. Incluye los avisos automáticos de los validadores y una nota
preliminar. Las columnas de revisión quedan para las personas revisoras y se conservan
al regenerar la hoja. No cambia ningún dato del juego.

Uso: python -m codigo.nucleo.hoja_revision_traducciones
Salida: docs/traducciones/revision_es_pt.csv (UTF-8 con BOM; abre bien en Excel).
"""
from __future__ import annotations

import csv
import json

from codigo.nucleo.datos import RAIZ_PROYECTO
from codigo.nucleo.validar_catalogo import validar as validar_catalogo
from codigo.nucleo.validar_textos_interfaz import _pendientes_frontend

SALIDA = RAIZ_PROYECTO / "docs/traducciones/revision_es_pt.csv"
COLUMNAS = ["grupo", "id", "es", "pt_BR", "uso", "aviso_automatico", "nota_preliminar",
            "revision_es", "revision_pt_BR", "cambio_propuesto", "observaciones"]
REVISION = ["revision_es", "revision_pt_BR", "cambio_propuesto", "observaciones"]

# Notas de una primera lectura (no son decisiones: las confirma la revisión humana).
NOTAS = {
    "P_R54": "«Algas altas» suena poco natural en pt-BR; valorar «algas grandes».",
    "A06": "El campo de nombre científico incluye una nota; separarla en el futuro.",
}
IDENTICOS_CORRECTOS = "Nombre igual en pt-BR; parece correcto."
# Notas para mensajes identificados por su texto en español (no tienen ID propio).
NOTAS_TEXTO = {
    "Partida en pausa. Puedes reanudarla.": "pt-BR «retomá-la» (ênclise) es correcto pero formal; valorar «retomar a partida».",
}


def _filas() -> list[dict]:
    exp = RAIZ_PROYECTO / "datos/expedicion"
    leer = lambda n: json.loads((exp / n).read_text("utf-8"))["items"]
    pt = json.loads((RAIZ_PROYECTO / "datos/traducciones_pt_BR.json").read_text("utf-8"))
    filas = []

    def fila(grupo, ident, es, pt_br, uso, nota=""):
        filas.append({"grupo": grupo, "id": ident, "es": es, "pt_BR": pt_br, "uso": uso,
                      "nota_preliminar": NOTAS.get(ident) or NOTAS_TEXTO.get(es) or nota})

    for es, tr in pt["interfaz"].items():
        fila("interfaz", "", es, tr, "pantalla")
    for es, tr in _pendientes_frontend().items():
        if es in pt["interfaz"]:
            continue  # Ya tiene traducción revisada.
        fila("interfaz", "", es, tr, "pantalla", "Borrador pt-BR nuevo de la 6.0: pendiente de revisión.")
    for es, tr in pt["textos"].items():
        fila("mensaje", "", es, tr, "pantalla y voz")
    for es, tr in pt["errores"].items():
        fila("error", "", es, tr, "pantalla")
    fila("mensaje", "SALUDO", "Hola. Vamos a descubrir dónde viven los animales.", pt["saludo"], "voz (Probar voz)")
    for a in leer("animales.json"):
        fila("animal", a["id"], a["nombre"], a["nombre_pt"], "pantalla", f"Nombre científico: {a['taxon']}")
        for h, sec in a["secundarios"].items():
            if sec.get("contexto"):
                fila("contexto", f"{a['id']}/{h}", sec["contexto"], sec["contexto_pt"], "pantalla y voz",
                     "Contenido educativo: revisar también el significado científico.")
    for h in leer("habitats.json"):
        fila("habitat", h["id"], h["nombre"], h["nombre_pt"], "pantalla")
        fila("habitat_frase", h["id"], h["frase_locativa"], h["frase_locativa_pt"], "voz (confirmación)")
    for p in leer("pistas.json"):
        fila("pista", p["id"], p["texto"], p["texto_pt"], "pantalla y voz")
    for p in leer("pictogramas.json"):
        fila("pictograma", p["id"], p["etiqueta"], p["etiqueta_pt"], "pantalla (bajo el pictograma)")
    return filas


def generar() -> dict:
    filas = _filas()
    avisos = {}
    for a in validar_catalogo()["avisos"]:
        avisos.setdefault(a["id"].split("/")[0] if a["campo"] != "contexto" else a["id"], []).append(a["motivo"])
    previas = {}
    if SALIDA.is_file():
        with SALIDA.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                previas[(r["grupo"], r["id"], r["es"])] = r
    for f in filas:
        motivos = avisos.get(f["id"], [])
        f["aviso_automatico"] = "; ".join(sorted(set(motivos)))
        if "texto idéntico en es y pt-BR (puede ser correcto)" in motivos and f["id"] not in NOTAS:
            f["nota_preliminar"] = IDENTICOS_CORRECTOS
        previa = previas.get((f["grupo"], f["id"], f["es"]), {})
        for c in REVISION:
            f[c] = previa.get(c, "")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    grupos = {}
    for f in filas:
        grupos[f["grupo"]] = grupos.get(f["grupo"], 0) + 1
    return {"filas": len(filas), "por_grupo": grupos,
            "con_aviso": sum(1 for f in filas if f["aviso_automatico"]),
            "con_nota": sum(1 for f in filas if f["nota_preliminar"])}


if __name__ == "__main__":
    print(json.dumps(generar(), ensure_ascii=False, indent=2))
