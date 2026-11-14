# Pantallas 6.0 — registro de la Fase 4

> **Superado el 2026-11-14.** Este registro describe la fase 4 (paleta clara, luego oscura y
> lima, carrusel de 8 paisajes). La 6.0 actual es azul noche y cian, con la portada «Bosque de
> luz» y la composición de la 5.0: ver `identidad.md` y `accesibilidad_rendimiento.md`.


Interfaz en `/v6/` (rama `experimental/zoonauta-v6-modern-web`). Reglas, modos y
datos educativos sin cambios: solo cambia la presentación.

## Dirección visual: «tablero de expedición»

Inspirada en los tableros de comunicación aumentativa (CAA) que usa parte del público:
la pieza central es la **tira de frase**, los pictogramas en orden de lectura sobre una
banda, cada uno en una celda con borde fuerte. El resto es sereno.

| Token | Valor | Uso |
|---|---|---|
| `--niebla` | `#eef2ec` | fondo |
| `--tinta` | `#1b2b24` | texto (13,9:1 sobre el fondo) |
| `--expedicion` | `#2f6b4f` | marca, progreso, acciones de partida |
| `--ambar` | `#f0b43c` | Pista y acción principal |
| `--agua` | `#2c6e8f` | Repetir (audio) |
| `--alerta` | `#9b2c1f` | avisos de error |

- Tipografía: **Atkinson Hyperlegible Next** (Braille Institute, OFL-1.1, 53 KB en
  WoFF2 variable), diseñada para baja visión. Escala modular 1,25 sobre 18 px.
- Radios por jerarquía: control 14 px < tarjeta 18 px < panel 26 px. Bordes en lugar de
  sombras.
- Se quitaron rasgos de plantilla señalados por la skill frontend-design: etiquetas en
  mayúsculas, el número de animal en las tarjetas (no es una secuencia útil) y el color
  de acento en «Su mundo.» de la portada.

## Cambios por pantalla

- **Catálogo**: tarjetas-botón con la ilustración y el nombre (nombre accesible = texto
  visible); rejilla con `role="group"`; el foco pasa al primer animal tras paginar.
- **Tablero**: animal y guía arriba; controles en dos grupos fijos (ayuda: Pista y
  Repetir; partida: Pausar y Salir); hábitats debajo con título propio. En móvil, dos
  columnas de hábitats para compararlos sin un desplazamiento largo.
- **Pausa y cierre**: robot existente, tira de pictogramas, progreso y una acción clara.
- **Preferencias**: interruptores `<input type="checkbox" switch>` dibujados con CSS
  (Chrome aún no los dibuja); con «reducir movimiento» del sistema, el interruptor
  queda activado y bloqueado con explicación.
- **Avisos**: los errores quedan visibles hasta que se cierran (antes desaparecían a
  los 8 s), con `role="alert"`, sin duplicados y con el foco gestionado al cerrar.
- **Voz**: el frontend 6.0 reproduce primero la grabación completa del mensaje
  (`/api/voz/grabada`) y, si no existe, lo lee entero con la voz elegida.

## Modern Web Guidance aplicado

| Guía | Aplicación | Prueba |
|---|---|---|
| `switch` | `switch` + `role="switch"`, `accent-color`/dibujo propio, foco visible | Preferencias en `--portada` (bloqueado con `reduce`) |
| `persistent-toast-notifications` | avisos persistentes en una región con nombre; cierre explícito; foco al cerrar | revisión manual; pendiente prueba dedicada |
| `card` | elecciones como `<button>`; sin cambios de tamaño al seleccionar | `--v6` + axe |
| `progress` | `<progress>` nativo con `appearance: none` y contraste ≥ 3:1 | axe sin incidencias |
| `visually-stable-font-fallbacks` | `font-size-adjust: from-font` en `body` | revisión visual |
| `form-factor-adaptation` | `--toque` 48 px, 52 px en `pointer: coarse` | `--portada` (tamaño mínimo) |
| `natural-interactions` | hover, pulsación (solo con movimiento) y foco distintos | revisión visual |

axe-core 4.14: 0 incidencias en portada, selector, catálogo, tablero y pausa.

## Pictogramas ligeros

`/media/<id>` sirve copias derivadas de 384 px (WebP, calidad 82) de
`assets/pictogramas_ligeros/`; los 441 originales (87 MB) se conservan sin cambios.
`indice.json` guarda la huella de cada original y `tests/test_imagenes_ligeras.py`
falla si alguna copia queda desactualizada. Regenerar con
`python -m codigo.interfaz.preparar_imagenes_ligeras` (requiere Pillow).
Medición (catálogo + tablero, Chrome 157): 1.173 KB → 53 KB en pictogramas.

## Pendiente

- Prueba automatizada específica de los avisos persistentes.
- Lector de pantalla real (NVDA) y Lighthouse.
- Textos pt-BR nuevos pendientes de revisión humana.

## Revisión visual (2026-11-14): identidad oscura y lima, con mejoras sobre la 5.0

La primera versión de la 6.0 usó una paleta clara genérica y perdió rasgos de la 5.0
(franja de cifras, nota de cabecera, acento lima, titular grande y ligero). Se corrigió
partiendo de la identidad de la 5.0 y añadiendo lo siguiente:

- **Acento por paisaje** en la portada: lima (selva), ámbar (sabana), arena (desierto),
  celeste (hielo), crema (montaña), turquesa (arrecife), arena clara (cueva) y verde
  claro (lago). Cambia título, botón, línea y etiquetas; la transición es de color.
- **Miniaturas** de los 8 paisajes (acceso directo) y **línea de tiempo** de 10 s que
  muestra cuándo cambia el siguiente; solo existe con movimiento permitido y mientras
  la rotación corre.
- **Tema oscuro y lima en todas las pantallas** (`tema.css`); los pictogramas y las
  ilustraciones, pensados para fondo claro, van siempre sobre una base clara.
- **Momento de acierto**: el hábitat elegido se destaca con ✓ y los demás se atenúan; la
  foto del hábitat acertado aparece junto a la frase de confirmación.
- Corregidas variables de radio inexistentes en `portada.css` y el foco visible sobre
  fondo oscuro (blanco + anillo azul).
