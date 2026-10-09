# Comprobación de la PoC en consola

Fecha: 9 de octubre de 2026. Versión: 1.0.0.

## Resultado de la ejecución

Se ejecutaron `python -m codigo.poc.aceptacion` y
`python -m unittest discover -s tests -v`. Ambos terminaron correctamente.
Los ocho casos de aceptación pasaron y las 19 pruebas automáticas finalizaron
con resultado OK. Posteriormente se ejecutó la demostración que produjo los
archivos de esta carpeta.

| Comprobación | Resultado |
|---|---|
| Ocho recorridos de aceptación CP01–CP08 | 8/8 correctos. |
| Pruebas automáticas del núcleo y la consola | 19/19 correctas. |
| Construcción ID3 mediante ganancia de información | Raíz entorno; ganancia 2,00 bits. |
| Clasificación de los ocho perfiles usados para construir el árbol | Ocho hojas coherentes; comprobación estructural. |
| 69 asociaciones confirmadas | Todas resuelven el reto y confirman el hábitat seleccionado. |
| 315 relaciones pendientes | Todas reciben respuesta neutral, sin aumentar nivel o progreso. |
| Partida automática de 48 retos | Recorre los 48 animales y cierra con c = N. |
| Repetir, pausar y reanudar | Conservan contenido, nivel, ruta y atribución de la ayuda. |
| Eventos duplicados, ignorados y de retos anteriores | No vuelven a ejecutar una transición. |
| Selectores ID3, rotación y probabilístico | Respetan su regla de selección; parámetros congelados. |
| Consola JUGADOR y AGENTE | Sesiones completas y salida por fin de entrada comprobadas. |
| Registro JSONL | Conserva los resultados sin etiqueta como null. |

## Evidencia incluida

- `demo_consola.txt`: salida textual de la demostración ejecutada.
- `arbol_id3.json`: árbol calculado, entropía y ganancias.
- `casos_ejecutados.json`: acciones y salidas de los ocho recorridos ejecutados.
- `eventos_demo.jsonl`: eventos y observaciones de esas pruebas de control.

Los registros llevan procedencia de control sintético. Las observaciones abiertas
al final de un caso corto indican que ese caso comprobó una transición intermedia;
no se consideran etiquetas de entrenamiento. Cada caso comienza con un gestor nuevo.

Se ejecutó la construcción del baseline ID3. No se ejecutó el aprendizaje
bayesiano del modelo principal, una comparación experimental de efectividad,
pruebas con jugadores, la interfaz digital ni la reproducción de voz.

