"""Comprobar coherencia del banco y de las pistas sin inferir nuevas asociaciones."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos, DATOS_PREDETERMINADOS
from codigo.respuestas.generador import GeneradorRespuestas
from codigo.interfaz import idiomas


def auditar(banco: BancoDatos) -> dict:
    motor = MotorGuia(banco)
    generador = GeneradorRespuestas(banco)
    fuentes = {f["id"] for f in banco.leer("fuentes.json")["items"]}
    errores = []
    relaciones = Counter(r["estado"] for r in banco.asociaciones.values())
    for (animal, habitat), fila in banco.asociaciones.items():
        if fila["estado"] == "VALIDA":
            if not fila["fuentes_del_animal"] or not set(fila["fuentes_del_animal"]) <= fuentes:
                errores.append(f"{animal}/{habitat}: falta una referencia registrada.")
        if fila["es_referencia"] != (habitat == banco.animales[animal]["habitat_referencia_id"]):
            errores.append(f"{animal}/{habitat}: referencia inconsistente.")
    revisadas = 0
    for animal, escenario in banco.escenario_por_animal.items():
        habitat = escenario["habitat_guia_id"]
        for nivel in (1, 2, 3):
            for ayuda in motor.disponibles(habitat, nivel).values():
                respuesta = generador.ayuda(ayuda, animal)
                explicitos = {p for p in respuesta.pictogramas if p.startswith("P_H0")}
                if explicitos - {banco.habitats[habitat]["pictograma_id"]}:
                    errores.append(f"{animal}/{ayuda['id']}: pictograma de otro hábitat.")
                if nivel == 3 and banco.habitats[habitat]["pictograma_id"] not in explicitos:
                    errores.append(f"{animal}/{ayuda['id']}: falta el apoyo explícito.")
                for p in respuesta.pictogramas:
                    if p not in banco.pictogramas:
                        errores.append(f"{animal}/{ayuda['id']}: recurso inexistente {p}.")
                for idioma in ("es", "pt-BR"):
                    try:
                        idiomas.texto(respuesta.texto_voz, idioma)
                    except ValueError:
                        errores.append(f"{animal}/{ayuda['id']}: falta traducción {idioma}.")
                revisadas += 1
    return {"schema_version": "1.0.0", "alcance": "COHERENCIA_ESTRUCTURAL_Y_TRADUCCIONES",
        "animales": len(banco.animales), "relaciones": dict(relaciones),
        "variantes": len(banco.variantes), "secuencias_animal_ayuda_revisadas": revisadas,
        "errores": errores, "correcto": not errores,
        "nota": "Comprueba referencias y coherencia interna; no revalida la evidencia biológica ni la comprensión CAA. Las relaciones pendientes siguen pendientes."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=DATOS_PREDETERMINADOS)
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    resultado = auditar(BancoDatos(args.datos))
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(texto, encoding="utf-8")
    print(texto)
    raise SystemExit(0 if resultado["correcto"] else 1)


if __name__ == "__main__":
    main()
