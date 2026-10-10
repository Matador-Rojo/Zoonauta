# Zoonauta: dirección visual 3.3

La portada ocupa una sola pantalla. Sus ocho paisajes cambian cada 10 segundos,
con nombre y contador sincronizados, controles de pausa y navegación manual.
No existe una sección inferior ni desplazamiento vertical en el inicio. Los ocho
fondos comparten un estilo de fotografía de naturaleza; la selva se renovó sin
el guacamayo. Los botones de modalidad son compactos, con bordes redondeados e
iconos lineales. Preferencias comparte la paleta oscura y el acento lima.
El tablero conserva sus pictogramas originales sobre superficies claras.
No se usan vídeos, GIF, escenas WebGL ni fuentes externas. Las fotografías aparentes
son imágenes generadas con IA. El carrusel respeta movimiento reducido y se pausa
al abrir Preferencias o dejar la pestaña.

## Referencias de composición

Se revisaron visualmente ejemplos dentro de las tres galerías indicadas por el usuario:

- MotionSites: imágenes protagonistas, títulos amplios y superficies oscuras.
  https://motionsites.ai/
- Scrolltide, ejemplo Macaw: una escena de naturaleza ocupa la portada.
  https://www.scrolltide.co/templates/macaw
- SceneAI, vista ampliada Stories in Light: fotografía dominante y texto superpuesto.
  https://sceneai.art/

Se adaptaron ideas generales de composición. No se descargaron ni reutilizaron
los vídeos, imágenes, prompts de pago o código de estas referencias.

## Imágenes propias

| Ruta | Uso | Dimensiones |
|---|---|---|
| `codigo/interfaz/web/portada-selva.webp` | Selva renovada, fondo 01 del carrusel | 1536 × 1024 |
| `codigo/interfaz/web/fondos/H02.webp` a `H08.webp` | Fondos 02 a 08 del carrusel | 1536 × 1024 cada uno |
| `codigo/interfaz/web/paisajes.webp` | Atlas de ocho paisajes, en cuatro columnas y dos filas | 1774 × 887 |

Se usó la herramienta integrada imagegen, sin API ni CLI de respaldo. Las imágenes
generadas se codificaron como WebP para reducir su peso, conservando la composición
y las dimensiones. CSS presenta las regiones del atlas en las tarjetas. Los
pictogramas y sus metadatos permanecen separados; el banco de asociaciones no se
modificó. Los paisajes no constituyen evidencia biológica ni validación CAA.

## Prompt de portada anterior (3.2, sustituida)

Use case: photorealistic-natural. Asset type: original static full-bleed website hero background for Zoonauta, an animal/habitat exploration game. Create a premium cinematic wildlife photograph, landscape aspect ratio 3:2, high resolution. A magnificent scarlet macaw with anatomically plausible red, yellow and blue plumage perched calmly on a mossy branch in the right third of a lush tropical rainforest. Mid-shot bird, beautifully sharp face and feather detail, not enormous close-up. Atmospheric rainforest depth, broad emerald leaves, tall palms, subtle distant waterfall on the right, warm shafts of light from the upper right, organic natural texture. Left half is richly shadowed foliage and soft forest atmosphere with generous quiet dark negative space for white website text and buttons. Overall deep forest green and charcoal with warm sunlight and vibrant red accent from bird. Sophisticated editorial wildlife photography, realistic camera depth and materials, quiet majestic atmosphere. Keep the bird fully visible within right half with ample padding from edges. No UI, no frames, no panels, no map, no floating islands, no icons, no text, no letters, no logos, no watermark, no human. This image is decoration for a static website; no animation or video.

## Prompt del atlas

Use case: photorealistic-natural. Asset type: a single decorative habitat photo atlas for a static animal exploration game website. Generate exactly 8 separate photographic square landscapes in a perfectly aligned 4-column by 2-row contact sheet, total aspect ratio 2:1. No gaps, no borders, no margins, no labels. Every tile is the same square size and occupies exactly one fourth of the width and one half of the height; distinct hard image boundaries at 25%, 50%, 75% width and 50% height. Top row left to right: 1 lush tropical rainforest with tall palms and dense foliage; 2 golden African savanna with one distant acacia and grass; 3 warm sandy desert dunes with dramatic evening light; 4 deep turquoise open sea with gentle waves and pale horizon. Bottom row left to right: 5 temperate woodland with autumnal leafy trees; 6 freshwater river winding through green reeds and lakeshore; 7 polar sea ice, blue-white glaciers and snowy land; 8 rugged high snowy mountains with rocky alpine slopes. Premium cinematic travel photography, beautifully natural textures, varied lighting and atmospheric depth, realistic environments. Each tile must be easily distinguishable by landscape alone. No animals, no humans, no buildings, no typography, no letters, no symbols, no icons, no logos, no UI, no watermarks. These landscapes are decorative, not educational pictograms. The website will keep its existing educational pictograms separately.

## Prompts y archivos de los ocho fondos actuales

La herramienta integrada imagegen generó un archivo por paisaje. Los ocho prompts
completos, las rutas de origen y las rutas finales están en
[`fondos_generados.json`](fondos_generados.json). La conversión a WebP mantiene
1536 × 1024 píxeles y la composición; los originales generados se conservaron.
Cada fondo tiene su propia imagen completa para evitar ampliar una celda pequeña
del atlas. El atlas anterior se mantiene en las tarjetas de hábitat del tablero.

## Revisión

Se inspeccionaron los ocho fondos y las capturas de portada, catálogo, tablero,
Preferencias y móvil. Se comprobaron 35 pruebas de Python y trece casos de navegador.
La interfaz conserva 48 animales, ocho hábitats y ambas modalidades. Las pruebas
de voz usan síntesis, API y reproductor controlados; no certifican voz real ni
sonido audible en el dispositivo del usuario.
