"""Evaluación reproducible del agente de la 6.0 con el catálogo ampliado.

Dos partes, ambas con el gestor real de la partida (``GestorPartida``):

1. **Estructural y exhaustiva** (sin jugador simulado): los 288 animales con 2, 4 y 8
   opciones. Mide qué ayuda daría cada política al pedir la primera pista y después de
   elegir cada hábitat no confirmado, y comprueba que ninguna ayuda sea incompatible.
2. **Jugador sintético** (datos simulados, no personas): tres perfiles con parámetros
   inventados y documentados. Sirve para comparar políticas en igualdad de condiciones
   (mismos sorteos), no para predecir lo que hará una persona real.

Nada se aprende: los parámetros del agente son fijos. Uso:

    PYTHONUTF8=1 python -m codigo.entrenamiento.evaluar_agente6 --salida docs/experimentos/agente6
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from codigo.motores.agente import MotorAgente, MotorID3Opciones, Representacion
from codigo.motores.guia import MotorPistas
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.gestor import GestorPartida

CANTIDADES = (2, 4, 8)

# Perfiles del jugador sintético: valores elegidos a mano para cubrir desde quien casi no
# necesita ayuda hasta quien necesita mucha. NO proceden de observar a personas.
PERFILES = {
    "autonomo": {"acierta_sin_ayuda": 0.40, "entiende_una_idea": 0.95, "pide_pista": 0.30},
    "apoyo_medio": {"acierta_sin_ayuda": 0.25, "entiende_una_idea": 0.80, "pide_pista": 0.50},
    "apoyo_alto": {"acierta_sin_ayuda": 0.10, "entiende_una_idea": 0.60, "pide_pista": 0.70},
}
CAIDA_POR_IDEA = 0.85     # cada idea extra de la frase reduce la probabilidad de entenderla
USA_PROPIA = 0.5          # una diferencia no documentada sí la usa una persona a veces
USA_PARCIAL = 0.25
ACIERTA_TRAS_SENALAR = 0.95
MAX_ACCIONES = 14


def politicas(banco: BancoDatos) -> dict:
    """Las cinco variantes comparadas; «grabadas» = solo ayudas con grabación hoy."""
    return {
        "PISTAS_PROGRESIVAS": MotorPistas(banco),
        "ID3_OPCIONES_grabadas": MotorID3Opciones(banco, solo_grabadas=True),
        "ID3_OPCIONES_todas": MotorID3Opciones(banco, solo_grabadas=False),
        "AGENTE_grabadas": MotorAgente(banco, solo_grabadas=True),
        "AGENTE_todas": MotorAgente(banco, solo_grabadas=False),
    }


def _gestor(banco, motor, animal, k):
    g = GestorPartida(banco, 1, motor=motor, ayuda_en_pendiente=True, traza_completa=False,
                      semilla_opciones=0, origen="EVALUACION_AGENTE6")
    g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=k))
    g.procesar(g.crear_evento("elegir_animal", animal_id=animal))
    g.avanzar_preparacion()
    return g


def _candidata(rep: Representacion, guia: str, contenido_id: str):
    for c in [*rep._candidatas[guia], rep.senalar(guia)]:
        if c.id == contenido_id:
            return c
    return None


def compatible(rep: Representacion, banco: BancoDatos, gestor: GestorPartida, contenido_id: str) -> bool:
    """La ayuda habla del hábitat guía visible y solo afirma rasgos documentados de él."""
    s = gestor.estado
    c = _candidata(rep, s.habitat_guia_id, contenido_id)
    if c is None or s.habitat_guia_id not in s.opciones_habitat:
        return False
    if c.tipo == "SENALAR":
        return c.plantilla["habitat_guia_id"] == s.habitat_guia_id
    documentados = {a: v for a, (v, _) in banco.rasgos_habitat[s.habitat_guia_id].items()}
    return all(documentados.get(a) == v for a, v in c.rasgos.items())


def estructural(banco: BancoDatos, motores: dict) -> dict:
    rep = Representacion(banco)
    resultado = {}
    for nombre, motor in motores.items():
        por_k = {}
        for k in CANTIDADES:
            c = Counter()
            ideas = []
            for animal, ficha in banco.animales.items():
                g = _gestor(banco, motor, animal, k)
                guia = g.estado.habitat_guia_id
                confirmados = set(ficha["habitats_confirmados"])
                distractores = [o for o in g.estado.opciones_habitat if o not in confirmados]
                validas = [o for o in g.estado.opciones_habitat if o in confirmados and o != guia]
                # Primera pista sin elecciones previas.
                r = g.procesar(g.crear_evento("ayuda")).respuesta
                cand = _candidata(rep, guia, r.contenido_id)
                c["retos"] += 1
                c["incompatibles"] += not compatible(rep, banco, g, r.contenido_id)
                c["primera_senala"] += cand.tipo == "SENALAR"
                ideas.append(len(cand.conceptos))
                c["primera_aleja_de_valida"] += any(rep.relacion(cand, v) == "conflicto" for v in validas)
                if distractores:
                    c["retos_con_distractores"] += 1
                    rel = [rep.relacion(cand, d) for d in distractores] if cand.tipo != "SENALAR" else []
                    c["primera_descarta_documentado"] += "conflicto" in rel
                    c["primera_sin_valor"] += bool(rel) and all(x == "compartida" for x in rel)
                    c["distractores"] += len(distractores)
                    c["distractores_descartados_primera"] += rel.count("conflicto")
                # Tras elegir cada hábitat no confirmado como primera acción.
                for d in distractores:
                    g = _gestor(banco, motor, animal, k)
                    r = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=d)).respuesta
                    cand = _candidata(rep, guia, r.contenido_id)
                    c["tras_eleccion"] += 1
                    c["incompatibles"] += not compatible(rep, banco, g, r.contenido_id)
                    if cand.tipo == "SENALAR":
                        c["tras_eleccion_senala"] += 1
                        continue
                    rel = rep.relacion(cand, d)
                    c["tras_eleccion_distingue_documentado"] += rel == "conflicto"
                    c["tras_eleccion_describe_lo_elegido"] += rel in ("compartida", "parcial")
            por_k[str(k)] = {
                **dict(c),
                "ideas_media_primera": round(mean(ideas), 3),
                "tasa_primera_descarta_documentado": _tasa(c["primera_descarta_documentado"], c["retos_con_distractores"]),
                "tasa_primera_sin_valor": _tasa(c["primera_sin_valor"], c["retos_con_distractores"]),
                "fraccion_distractores_descartados_primera": _tasa(c["distractores_descartados_primera"], c["distractores"]),
                "tasa_tras_eleccion_distingue_documentado": _tasa(c["tras_eleccion_distingue_documentado"], c["tras_eleccion"]),
                "tasa_tras_eleccion_describe_lo_elegido": _tasa(c["tras_eleccion_describe_lo_elegido"], c["tras_eleccion"]),
                "tasa_tras_eleccion_senala": _tasa(c["tras_eleccion_senala"], c["tras_eleccion"]),
            }
        resultado[nombre] = por_k
    return resultado


def _tasa(a, b):
    return round(a / b, 4) if b else None


def _u(*clave) -> float:
    """Sorteo determinista: todas las políticas comparten los mismos números aleatorios."""
    h = hashlib.blake2b(json.dumps(clave, separators=(",", ":")).encode(), digest_size=8).digest()
    return (int.from_bytes(h, "big") >> 11) / (1 << 53)


def simular_reto(banco, rep, motor, animal, k, perfil, replica):
    p = PERFILES[perfil]
    g = _gestor(banco, motor, animal, k)
    s = g.estado
    guia = s.habitat_guia_id
    confirmados = set(banco.animales[animal]["habitats_confirmados"])
    posibles = list(s.opciones_habitat)       # lo que la persona aún considera
    m = Counter()
    clave = (replica, animal, k, perfil)
    senalado = False
    for paso in range(MAX_ACCIONES):
        if s.fase != "ESPERANDO_RESPUESTA":
            break
        validas = [o for o in posibles if o in confirmados]
        if not senalado and _u(*clave, paso, "pide") < p["pide_pista"]:
            respuesta = g.procesar(g.crear_evento("ayuda")).respuesta
            m["ayudas"] += 1
        else:
            if senalado and _u(*clave, paso, "senalado") < ACIERTA_TRAS_SENALAR:
                eleccion = guia
            elif validas and _u(*clave, paso, "acierta") < p["acierta_sin_ayuda"]:
                eleccion = sorted(validas)[int(_u(*clave, paso, "cual") * len(validas))]
            else:
                eleccion = sorted(posibles)[int(_u(*clave, paso, "azar") * len(posibles))]
            salida = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=eleccion))
            if s.fase == "RETO_RESUELTO":
                m["resuelto"] = 1
                break
            m["elecciones_no_confirmadas"] += 1
            if eleccion in posibles and len(posibles) > 1:
                posibles.remove(eleccion)
            respuesta = salida.respuesta
            m["ayudas"] += 1
        cand = _candidata(rep, guia, respuesta.contenido_id)
        m["ideas"] += len(cand.conceptos)
        if cand.tipo == "SENALAR":
            senalado = True
            m["llego_a_senalar"] = 1
            continue
        entiende = p["entiende_una_idea"] * CAIDA_POR_IDEA ** (len(cand.conceptos) - 1)
        if _u(*clave, paso, "entiende") >= entiende:
            continue
        for o in list(posibles):
            if o == guia or len(posibles) == 1:
                continue
            rel = rep.relacion(cand, o)
            umbral = {"conflicto": 1.0, "propia": USA_PROPIA, "parcial": USA_PARCIAL}.get(rel, 0.0)
            if _u(*clave, paso, "descarta", o) < umbral:
                posibles.remove(o)
                m["descartes_de_validas"] += o in confirmados
    return m


def sintetico(banco, motores, replicas):
    rep = Representacion(banco)
    resultado = {}
    for nombre, motor in motores.items():
        acumulado = defaultdict(list)
        for perfil in PERFILES:
            for k in CANTIDADES:
                filas = [simular_reto(banco, rep, motor, a, k, perfil, r)
                         for r in range(replicas) for a in banco.animales]
                ayudas = sum(f["ayudas"] for f in filas)
                acumulado[perfil].append({
                    "cantidad_opciones": k, "retos": len(filas),
                    "resueltos": _tasa(sum(f["resuelto"] for f in filas), len(filas)),
                    "elecciones_no_confirmadas_media": round(mean(f["elecciones_no_confirmadas"] for f in filas), 4),
                    "ayudas_media": round(mean(f["ayudas"] for f in filas), 4),
                    "llego_a_senalar": _tasa(sum(f["llego_a_senalar"] for f in filas), len(filas)),
                    "ideas_por_ayuda": round(sum(f["ideas"] for f in filas) / ayudas, 4) if ayudas else None,
                })
        resultado[nombre] = dict(acumulado)
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--replicas", type=int, default=5)
    args = parser.parse_args()
    banco = BancoDatos(ampliado=True)
    motores = politicas(banco)
    documento = {
        "fecha": "2026-11-14",
        "aviso": ("Parte estructural: exhaustiva y determinista, sin personas. Parte sintética: jugador "
                  "simulado con parámetros inventados; no son resultados de usuarios reales. El jugador "
                  "simulado usa la misma representación de rasgos que el agente, lo que favorece a las "
                  "políticas que la usan. Ningún parámetro se aprendió de datos."),
        "versiones": {"atributos": banco.huellas["expedicion/atributos_habitats.json"],
                      "pistas": banco.huellas["expedicion/pistas.json"]},
        "ayudas_por_rasgo_con_grabacion": sorted(motores["AGENTE_grabadas"].rep.ayudas_activas),
        "perfiles_sinteticos": PERFILES,
        "supuestos_sinteticos": {"caida_por_idea": CAIDA_POR_IDEA, "usa_diferencia_no_documentada": USA_PROPIA,
                                 "usa_diferencia_parcial": USA_PARCIAL, "acierta_tras_senalar": ACIERTA_TRAS_SENALAR,
                                 "replicas": args.replicas},
        "estructural": estructural(banco, motores),
        "sintetico": sintetico(banco, motores, args.replicas),
    }
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "evaluacion.json").write_text(json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
                                                 encoding="utf-8", newline="\n")
    print(json.dumps({n: {k: {x: v[x] for x in ("tasa_primera_descarta_documentado", "tasa_primera_sin_valor",
                                                 "tasa_tras_eleccion_distingue_documentado",
                                                 "tasa_tras_eleccion_describe_lo_elegido", "incompatibles")}
                          for k, v in por_k.items()} for n, por_k in documento["estructural"].items()},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
