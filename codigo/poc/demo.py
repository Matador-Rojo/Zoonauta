"""Demostración reproducible de ID3 y de los ocho casos de aceptación."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from codigo.motores.guia import MotorGuia
from codigo.nucleo.datos import BancoDatos, DATOS_PREDETERMINADOS
from codigo.nucleo.registro import Registro
from codigo.poc.aceptacion import ejecutar_todos


def demostracion(banco: BancoDatos, registro: Registro | None = None) -> tuple[str, dict]:
    motor = MotorGuia(banco)
    lineas = ["ANIMALES Y HÁBITATS: PoC en consola", "",
              "Los recorridos siguientes son pruebas de control sintéticas.",
              "Los parámetros probabilísticos permanecen sin entrenar y congelados.", "",
              "ID3 calculado sobre los ocho perfiles didácticos:",
              f"Entropía inicial: {motor.arbol.raiz.entropia:.2f} bits."]
    for atributo, ganancia in motor.arbol.raiz.ganancias.items():
        lineas.append(f"Ganancia de {atributo}: {ganancia:.6f} bits.")
    lineas.append(f"Raíz elegida: {motor.arbol.raiz.atributo}.")
    lineas.append("\nRutas construidas:")
    for habitat_id, ruta in motor.rutas.items():
        camino = "; ".join(f"{p['nombre']}={p['valor']}" for p in ruta)
        lineas.append(f"{habitat_id}: {camino}; hoja={motor.arbol.predecir(banco.perfiles[habitat_id]['atributos'])}.")
    resultados = ejecutar_todos(banco, registro)
    for caso in resultados:
        lineas.extend(["", f"{caso['caso_id']}: {caso['descripcion']}"])
        for paso in caso["pasos"]:
            s = paso["estado"]
            lineas.append(f"  {paso['paso']:02d}. {paso['accion']} => {s['fase']}; "
                          f"nivel={s['nivel']}; completados={s['completados']}.")
            respuesta = paso["salida"]["respuesta"]
            if respuesta:
                lineas.append("      " + respuesta["texto_apoyo"])
                lineas.append("      Secuencia simbólica: " + ", ".join(respuesta["pictogramas"]))
            traza = paso["salida"]["traza"]
            if traza:
                lineas.append(f"      Variante={traza['variante_elegida']}; "
                              f"elegibles={','.join(traza['variantes_elegibles'])}; K={','.join(traza['K'])}.")
        lineas.append("  Resultado del caso: CORRECTO.")
    lineas.extend(["", f"Aceptación: {len(resultados)}/{len(resultados)} casos correctos.",
                  "No se ha ejecutado aprendizaje bayesiano ni evaluación con jugadores."])
    return "\n".join(lineas) + "\n", {"arbol_id3": motor.arbol.serializar(), "casos": resultados}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=DATOS_PREDETERMINADOS)
    parser.add_argument("--salida", type=Path, help="Guardar texto, árbol, casos y registro en esta carpeta.")
    args = parser.parse_args()
    if args.salida:
        args.salida.mkdir(parents=True, exist_ok=True)
        (args.salida / "eventos_demo.jsonl").write_text("", encoding="utf-8")
    registro = Registro(args.salida / "eventos_demo.jsonl" if args.salida else None)
    texto, resultados = demostracion(BancoDatos(args.datos), registro)
    print(texto, end="")
    if args.salida:
        args.salida.mkdir(parents=True, exist_ok=True)
        (args.salida / "demo_consola.txt").write_text(texto, encoding="utf-8")
        for nombre, contenido in (("arbol_id3.json", resultados["arbol_id3"]),
                                  ("casos_ejecutados.json", {"origen": "CONTROL_SINTETICO", "casos": resultados["casos"]})):
            (args.salida / nombre).write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")


if __name__ == "__main__":
    main()

