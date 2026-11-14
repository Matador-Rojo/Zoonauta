"""Entrenamiento del agente 6.0 fuera de la partida, y su análisis con jugadores simulados.

Un único camino de datos para sesiones reales y simuladas:

    registro de la partida (JSONL) → etiquetas() → ModeloAyudas.actualizar() → modelo congelado

Usos:

    # Con registros de partidas reales (p. ej. sesiones con educadores de Kallpa):
    PYTHONUTF8=1 python -m codigo.entrenamiento.entrenar_agente6 entrenar \\
        --registros registros/interfaz --salida resultados_nuevos/modelo_sesiones.json

    # Experimento con jugadores SIMULADOS (entrenamiento, convergencia y evaluación congelada):
    PYTHONUTF8=1 python -m codigo.entrenamiento.entrenar_agente6 simular \\
        --salida docs/experimentos/agente6/aprendizaje

El jugador simulado tiene unas probabilidades «plantadas» por tipo de ayuda que el agente
no conoce (tres condiciones). El experimento mide si el modelo las recupera y cómo cambia la
guía. Son datos sintéticos: no describen a personas reales.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from statistics import mean

from codigo.motores.agente import MotorAgente, MotorID3Opciones
from codigo.motores.aprendizaje6 import CLAVES, ModeloAyudas, MotorAgenteAprendido
from codigo.motores.guia import MotorPistas
from codigo.nucleo.datos import BancoDatos
from codigo.nucleo.gestor import GestorPartida
from codigo.nucleo.registro import Registro

# Recompensa: evento que cierra la observación de una ayuda → resultado.
# El gestor marca SELECCION_PENDIENTE como «sin etiqueta» (protocolo del catálogo original, que
# no castigaba una relación desconocida). Para el agente 6.0 se propuso, y el propietario
# aceptó el 2026-11-14, contarla como 0: «la ayuda no llevó a una respuesta confirmada», nunca como
# «hábitat incorrecto». En el catálogo ampliado no existe SELECCION_INCORRECTA_VALIDADA.
RECOMPENSA = {"SELECCION_VALIDA": 1, "NUEVA_AYUDA": 0, "SELECCION_PENDIENTE": 0, "SALIDA": None}
ORIGEN_SIMULADO = "SIMULACION_ENTRENAMIENTO_AGENTE6"
CANTIDADES = (2, 4, 8)
MAX_ACCIONES = 10


def etiquetas(filas: list[dict], version: str | None = None) -> list[dict]:
    """Empareja cada ayuda presentada con su cierre y aplica la recompensa.

    Se descartan las ayudas sin tipo (p. ej. «Señala…» o motores sin clave), las cerradas
    sin resultado (salir) y, si se indica ``version`` (huellas de rasgos y pistas), las
    jugadas con otros datos. La clave se fija al presentar la ayuda: si después se pulsa
    Repetir, la señal de dificultad no se añade a esa ayuda (límite documentado).
    """
    claves = {}
    salida = []
    for fila in filas:
        if fila.get("tipo_registro") == "AYUDA_PRESENTADA":
            if version and not str(fila.get("modelo_version", "")).startswith(version):
                continue
            claves[fila["observacion_id"]] = (fila.get("decision") or {}).get("clave_aprendizaje")
        elif fila.get("tipo_registro") == "OBSERVACION_CERRADA":
            clave = claves.pop(fila["observacion_id"], None)
            resultado = RECOMPENSA.get(fila.get("evento_cierre"))
            if clave in CLAVES and resultado is not None:
                salida.append({"observacion_id": fila["observacion_id"], "clave": clave,
                               "resultado": resultado, "origen": fila.get("origen")})
    return salida


def leer_registros(carpeta: Path) -> list[dict]:
    filas = []
    for archivo in sorted(Path(carpeta).glob("*.jsonl")):
        with archivo.open(encoding="utf-8") as h:
            filas += [json.loads(linea) for linea in h if linea.strip()]
    return filas


# ---------------------------------------------------------------- jugador simulado ----

CONDICIONES = {
    # Las ideas de más pesan mucho; tipo de frase indiferente.
    "IDEAS": {"ideas_2": -0.20, "RASGO": 0.00, "PISTA": 0.00},
    # Las frases breves por rasgo se entienden mejor que las pistas editadas.
    "RASGOS": {"ideas_2": -0.05, "RASGO": 0.10, "PISTA": -0.10},
    # Las pistas editadas se entienden mejor que las frases por rasgo.
    "PISTAS": {"ideas_2": 0.00, "RASGO": -0.15, "PISTA": 0.10},
}
BASE_INFORMA = {"documentado": 0.70, "sin_comprobar": 0.50, "ninguno": 0.30}
AJUSTE_OPCIONES = {"2": 0.10, "4": 0.00, "8": -0.10}
AJUSTE_DIFICULTAD = -0.15
ACIERTA_TRAS_SENALAR = 0.95
ACIERTA_SIN_AYUDA = 0.20
PIDE_PISTA_PRIMERO = 0.5
PIDE_OTRA_SI_NO_ACIERTA = 0.5


def probabilidad_plantada(condicion: str, clave: str) -> float:
    """P(la siguiente acción es un hábitat confirmado | tipo de ayuda): inventada, oculta al agente."""
    tipo, ideas, opciones, dificultad, informa = clave.split("|")
    c = CONDICIONES[condicion]
    q = (BASE_INFORMA[informa] + AJUSTE_OPCIONES[opciones] + c[tipo]
         + (c["ideas_2"] if ideas == "2+" else 0.0) + (AJUSTE_DIFICULTAD if dificultad == "1" else 0.0))
    return min(0.95, max(0.05, q))


def clave_mostrada(evaluador: MotorAgente, banco, s, tras_eleccion: bool) -> str | None:
    """Tipo de la última ayuda mostrada, calculado igual que el agente (sirve para cualquier política)."""
    g = s.habitat_guia_id
    mostrada = s.ayudas_reto[-1]["contenido_id"]
    cand = next((c for c in evaluador.rep._candidatas[g] if c.id == mostrada), None)
    if cand is None:
        return None  # «Señala el hábitat…»
    confirmados = set(banco.animales[s.animal_id]["habitats_confirmados"])
    pendientes = [e["habitat_id"] for e in s.elecciones_reto if e["resultado"] != "VALIDA"]
    restantes = [o for o in s.opciones_habitat if o not in pendientes]
    distractores = [o for o in restantes if o not in confirmados]
    validas = [o for o in restantes if o in confirmados]
    ultima = pendientes[-1] if pendientes and tras_eleccion else None
    previas = {a["contenido_id"] for a in s.ayudas_reto[:-1]}
    ya = [c for c in evaluador.rep._candidatas[g] if c.id in previas]
    no_entendida = bool(ultima and any(evaluador.rep.relacion(c, ultima) == "conflicto" for c in ya))
    dificultad = bool(s.repeticion_previa) or no_entendida
    contexto = {"habitat_guia_id": g, "opciones": list(s.opciones_habitat)}
    return evaluador.evaluar(cand, contexto, restantes, distractores, validas, ultima, dificultad,
                             pendientes)["clave_aprendizaje"]


def jugar_reto(banco, motor, animal: str, k: int, condicion: str, azar: Random,
               registro: Registro, evaluador: MotorAgente) -> dict:
    g = GestorPartida(banco, 1, motor=motor, ayuda_en_pendiente=True, traza_completa=False,
                      semilla_opciones=0, origen=ORIGEN_SIMULADO, registro=registro)
    g.procesar(g.crear_evento("iniciar", modalidad="JUGADOR", cantidad_opciones=k))
    g.procesar(g.crear_evento("elegir_animal", animal_id=animal))
    g.avanzar_preparacion()
    s = g.estado
    confirmadas = [o for o in s.opciones_habitat if o in banco.animales[animal]["habitats_confirmados"]]
    acciones = ayudas = 0
    ultima = None  # (es «Señala», tipo de ayuda) de la última ayuda vista
    while s.fase == "ESPERANDO_RESPUESTA" and acciones < MAX_ACCIONES:
        acciones += 1
        elegidas = {e["habitat_id"] for e in s.elecciones_reto}
        otras = [o for o in s.opciones_habitat if o not in confirmadas and o not in elegidas]
        if ultima is None:
            pedir = azar.random() < PIDE_PISTA_PRIMERO
            acierta = not pedir and azar.random() < ACIERTA_SIN_AYUDA
        else:
            senala, clave = ultima
            q = ACIERTA_TRAS_SENALAR if senala or clave is None else probabilidad_plantada(condicion, clave)
            acierta = azar.random() < q
            pedir = not acierta and (not otras or azar.random() < PIDE_OTRA_SI_NO_ACIERTA)
        if pedir:
            salida = g.procesar(g.crear_evento("ayuda"))
        else:
            eleccion = azar.choice(confirmadas) if (acierta or not otras) else azar.choice(otras)
            salida = g.procesar(g.crear_evento("seleccionar_habitat", habitat_id=eleccion))
        if salida.traza:
            ultima = (s.nivel == 3, clave_mostrada(evaluador, banco, s, not pedir))
            ayudas += 1
    return {"resuelto": int(s.fase == "RETO_RESUELTO"), "acciones": acciones, "ayudas": ayudas,
            "elecciones_no_confirmadas": sum(e["resultado"] != "VALIDA" for e in s.elecciones_reto),
            "senalo": int(any(a["nivel"] == 3 for a in s.ayudas_reto))}


def error_frente_a_plantadas(modelo: ModeloAyudas, condicion: str) -> dict:
    vistas = [c for c in CLAVES if modelo.parametros[c]["n"] > 0]
    n = sum(modelo.parametros[c]["n"] for c in vistas)
    ponderado = sum(modelo.parametros[c]["n"] * abs(modelo.media(c) - probabilidad_plantada(condicion, c))
                    for c in vistas) / n if n else None
    suficientes = [c for c in vistas if modelo.parametros[c]["n"] >= 30]
    return {"error_medio_ponderado": round(ponderado, 4) if ponderado is not None else None,
            "error_medio_tipos_con_30_o_mas": round(mean(abs(modelo.media(c) - probabilidad_plantada(condicion, c))
                                                         for c in suficientes), 4) if suficientes else None,
            "tipos_vistos": len(vistas), "tipos_con_30_o_mas": len(suficientes), "observaciones": n}


def retos(banco, pasadas: int, semilla: int) -> list[tuple[str, int]]:
    lista = [(a, k) for _ in range(pasadas) for a in banco.animales for k in CANTIDADES]
    Random(semilla).shuffle(lista)
    return lista


def entrenar_simulado(banco, condicion: str, replica: int, pasadas: int, cada: int) -> tuple[ModeloAyudas, list]:
    semilla = 1000 * (list(CONDICIONES).index(condicion) + 1) + replica
    modelo = ModeloAyudas.nuevo(banco, ORIGEN_SIMULADO, {
        "condicion": condicion, "replica": replica, "semilla_entrenamiento": semilla,
        "aviso": "Entrenado con jugadores SIMULADOS de probabilidades inventadas; no con personas."})
    motor = MotorAgenteAprendido(banco, modelo, azar=Random(semilla + 250_000), solo_grabadas=False)
    azar = Random(semilla + 500_000)
    curva = []
    for i, (animal, k) in enumerate(retos(banco, pasadas, semilla), 1):
        registro = Registro()
        jugar_reto(banco, motor, animal, k, condicion, azar, registro, motor)
        for e in etiquetas(registro.filas):
            modelo.actualizar(e["clave"], e["resultado"])
        if i % cada == 0:
            curva.append({"retos": i, **error_frente_a_plantadas(modelo, condicion)})
    return modelo, curva


def evaluar(banco, motores: dict, condicion: str, replica: int, evaluador: MotorAgente) -> dict:
    """Modelos congelados y semillas distintas de las de entrenamiento."""
    resultado = {}
    semilla = 9_000_000 + 1000 * (list(CONDICIONES).index(condicion) + 1) + replica
    for nombre, motor in motores.items():
        filas = defaultdict(list)
        for animal, k in retos(banco, 1, semilla):
            # Misma semilla por reto para todas las políticas (números aleatorios comunes).
            azar = Random(f"{semilla}:{animal}:{k}")
            filas[k].append(jugar_reto(banco, motor, animal, k, condicion, azar, Registro(), evaluador))
        resultado[nombre] = {str(k): {
            "retos": len(f), "tasa_exito": round(mean(x["resuelto"] for x in f), 4),
            "tasa_exito_sin_senalar": round(mean(x["resuelto"] and not x["senalo"] for x in f), 4),
            "acciones_medias": round(mean(x["acciones"] for x in f), 4),
            "ayudas_medias": round(mean(x["ayudas"] for x in f), 4),
            "elecciones_no_confirmadas_medias": round(mean(x["elecciones_no_confirmadas"] for x in f), 4),
            "llego_a_senalar": round(mean(x["senalo"] for x in f), 4)} for k, f in sorted(filas.items())}
    return resultado


def simular(salida: Path, replicas: int, pasadas: int, cada: int) -> dict:
    banco = BancoDatos(ampliado=True)
    salida.mkdir(parents=True, exist_ok=True)
    documento = {
        "fecha": "2026-11-14",
        "aviso": ("Datos SIMULADOS. Las probabilidades del jugador están inventadas (plantadas) y el "
                  "agente no las conoce; el experimento mide si el modelo las recupera y cómo cambia la "
                  "guía. No son resultados de personas ni de sesiones de Kallpa."),
        "recompensa": RECOMPENSA,
        "condiciones": CONDICIONES, "base_por_informacion": BASE_INFORMA,
        "ajuste_por_opciones": AJUSTE_OPCIONES, "ajuste_por_dificultad": AJUSTE_DIFICULTAD,
        "jugador": {"acierta_sin_ayuda": ACIERTA_SIN_AYUDA, "pide_pista_primero": PIDE_PISTA_PRIMERO,
                    "pide_otra_si_no_acierta": PIDE_OTRA_SI_NO_ACIERTA,
                    "acierta_tras_senalar": ACIERTA_TRAS_SENALAR, "max_acciones": MAX_ACCIONES},
        "protocolo": {"replicas": replicas, "pasadas_entrenamiento": pasadas,
                      "retos_entrenamiento_por_modelo": pasadas * len(banco.animales) * len(CANTIDADES),
                      "retos_evaluacion_por_politica": len(banco.animales) * len(CANTIDADES),
                      "ayudas": "las 32 ayudas por rasgo activas (estado futuro con todas las grabaciones)"},
        "entrenamiento": {}, "evaluacion": {},
    }
    fijo = MotorAgente(banco, solo_grabadas=False)
    base = {"PISTAS_PROGRESIVAS": MotorPistas(banco), "ID3_OPCIONES": MotorID3Opciones(banco, solo_grabadas=False),
            "AGENTE_ADAPTATIVO": fijo}
    for condicion in CONDICIONES:
        for replica in range(1, replicas + 1):
            nombre = f"{condicion}_R{replica:02d}"
            modelo, curva = entrenar_simulado(banco, condicion, replica, pasadas, cada)
            modelo.guardar(salida / "modelos" / f"{nombre}.json")
            documento["entrenamiento"][nombre] = {
                "curva": curva, "final": error_frente_a_plantadas(modelo, condicion),
                "variacion_ultimos_tramos": [round(abs(a["error_medio_ponderado"] - b["error_medio_ponderado"]), 4)
                                             for a, b in zip(curva[-4:-1], curva[-3:], strict=True)]}
            congelado = MotorAgenteAprendido(banco, modelo, solo_grabadas=False)
            documento["evaluacion"][nombre] = evaluar(banco, {**base, "AGENTE_APRENDIDO": congelado},
                                                      condicion, replica, fijo)
            print(nombre, documento["entrenamiento"][nombre]["final"], flush=True)
    (salida / "experimento.json").write_text(json.dumps(documento, ensure_ascii=False, indent=1) + "\n",
                                             encoding="utf-8", newline="\n")
    return documento


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="orden", required=True)
    e = sub.add_parser("entrenar", help="entrenar con registros JSONL de partidas")
    e.add_argument("--registros", type=Path, required=True)
    e.add_argument("--salida", type=Path, required=True)
    s = sub.add_parser("simular", help="experimento con jugadores simulados")
    s.add_argument("--salida", type=Path, required=True)
    s.add_argument("--replicas", type=int, default=3)
    s.add_argument("--pasadas", type=int, default=5, help="vueltas a los 288 animales × 3 tamaños")
    s.add_argument("--cada", type=int, default=144, help="retos entre puntos de la curva")
    args = parser.parse_args()
    if args.orden == "entrenar":
        banco = BancoDatos(ampliado=True)
        huellas = banco.huellas
        version = f"{huellas['expedicion/atributos_habitats.json']}:{huellas['expedicion/pistas.json']}"
        filas = leer_registros(args.registros)
        lista = etiquetas(filas, version)
        descartadas = len(etiquetas(filas)) - len(lista)
        modelo = ModeloAyudas.nuevo(banco, "SESIONES_REGISTRADAS", {
            "registros": str(args.registros), "observaciones": len(lista),
            "descartadas_por_otra_version_de_datos": descartadas,
            "origenes": dict(Counter(x["origen"] for x in lista)),
            "aviso": "Revisar quién jugó estas sesiones antes de usar el modelo."})
        for x in lista:
            modelo.actualizar(x["clave"], x["resultado"])
        modelo.guardar(args.salida)
        print(json.dumps({"observaciones": len(lista), "descartadas_por_otra_version": descartadas,
                          "modelo": str(args.salida)}, ensure_ascii=False))
    else:
        simular(args.salida, args.replicas, args.pasadas, args.cada)


if __name__ == "__main__":
    main()
