# Alternativas de voz para Zoonauta

Revisión de documentación oficial: 10 de octubre de 2026. La interfaz actual
utiliza las voces españolas del navegador. Los motores de esta comparación aún
no están instalados ni integrados; no se ha evaluado su sonido en Zoonauta.

| Opción | Uso en Zoonauta | Preparación | Estado |
|---|---|---|---|
| Voces del navegador | Leen cualquier respuesta preparada; Google español se elige primero cuando existe. | Ninguna instalación del proyecto; las voces dependen del navegador y del sistema. | Integrada. |
| Piper | Motor neuronal local con modelos para español de España, México y Argentina; permite trabajar sin conexión tras descargar la voz. | Instalar el motor y descargar un modelo ONNX y su configuración. | Candidata recomendada para la primera prueba. |
| Kokoro-82M | Modelo abierto que ofrece las voces españolas Dora, Alex y Santa; puede ejecutarse localmente. | Instalar motor, dependencias y pesos del modelo. | Candidata para comparar con Piper. |
| Grabaciones humanas | Permiten controlar la pronunciación y el tono de cada frase de la guía. | Grabar y revisar todo el repertorio; añadir audios cuando cambien los textos. | Alternativa de diseño. |

Piper y Kokoro ejecutados localmente no necesitan una clave ni cobran por solicitud.
Consumirán recursos del equipo. Esto no equivale a contratar un servicio hospedado
por otra empresa. La distribución de una voz Piper requiere revisar su ficha de
licencia; el motor usa GPL-3.0 y las voces tienen licencias propias. Kokoro-82M
publica los pesos bajo Apache-2.0.

La primera prueba propuesta es Piper, por su ejecución local y sus variantes de
español. La selección definitiva debe basarse en muestras de las respuestas del
juego, escuchando pronunciación de los animales, claridad y tiempo de preparación.
No se garantiza que cualquiera de estos motores resulte más natural que Google
español sin esa comparación. La ficha de Kokoro también advierte que las frases
muy cortas y algunos idiomas pueden presentar limitaciones.

Fuentes del proyecto:

- [Piper: repositorio oficial](https://github.com/OHF-Voice/piper1-gpl).
- [Piper: modelos, idiomas y licencias](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md).
- [Piper: ejecución e instalación](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md).
- [Kokoro-82M: ficha del modelo](https://huggingface.co/hexgrad/Kokoro-82M).
- [Kokoro-82M: voces españolas](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).
- [Kokoro: repositorio del motor](https://github.com/hexgrad/kokoro).
