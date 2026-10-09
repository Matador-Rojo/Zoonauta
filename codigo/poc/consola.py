"""Interacción textual con el mismo gestor que utilizará la interfaz digital."""
from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from codigo.motores.guia import POLITICAS, MotorGuia
from codigo.nucleo.datos import BancoDatos, DATOS_PREDETERMINADOS, ErrorDatos
from codigo.nucleo.estado import TERMINALES
from codigo.nucleo.gestor import GestorPartida
from codigo.nucleo.registro import Registro


def normalizar_id(texto: str, prefijo: str) -> str:
    texto = texto.strip().upper()
    if texto.isdigit():
        return f"{prefijo}{int(texto):02d}"
    if texto.startswith(prefijo) and texto[1:].isdigit():
        return f"{prefijo}{int(texto[1:]):02d}"
    return texto


def mostrar_respuesta(respuesta, banco: BancoDatos, simbolos: bool) -> None:
    if respuesta is None:
        return
    print("\n" + respuesta.texto_apoyo)
    if simbolos:
        # Vista de inspección de la PoC; no representa archivos de imagen.
        etiquetas = [f"{p} ({banco.pictogramas[p]['etiqueta']})" for p in respuesta.pictogramas]
        print("Secuencia simbólica: " + " | ".join(etiquetas))


def mostrar_catalogo(gestor: GestorPartida) -> None:
    print("\nAnimales disponibles:")
    for animal in gestor.vista()["catalogo_animales"]:
        print(f"  {animal['id']}: {animal['nombre']}")


def preguntar_modalidad() -> str:
    while True:
        opcion = input("¿Quién inicia? 1: jugador; 2: agente. > ").strip().upper()
        if opcion in {"1", "JUGADOR"}:
            return "JUGADOR"
        if opcion in {"2", "AGENTE"}:
            return "AGENTE"
        print("Elige 1 o 2.")


def interactuar(gestor: GestorPartida, modalidad: str, *, simbolos: bool = False) -> None:
    banco = gestor.banco
    print("\nAnimales y hábitats — prueba de concepto en texto")
    print("Puedes pedir ayuda, repetir el mensaje, pausar o salir cuando lo necesites.")
    mostrar_respuesta(gestor.procesar(gestor.crear_evento("iniciar", modalidad=modalidad)).respuesta,
                       banco, simbolos)
    aliases = {"a": "ayuda", "ayuda": "ayuda", "r": "repetir", "repetir": "repetir",
               "p": "pausar", "pausa": "pausar", "pausar": "pausar", "c": "continuar",
               "continuar": "continuar", "s": "salir", "salir": "salir",
               "reanudar": "reanudar", "volver": "reanudar"}
    try:
        while gestor.estado.fase not in TERMINALES:
            for salida in gestor.avanzar_preparacion():
                mostrar_respuesta(salida.respuesta, banco, simbolos)
            vista = gestor.vista()
            fase = vista["fase"]
            if fase == "SELECCION_ANIMAL":
                mostrar_catalogo(gestor)
                entrada = input("\nElige un animal por número o ID; también puedes pausar o salir. > ")
                tipo = aliases.get(entrada.strip().lower())
                evento = (gestor.crear_evento(tipo) if tipo else
                          gestor.crear_evento("elegir_animal", animal_id=normalizar_id(entrada, "A")))
            elif fase == "ESPERANDO_RESPUESTA":
                print(f"\nAnimal: {vista['animal']['nombre']}")
                for habitat in vista["opciones_habitat"]:
                    print(f"  {habitat['id']}: {habitat['nombre']}")
                entrada = input("Hábitat por número o ID; ayuda / repetir / pausar / salir. > ")
                tipo = aliases.get(entrada.strip().lower())
                evento = (gestor.crear_evento(tipo) if tipo else
                          gestor.crear_evento("seleccionar_habitat", habitat_id=normalizar_id(entrada, "H")))
            elif fase == "RETO_RESUELTO":
                p = vista["progreso"]
                print(f"\nRetos completados: {p['completados']} de {p['total']}.")
                entrada = input("continuar / repetir / pausar / salir. > ")
                evento = gestor.crear_evento(aliases.get(entrada.strip().lower(), "desconocida"))
            elif fase == "PAUSADA":
                entrada = input("Partida en pausa: reanudar / salir. > ")
                evento = gestor.crear_evento(aliases.get(entrada.strip().lower(), "desconocida"))
            else:
                raise RuntimeError(f"Fase inesperada en la consola: {fase}.")
            salida = gestor.procesar(evento)
            if salida.aceptada:
                mostrar_respuesta(salida.respuesta, banco, simbolos)
            else:
                print("Esa entrada no está disponible ahora. Usa una de las opciones indicadas.")
    except (EOFError, KeyboardInterrupt):
        if gestor.estado.fase not in TERMINALES:
            salida = gestor.procesar(gestor.crear_evento("salir"))
            mostrar_respuesta(salida.respuesta, banco, simbolos)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=DATOS_PREDETERMINADOS)
    parser.add_argument("--modalidad", choices=("JUGADOR", "AGENTE"))
    parser.add_argument("--retos", type=int, help="Entre 1 y 48; valor inicial editable: 8.")
    parser.add_argument("--politica", choices=POLITICAS, default="ID3")
    parser.add_argument("--simbolos", action="store_true", help="Inspeccionar IDs y etiquetas simbólicas.")
    parser.add_argument("--registro", type=Path, help="Ruta opcional del registro JSONL.")
    parser.add_argument("--parametros", type=Path, help="Modelo aprendido que se usará congelado.")
    args = parser.parse_args()
    try:
        banco = BancoDatos(args.datos)
        sesion_id = f"CONSOLA-{uuid4().hex}"
        ruta_registro = args.registro or banco.directorio / "registros" / f"{sesion_id}.jsonl"
        gestor = GestorPartida(banco, args.retos, args.politica,
                               sesion_id=sesion_id, registro=Registro(ruta_registro),
                               motor=MotorGuia(banco, args.politica, args.parametros))
        try:
            modalidad = args.modalidad or preguntar_modalidad()
        except (EOFError, KeyboardInterrupt):
            gestor.procesar(gestor.crear_evento("salir"))
            print("\nLa partida ha terminado.")
            return
        interactuar(gestor, modalidad, simbolos=args.simbolos)
    except (ErrorDatos, ValueError, OSError) as exc:
        parser.exit(2, f"No se pudo iniciar la PoC: {exc}\n")


if __name__ == "__main__":
    main()

