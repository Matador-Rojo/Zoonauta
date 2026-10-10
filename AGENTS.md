# Zoonauta: instrucciones de trabajo

Proyecto del trabajo parcial de Inteligencia Artificial. Responde al usuario en español, con explicaciones claras y breves. Al incorporarte al proyecto, lee `CONTEXTO_CODEX.md`; para ejecutar el juego consulta `README.md`. Después revisa los archivos relacionados con la tarea concreta.

## Reglas del proyecto

- Conserva los 48 animales, los ocho hábitats y las modalidades `JUGADOR` y `AGENTE`. El progreso cuenta retos completados; no hay puntos competitivos ni límites de tiempo o intentos.
- Acepta todas las asociaciones confirmadas del animal. Una asociación `PENDIENTE` produce una respuesta neutral y conserva el nivel de ayuda. No la conviertas en incorrecta por descarte.
- `Repetir` conserva el contenido educativo, la secuencia y el nivel. Pausar/reanudar conserva el reto. Resolver un reto incrementa el progreso una sola vez.
- El núcleo decide las transiciones y las ayudas. La interfaz y las traducciones presentan sus respuestas; no modifican las asociaciones ni los parámetros del modelo.
- El modelo principal combina reglas, la ruta ID3 y selección probabilística de variantes. El modelo de la partida está congelado. Conserva las evidencias sintéticas existentes; cualquier experimento nuevo se guarda por separado.
- Mantén español y portugués brasileño, con siete opciones de voz local por idioma. Piper y Kokoro funcionan sin claves de API. Conserva las dependencias probadas y el catálogo con sus huellas.
- Mantén la dirección visual acordada: imágenes estáticas, portada de una pantalla, ocho paisajes con contador sincronizado y preferencias integradas. El catálogo y el tablero pueden desplazarse para conservar todas sus opciones en móvil.
- Conserva los créditos y la procedencia de pictogramas e imágenes. El informe académico, la PPT y el video siguen pendientes; las guías técnicas del repositorio no equivalen a esos entregables.

## Desarrollo y comprobaciones

- Trabaja sobre la versión actual de la rama y conserva los cambios ajenos. Limita cada cambio a la petición del usuario.
- El núcleo usa la biblioteca estándar. La voz necesita el entorno Python 3.12 preparado por `iniciar_juego.bat` o `bash iniciar_juego.sh`.
- Para cambios de comportamiento: `python -m unittest discover -s tests -v` y `python -m codigo.poc.aceptacion`.
- Para cambios de interfaz: `python -m tests.ejecutar_navegador` con Node, Playwright y Chromium disponibles. Para cambios de voz, consulta las comprobaciones reales de `CONTEXTO_CODEX.md`.
- Una edición solo de documentación requiere comprobar sus referencias e integridad, sin descargar los modelos de voz ni repetir los experimentos.
- Los pesos de voz, entornos y registros locales están excluidos de Git. Actualiza bytes y SHA-256 de los archivos modificados en `datos/manifest.json`, que no se incluye a sí mismo.
- Informa qué cambió y qué verificaste. Distingue resultados ejecutados de comprobaciones pendientes y simulaciones de pruebas con personas.
