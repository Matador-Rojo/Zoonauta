"""Comprobar que los textos de interfaz tienen traducción pt-BR y las mismas variables.

Busca los textos que el código pasa al traductor `t(...)` en el frontend 6.0
(frontend/src) y en el de 5.0 (codigo/interfaz/web/app.js), además de los textos
pasados como `titulo=`, `subtitulo=` o `texto:` que luego se traducen. Cada uno debe
estar en datos/traducciones_pt_BR.json («interfaz») o, si es nuevo de la 6.0, en
TEXTOS_NUEVOS_PENDIENTES (borrador pendiente de revisión humana).

Uso: python -m codigo.nucleo.validar_textos_interfaz [--salida informe.json]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from codigo.nucleo.datos import RAIZ_PROYECTO

VARIABLE = re.compile(r"\{[a-z_]+\}")
CADENA = re.compile(r'"((?:[^"\\]|\\.)*)"')
# Textos que se pasan a componentes que los traducen después (Encabezado, controles…).
PROPS_TRADUCIDAS = re.compile(r'\b(?:titulo|subtitulo|texto)\s*[=:]\s*"([^"]+)"')
# Cadenas que no son texto visible (selectores, clases, rutas, valores técnicos).
NO_TEXTO = re.compile(r"^[a-z0-9_.\-/#:\[\]=\" ]*$|^[A-Z_]+$|^P_|^H\d|^(es|pt-BR|es-419)$|^\W$")
# 5.0 (app.js): nodo(tag, clase, texto) y boton(texto, ...) traducen su texto con t().
NODO_50 = re.compile(r'\bnodo\(\s*"[^"]*"\s*,\s*"[^"]*"\s*,\s*"([^"]+)"')
BOTON_50 = re.compile(r'\bboton\(\s*"([^"]+)"')


def _llamadas_t(fuente: str) -> list[str]:
    """Cadenas dentro de cada llamada t(...), con paréntesis equilibrados."""
    textos = []
    for m in re.finditer(r"\bt\(", fuente):
        i, nivel = m.end(), 1
        while i < len(fuente) and nivel:
            if fuente[i] == "(":
                nivel += 1
            elif fuente[i] == ")":
                nivel -= 1
            elif fuente[i] == '"':
                fin = CADENA.match(fuente, i)
                if fin:
                    i = fin.end() - 1
            i += 1
        cuerpo = fuente[m.end():i - 1]
        # Solo el primer argumento (antes de las variables {n: ...}).
        primero = re.split(r",\s*\{", cuerpo, maxsplit=1)[0]
        textos += [c.encode().decode("unicode_escape").encode("latin-1").decode("utf-8")
                   if "\\u" in c else c for c in CADENA.findall(primero)]
    return textos


def _pendientes_frontend() -> dict[str, str]:
    fuente = (RAIZ_PROYECTO / "frontend/src/i18n.ts").read_text("utf-8")
    bloque = fuente[fuente.index("TEXTOS_NUEVOS_PENDIENTES"):fuente.index("};", fuente.index("TEXTOS_NUEVOS_PENDIENTES"))]
    pares = re.findall(r'"([^"]+)":\s*\n?\s*"([^"]+)"', bloque)
    return dict(pares)


def validar() -> dict:
    interfaz = json.loads((RAIZ_PROYECTO / "datos/traducciones_pt_BR.json").read_text("utf-8"))["interfaz"]
    pendientes = _pendientes_frontend()
    usados: dict[str, set[str]] = {}
    archivos = sorted((RAIZ_PROYECTO / "frontend/src").rglob("*.ts*")) + [RAIZ_PROYECTO / "codigo/interfaz/web/app.js"]
    for archivo in archivos:
        if archivo.name.endswith(".test.ts") or archivo.name.endswith(".test.tsx") or archivo.name == "i18n.ts":
            continue
        fuente = archivo.read_text("utf-8")
        extra = NODO_50.findall(fuente) + BOTON_50.findall(fuente) if archivo.suffix == ".js" else []
        for texto in _llamadas_t(fuente) + PROPS_TRADUCIDAS.findall(fuente) + extra:
            if texto and not NO_TEXTO.match(texto):
                usados.setdefault(texto, set()).add(archivo.relative_to(RAIZ_PROYECTO).as_posix())
    sin_traduccion, en_borrador, variables = [], [], []
    for texto, origen in sorted(usados.items()):
        if texto in interfaz:
            if set(VARIABLE.findall(texto)) != set(VARIABLE.findall(interfaz[texto])):
                variables.append(texto)
        elif texto in pendientes:
            en_borrador.append({"es": texto, "pt-BR (borrador)": pendientes[texto], "usado_en": sorted(origen)})
        else:
            sin_traduccion.append({"es": texto, "usado_en": sorted(origen)})
    for texto, traduccion in interfaz.items():
        if set(VARIABLE.findall(texto)) != set(VARIABLE.findall(traduccion)) and texto not in variables:
            variables.append(texto)
    return {"schema_version": "1.0.0", "textos_usados": len(usados), "traducciones_interfaz": len(interfaz),
            "correcto": not sin_traduccion and not variables,
            "sin_traduccion": sin_traduccion, "variables_distintas": variables,
            "borradores_pendientes_de_revision": en_borrador}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    resultado = validar()
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8")
    print(texto)
    raise SystemExit(0 if resultado["correcto"] else 1)


if __name__ == "__main__":
    main()
