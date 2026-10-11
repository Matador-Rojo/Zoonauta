# Zoonauta: dirección visual 3.8

La portada ocupa una sola pantalla. Sus ocho paisajes cambian cada 10 segundos,
con nombre y contador sincronizados, controles de pausa y navegación manual.
No existe una sección inferior ni desplazamiento vertical en el inicio. Los ocho
fondos comparten un estilo de fotografía de naturaleza; la selva se renovó sin
el guacamayo. Un único botón principal Comenzar abre la elección entre Yo elijo
y El agente elige, mediante dos tarjetas con pictogramas. Volver al inicio o Escape
cierran el selector sin iniciar una partida. Preferencias comparte la paleta oscura
y el acento lima.
El tablero usa caricaturas originales transparentes en preguntas, pistas, tarjetas,
retratos y cierres. Los nuevos apoyos siguen el mismo estilo de la capibara aprobada.
No se usan vídeos, GIF, escenas WebGL ni fuentes externas. Las fotografías aparentes
son imágenes generadas con IA. El carrusel empieza en marcha y solo el botón central
activa la pausa manual. Play o cualquiera de las flechas reanuda la rotación y reinicia
los 10 segundos. Movimiento reducido elimina las animaciones, conservando el cambio
de fotografías estáticas. Preferencias o el selector abiertos, o la pestaña oculta, suspenden temporalmente
la rotación.

## Catálogo, tablero y cierre

El catálogo conserva sus 48 opciones en ocho páginas de seis, con búsqueda global
sin tildes. Anteriores y Siguientes permiten recorrerlas; la pausa conserva la página.
Las tarjetas oscuras
dan protagonismo a los animales, sin cajas blancas detrás de sus recortes. El tablero
presenta el retrato y la guía encima de ocho tarjetas de paisaje realista con
composición central, nombre y número 01–08. Las tarjetas ocupan todo el ancho,
sin dibujos superpuestos. Los controles usan caricaturas transparentes con texto.

La pantalla de pausa conserva el retrato del animal; los cierres completado y de salida
presentan el progreso real junto a una composición de animales y la acción de reiniciar.
El diseño mantiene cuatro columnas de hábitats en escritorio y dos en móvil. El catálogo
usa tres columnas en escritorio y dos en móvil. Ambas pantallas permiten desplazamiento
cuando el alto disponible lo requiere.

Hay 48 caricaturas de animales generadas individualmente con la herramienta integrada
imagegen, con fondo alfa transparente. Los prompts y la procedencia se registran en
`datos/imagenes_animales_ia.json`. Se optimizaron como WebP para servirlas localmente.
No son fotografías de ejemplares reales ni evidencia biológica. El banco tiene 95
pictogramas originales generados con IA; sus identificadores conservan las secuencias,
reglas, ayudas y modelo. Los recursos anteriores se documentan como antecedentes.

## Símbolo de Zoonauta

La cabecera utiliza un símbolo propio de un animal explorador: un rostro de zorro,
una oreja con forma de hoja, una órbita abierta y una estrella. La silueta conecta
los animales, la naturaleza y la exploración. Conserva el lima y el blanco de la
interfaz, junto al texto existente de Zoonauta y su subtítulo.

El archivo `codigo/interfaz/web/zoonauta-logo.svg` contiene únicamente formas
vectoriales editables, sin imágenes incrustadas ni fondo. Se puede ampliar sin
perder definición. El símbolo es decorativo y no sustituye los pictogramas educativos.

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
y las dimensiones. El atlas permanece como antecedente; las tarjetas actuales usan
imágenes completas propias. Los pictogramas y metadatos permanecen separados;
el banco de asociaciones no se
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
del atlas. Las tarjetas actuales usan ocho paisajes centrados específicos, registrados
en `datos/imagenes_paisajes_tarjetas_ia.json`. Los fondos de portada se conservan.

## Apoyos pictográficos actuales

Se utiliza una sola caricatura por animal en todo el recorrido. Las 33 imágenes
nuevas de apoyo para preguntas, pistas y acciones tienen fondo transparente y
siguen el estilo aprobado de los animales: contornos definidos, colores naturales
y sombreado suave. Cada concepto usa una imagen propia: Explorar lleva mapa y
brújula, Buscar lleva lupa; agua salada combina una ola y un salero, y agua dulce
una gota y una pequeña laguna. Los prompts y las huellas están en
`datos/imagenes_apoyos_ia.json`.

Las preguntas y pistas mantienen secuencias de 84–96 px; los controles, 56 px.
Se eliminaron los fondos, bordes y rellenos blancos de cada imagen, incluidos
Iniciar y Salir. Los pictogramas de hábitat permanecen en las secuencias educativas.
Las tarjetas muestran paisaje y nombre, sin símbolos superpuestos.

La captura de portada y la revisión actual están en `docs/interfaz/3.8/`.
La versión 3.8 pasó 70 pruebas Python y 21 casos de navegador: 17 de interfaz
y cuatro de voces controladas. La comprensión CAA requiere evaluación con usuarios;
las pruebas técnicas no demuestran aprendizaje.

## Revisión anterior

Se inspeccionaron los ocho fondos y las capturas de portada, catálogo, tablero,
Preferencias y móvil. En la versión 3.4.0 se añadieron capturas de tablero,
Preferencias y portada móvil en portugués. Pasaron 49 pruebas de Python y 14 casos
de interfaz en navegador. Se comprobó síntesis real de las 14 opciones locales y
reproducción nativa de una muestra de Piper español y otra de Kokoro portugués.
Estas verificaciones no certifican escucha humana o pronunciación en otro equipo.
La interfaz conserva 48 animales, ocho hábitats y ambas modalidades.
