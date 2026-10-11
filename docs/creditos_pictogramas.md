# Créditos y alcance de los recursos visuales

## Caricaturas seleccionadas el 10 de octubre de 2026

La interfaz usa una única caricatura original por animal: 48 ilustraciones generadas
con la herramienta integrada image_gen, siguiendo el estilo de la segunda capibara
seleccionada por el usuario. Las mismas imágenes se utilizan en catálogo, preguntas,
pistas y retratos del tablero. En la versión 3.8 se sustituyen los 33 SVG de apoyo
por 33 ilustraciones originales transparentes del mismo estilo de la capibara,
generadas con image_gen integrada. Sus prompts y huellas están en
`datos/imagenes_apoyos_ia.json`. Se ofrecen bajo CC BY-NC-SA 4.0.
El 11 de octubre se sustituyeron los símbolos de persona y agente por dos
caricaturas originales transparentes, generadas con image_gen integrada y ofrecidas
bajo CC BY-NC-SA 4.0. Los prompts y huellas están en
`datos/imagenes_modalidad_ia.json`; su comprensión CAA está pendiente de evaluación.
También se renovaron los ocho símbolos de hábitat y los controles Pista, Repetir,
Pausar y Salir con ilustraciones originales transparentes bajo CC BY-NC-SA 4.0.
Se documentan en `datos/imagenes_habitats_controles_ia.json`. Los paisajes realistas
locales siguen siendo la imagen principal de las tarjetas de hábitat. Estas tarjetas
usan ocho paisajes nuevos con composición central, generados con image_gen integrada
y ofrecidos bajo CC BY-NC-SA 4.0. Son representaciones realistas generadas con IA,
no fotografías de lugares específicos. Se documentan en
`datos/imagenes_paisajes_tarjetas_ia.json`; los fondos de portada se conservan.
Las caricaturas no derivan de los PNG de ARASAAC. Sus prompts y huellas se encuentran
en `datos/imagenes_animales_ia.json`; se ofrecen con el material original del prototipo
bajo CC BY-NC-SA 4.0. La comprensión CAA sigue pendiente de evaluación con usuarios.

En 4.2 se incorporan dos ilustraciones originales del robot guía: despedida
con cuaderno y descanso sentado en un banco. Generadas con image_gen integrada,
elegidas por el usuario y convertidas a WebP sin pérdida con alpha conservado.
Se ofrecen bajo CC BY-NC-SA 4.0. Sus prompts, rutas y huellas se registran en
`datos/imagenes_cierre_pausa_ia.json`. Son ilustraciones de pantalla adicionales
al banco de 95 pictogramas y no sustituyen las secuencias de preguntas y pistas.

Los recursos anteriores y sus metadatos se conservaron en un respaldo local antes
de la sustitución. La información siguiente documenta esas versiones históricas.

9 de octubre de 2026.

Los símbolos pictográficos ARASAAC incluidos son propiedad del Gobierno de Aragón
y fueron creados por Sergio Palao. Proceden de https://arasaac.org y se distribuyen
bajo licencia Creative Commons BY-NC-SA. Se conservaron 28 PNG originales, sin
recolorear, recortar ni trazar. Los identificadores, URL, metadatos, rutas y SHA-256
están en `datos/fuentes_pictogramas.json` y `datos/pictogramas.json`.

Condiciones oficiales consultadas: https://arasaac.org/terms-of-use.
El uso es no comercial, con atribución y compartir igual según esas condiciones.
El material visual del prototipo se ofrece respetando CC BY-NC-SA.

Las otras 67 imágenes son SVG originales realizados mediante código, sin usar
imágenes ARASAAC como base: 20 animales, ocho hábitats y 39 apoyos o controles.
Su fuente editable es `codigo/interfaz/crear_svg.py`. Se ofrecen bajo CC BY-NC-SA 4.0:
https://creativecommons.org/licenses/by-nc-sa/4.0/.
Autoría: elaboración original del prototipo con asistencia de Codex.
La misma licencia se aplica a las composiciones y capturas con estos recursos.

En la versión 3.1 se añadió `codigo/interfaz/web/mundo.svg`, una ilustración
decorativa original de paisajes realizada mediante código con asistencia de Codex,
bajo CC BY-NC-SA 4.0. No deriva de imágenes ARASAAC ni forma parte del conjunto de
95 pictogramas educativos. La marca de brújula y los iconos de navegación se dibujaron
como SVG en el código de la interfaz, con la misma autoría y licencia.

La versión 3.3 utiliza `codigo/interfaz/web/portada-selva.webp`, siete imágenes en
`codigo/interfaz/web/fondos/` y `codigo/interfaz/web/paisajes.webp`: ocho fotografías
aparentes de paisaje para el inicio y un atlas para el tablero. Son imágenes decorativas
generadas con la herramienta integrada imagegen mediante prompts propios. La selva
anterior con guacamayo se sustituyó por un paisaje sin animales para mantener el
estilo de los otros siete fondos. Los prompts y las rutas están en
`docs/interfaz/diseno_visual.md` y `docs/interfaz/fondos_generados.json`.
No se copiaron imágenes ni código de las galerías de referencia. Estos nueve archivos
se ofrecen junto al material visual del prototipo bajo CC BY-NC-SA 4.0 y no forman
parte de los 95 pictogramas educativos.

Los símbolos genéricos representan la clase del animal; la etiqueta mantiene la
especie del banco. Las ilustraciones propias son esquemáticas. Hay revisión
técnica de carga y legibilidad; la comprensión CAA de las secuencias aún requiere
validación con usuarios. La disponibilidad de una imagen no implica validación CAA.
