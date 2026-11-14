# Accesibilidad y rendimiento — interfaz 6.0 («/», antes /v6/)

Fecha: 2026-11-14 · Rama `experimental/zoonauta-v6-modern-web` · Chrome 157 · Windows.

## Lighthouse 13.6 (`python -m tests.lighthouse_v6`)

Cada pantalla se mide con una sesión real (cookie) en ese estado. Móvil: emulación de
Lighthouse (4G lenta simulada, CPU ×4). Escritorio: preset `desktop`.

| Pantalla | Rendimiento (antes → después) | Accesibilidad | Buenas prácticas | SEO |
|---|---|---|---|---|
| Portada · escritorio | 98 → **99** | 100 | 100 | 91 → **100** |
| Portada · móvil | 79 → **79** | 100 | 100 | 91 → **100** |
| Catálogo · escritorio | 85 → **99** | 100 | 100 | 91 → **100** |
| Catálogo · móvil | 59 → **87** | 100 | 100 | 91 → **100** |
| Tablero · escritorio | 79 → **95** | 100 | 100 | 91 → **100** |
| Tablero · móvil | 75 → **77** | 100 | 100 | 91 → **100** |
| Pausa · escritorio | 96 → **100** | 100 | 100 | 91 → **100** |
| Pausa · móvil | 66 → **89** | 100 | 100 | 91 → **100** |

LCP después (escritorio / móvil): portada 1,0 / 5,6 s · catálogo 0,8 / 4,1 s · tablero
1,6 / 6,5 s · pausa 0,7 / 3,8 s. CLS ≤ 0,044 en todas (antes, catálogo 0,44 y pausa 0,21).

### Correcciones aplicadas

1. **Fotos de hábitat** de las tarjetas: copias de 560 px (calidad 75) en lugar de los
   originales cuadrados de 1080 px. 17 MB → 3,7 MB en total; unos 101 KB por foto.
2. **Robot** de pausa y cierre: copias de 640 px. 1,1 MB → 89 KB.
3. **Precarga de la portada** solo cuando la sesión está en la portada (el servidor quita
   el bloque `portada:inicio…fin` del HTML en las demás pantallas): 338 KB menos.
   Incluye la capa de hojas, que es el LCP en móvil.
4. **Siguiente paisaje**: se precarga cuando el primero terminó de cargar.
5. **Saltos de diseño**: la imagen de cada tarjeta reserva su espacio
   (`aspect-ratio`) y el robot declara su proporción (`width`/`height`).
6. **Caché**: los compilados de `/v6/assets/` (con huella en el nombre) se sirven con
   `immutable`; la API y el HTML siguen con `no-store` porque llevan estado de sesión.
7. **SEO**: meta descripción.
8. Servidor: se ignora `ConnectionAbortedError` (Windows) cuando el navegador cancela
   una descarga, igual que ya se hacía con las equivalentes de Linux.

Originales intactos: las copias se derivan solo cambiando el tamaño
(`python -m codigo.interfaz.preparar_imagenes_ligeras`), con la huella de cada original
en `indice.json`; `tests/test_imagenes_ligeras.py` detecta copias desactualizadas.

### Límites conocidos

- **Portada en móvil (79)**: en un teléfono vertical, la foto 16:9 se recorta y necesita
  la versión de 1920 px para verse nítida. Los recortes verticales opcionales
  (`imagenes_por_capas.md`) bajarían el peso y mejorarían el LCP.
- **Tablero en móvil (77)**: el LCP es el texto de la guía, que espera al JavaScript
  (247 KB; React incluido) y a `/api/vista` (53 KB) con la red simulada lenta.
- El pequeño CLS constante (0,022 × 2) proviene de `body` al cargar los datos; está
  muy por debajo del umbral de 0,1.
- `bf-cache`: no aplica porque el HTML usa `no-store` (estado de sesión), decisión
  deliberada.

## Pruebas automatizadas de accesibilidad y uso

| Prueba | Qué comprueba | Resultado |
|---|---|---|
| axe-core 4.14 (`--portada`, `--v6`) | WCAG 2.0/2.1/2.2 A y AA + buenas prácticas en portada, selector, catálogo, tablero y pausa | 0 incidencias |
| `--partidas-v6` | 4 partidas completas con teclado: ambas modalidades, 2/4/8 hábitats, pt-BR, 320 px sin desplazamiento horizontal; foco al título del cierre | OK |
| `--portada` | 8 paisajes, rotación 10 s, pausa del movimiento, reducir movimiento (sistema y preferencia), marcas, móvil, capas | 8 casos OK |
| `--v6` | Pista y Repetir sin parpadeo ni pérdida de foco, recarga, pausa | 10 casos OK |
| `--voz-v6` | Una sola voz, cancelación, velocidad, interruptor, fallo de red | 8 casos OK |

Nota: en `--partidas-v6`, los hábitats se enfocan directamente y se activan con Intro
(recorrerlos con Tab haría la prueba muy lenta); el resto de controles se alcanza con Tab.

Estabilidad: la prueba general de la 5.0 (`python -m tests.ejecutar_navegador`, 20 casos)
falló una vez de cuatro ejecuciones seguidas en esta sesión, justo después de la batería
completa; las otras tres pasaron. No se conservó la salida del fallo: vigilarla.

## Lo que la automatización no cubre

- **Lector de pantalla real** (NVDA, VoiceOver, TalkBack): pendiente de prueba manual.
- **Teléfonos y tabletas reales** con distintas densidades y redes.
- **Comprensión de pictogramas y mensajes** por el público objetivo: cumplir WCAG no
  equivale a validar la comprensión. Requiere pruebas con usuarios, con autorización,
  acompañamiento y criterios apropiados.

## Medición tras el rediseño azul y «Bosque de luz» (2026-11-14)

`python -m tests.lighthouse_v6 --salida output/lighthouse-azul`. Accesibilidad, buenas prácticas
y SEO: 100 en las 8 mediciones.

| Pantalla | Escritorio | Móvil (antes → ahora) | LCP móvil |
| --- | --- | --- | --- |
| Portada «Bosque de luz» | 99 | 79 → 81 | 5,1 s |
| Catálogo | 99 | 87 → 84 | 4,5 s |
| Tablero | 95 | 77 → 75 | 8,9 s |
| Pausa | 100 | 89 → 89 | 3,8 s |

El tablero en móvil no mejora: las fotos de los hábitats ahora llenan la pantalla y son el LCP.
Pendiente: servir en móvil una copia de 560 px de las fotos de hábitat (`paisajes_ligeros`).
Las diferencias de ±3 puntos están dentro de la variación habitual de Lighthouse.

Sin desplazamiento (medido con `comparar_versiones`, `medidas.json`): ninguna pantalla se
desplaza en 1440×900, 1280×720 ni 390×844. En vistas bajas (720×450 = zoom 200 %, 360×640,
844×390) la página se desplaza como último recurso y ninguna tarjeta queda por debajo de su
tamaño mínimo (hábitats ≥ 56 px, controles ≥ 44 px, imágenes ≥ 48 px).
