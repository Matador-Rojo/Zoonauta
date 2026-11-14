"""Validar el catálogo ampliado (288 animales, 48 hábitats, 144 pistas) y sus textos.

Errores (bloquean): IDs duplicados o con formato incorrecto, referencias rotas entre
archivos, archivos de imagen ausentes, traducciones vacías, variables distintas entre
idiomas, pistas incompletas por hábitat y secundarios sin fuente.

Avisos (revisión humana, no bloquean): texto idéntico en ambos idiomas, signos o
letras propios del otro idioma, formas de España (es-ES) o de Portugal (pt-PT) y
nombres científicos con formato inusual. Ningún aviso cambia datos: solo los señala.

No revalida la evidencia biológica ni la comprensión de los pictogramas.
Uso: python -m codigo.nucleo.validar_catalogo [--salida informe.json]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from codigo.nucleo.datos import RAIZ_PROYECTO

CARPETA = RAIZ_PROYECTO / "datos/expedicion"
VARIABLE = re.compile(r"\{[a-z_]+\}")
TAXON = re.compile(r"^[A-Z][a-z]+ [a-z]+( [a-z]+)?$")
# Marcadores léxicos frecuentes de las variedades que no deben presentarse como es-419 o pt-BR.
ES_ES = re.compile(r"\b(vosotros|vosotras|os\b|coger|ordenador|vale\b|móvil\b|zumo|gafas|conducir)", re.I)
PT_PT = re.compile(r"\b(facto|equipa|autocarro|rapariga|comboio|ecrã|telemóvel|estás a|está a)\b", re.I)
SOLO_ES = re.compile(r"[ñ¿¡]")
SOLO_PT = re.compile(r"[ãõç]")


def _cargar(nombre: str) -> list[dict]:
    return json.loads((CARPETA / nombre).read_text("utf-8"))["items"]


def validar() -> dict:
    animales, habitats = _cargar("animales.json"), _cargar("habitats.json")
    pistas, pictogramas = _cargar("pistas.json"), _cargar("pictogramas.json")
    errores: list[str] = []
    avisos: list[dict] = []

    def aviso(identificador: str, campo: str, motivo: str, texto: str):
        avisos.append({"id": identificador, "campo": campo, "motivo": motivo, "texto": texto})

    # 1. Identificadores únicos y con formato.
    # Animales: A01–A48 (catálogo original) y N001–N240 (ampliación).
    for nombre, filas, patron, esperado in (("animales", animales, r"^(A\d{2}|N\d{3})$", 288),
                                            ("habitats", habitats, r"^H\d{2}$", 48),
                                            ("pistas", pistas, r"^AY_H\d{2}_L[123]$", 144),
                                            ("pictogramas", pictogramas, r"^P_[A-Z0-9_]+$", None)):
        ids = [f["id"] for f in filas]
        for repetido, n in Counter(ids).items():
            if n > 1:
                errores.append(f"{nombre}: ID duplicado {repetido} ({n} veces).")
        for i in ids:
            if not re.match(patron, i):
                errores.append(f"{nombre}: ID con formato inesperado {i}.")
        if esperado is not None and len(ids) != esperado:
            errores.append(f"{nombre}: hay {len(ids)}, se esperaban {esperado}.")

    h_ids = {h["id"] for h in habitats}
    p_ids = {p["id"] for p in pictogramas}
    # Los pictogramas del catálogo original también son válidos como referencia.
    p_ids |= {p["id"] for p in json.loads((RAIZ_PROYECTO / "datos/pictogramas.json").read_text("utf-8"))["items"]}

    # 2. Referencias entre archivos y recursos.
    for a in animales:
        i = a["id"]
        if a["pictograma_id"] not in p_ids:
            errores.append(f"{i}: pictograma inexistente {a['pictograma_id']}.")
        if a["habitat_referencia_id"] not in h_ids:
            errores.append(f"{i}: hábitat de referencia inexistente {a['habitat_referencia_id']}.")
        for h, sec in a["secundarios"].items():
            if h not in h_ids:
                errores.append(f"{i}: hábitat secundario inexistente {h}.")
            if h == a["habitat_referencia_id"]:
                errores.append(f"{i}: el secundario {h} repite el hábitat de referencia.")
            if not sec.get("fuentes") or not all(str(f).startswith("http") for f in sec["fuentes"]):
                errores.append(f"{i}/{h}: secundario sin fuente verificable.")
        for h in a["contrastes_preferentes"]:
            if h not in h_ids:
                errores.append(f"{i}: contraste inexistente {h}.")
            if h == a["habitat_referencia_id"] or h in a["secundarios"]:
                errores.append(f"{i}: el contraste {h} es un hábitat válido del animal.")
        if not TAXON.match(a["taxon"]):
            aviso(i, "taxon", "nombre científico con formato inusual", a["taxon"])
    for h in habitats:
        i = h["id"]
        if h["pictograma_id"] not in p_ids:
            errores.append(f"{i}: pictograma inexistente {h['pictograma_id']}.")
        if not (RAIZ_PROYECTO / h["paisaje"]).is_file():
            errores.append(f"{i}: falta el paisaje {h['paisaje']}.")
        for afin in h["afines"]:
            if afin not in h_ids or afin == i:
                errores.append(f"{i}: hábitat afín no válido {afin}.")
    niveles = Counter()
    for p in pistas:
        if p["habitat_guia_id"] not in h_ids:
            errores.append(f"{p['id']}: hábitat inexistente {p['habitat_guia_id']}.")
        if p["nivel"] not in (1, 2, 3):
            errores.append(f"{p['id']}: nivel {p['nivel']} no válido.")
        niveles[(p["habitat_guia_id"], p["nivel"])] += 1
        for pic in p["pictogramas"]:
            pic = pic["id"] if isinstance(pic, dict) else pic
            if pic not in p_ids:
                errores.append(f"{p['id']}: pictograma inexistente {pic}.")
    for h in h_ids:
        for nivel in (1, 2, 3):
            if niveles[(h, nivel)] == 0:
                errores.append(f"{h}: falta la pista de nivel {nivel}.")
    for p in pictogramas:
        if not (RAIZ_PROYECTO / p["archivo_imagen"]).is_file():
            errores.append(f"{p['id']}: falta la imagen {p['archivo_imagen']}.")

    # 3. Traducciones por ID: presentes, con las mismas variables y señales de variedad.
    pares = []
    for a in animales:
        pares.append((a["id"], "nombre", a["nombre"], a["nombre_pt"]))
        for h, sec in a["secundarios"].items():
            if sec.get("contexto") or sec.get("contexto_pt"):
                pares.append((f"{a['id']}/{h}", "contexto", sec.get("contexto", ""), sec.get("contexto_pt", "")))
    for h in habitats:
        pares.append((h["id"], "nombre", h["nombre"], h["nombre_pt"]))
        pares.append((h["id"], "frase_locativa", h["frase_locativa"], h["frase_locativa_pt"]))
    for p in pistas:
        pares.append((p["id"], "texto", p["texto"], p["texto_pt"]))
    for p in pictogramas:
        pares.append((p["id"], "etiqueta", p["etiqueta"], p["etiqueta_pt"]))
    for identificador, campo, es, pt in pares:
        if not es.strip() or not pt.strip():
            errores.append(f"{identificador}.{campo}: falta texto en {'es' if not es.strip() else 'pt-BR'}.")
            continue
        if set(VARIABLE.findall(es)) != set(VARIABLE.findall(pt)):
            errores.append(f"{identificador}.{campo}: variables distintas entre idiomas.")
        if es.strip() == pt.strip() and len(es) > 3:
            aviso(identificador, campo, "texto idéntico en es y pt-BR (puede ser correcto)", es)
        if SOLO_ES.search(pt):
            aviso(identificador, f"{campo}_pt", "signo o letra propios del español en pt-BR", pt)
        if SOLO_PT.search(es):
            aviso(identificador, campo, "letra propia del portugués en es", es)
        if ES_ES.search(es):
            aviso(identificador, campo, "posible forma de España (es-ES)", es)
        if PT_PT.search(pt):
            aviso(identificador, f"{campo}_pt", "posible forma de Portugal (pt-PT)", pt)

    return {"schema_version": "1.0.0", "alcance": "CATALOGO_AMPLIADO",
            "conteos": {"animales": len(animales), "habitats": len(habitats), "pistas": len(pistas),
                        "pictogramas": len(pictogramas),
                        "secundarios": sum(len(a["secundarios"]) for a in animales),
                        "pares_traducidos": len(pares)},
            "correcto": not errores, "errores": errores,
            "avisos_por_motivo": dict(Counter(a["motivo"] for a in avisos)), "avisos": avisos,
            "nota": "Comprueba estructura, referencias y señales de idioma; no revalida la evidencia "
                    "biológica ni sustituye la revisión humana en ambos idiomas."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    resultado = validar()
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8")
    print(json.dumps({k: resultado[k] for k in ("conteos", "correcto", "errores", "avisos_por_motivo")},
                     ensure_ascii=False, indent=2))
    raise SystemExit(0 if resultado["correcto"] else 1)


if __name__ == "__main__":
    main()
