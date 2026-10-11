# Una sola caricatura por animal

Los 48 animales usan una caricatura original con transparencia, siguiendo el estilo del capibara elegido por el usuario. Se comparte el mismo archivo en el catálogo, las preguntas, las pistas, el retrato y el cierre. Se retiraron las segundas imágenes activas; el catálogo conserva ocho páginas de seis animales.

Los 47 símbolos de hábitat, atributos y controles se conservan. Los datos biológicos, las relaciones animal–hábitat y los modelos de aprendizaje no cambiaron.

## Comprobación

- 48 PNG originales y 48 WebP con transparencia real; conversión sin modificar el alfa.
- 68 pruebas de Python correctas.
- 17 casos de navegador correctos, sin errores JavaScript. Comprueban una imagen por animal, todas las páginas, preguntas y pistas, ambos modos de juego, cierre, portugués y pantallas entre 320 y 1920 píxeles.
- Capturas de catálogo, partida y cierre revisadas visualmente.
- Imágenes generadas con la herramienta integrada `image_gen`; los prompts y las huellas de cada archivo están en `datos/imagenes_animales_ia.json`.

La comprensión de estas ilustraciones como pictogramas de comunicación está pendiente de evaluación con usuarios de Kallpa. Estas pruebas verifican la integración técnica, no esa comprensión.
