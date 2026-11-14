# Contrato de identidad visual — Zoonauta 6.0

Lo que no se puede quitar ni empeorar sin avisar. Se revisa en cada cambio visual con
`python -m tests.comparar_versiones` (5.0 a la izquierda, 6.0 a la derecha). La 5.0 (`/`)
conserva su identidad verde y lima; este contrato rige solo la 6.0 (`/v6/`).

## Identidad (decidida por el propietario el 2026-11-14)

- **Base azul noche** (`#04141f`, superficies `#0b2436`–`#081c2b`) y **acento cian/turquesa**
  (`#5eead4`, secundario `#22d3ee`, claro `#a5f3fc`) para botones, foco de teclado, brillos y
  estados activos. Se aplica a todo el juego 6.0, no solo a la portada.
- **Portada «Bosque de luz»**: fondo aprobado (ciervo y búho bajo la luna) sin filtros, capas ni
  animaciones; velo oscuro a la izquierda; titular serif grande («Descubre el / bosque de luz.»,
  segunda línea en cian); Comenzar es la acción más visible; Preferencias arriba a la derecha.
  **Sin pictogramas en la portada.**
- Titulares de pantalla en serif (Georgia) como la portada; cuerpo en Atkinson Hyperlegible
  Next (la tipografía del cuerpo queda pendiente de confirmar por el propietario).
- Pictogramas e ilustraciones dentro del juego, siempre sobre base clara; logo y robot sin cambios.

## Rasgos de la 5.0 que deben conservarse o mejorarse

- Pista, Repetir, Pausar, Reanudar, Salir; búsqueda y paginación; 2/4/8 opciones.
- Yo elijo / El agente elige; guía con pictogramas; contador «N de 8 completados».
- Composición del tablero de la 5.0 en escritorio: animal grande a la izquierda con los cuatro
  controles debajo, guía arriba y dos filas de hábitats visibles sin desplazar.
- Preferencias: «Tu expedición / A tu manera.», idioma, retos 1–48, hábitats 2/4/8, voz, ritmo,
  Probar voz, créditos con versión y «Volver al juego ↗».

## Voz

Solo español por ahora: todas las voces descargadas (Piper y Kokoro), las grabaciones es-419 y
las del navegador. En pt-BR la voz está bloqueada (cero voces, controles desactivados).

## Movimiento y accesibilidad

- Solo ambiental, leve y desactivable (`prefers-reduced-motion` y «Reducir movimiento»); la
  pausa detiene todo movimiento. Sin zoom continuo, parallax intenso ni destellos.
- Objetivos táctiles ≥ 44 px; textos ≥ 14 px; foco visible en cian claro; axe sin infracciones.
- La portada y los diálogos no provocan desplazamiento de la página.
