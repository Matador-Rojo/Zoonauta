# Contrato de identidad visual — Zoonauta 6.0

Lo que no se puede quitar ni empeorar sin avisar. Se revisa en cada cambio visual con
`python -m tests.comparar_versiones` (5.0 a la izquierda, 6.0 a la derecha).

## Identidad del propietario (manda sobre cualquier guía genérica)

- Fondo oscuro verdoso (`#091713`), acento lima (`#d2ee8b`), titular grande y LIGERO.
- Tipografía de la 5.0: sans neutra, titulares en peso ligero.
- Logo y robot sin cambios; ilustraciones y pictogramas sin sustituir.

## Rasgos de la 5.0 que deben conservarse o mejorarse

- Pista, Repetir, Pausar, Reanudar, Salir; búsqueda y paginación; 2/4/8 opciones.
- Yo elijo / El agente elige; guía con pictogramas; contador «N de 8 completados».
- Rótulos pequeños sobre el titular («ENCUENTRA SU HÁBITAT», «EXPLORA LOS ANIMALES»).

## Cambios de la 6.0 pendientes de aprobación del propietario

- Pictogramas sobre base clara (en la 5.0 van directos sobre fondo oscuro).
- Pista en ámbar (en la 5.0 es lima, el acento de la marca).

## Comparación del 2026-11-14 (vistas: portada, catálogo, tablero, acierto; escritorio y móvil del tablero)

Mejor en la 6.0:
- Móvil del tablero: animal legible junto a su nombre (en la 5.0 es diminuto en una tarjeta enorme).
- Pictogramas de la guía más grandes y con etiqueta legible; Preferencias visible en todas las pantallas.
- Portada: miniaturas de los 8 paisajes y número «1 / 8»; el botón Comenzar y el lema son equivalentes.

Peor en la 6.0:
- Titulares y textos en negrita pesada: la identidad pide titular ligero (5.0 lo es).
- Escritorio 1440×900: el catálogo deja Pausar/Salir fuera de la primera pantalla; el tablero
  y la pantalla de acierto muestran solo una fila de hábitats y el animal es más pequeño.
- Perdidos: rótulo superior pequeño y numeración 01–06 del catálogo.
- Pista ámbar en lugar de lima.

Sin ver todavía: portada móvil, catálogo móvil, acierto móvil, pausa (ambos).

## Movimiento y accesibilidad

- Solo ambiental, leve y desactivable (`prefers-reduced-motion` y control propio); la pausa
  detiene todo movimiento. Sin zoom continuo, parallax intenso ni destellos.
- Objetivos táctiles ≥ 44 px; foco visible; axe sin violaciones.

## Decisiones abiertas

Prototipo definitivo de portada (`prototipo-portada` vs `prototipo-bosque-de-luz`) y si su zoom
de cámara contradice «sin zoom continuo».
