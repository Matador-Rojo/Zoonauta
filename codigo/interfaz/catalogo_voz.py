"""Inventario de locuciones completas para grabaciones definitivas (ElevenLabs).

Regla: cada audio contiene el mensaje completo que la partida lee de una vez
(``texto_voz``), con su entonación natural. No se graban palabras sueltas ni se
unen fragmentos. La 6.0 solo usa estas grabaciones; la 5.0 (/v5/) leía un mensaje
sin grabación con Piper, Kokoro o la voz del navegador.

Los textos se obtienen con el mismo generador y la misma traducción que usa el
servidor, así que son idénticos a lo que se reproduce. Este módulo no redacta
ni corrige contenido; solo añade avisos para la revisión humana.

Uso:
    python -m codigo.interfaz.catalogo_voz             # escribe el CSV y el resumen
    python -m codigo.interfaz.catalogo_voz --verificar # compara con los audios descargados
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from codigo.interfaz import idiomas
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO
from codigo.respuestas.generador import GeneradorRespuestas

IDIOMAS_GRABACION = {"es": "es-419", "pt-BR": "pt-BR"}
CARPETA_DOCS = RAIZ_PROYECTO / "docs/voz/elevenlabs"
CSV_CATALOGO = CARPETA_DOCS / "catalogo_voces.csv"
RESUMEN = CARPETA_DOCS / "resumen_catalogo.json"
CARPETA_AUDIO = RAIZ_PROYECTO / "assets/voz/grabada"
EXTENSIONES = (".mp3", ".wav")
ESTADOS = ("pendiente", "generado", "descargado", "verificado", "rechazado", "usa_duplicado")

# Créditos por carácter al generar en la web de ElevenLabs (consultado el
# 2026-11-14). Confirmar en la pantalla de generación: la tarifa puede cambiar.
MODELO_PROPUESTO = "eleven_v4"  # elegido por el propietario el 2026-11-14
TARIFAS = {"eleven_v4": 1.0, "eleven_multilingual_v2": 1.0, "eleven_v3": 1.0,
           "eleven_flash_v2_5": 0.5, "eleven_turbo_v2_5": 0.5}
MARGEN_REPETICIONES = 0.5  # 50 % extra para tomas descartadas

# Orden de grabación: primero los hábitats de la portada 6.0, luego el resto.
PORTADA = ["H01", "H09", "H17", "H22", "H20", "H37", "H21", "H25"]

FIJOS = {
    "MSG_INICIO": ("navegacion", "Pantalla inicial; también tras Nueva partida."),
    "MSG_ELEGIR_ANIMAL": ("instruccion", "Modalidad Yo elijo: antes de cada reto."),
    "MSG_PREGUNTA": ("pregunta", "Presentación de cada reto; también con Repetir y Reanudar."),
    "MSG_PAUSA": ("navegacion", "Al pulsar Pausar."),
    "MSG_CIERRE": ("navegacion", "Al completar todos los retos de la partida."),
    "MSG_SALIDA": ("navegacion", "Al pulsar Salir."),
}

ES_PENINSULAR = re.compile(r"\b(vosotr[oa]s|vale|coger|ordenador|móvil|zumo|gafas|"
                           r"tenéis|podéis|sabéis|queréis|habéis|estáis|sois)\b", re.I)
PT_EUROPEU = re.compile(r"\b(estás a|facto|equipa|ecrã|autocarro|telemóvel|"
                        r"rapariga|pequeno-almoço|connosco|registo|utilizador)\b", re.I)
ENCLISE = re.compile(r"\b\w+-(se|la|lo|las|los)\b", re.I)


@dataclass
class Locucion:
    id: str
    componentes: str          # IDs originales de los que procede el mensaje
    categoria: str
    tipo_texto: str           # fijo | variable | dinamico
    prioridad: str
    contexto: str
    origen: str
    textos: dict[str, str]
    orden: int = 0
    notas: dict[str, list[str]] = field(default_factory=dict)


def _orden_habitats(banco: BancoDatos) -> list[str]:
    return PORTADA + [h for h in banco.habitats if h not in PORTADA]


def extraer(banco: BancoDatos | None = None) -> list[Locucion]:
    """Todas las locuciones completas que puede emitir la partida web (catálogo ampliado)."""
    banco = banco or BancoDatos(ampliado=True)
    g = GeneradorRespuestas(banco)
    pt = lambda texto: idiomas.texto(texto, "pt-BR", banco)
    lista: list[Locucion] = []

    def agregar(id, componentes, categoria, tipo, prioridad, contexto, origen, es, pt_br=None):
        lista.append(Locucion(id, componentes, categoria, tipo, prioridad, contexto, origen,
                              {"es": es, "pt-BR": pt_br if pt_br is not None else pt(es)}))

    pregunta = "¿Quién elige el animal?"
    agregar("INTERFAZ_MODALIDAD", "interfaz:¿Quién elige el animal?", "pregunta", "fijo", "P1",
            "Al abrir el selector de modalidad (Comenzar).",
            "codigo/interfaz/servicio.py; datos/traducciones_pt_BR.json#interfaz",
            pregunta, idiomas.PORTUGUES["interfaz"][pregunta])
    # El saludo de "Probar voz" no se graba: en la 5.0 ese botón prueba la voz alternativa;
    # en la 6.0 reproduce la grabación del mensaje que está en pantalla.
    for mid, (categoria, contexto) in FIJOS.items():
        agregar(mid, mid, categoria, "fijo", "P1", contexto, "datos/mensajes_sistema.json",
                g.mensaje(mid, "A01").texto_voz)  # el texto no depende del animal

    apoyo = g.mensaje("MSG_APOYO_AUTO")
    contextos = {}
    for (animal, h), asociacion in banco.asociaciones.items():
        if asociacion["estado"] == "VALIDA" and asociacion["contexto"]:
            contextos.setdefault(h, []).append((animal, asociacion["contexto"]))
    for h in _orden_habitats(banco):
        prioridad = "P1" if h in PORTADA else "P2"
        habitat = banco.habitats[h]
        agregar(f"MSG_VALIDA__{h}", f"MSG_VALIDA+{h}", "confirmacion", "dinamico", prioridad,
                f"Al acertar {h} ({habitat['nombre']}) sin contexto adicional. "
                "También con Repetir y Reanudar.",
                "datos/mensajes_sistema.json#MSG_VALIDA; datos/expedicion/habitats.json#frase_locativa",
                g.mensaje("MSG_VALIDA", "A01", h).texto_voz)
        for nivel in (1, 2, 3):
            pista = banco.pistas_progresivas[(h, nivel)]
            agregar(pista["id"], pista["id"], "pista", "variable", prioridad,
                    f"Al pulsar Pista: nivel {nivel} para un animal de {h}.",
                    "datos/expedicion/pistas.json", g.ayuda(pista, "A01").texto_voz)
            agregar(f"MSG_APOYO_AUTO__{pista['id']}", f"MSG_APOYO_AUTO+{pista['id']}",
                    "apoyo_con_pista", "dinamico", prioridad,
                    f"Al elegir un hábitat no confirmado; sigue la pista nivel {nivel} de {h}.",
                    "datos/mensajes_sistema.json#MSG_APOYO_AUTO; datos/expedicion/pistas.json",
                    g.ayuda(pista, "A01", apoyo).texto_voz)
        for animal, contexto in contextos.get(h, []):
            agregar(f"MSG_VALIDA__{h}__{animal}", f"MSG_VALIDA+{h}+{animal}.secundarios.{h}.contexto",
                    "confirmacion_con_contexto", "dinamico", "P3",
                    f"Al acertar {h} con el animal {animal} ({banco.animales[animal]['nombre']}).",
                    "datos/mensajes_sistema.json#MSG_VALIDA; datos/expedicion/animales.json#secundarios",
                    g.mensaje("MSG_VALIDA", animal, h, contexto).texto_voz)

    # Ayudas breves por rasgo del agente 6.0 (datos/expedicion/atributos_habitats.json).
    # Van al final para que un texto idéntico a una pista ya grabada reutilice esa grabación.
    # El agente solo las usa cuando existen sus dos grabaciones (sola y tras el apoyo).
    for ayuda_id, ayuda in banco.ayudas_rasgo.items():
        guias = ", ".join(sorted(h for h, rasgos in banco.rasgos_habitat.items()
                                 if rasgos.get(ayuda["atributo"], ("",))[0] == ayuda["valor"]))
        plantilla = {"id": ayuda_id, "texto": ayuda["texto"], "pictogramas": ayuda["pictogramas"],
                     "nivel": 1, "variante_id": "RASGO"}
        agregar(ayuda_id, ayuda_id, "pista_rasgo", "variable", "P2",
                f"Agente 6.0, al pulsar Pista: rasgo «{ayuda['atributo']} = {ayuda['valor']}» "
                f"de {guias}.", "datos/expedicion/atributos_habitats.json",
                g.ayuda(plantilla, "A01").texto_voz, ayuda["texto_pt"])
        agregar(f"MSG_APOYO_AUTO__{ayuda_id}", f"MSG_APOYO_AUTO+{ayuda_id}", "apoyo_con_pista_rasgo",
                "dinamico", "P2", f"Agente 6.0, al elegir un hábitat no confirmado; sigue {ayuda_id}.",
                "datos/mensajes_sistema.json#MSG_APOYO_AUTO; datos/expedicion/atributos_habitats.json",
                g.ayuda(plantilla, "A01", apoyo).texto_voz)

    for n, loc in enumerate(lista, 1):
        loc.orden = n
        loc.notas = {i: revisar_pronunciacion(t, i) for i, t in loc.textos.items()}
    return lista


def revisar_pronunciacion(texto: str, idioma: str) -> list[str]:
    """Avisos para la revisión humana. Nunca modifica el texto."""
    notas = []
    if re.search(r"\d", texto):
        notas.append("Contiene cifras: escuchar cómo se leen.")
    if re.search(r"[()/;:\"]|\b[A-Z]{2,}\b", texto):
        notas.append("Signos o siglas que la voz puede leer de forma literal.")
    if "«" in texto:
        notas.append("Comillas «»: no se leen; comprobar que el nombre del hábitat no suene a cita "
                     "ni lleve pausas forzadas.")
    if re.search(r"\b(México|Antártic[oa]|ártica)\b", texto):
        notas.append("Nombre geográfico: comprobar acento y sílaba tónica.")
    if idioma == "es" and ES_PENINSULAR.search(texto):
        notas.append("Posible forma peninsular: revisar para es-419.")
    if idioma == "pt-BR":
        if PT_EUROPEU.search(texto):
            notas.append("Posible forma de pt-PT: revisar para pt-BR.")
        if ENCLISE.search(texto):
            notas.append("Ênclise (-se/-la): correcta, pero formal en pt-BR hablado; "
                         "decidir en revisión humana sin cambiar el texto aquí.")
    if texto.startswith(("¡", "Sim!")):
        notas.append("Exclamación inicial: entonación alegre y breve, sin gritar.")
    if len(re.findall(r"[.!?](\s|$)", texto)) > 1:
        notas.append("Varias oraciones: mantener una pausa breve y natural entre ellas.")
    return notas


def _creditos(caracteres: int, modelo: str) -> float:
    return caracteres * TARIFAS.get(modelo, 1.0)  # modelo desconocido: estimación prudente


def filas(locuciones: list[Locucion], anteriores: dict | None = None) -> list[dict]:
    """Una fila por mensaje e idioma; un texto idéntico se graba una sola vez."""
    anteriores = anteriores or {}
    resultado, primeros = [], {}
    for idioma_juego, idioma in IDIOMAS_GRABACION.items():
        for loc in locuciones:
            texto = loc.textos[idioma_juego]
            canonico = primeros.setdefault((idioma, texto), loc.id)
            duplicado = canonico != loc.id
            previo = anteriores.get((loc.id, idioma), {})
            cambio = bool(previo) and previo.get("texto") != texto
            modelo = previo.get("modelo_elevenlabs") or MODELO_PROPUESTO
            caracteres = len(texto)
            if duplicado:
                estado = "usa_duplicado"
            elif cambio:
                estado = "pendiente"
            else:
                estado = previo.get("estado_generacion", "pendiente")
            resultado.append({
                "orden": loc.orden, "id": loc.id, "idioma": idioma, "texto": texto,
                "categoria": loc.categoria, "tipo_texto": loc.tipo_texto, "prioridad": loc.prioridad,
                "contexto_reproduccion": loc.contexto,
                "voz_elevenlabs": previo.get("voz_elevenlabs", ""),
                "voice_id": previo.get("voice_id", ""),
                "modelo_elevenlabs": modelo,
                "archivo": f"{idioma}/{canonico}.mp3",
                "estado_generacion": estado,
                "caracteres": caracteres,
                "creditos_estimados": 0 if duplicado else _creditos(caracteres, modelo),
                "duplicado_de": canonico if duplicado else "",
                "grabar": "no" if duplicado else "si",
                "componentes_origen": loc.componentes, "origen": loc.origen,
                "nota_pronunciacion": " | ".join(loc.notas[idioma_juego]),
                "revision_humana": "" if cambio else previo.get("revision_humana", ""),
                "observaciones": previo.get("observaciones", ""),
            })
    return resultado


def resumen(tabla: list[dict]) -> dict:
    datos = {"fecha": "2026-11-14", "creditos_por_caracter_web": TARIFAS,
             "margen_repeticiones": MARGEN_REPETICIONES, "por_idioma": {}, "por_prioridad": {}}
    for fila in tabla:
        for grupo, clave in (("por_idioma", fila["idioma"]),
                             ("por_prioridad", f"{fila['prioridad']} {fila['idioma']}")):
            d = datos[grupo].setdefault(clave, {"mensajes": 0, "a_grabar": 0, "duplicados": 0,
                                                "caracteres_a_grabar": 0})
            d["mensajes"] += 1
            if fila["grabar"] == "si":
                d["a_grabar"] += 1
                d["caracteres_a_grabar"] += fila["caracteres"]
            else:
                d["duplicados"] += 1
    for grupo in ("por_idioma", "por_prioridad"):
        for d in datos[grupo].values():
            c = d["caracteres_a_grabar"]
            d["creditos"] = {m: round(c * t) for m, t in TARIFAS.items()}
            d["creditos_con_margen"] = {m: round(c * t * (1 + MARGEN_REPETICIONES))
                                        for m, t in TARIFAS.items()}
    return datos


def leer_csv(ruta: Path = CSV_CATALOGO) -> dict:
    if not ruta.is_file():
        return {}
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return {(r["id"], r["idioma"]): r for r in csv.DictReader(f)}


def escribir(tabla: list[dict], ruta: Path = CSV_CATALOGO, ruta_resumen: Path = RESUMEN) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # BOM para que Excel abra el UTF-8 sin romper tildes.
    with ruta.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(tabla[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(tabla)
    ruta_resumen.write_text(json.dumps(resumen(tabla), ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8", newline="\n")


def verificar_audios(tabla: list[dict], carpeta: Path = CARPETA_AUDIO) -> dict:
    """Compara los audios descargados con los nombres esperados (no reproduce nada)."""
    esperados = {f["archivo"].rsplit(".", 1)[0] for f in tabla if f["grabar"] == "si"}
    presentes = {}
    for ext in EXTENSIONES:
        for archivo in carpeta.glob(f"*/*{ext}"):
            presentes[f"{archivo.parent.name}/{archivo.stem}"] = archivo
    sobran = sorted(str(presentes[k].relative_to(carpeta)) for k in presentes.keys() - esperados)
    pequenos = sorted(k for k in esperados & presentes.keys() if presentes[k].stat().st_size < 1024)
    p1 = {f["archivo"].rsplit(".", 1)[0] for f in tabla if f["grabar"] == "si" and f["prioridad"] == "P1"}
    return {"esperados": len(esperados), "presentes": len(esperados & presentes.keys()),
            "faltan": len(esperados - presentes.keys()), "faltan_p1": sorted(p1 - presentes.keys()),
            "sobran_o_mal_nombrados": sobran, "demasiado_pequenos": pequenos}


PENDIENTES = CARPETA_DOCS / "textos_pendientes_es-419.txt"


def pendientes(tabla: list[dict], idioma: str = "es-419", carpeta: Path = CARPETA_AUDIO) -> list[dict]:
    """Filas que hay que grabar y cuyo audio todavía no está en la carpeta del idioma."""
    return [f for f in tabla if f["idioma"] == idioma and f["grabar"] == "si"
            and not any((carpeta / (f["archivo"].rsplit(".", 1)[0] + ext)).is_file() for ext in EXTENSIONES)]


def escribir_pendientes(filas_pendientes: list[dict], ruta: Path = PENDIENTES) -> None:
    """Lista para grabar: el nombre exacto del MP3 en una línea y el texto en la siguiente."""
    total = sum(f["caracteres"] for f in filas_pendientes)
    cabecera = [
        "# Zoonauta 6.0 · mensajes nuevos pendientes de grabar en español (es-419)",
        "# Voz: Marcela (ElevenLabs), el mismo modelo y ajustes que las 350 grabaciones existentes.",
        "# Generado con: PYTHONUTF8=1 python -m codigo.interfaz.catalogo_voz --pendientes",
        "# Formato: una línea con el nombre exacto del archivo MP3 y, en la siguiente, el texto",
        "# completo que se pronuncia (copiar tal cual). Las líneas que empiezan con # son comentarios.",
        "# Cada audio es el mensaje completo: no partir ni unir audios. Textos redactados con IA a partir",
        "# de pistas revisadas: necesitan revisión humana antes de gastar créditos.",
        "# Al terminar, copiar los MP3 en assets/voz/grabada/es-419/ (ver docs/voz/elevenlabs/README.md).",
        f"# Total: {len(filas_pendientes)} mensajes · {total} caracteres",
        "",
    ]
    cuerpo = []
    for f in filas_pendientes:
        cuerpo += [f["archivo"].split("/", 1)[1], f["texto"], ""]
    ruta.write_text("\n".join(cabecera + cuerpo), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verificar", action="store_true", help="solo comparar con assets/voz/grabada")
    parser.add_argument("--pendientes", action="store_true",
                        help=f"escribir {PENDIENTES.name} con los mensajes es-419 sin grabación")
    args = parser.parse_args()
    tabla = filas(extraer(), leer_csv())
    if args.verificar:
        print(json.dumps(verificar_audios(tabla), ensure_ascii=False, indent=2))
        return
    if args.pendientes:
        lista = pendientes(tabla)
        escribir_pendientes(lista)
        print(f"{len(lista)} mensajes, {sum(f['caracteres'] for f in lista)} caracteres -> {PENDIENTES}")
        return
    escribir(tabla)
    print(json.dumps(resumen(tabla)["por_idioma"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
