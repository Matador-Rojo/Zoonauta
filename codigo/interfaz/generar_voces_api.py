"""Genera las grabaciones pendientes con la API de ElevenLabs (opcional).

Por defecto NO hace nada: solo cuenta mensajes, caracteres y créditos.
Para generar hay que pasar --ejecutar y --confirmar con el número exacto de
mensajes que se van a generar (lo muestra la ejecución sin --ejecutar).

La clave se lee de la variable de entorno ELEVENLABS_API_KEY. Nunca va en el
repositorio ni en el CSV. Los audios se guardan en assets/voz/grabada/<idioma>/
con el nombre del inventario, y los que ya existen se omiten.

Uso:
    python -m codigo.interfaz.generar_voces_api                       # simulación
    python -m codigo.interfaz.generar_voces_api --ejecutar --confirmar 294
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

from codigo.interfaz import catalogo_voz
from codigo.nucleo.datos import BancoDatos

URL = "https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128"
AJUSTES = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True}
PAUSA_SEG = 0.5
REINTENTOS = 3


# Textos nuevos del agente 6.0 redactados con IA: no se gastan créditos en ellos hasta que la
# columna revision_humana del CSV diga que están revisados.
SIN_REVISAR = ("pista_rasgo", "apoyo_con_pista_rasgo")


def pendientes(tabla: list[dict], idioma: str = "es-419", prioridad: str | None = None) -> list[dict]:
    """Mensajes que tienen que grabarse y todavía no tienen audio ni fueron generados."""
    return [f for f in tabla if f["idioma"] == idioma and f["grabar"] == "si"
            and f["estado_generacion"] == "pendiente"
            and (f["categoria"] not in SIN_REVISAR or f.get("revision_humana", "").strip())
            and (prioridad is None or f["prioridad"] == prioridad)]


def resumen(lista: list[dict]) -> dict:
    return {"mensajes": len(lista), "caracteres": sum(f["caracteres"] for f in lista),
            "creditos_estimados": sum(f["caracteres"] for f in lista)}


def generar(fila: dict, voz: str, clave: str, carpeta: Path) -> Path:
    destino = carpeta / fila["archivo"].split("/")[1]
    if destino.exists():
        return destino
    cuerpo = json.dumps({"text": fila["texto"], "model_id": fila["modelo_elevenlabs"],
                         "voice_settings": AJUSTES}).encode("utf-8")
    peticion = urllib.request.Request(URL.format(voz=voz), data=cuerpo, method="POST",
                                      headers={"xi-api-key": clave, "Content-Type": "application/json",
                                               "Accept": "audio/mpeg"})
    for intento in range(REINTENTOS):
        try:
            with urllib.request.urlopen(peticion, timeout=120) as respuesta:
                audio = respuesta.read()
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503) and intento + 1 < REINTENTOS:
                time.sleep(2 ** intento)
                continue
            raise RuntimeError(f"{fila['id']}: HTTP {exc.code}") from None
    temporal = destino.with_suffix(".parcial")
    temporal.write_bytes(audio)
    temporal.replace(destino)  # sólo aparece un .mp3 completo
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--idioma", default="es-419", choices=["es-419", "pt-BR"])
    parser.add_argument("--prioridad", choices=["P1", "P2", "P3"])
    parser.add_argument("--ejecutar", action="store_true")
    parser.add_argument("--confirmar", type=int, help="número exacto de mensajes a generar")
    args = parser.parse_args()

    banco = BancoDatos(ampliado=True)
    tabla = catalogo_voz.filas(catalogo_voz.extraer(banco), catalogo_voz.leer_csv())
    lista = pendientes(tabla, args.idioma, args.prioridad)
    datos = resumen(lista)
    voz = next((f["voice_id"] for f in tabla if f["idioma"] == args.idioma and f["voice_id"]), "")
    print(json.dumps({"idioma": args.idioma, "prioridad": args.prioridad or "todas",
                      "voice_id": voz or "(falta)", **datos}, ensure_ascii=False, indent=2))
    if not args.ejecutar:
        print("Simulación: no se ha llamado a la API ni gastado créditos.")
        print(f"Para generar: --ejecutar --confirmar {datos['mensajes']}")
        return
    if not voz:
        raise SystemExit("Falta el voice_id en el inventario.")
    if args.confirmar != datos["mensajes"]:
        raise SystemExit("--confirmar no coincide con los mensajes pendientes. No se gasta nada.")
    clave = os.environ.get("ELEVENLABS_API_KEY", "")
    if not clave:
        raise SystemExit("Define ELEVENLABS_API_KEY en el entorno.")
    carpeta = catalogo_voz.CARPETA_AUDIO / args.idioma
    carpeta.mkdir(parents=True, exist_ok=True)
    generadas, errores = {}, []
    for fila in lista:
        try:
            generar(fila, voz, clave, carpeta)
            generadas[fila["id"]] = True
            print("ok", fila["archivo"], flush=True)
        except Exception as exc:  # se registra y se sigue con el resto
            errores.append(str(exc))
            print("error", str(exc), flush=True)
        time.sleep(PAUSA_SEG)
    # Actualiza el inventario: solo las generadas pasan a descargado.
    ant = catalogo_voz.leer_csv()
    for (id_, idioma), r in ant.items():
        if idioma == args.idioma and id_ in generadas:
            r["estado_generacion"] = "descargado"
            r["voz_elevenlabs"] = r.get("voz_elevenlabs") or "Marcela - Youthful, Smooth and Natural"
            r["voice_id"] = voz
    catalogo_voz.escribir(catalogo_voz.filas(catalogo_voz.extraer(banco), ant))
    print(json.dumps({"generadas": len(generadas), "errores": errores}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
