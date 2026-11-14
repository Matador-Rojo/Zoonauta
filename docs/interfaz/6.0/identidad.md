# Contrato de identidad visual — Zoonauta 6.0

Lo que NO se puede quitar ni empeorar sin avisar. Se revisa en cada cambio visual con
`python -m tests.comparar_versiones` (5.0 a la izquierda, 6.0 a la derecha).

## Identidad (manda sobre cualquier guía genérica)

- Fondo oscuro verdoso (`#091713`), acento lima (`#d2ee8b`), titular grande y ligero.
- Tipografía Atkinson Hyperlegible Next.
- Pictogramas e ilustraciones siempre sobre base clara (`--base-pictograma`); no se sustituyen.
- Fotos de hábitat reales en las tarjetas del tablero; logo y robot sin cambios.

## Rasgos que existen en la 5.0 y deben conservarse o mejorarse

- Pista, Repetir, Pausar, Reanudar, Salir; búsqueda y paginación del catálogo; 2/4/8 opciones.
- Yo elijo / El agente elige; guía con pictogramas («Qué lugar · animal · Vivir»).
- Contador «N de 8 completados».

## Observaciones de la comparación del 2026-11-14 (honesto)

Mejor en la 6.0: cabecera con Preferencias visible, pictogramas con base clara legible,
botones de acción con color y etiqueta, búsqueda arriba.
Peor o dudoso en la 6.0 (pendiente de decidir con el propietario):
- Escritorio 1440×900: el catálogo deja Pausar/Salir fuera de la primera pantalla y el
  tablero muestra solo una fila y media de hábitats.
- Se perdió el rótulo pequeño («ENCUENTRA SU HÁBITAT», «EXPLORA LOS ANIMALES») y la
  numeración 01–06 de las tarjetas del catálogo.
- El animal del tablero es más pequeño que en la 5.0 (columna lateral alta).

## Reglas de movimiento y accesibilidad

- Movimiento solo ambiental, leve y desactivable; `prefers-reduced-motion` y control propio.
- Pausa detiene todo movimiento. Sin zoom continuo, parallax intenso ni destellos.
- Objetivos táctiles ≥ 44 px; foco visible; axe sin violaciones.

## Decisiones abiertas

Prototipo definitivo de portada (`prototipo-portada` vs `prototipo-bosque-de-luz`);
si su zoom de cámara contradice la regla de «sin zoom continuo».
