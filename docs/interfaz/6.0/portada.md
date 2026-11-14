# Portada 6.0 — registro de la Fase 3

Rama `experimental/zoonauta-v6-modern-web`, 2026-11-13. Interfaz en `/v6/`.

## Paisajes

Exactamente ocho, en este orden: H01, H09, H17, H22, H20, H37, H21, H25. Fotos
reutilizadas de `codigo/interfaz/web/fondos/catalogo/` (1920 × 1080). Se añadieron
versiones de 960 px en `codigo/interfaz/web/fondos/portada/` derivadas de esas mismas
fotos (Pillow, LANCZOS, WebP calidad 78); no son imágenes nuevas.

## Movimiento ambiental (nivel 1)

Solo con `prefers-reduced-motion: no-preference` y sin «Reducir movimiento». La foto
base nunca se anima: los efectos son capas de luz o copias recortadas de la misma foto.

| Paisaje | Efecto | Ciclo |
|---|---|---|
| H01 Selva | niebla que deriva ±3 %; textura tenue en la cascada | 48 s / 6 s |
| H09 Sabana | franja de hierba oscila ±0,4° desde el suelo; halo del sol | 7 s / 24 s |
| H17 Desierto | variación mínima de luz cálida | 30 s |
| H22 Hielo | reflejo frío en el agua, sin destellos | 50 s |
| H20 Montaña | nubes suaves que cruzan ±6 % | 90 s |
| H37 Arrecife | rayos de luz y brillo submarino | 22 s / 28 s |
| H21 Cueva | estática | — |
| H25 Lago | el agua ondula 1–2 px en la mitad inferior | 9 s |

Sin zoom, cámara, parallax ni destellos. La pausa del carrusel detiene también el
movimiento ambiental (WCAG 2.2.2). La oscilación real de hojas o hierba por elementos
separados requeriría imágenes por capas, que no existen.

## Carrusel

- Rotación cada 10 s. Se detiene con la pausa, con Preferencias o el selector
  abiertos, con la pestaña oculta y mientras el foco o el puntero están en el carrusel.
  Cada cambio manual reinicia los 10 s.
- Con movimiento reducido (sistema o Preferencias): fotos fijas, avance manual, sin
  fundido y sin botón de pausa. Si el sistema lo pide, el interruptor aparece activado
  y bloqueado con una explicación.
- Controles: anterior, pausa/reanudar (sin `aria-pressed`), siguiente y 8 marcas con
  `aria-current` y área de 32 × 32 px. Región `aria-roledescription="carousel"`; el
  aviso «Paisaje N de 8» solo se emite en cambios pedidos por la persona.
- Montaje: paisaje actual, anterior (para el fundido de 1,4 s) y siguiente (precarga).
- La escena 16:9 cubre la pantalla con unidades de contenedor y `--fx/--fy` por
  paisaje, de modo que los efectos coinciden con la foto en cualquier proporción.

## Modern Web Guidance aplicado

| Guía | Aplicación | Prueba |
|---|---|---|
| `ui-behaviors/motion` | opt-in con `no-preference`; pausa visible; sin `aria-pressed` | `--portada`: sin animaciones con `reduce`; pausa detiene todas |
| `ui-components/carousel` | botones con nombre, marcas, estado polite tras cambios pedidos | `--portada`: marcas, contador, nombre |
| `ui-components/dialog` | `showModal`, `autofocus`, cierre con `form method=dialog`, scroll contenido | `--v6`: foco inicial, Esc, foco devuelto |
| `performance/optimize-image-priority` | `fetchpriority=high` en H01 + `<link rel=preload>`; `low` en la siguiente | medición abajo |
| `performance/deliver-optimized-decorative-images` | `srcset` 960/1920 con `sizes` real de la escena | `--portada` móvil |

## Accesibilidad y rendimiento

- axe-core 4.10.3 (WCAG 2.0/2.1/2.2 A y AA + buenas prácticas): 0 incidencias en la
  portada ni en el selector de modalidad.
- Medición con Chrome 157 (Playwright, sin caché):
  - Escritorio 1440 × 900: LCP ≈ 0,4 s; 881 KB transferidos.
  - Móvil 375 × 812, DPR 2, 1,6 Mbps / 150 ms y CPU × 4: FCP ≈ 2,8 s, LCP ≈ 3,9 s (texto).
- Corrección: los pictogramas del selector (~500 KB cada uno) se descargaban con la
  portada; ahora son diferidos y se precargan solo con intención (puntero o foco en
  Comenzar). Carga inicial: 1.915 KB → 881 KB.

## Pendiente

- Lighthouse y lector de pantalla real (NVDA/VoiceOver).
- Pictogramas de 1254 px y ~500 KB: conviene servir versiones derivadas más pequeñas
  sin reemplazar los originales.
- Recortes verticales específicos para móvil si se quieren fotos más nítidas.
- Textos pt-BR nuevos pendientes de revisión humana (`frontend/src/i18n.ts`).
