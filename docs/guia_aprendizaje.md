# Animales y hábitats: ejecutar el aprendizaje y la comparación

Versión 2.0.0 · 9 de octubre de 2026.

## 1. Abrir el proyecto

Extrae el ZIP y abre en VS Code la carpeta que contiene `codigo`, `datos`, `docs`
y `tests`. Utiliza Python 3.10 o superior. El núcleo, el aprendizaje y el informe
utilizan únicamente la biblioteca estándar. En Windows puedes usar `py` en lugar
de `python` si tu instalación utiliza ese lanzador.

El gráfico ya está incluido. Volver a exportar el PNG requiere matplotlib;
el experimento funciona sin esa dependencia cuando omites `--grafico`.

## 2. Resultados incluidos

Abre `docs/experimentos/informe_comparacion.md`. Se ejecutaron tres condiciones
y seis réplicas: 34 560 retos de entrenamiento y 51 840 de evaluación.
Se guardaron 18 modelos y 54 corridas de evaluación, con procedencia sintética.
Las 26 pruebas automáticas pasaron e incluyen los ocho casos de aceptación
de la primera PoC y las nuevas comprobaciones del aprendizaje.

## 3. Repetir el experimento completo

```console
python -m codigo.entrenamiento.experimento --salida resultados_nuevos
```

La configuración está en `datos/configuracion_experimentos.json`: 1 920 retos
de entrenamiento y 960 de evaluación por condición, réplica y política.
Cada réplica entrena un modelo propio y lo evalúa congelado con semillas distintas.
Elige una carpeta nueva para conservar las ejecuciones anteriores.

Si tienes matplotlib y quieres volver a generar el gráfico:

```console
python -m codigo.entrenamiento.experimento --salida resultados_con_grafico --grafico
```

Las decisiones y métricas de conteo son reproducibles con la misma versión y
semillas. Los tiempos del motor y los metadatos de compresión pueden variar.

## 4. Prueba pequeña de funcionamiento

```console
python -m codigo.entrenamiento.experimento --salida prueba_pequena --replicas 2 --entrenamiento 96 --evaluacion 48 --sin-registros
```

Una ejecución pequeña puede dejar contextos insuficientemente cubiertos;
sirve para comprobar el recorrido y no sustituye la comparación incluida.

## 5. Jugar con un modelo aprendido

Ejemplo con el modelo contextual de la primera réplica:

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 2 --politica PROBABILISTICO --parametros docs/experimentos/modelos/SIM_CONTEXTUAL_R01.json
```

La réplica se elige por su posición predefinida, no por sus resultados.
La consola carga el modelo congelado y no aprende de las entradas de esta sesión.
Sin `--parametros`, utiliza los priors originales Beta(1,1).

## 6. Archivos nuevos

| Archivo | Responsabilidad |
|---|---|
| `codigo/entrenamiento/bayes.py` | Actualizaciones únicas de α y β; exploración Thompson Sampling. |
| `codigo/entrenamiento/simulador.py` | Acciones legales al gestor y probabilidades sintéticas explícitas. |
| `codigo/entrenamiento/experimento.py` | Entrenamiento separado, evaluación congelada y comparación. |
| `codigo/entrenamiento/grafico.py` | Exportar el gráfico; matplotlib es opcional. |
| `datos/configuracion_experimentos.json` | Réplicas, semillas, tamaños y acciones del simulador. |
| `tests/test_aprendizaje.py` | Actualizaciones, procedencia, congelación y ejecución completa. |

El gestor admite un motor preparado. Al pedir otra ayuda, cierra primero la
observación anterior. El registro de entrenamiento actualiza la posterior antes
de elegir la siguiente intervención. En evaluación registra sin aprender.

Una selección válida cierra con y = 1; una nueva ayuda, con y = 0.
Se incrementa α para 1 y β para 0. Una selección pendiente o salida cierra
con null. Repetir y pausar conservan la observación; el contexto es el de la
pista emitida. Estas etiquetas no asignan puntos al jugador.

El tope de 30 ayudas protege solo al simulador. Un corte cierra sin etiqueta.
La consola conserva el tiempo y los intentos sin límite.

## 7. Inspeccionar y comprobar

`resumen_experimentos.json` contiene medias entre semillas y desviaciones estándar.
`corridas` conserva la cobertura por hábitat, nivel, b y variante. Los tiempos
miden el cálculo del motor en este equipo; no son límites para el jugador.

Los registros JSONL se comprimieron. Para consultar cinco observaciones en Python:

```python
import gzip
import json
from itertools import islice

ruta = "docs/experimentos/observaciones_EVAL_SIM_CONTEXTUAL_R01_PROBABILISTICO.jsonl.gz"
with gzip.open(ruta, "rt", encoding="utf-8") as archivo:
    for linea in islice(archivo, 5):
        print(json.loads(linea))
```

Para ejecutar los controles:

```console
python -m codigo.poc.aceptacion
python -m unittest discover -s tests -v
python -m codigo.entrenamiento.auditar --resultados docs/experimentos
```

## 8. Interpretación y siguiente etapa

El informe conserva el caso favorable a ID3 y el favorable al probabilístico.
En la condición uniforme las políticas comparten los sorteos y todas las variantes
tienen igual probabilidad; por eso sus resultados fueron exactamente iguales.

Los resultados no prueban comprensión ni eficacia con personas. La interfaz de
pictogramas, la selección por clic o toque y la voz corresponden a la siguiente
etapa. Los documentos anteriores se conservan como antecedentes; esta guía y
el informe describen el aprendizaje sintético ya ejecutado.

