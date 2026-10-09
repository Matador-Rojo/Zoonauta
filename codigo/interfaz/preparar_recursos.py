"""Construye recursos SVG propios y descarga los PNG originales de ARASAAC.

Solo hace falta para regenerar recursos; el ZIP ya contiene todas las imágenes.
Se distribuyen los PNG sin cambios, junto a sus créditos y metadatos de origen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from urllib.request import urlopen

from codigo.interfaz.crear_svg import svg
from codigo.nucleo.datos import RAIZ_PROYECTO


ARASAAC = {
    "A02": 39491, "A03": 2410, "A07": 25187, "A08": 2437,
    "A09": 2324, "A10": 2372, "A11": 39488, "A12": 2650,
    "A13": 2305, "A19": 2732, "A20": 2268, "A21": 2589,
    "A23": 3379, "A25": 2488, "A26": 5892, "A27": 2623,
    "A28": 2257, "A29": 39681, "A30": 2965, "A31": 39781,
    "A34": 6158, "A35": 7055, "A36": 34433, "A37": 2868,
    "A39": 10240, "A40": 38147, "A43": 37012, "A46": 36986,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadatos", type=Path, help="Catálogo oficial ARASAAC descargado, opcional.")
    args = parser.parse_args()
    metadatos = {p["_id"]: p for p in json.loads(args.metadatos.read_text())} if args.metadatos else {}
    directorio = RAIZ_PROYECTO / "assets/pictogramas"
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = RAIZ_PROYECTO / "datos/pictogramas.json"
    documento = json.loads(ruta.read_text())
    fuentes = []
    for p in documento["items"]:
        aid = p["referencia_id"]
        if p["tipo"] == "ANIMAL" and aid in ARASAAC:
            ident = ARASAAC[aid]
            archivo = directorio / (p["id"] + ".png")
            url = f"https://static.arasaac.org/pictograms/{ident}/{ident}_500.png"
            if not archivo.exists():
                with urlopen(url, timeout=30) as respuesta:
                    imagen = respuesta.read()
                if not imagen.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError(f"El recurso {ident} no es un PNG.")
                archivo.write_bytes(imagen)
            ancho, alto = struct.unpack(">II", archivo.read_bytes()[16:24])
            if ancho < 200 or alto < 200:
                raise ValueError(f"Imagen demasiado pequeña: {ident}.")
            meta = metadatos.get(ident)
            if meta is None:
                with urlopen(f"https://api.arasaac.org/v1/pictograms/es/{ident}", timeout=30) as respuesta:
                    meta = json.load(respuesta)
            p.update(fuente_imagen=f"https://arasaac.org/pictograms/es/{ident}",
                     licencia="CC BY-NC-SA (según condiciones de ARASAAC)",
                     autor_imagen="Sergio Palao", propietario="Gobierno de Aragón",
                     adaptacion_imagen="PNG original sin modificación",
                     precision_representacion="Símbolo de la clase de animal; el nombre completo conserva la especie del banco.")
            fuentes.append({"pictograma_id": p["id"], "arasaac_id": ident,
                "url_descarga": url, "fecha_consulta": "2026-10-09",
                "metadatos_originales": meta})
        else:
            archivo = directorio / (p["id"] + ".svg")
            archivo.write_text(svg(p["id"], p["etiqueta"]), encoding="utf-8")
            p.update(fuente_imagen="codigo/interfaz/crear_svg.py", licencia="CC BY-NC-SA 4.0",
                autor_imagen="Elaboración original del prototipo", propietario=None,
                adaptacion_imagen="Vector original, no derivado de imágenes ARASAAC",
                precision_representacion="Ilustración esquemática del concepto; requiere validación de comprensión CAA.")
        p.update(archivo_imagen=str(archivo.relative_to(RAIZ_PROYECTO)),
            estado_asset="DISPONIBLE_POC", validacion_visual_caa="PENDIENTE_CON_USUARIOS",
            sha256_imagen=hashlib.sha256(archivo.read_bytes()).hexdigest())
        print(p["id"], flush=True)
    documento["nota_assets"] = "95 imágenes disponibles. Revisión técnica visual; sin validación de comprensión con usuarios CAA."
    ruta.write_text(json.dumps(documento, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (RAIZ_PROYECTO / "datos/fuentes_pictogramas.json").write_text(json.dumps({
        "schema_version": "1.0.0", "fecha_consulta": "2026-10-09", "items": fuentes,
        "condiciones": "https://arasaac.org/terms-of-use"}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Completados: {len(ARASAAC)} ARASAAC y {95-len(ARASAAC)} SVG originales.", flush=True)


if __name__ == "__main__":
    main()
