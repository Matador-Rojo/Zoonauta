# Animales y hábitats: núcleo y PoC en consola

Versión 1.0.0 · 9 de octubre de 2026.

## 1. Qué se implementó

El programa carga los datos JSON y ejecuta la formalización del agente mediante
un gestor compartido. La consola recoge una acción, el gestor evalúa su permiso,
consulta la matriz o el motor de guía y devuelve una respuesta preparada.

La consola mantiene los 48 animales y las ocho opciones de hábitat. Acepta todas
las asociaciones confirmadas; las 315 pendientes producen una respuesta neutral.
No se asignan puntos competitivos, no hay límite de tiempo y pedir ayuda no penaliza.

Se implementaron ambas modalidades: en JUGADOR se elige el animal; en AGENTE se
recupera un escenario preconfigurado. El orden automático presenta primero un
animal de referencia por hábitat y después los restantes. Con N = 48 recorre los
48 animales. Un orden personalizado más corto se repite cuando se agota; repetir
animales como práctica está permitido por las reglas.

N sigue siendo configurable entre 1 y 48. El valor inicial de ocho retos es una
configuración editable de demostración. Cambiar N no reduce el catálogo.

## 2. Abrir y ejecutar en VS Code

1. Extrae el ZIP `poc_consola_animales_habitats_v1.zip`.
2. En VS Code, abre la carpeta que contiene `codigo`, `datos`, `docs` y `tests`.
3. Abre **Terminal → Nuevo terminal**.
4. Comprueba que tienes Python 3.10 o superior con `python --version`.
5. Ejecuta uno de los comandos siguientes desde esa carpeta.

No requiere `pip install` ni conexión de red para ejecutar el juego. Si tu
instalación de Windows utiliza el lanzador `py`, puedes sustituir `python` por `py`.

### Modalidad jugador

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 2
```

### Modalidad agente

```console
python -m codigo.poc.consola --modalidad AGENTE --retos 2
```

Si omites `--modalidad`, el programa pregunta quién inicia. Si omites `--retos`,
utiliza el valor configurado de ocho.

### Inspeccionar el selector probabilístico

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 2 --politica PROBABILISTICO --simbolos
```

`--simbolos` muestra los IDs y las etiquetas de la secuencia simbólica en esta
consola de inspección. Esas etiquetas todavía no son imágenes de pictogramas.

## 3. Controles de la partida

| Situación | Entrada |
|---|---|
| Elegir animal | Su número, por ejemplo `31`, o su ID, `A31`. |
| Elegir hábitat | Su número, por ejemplo `6`, o su ID, `H06`. |
| Pedir una nueva pista | `ayuda` o `a`. |
| Reproducir el contenido actual | `repetir` o `r`. |
| Pausar | `pausar` o `p`. |
| Reanudar | `reanudar` o `volver`. |
| Pasar al siguiente reto o al cierre | `continuar` o `c`, después de resolver. |
| Finalizar voluntariamente | `salir` o `s`. |

La consola muestra las entradas disponibles en cada fase. Las entradas fuera de
su fase no modifican el estado. Un fin de entrada o una interrupción de teclado
durante la partida produce una salida voluntaria y cierra sin etiqueta la ayuda
que estuviera abierta.

Repetir devuelve el mismo objeto de respuesta, con el mismo texto y la misma
secuencia. No pasa por el selector, no sube el nivel y no abre otra observación.
Durante el reto activo establece la señal auxiliar b = 1 para futuras ayudas.
La observación de la pista anterior conserva el contexto que tenía al presentarse.

## 4. Ejemplo para probar manualmente

Ejecuta la modalidad JUGADOR con un reto:

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 1
```

Escribe, en este orden:

```text
31
ayuda
repetir
pausar
reanudar
3
1
continuar
```

| Entrada | Resultado esperado |
|---|---|
| `31` | Presentar la capibara o ronsoco. |
| `ayuda` | Ofrecer una pista de nivel 1 hacia un entorno acuático. |
| `repetir` | Reproducir esa misma pista. |
| `pausar`, `reanudar` | Conservar animal, nivel, nodo, contenido y observación. |
| `3` | Desierto cálido: relación pendiente, respuesta neutral, sin aumentar nivel o progreso. |
| `1` | Selva tropical: asociación confirmada, reto resuelto aunque la guía apunte a agua dulce. |
| `continuar` | Mostrar el cierre de la partida. |

La selección pendiente cierra la atribución de la ayuda sin etiqueta. La selección
válida posterior completa el reto, pero no cambia ese cierre anterior.

## 5. Qué hace cada archivo de código

| Archivo | Responsabilidad |
|---|---|
| `codigo/nucleo/datos.py` | Cargar el banco, comprobar sus referencias y consultar la matriz. |
| `codigo/nucleo/estado.py` | Definir estado, evento, respuesta preparada y salida del gestor. |
| `codigo/nucleo/gestor.py` | Aplicar fases, transiciones, ayuda, pausa, repetición, cierre y protección de eventos. |
| `codigo/nucleo/registro.py` | Guardar eventos y observaciones como JSONL. |
| `codigo/motores/id3.py` | Calcular entropía y ganancias; construir y recorrer el árbol. |
| `codigo/motores/guia.py` | Elegir el contenido de la ruta y la variante según la política. |
| `codigo/respuestas/generador.py` | Resolver los slots del animal y del hábitat; preparar texto y símbolos. |
| `codigo/poc/consola.py` | Recoger entradas de teclado y presentar la interacción. |
| `codigo/poc/aceptacion.py` | Ejecutar los ocho recorridos esperados del diseño. |
| `codigo/poc/demo.py` | Mostrar cálculos de ID3 y las salidas de los ocho recorridos. |
| `tests/test_nucleo.py` | Comprobar comportamiento, registros, eventos y la consola completa. |

La futura interfaz digital importará `GestorPartida` y reutilizará sus métodos
`crear_evento`, `procesar`, `avanzar_preparacion` y `vista`. Los eventos conservan
sesión, evento y reto para impedir que una reconstrucción de pantalla o un clic
tardío ejecute otra vez una acción. La vista de interacción no expone K ni las
estimaciones; esos datos permanecen en la traza de inspección.

## 6. Árbol ID3 y políticas disponibles

El árbol se construye al preparar el motor, calculando las ganancias en cada nodo.
No se dibujan las rutas manualmente. Sobre los ocho perfiles actuales, la entropía
inicial es 3,00 bits y la raíz es entorno, con 2,00 bits de ganancia.

| Rama de la raíz | Atributo secundario calculado | Ganancia local |
|---|---|---:|
| Arbolado | Temperatura | 1,00 bit |
| Abierto y cálido | Vegetación | 1,00 bit |
| Acuático | Tipo de agua | 1,00 bit |
| Paisaje frío | Ubicación | 1,00 bit |

El nivel 1 recorre la raíz; el nivel 2 llega a una hoja; el nivel 3 hace explícita
la opción de guía. Llegar a una hoja no resuelve el reto: se requiere una selección
confirmada del jugador. K describe las hojas de la ruta, no los hábitats válidos
del animal, y nunca se utiliza para ocultar opciones.

| Política | Elección de variante |
|---|---|
| `ID3` | Presentación fija V1. |
| `ROTACION` | Alternar V1, V2 y V3 por pareja de hábitat y nivel. |
| `PROBABILISTICO` | Elegir la mayor media bayesiana entre las variantes elegibles. |

La política probabilística excluye la última variante de esa pareja cuando hay
alternativas. Los empates se resuelven en orden V1, V2, V3. Al solicitar Ayuda otra
vez en nivel 3 puede cambiar la variante, conservando el nivel; Repetir conserva
exactamente la forma anterior.

Los parámetros actuales siguen siendo 144 distribuciones Beta(1,1). Su media
inicial de 0,5 es una configuración previa, no un resultado de jugadores. Esta
implementación ejecuta el selector congelado y registra sus resultados; todavía
no ejecuta Thompson Sampling ni el aprendizaje bayesiano por simulación.

## 7. Registro de eventos y observaciones

Cada sesión de consola crea un JSONL en `datos/registros`, con un nombre único.
`--registro` permite elegir otra ruta. Contiene eventos aceptados e ignorados,
estados anterior y posterior, respuestas emitidas y trazas de decisión.

Las observaciones se abren cuando el gestor emite una ayuda preparada. Una llamada
aislada a `motor.decidir` no cambia el estado, no guarda una exposición y no abre
una observación. El adaptador recibe la respuesta emitida para presentarla.

| Evento posterior a una ayuda | Cierre |
|---|---|
| Selección válida | Resultado 1. |
| Nueva ayuda o asociación incorrecta verificada | Resultado 0. |
| Selección pendiente o salida | Sin etiqueta, representada por `null`. |
| Repetir, pausar, reanudar o esperar | Conservar la observación abierta. |

Cada observación se cierra como máximo una vez. Los parámetros no se actualizan
durante estas sesiones. Los resultados de control llevan procedencia sintética;
la consola manual lleva `CONSOLA_MANUAL`, que no implica una evaluación en Kallpa.
La pausa conserva el estado en el proceso activo; no se implementó recuperar una
partida después de cerrar el programa.

## 8. Demostración automática y comprobaciones ejecutadas

```console
python -m codigo.poc.demo
python -m codigo.poc.aceptacion
python -m unittest discover -s tests -v
```

Para guardar una nueva ejecución de la demostración:

```console
python -m codigo.poc.demo --salida resultados_demo
```

Ese comando crea o reemplaza en la carpeta indicada `demo_consola.txt`,
`arbol_id3.json`, `casos_ejecutados.json` y `eventos_demo.jsonl`.

Durante la preparación se ejecutaron correctamente los ocho casos de aceptación
y 19 pruebas automáticas. Estas incluyen todas las asociaciones de la matriz,
una partida automática con los 48 animales, los tres selectores y sesiones de
consola por ambas modalidades. La evidencia está en `docs/resultados`.

Reconocer los mismos ocho perfiles usados para construir ID3 comprueba la
estructura del árbol. Las pruebas de consola y de reglas comprueban el programa;
no representan generalización a ecosistemas nuevos ni eficacia con jugadores.

## 9. Texto para incorporar al informe

Se implementó una prueba de concepto textual sobre un núcleo común en Python. El
gestor ejecuta las fases y transiciones formalizadas, conserva el catálogo de
48 animales y presenta las ocho opciones de hábitat en cada reto. La evaluación
consulta la matriz de conocimiento y acepta cualquiera de las asociaciones
confirmadas; las relaciones pendientes reciben una respuesta neutral.

El baseline ID3 se construyó calculando la entropía y la ganancia de información
sobre los ocho perfiles didácticos de hábitat. El motor recorre la ruta de una
asociación de guía confirmada y conserva separados ese recorrido y la evaluación
de la selección del jugador. Se añadieron políticas de rotación y selección
probabilística de variantes, utilizando en esta fase parámetros iniciales
congelados y registrando las observaciones para el aprendizaje posterior.

La comprobación incluyó los ocho recorridos de aceptación y 19 pruebas
automáticas del núcleo y de la consola. Se verificaron la aceptación de
asociaciones adicionales, el tratamiento de pendientes, la conservación del
estado al repetir y pausar, el límite de nivel y la protección frente a eventos
duplicados o de retos anteriores. La implementación de pictogramas gráficos,
voz y selección por clic o toque corresponde a la siguiente etapa.

## 10. Alcance de esta entrega

Esta entrega contiene el código completo del núcleo y de la consola, los datos
JSON y las salidas de las pruebas de control. Las secuencias son simbólicas y los
textos de voz están preparados, pero no se reproducen audio ni imágenes.

Siguen pendientes la interfaz digital, los recursos visuales, el adaptador de
voz, el aprendizaje bayesiano con simulaciones separadas y la comparación
experimental. No es el ZIP final del trabajo parcial ni incluye la exposición.

Las especificaciones consultadas se conservan en `docs/diseno`; describen las
decisiones anteriores a esta implementación. La documentación del banco inicial
está en `docs/datos`. Esta guía y los resultados indican qué se ejecutó ahora.

