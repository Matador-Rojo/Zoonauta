# Animales y hábitats: diseño del modelo principal probabilístico

Versión 1 · 9 de octubre de 2026 · Especificación de diseño

## 1. Técnica elegida y decisión que aprenderá

Se propone un sistema experto probabilístico para seleccionar variantes de ayuda. Combina las reglas del juego, la ruta de contenido obtenida mediante ID3 y un modelo bayesiano que estima el resultado de las variantes a partir de interacciones registradas.

El enunciado admite un modelo principal de ML, RL o heurística avanzada y menciona expresamente los sistemas expertos probabilísticos. Esta propuesta desarrolla esa alternativa: las restricciones proceden de reglas explícitas y la elección entre intervenciones permitidas depende de probabilidades estimadas.

La decisión aprendida es qué forma de presentar la pista del nivel correspondiente conviene ofrecer en el contexto actual. El agente mantiene los niveles 0–3 y la regla de avance l' = min(l + 1, 3). La adaptación afecta al contenido estructurado y a su forma de presentación; no altera la validez de los hábitats.

La selección automática de animales queda fuera de este modelo de asistencia inicial. Ambas modalidades de inicio utilizan el mismo selector de pistas después de presentar el reto.

## 2. Funciones de cada componente

| Componente | Responsabilidad |
|---|---|
| Matriz animal–hábitat | Evaluar la selección del jugador como válida, incorrecta validada o pendiente. |
| Reglas del juego | Controlar fases, niveles, repetición, pausa, progreso y finalización. |
| Árbol ID3 | Determinar los atributos de la ruta de guía y el contenido informativo de los niveles 1 y 2. |
| Banco de variantes | Ofrecer distintas secuencias de pictogramas con la información permitida para cada nivel. |
| Modelo bayesiano | Estimar, entre observaciones con resultado etiquetado, la probabilidad de una selección válida antes de una nueva ayuda. |
| Selector del modelo principal | Elegir una variante permitida según las estimaciones y el historial de variantes presentadas. |

El conjunto de hábitats válidos V(x) conserva todas las asociaciones confirmadas. La guía hacia g = ref(x) no convierte ese hábitat en la única respuesta aceptada.

## 3. Información observable y contexto de decisión

La política utiliza el estado del juego y una señal sencilla de interacción: si el jugador ha utilizado «Repetir» durante el reto activo.

El contexto estadístico es:

$$
z=(g,l',b)
$$

| Variable | Significado |
|---|---|
| g | Hábitat de guía confirmado para el animal actual. |
| l' | Nivel de la ayuda que va a presentarse: 1, 2 o 3. |
| b | 0 si todavía no se ha utilizado «Repetir» durante este reto; 1 si ya se utilizó. |

b se reinicia a 0 al preparar cada reto. Cambia a 1 cuando se pulsa «Repetir» en ESPERANDO_RESPUESTA y permanece así hasta el siguiente reto. Esta señal solo registra una acción observable; no implica que el jugador haya cometido un error ni que tenga una determinada capacidad.

El contexto contiene 8 × 3 × 2 = 48 combinaciones posibles. Con tres variantes por combinación se mantienen 144 distribuciones de probabilidad.

Los datos se agrupan por hábitat de guía, nivel y uso de repetición. Esta versión no aprende un perfil individual permanente ni estima un diagnóstico. Tampoco supone que todos los animales de un mismo grupo sean igualmente fáciles: esa diferencia será una limitación que deberá revisarse con datos.

La modalidad de inicio, el animal y el último resultado siguen disponibles en el estado general para aplicar las reglas, aunque no sean dimensiones de esta primera tabla estadística.

## 4. Banco de variantes de ayuda

Se define una versión ampliada de la función de pistas:

$$
P(x,l,v)
$$

v identifica la forma de presentar la información:

| Variante | Forma de intervención | Ejemplo con una pista de nivel 2 para la jirafa |
|---|---|---|
| V1: descripción | Presentar directamente la característica que debe buscarse. | «Busca mucho pasto y árboles separados». |
| V2: relación | Vincular el animal con esa misma característica. | «La jirafa vive en un lugar con mucho pasto y árboles separados». |
| V3: pregunta | Formular una consulta breve sobre la característica. | «¿Qué lugar tiene mucho pasto y árboles separados?». |

Las tres variantes mantienen el mismo objetivo de selección de hábitat. Una pregunta V3 no añade una pregunta auxiliar que el jugador tenga que responder en otra pantalla.

Las frases son textos de apoyo para explicar el diseño. Su salida principal deberá ser una secuencia de pictogramas; el texto y la voz la acompañarán. Las secuencias concretas y su comprensión todavía deben prepararse y revisarse. Una diferencia de redacción que produzca la misma secuencia de pictogramas no contará como una variante distinta.

### Información permitida por nivel

| Nivel | Información que pueden comunicar las variantes |
|---|---|
| 0 | Pregunta inicial sobre el animal, sin pistas de hábitat. El selector probabilístico todavía no interviene. |
| 1 | El valor del atributo raíz de ID3 correspondiente a g: entorno principal. |
| 2 | El atributo que diferencia las tarjetas de la rama, conservando el contexto de la pista anterior. |
| 3 | El nombre y pictograma de g, con una invitación explícita a seleccionarlo. |

Por ejemplo, para la sabana:

| Nivel | V1: descripción | V2: relación | V3: pregunta |
|---|---|---|---|
| 1 | Busca un lugar abierto y cálido. | La jirafa vive en un lugar abierto y cálido. | ¿Qué lugar es abierto y cálido? |
| 2 | Busca mucho pasto y árboles separados. | La jirafa vive en un lugar con mucho pasto y árboles separados. | ¿Qué lugar tiene mucho pasto y árboles separados? |
| 3 | Una opción es la sabana. Toca su pictograma. | La jirafa puede vivir en la sabana. Toca su pictograma. | ¿Puedes señalar la sabana? |

La referencia al animal se sustituirá por el animal activo y su pictograma. Solo se utilizarán plantillas verificadas como apropiadas para la asociación y el perfil de escena correspondiente.

El banco propuesto necesita 8 hábitats × 3 niveles × 3 variantes = 72 plantillas parametrizadas. Es una especificación de contenido pendiente de elaboración completa; este documento no afirma que las 72 secuencias estén creadas. Los 48 animales se insertarán como parámetros, sin convertir estas plantillas en 432 observaciones reales de aprendizaje.

Las 144 pistas por animal ya preparadas conservan su identidad. Podrán incorporarse como variantes cuando se compruebe su correspondencia con los niveles y atributos, sin asumir que todas sirven automáticamente para este selector.

## 5. Reglas expertas que restringen la decisión

La política probabilística actúa después de aplicar las reglas siguientes:

1. Intervenir con una nueva pista solo cuando se solicita «Ayuda» o cuando se evalúa una asociación expresamente validada como incorrecta.
2. Calcular l' = min(l + 1, 3) y recuperar exclusivamente variantes del nivel resultante.
3. Usar contenido verificado para g; no generar asociaciones nuevas.
4. Mantener disponibles las ocho opciones de hábitat.
5. Aceptar cualquier selección incluida en V(x), aunque difiera de g.
6. Tratar las relaciones pendientes de forma neutral, conservando el nivel.
7. Reproducir exactamente u al utilizar «Repetir», sin pasar por el selector de variantes.
8. Conservar el reto durante una pausa y esperar indefinidamente si no existe interacción.
9. Ante una nueva solicitud de ayuda, evitar la última variante utilizada para ese mismo hábitat y nivel cuando exista otra variante disponible.

En la matriz actual I = ∅: la regla para una respuesta incorrecta validada permanece especificada, pero una celda pendiente nunca activa esa transición.

Se mantiene v_ant(g,l), la última variante presentada en la sesión para cada pareja de hábitat y nivel. Esta memoria puede proceder de un reto anterior. Se reinicia al comenzar una nueva sesión.

Sea W(x,g,l') el conjunto de variantes verificadas y disponibles. El conjunto elegible es:

$$
E=
\begin{cases}
W\setminus\{v_{\mathrm{ant}}(g,l')\},
& |W|>1\ \land\ v_{\mathrm{ant}}(g,l')\in W\\
W, & \text{en otro caso}
\end{cases}
$$

La restricción reduce la repetición automática de formas de ayuda. El botón «Repetir» permite recuperar la forma anterior deliberadamente.

Si solo existe una variante verificada, se utiliza esa variante. Si falta una variante nueva, se conserva la pista base validada del nivel correspondiente. La carencia de contenido no se resuelve inventando mensajes.

## 6. Resultado observable de una intervención

Al presentar una variante se abre una observación d = (z,v). Solo puede existir una observación abierta a la vez.

El resultado y se define sobre la interacción posterior:

| Evento después de la pista | Registro para el aprendizaje |
|---|---|
| Selección válida antes de una nueva ayuda | y = 1; cerrar la observación. |
| Nueva solicitud de ayuda antes de resolver | y = 0; cerrar la observación y después presentar la nueva ayuda. |
| Selección incorrecta expresamente validada | y = 0; cerrar la observación y después aplicar la siguiente ayuda. |
| Selección pendiente | Cerrar la observación sin etiqueta; no actualizar el modelo. |
| Repetir | Mantener la observación abierta; no registrar un resultado adicional. |
| Pausar y reanudar | Mantener la observación abierta; no registrar un resultado adicional. |
| Salir o terminar el registro sin resolver | Cerrar la observación sin etiqueta; no actualizar el modelo. |
| Ausencia de interacción | Mantener la observación abierta; no registrar un resultado ni usar un tiempo límite. |

Una selección válida tras utilizar «Repetir» puede producir y = 1: el objetivo de esta señal es una selección válida antes de una nueva ayuda, no necesariamente tras una única reproducción del mensaje.

y = 0 indica que el registro alcanzó otra intervención o una respuesta incorrecta validada antes de resolver. No evalúa negativamente el acto de pedir ayuda. La señal se utiliza para estimar el resultado de la forma de asistencia.

Al llegar a un resultado pendiente se interrumpe la atribución a la pista anterior porque el mensaje neutral constituye otra intervención. Si después se produce una selección válida sin una nueva ayuda, esa selección completa el reto, pero no actualiza una observación de pista ya cerrada.

Cada observación recibe como máximo una etiqueta. Las confirmaciones y los clics posteriores al reto resuelto no generan resultados duplicados.

## 7. Estimación bayesiana

Para cada contexto z y variante v se estima el resultado entre registros que pudieron etiquetarse. Sea o = 1 cuando existe una etiqueta 0 o 1:

$$
p_{z,v}=P(y=1\mid z,v,o=1)
$$

Se propone el modelo Beta–Bernoulli:

$$
p_{z,v}\sim\operatorname{Beta}(1,1)
$$

Tras observar a resultados etiquetados como 1 y e resultados etiquetados como 0:

$$
p_{z,v}\mid D\sim\operatorname{Beta}(1+a,1+e)
$$

La probabilidad predictiva es:

$$
\widehat p_{z,v}=\frac{1+a}{2+a+e}
$$

La actualización equivale a incrementar α cuando y = 1 o β cuando y = 0. Los registros sin etiqueta no modifican ninguno.

La distribución inicial Beta(1,1) es una decisión de configuración: expresa ausencia de preferencia inicial. No representa observaciones reales ni una probabilidad pedagógica validada.

La estimación supone una probabilidad aproximadamente estable dentro de cada pareja contexto–variante y observaciones adecuadas para ese agrupamiento. Fatiga, familiaridad con un animal, diferencias entre personas y otras variables pueden modificar el resultado y no están completamente representadas en z.

La probabilidad describe la señal de interacción definida en la sección anterior, condicionada a que el registro pudo etiquetarse. No equivale a comprensión, aprendizaje duradero o efecto terapéutico. Si los cierres sin etiqueta son frecuentes o dependen de la variante, las estimaciones pueden representar grupos de observaciones diferentes; por eso se informará su proporción por contexto y variante, sin interpretar estas estimaciones como probabilidades incondicionales de todos los retos.

## 8. Elección de la variante y aprendizaje preliminar

### Política de ejecución

Durante la evaluación de la PoC se congelarán los parámetros aprendidos. La variante se elegirá mediante:

$$
v^*=\arg\max_{v\in E}\widehat p_{z,v}
$$

Los empates se resolverán con el orden V1, V2 y V3. Con parámetros iniciales iguales, la primera ayuda usa V1; si V1 queda excluida por repetición, se utiliza la primera alternativa elegible.

El criterio maximiza la probabilidad estimada de la señal inmediata entre las variantes permitidas y los registros etiquetados. No demuestra una política global óptima ni garantiza resolver con menos ayudas en todos los casos.

Se registrarán la variante elegida, las alternativas elegibles, sus estimaciones y la razón de cualquier exclusión. De ese modo una decisión puede explicarse a partir de las reglas y los datos utilizados.

### Aprendizaje en el simulador

En la futura PoC se podrá explorar las variantes mediante Thompson Sampling: se toma una muestra de cada distribución Beta elegible y se selecciona la variante con mayor muestra. Después se actualiza solo la variante que se presentó y tuvo un resultado etiquetado.

El simulador aplicará las mismas restricciones de fase, nivel, asociaciones y repetición. El muestreo sirve para recopilar resultados de distintas variantes, evitando evaluar únicamente la variante que empezó con una estimación mayor.

La combinación de contextos discretos, restricciones expertas y selección de variantes es una aplicación propia al juego. No se trasladan automáticamente a esta política las garantías teóricas del problema de bandits sin restricciones.

La primera implementación recogerá y aprenderá de interacciones sintéticas. La política de evaluación permanecerá congelada para que sus resultados puedan compararse. Incorporar registros de jugadores reales será una fase posterior; los datos sintéticos y reales conservarán su procedencia y no se mezclarán como si fueran equivalentes.

## 9. Ejemplo numérico de una decisión

Los datos siguientes son inventados únicamente para explicar el cálculo. No proceden de una prueba ejecutada ni de jugadores reales.

Supongamos que el reto presenta a la jirafa, con g = H02, y corresponde entregar una ayuda de nivel 2. El jugador ya utilizó «Repetir», por lo que z = (H02,2,1).

La última variante utilizada para H02 y nivel 2 en un reto anterior de la misma sesión fue V3. Las tres variantes están disponibles:

| Variante | Resultados y = 1 | Resultados y = 0 | Posterior | Probabilidad predictiva | Elegible |
|---|---:|---:|---|---:|---|
| V1 | 6 | 4 | Beta(7,5) | 7/12 = 58,33 % | Sí |
| V2 | 8 | 2 | Beta(9,3) | 9/12 = 75,00 % | Sí |
| V3 | 9 | 1 | Beta(10,2) | 10/12 = 83,33 % | No: fue la última variante de esa pareja. |

El selector elige V2 entre las variantes elegibles:

«La jirafa vive en un lugar con mucho pasto y árboles separados».

Las ocho tarjetas de hábitat siguen disponibles. Si el jugador selecciona la sabana, C(A08,H02) = VALIDA y el reto se completa.

Ese resultado se registra como y = 1 para V2. Durante una fase de aprendizaje, la posterior cambiaría de Beta(9,3) a Beta(10,3), con media 10/13 = 76,92 %. Durante la evaluación congelada se registra el resultado, pero no se modifica el modelo hasta una fase posterior de entrenamiento.

El ejemplo muestra que la restricción de variedad puede excluir la mayor estimación absoluta. La política selecciona la mejor estimación dentro de E; esa restricción tiene un coste potencial que deberá medirse.

## 10. Extensión del estado y transiciones

El estado de interacción ampliado será:

$$
s_{\mathrm{principal}}=(s,n,b,v_{\mathrm{ant}},d)
$$

s contiene las variables ya formalizadas. n sigue siendo el nodo de la ruta ID3. Los parámetros probabilísticos Θ = {α_zv, β_zv} se guardan como modelo separado; durante la evaluación permanecen fijos.

| Evento | Cambios relevantes |
|---|---|
| Preparar reto | Reiniciar n en la raíz, l = 0, b = 0 y d = ⊥; conservar la memoria de variantes de la sesión. |
| Pedir ayuda | Cerrar d con y = 0 si seguía abierta; calcular l'; construir E y z; seleccionar v; presentar P(x,l',v); actualizar n, l, u y v_ant; abrir una nueva d. |
| Repetir en ESPERANDO_RESPUESTA | Reproducir u exactamente; establecer b = 1; conservar el estado educativo, n y la observación d. |
| Selección válida | Cerrar d con y = 1 si estaba abierta; aplicar la confirmación y el incremento único de c establecidos en la formalización. |
| Selección pendiente | Cerrar d sin etiqueta; emitir el mensaje neutral; conservar l, n y c. |
| Selección incorrecta validada | Cerrar d con y = 0 si estaba abierta; avanzar el nivel y seleccionar la nueva variante como en una solicitud de ayuda. |
| Pausar y reanudar | Conservar n, b, v_ant y d junto al estado previo. |
| Repetir en RETO_RESUELTO | Reproducir la confirmación; no abrir ni actualizar observaciones de pistas. |
| Continuar | Pasar a selección de animal o al cierre, según c y N; al preparar un nuevo reto reiniciar los datos locales. |
| Salir | Cerrar cualquier d sin etiqueta y finalizar voluntariamente. |

La primera ayuda de un reto abre una observación nueva aunque no hubiera una observación anterior que cerrar.

b cambia como dato auxiliar cuando se utiliza «Repetir». El nivel, el contenido u y el progreso c se conservan, tal como exige la regla de repetición.

### Refinamiento respecto de los documentos anteriores

La función original P(x,l) pasa a P(x,l,v). La regla de avance de nivel se conserva. Al solicitar «Ayuda» cuando l = 3, el apoyo seguirá siendo explícito y de nivel 3, pero podrá presentarse con otra variante. «Repetir» seguirá reproduciendo exactamente u.

Este refinamiento desarrolla la selección de variantes prevista en la formalización. El baseline ID3 conserva V1 como su presentación fija.

## 11. Datos que necesitará la futura PoC

Cada observación de ayuda tendrá un registro con los campos siguientes:

| Campo | Uso |
|---|---|
| sesion_id y reto_id | Agrupar los eventos y evitar duplicados. |
| origen | Distinguir simulación de registros reales. |
| animal_id y habitat_guia | Identificar el escenario. |
| nivel y repeticion_previa | Reconstruir z. |
| variante_id y contenido_id | Identificar qué se presentó. |
| variantes_elegibles y variante_anterior | Explicar las restricciones de la decisión. |
| modelo_version | Identificar los parámetros utilizados. |
| evento_cierre | Selección válida, nueva ayuda, pendiente, salida u otro cierre. |
| resultado | 1, 0 o sin etiqueta. |

El catálogo animal–hábitat no contiene estos resultados: los 48 animales son contenido del juego, no 48 usuarios ni 48 experiencias de aprendizaje.

Para el Hito 1 se propone un simulador con condiciones declaradas:

- Condición uniforme: todas las variantes tienen la misma probabilidad de y = 1.
- Condición con diferencias: algunas variantes tienen mayor probabilidad que otras.
- Condición dependiente de contexto: la variante más favorable cambia al cambiar b.
- Casos de control: resultados pendientes, repeticiones, pausas y salida.

Las probabilidades del simulador serán parámetros sintéticos explícitos. Permitirán comprobar si el selector recupera diferencias introducidas artificialmente; no demostrarán que esas diferencias existen en Kallpa.

Los casos y semillas de entrenamiento se separarán de los de evaluación. Los parámetros se congelarán antes de evaluar. La separación permitirá estudiar el comportamiento en nuevas simulaciones del mismo entorno, sin presentarlo como validación con personas.

## 12. Comparación con el baseline

Se utilizarán el mismo catálogo, las mismas asociaciones, las mismas ocho opciones y los mismos niveles de ayuda.

| Aspecto | Baseline ID3 | Modelo principal |
|---|---|---|
| Contenido informativo | Ruta de atributos del árbol. | La misma ruta y límites por nivel. |
| Presentación de la pista | V1 fija. | Variante elegida mediante probabilidades y reglas. |
| Historial de repetición | No modifica la elección de variante. | Forma parte del contexto observable. |
| Variedad automática | Mantiene su plantilla fija. | Evita la última variante cuando hay alternativas. |
| Aprendizaje de resultados de asistencia | No estima resultados de variantes. | Actualiza distribuciones con observaciones etiquetadas durante entrenamiento. |
| Evaluación del hábitat | Matriz de asociaciones. | La misma matriz. |

Para separar el efecto del aprendizaje y el de la variedad se recomienda comparar tres políticas en la futura PoC:

1. ID3 con V1 fija.
2. Rotación V1–V2–V3 mediante reglas, sin aprender probabilidades.
3. Modelo probabilístico con las restricciones descritas.

Si el modelo principal obtiene menos repeticiones automáticas, pero no mejora respecto de la rotación en la señal y, deberá explicarse ese resultado. La novedad de los mensajes por sí sola no prueba una mejora del aprendizaje.

### Indicadores

| Indicador | Definición y límite |
|---|---|
| Selección válida antes de una nueva ayuda | Proporción de y = 1 entre observaciones etiquetadas; mide el resultado inmediato definido. |
| Observaciones sin etiqueta | Número y proporción de cierres pendientes o incompletos, también por contexto y variante; se informa por separado. |
| Retos completados | Proporción de retos resueltos; distinguir salida voluntaria y registros interrumpidos. |
| Ayudas por reto completado | Número medio de nuevas ayudas; usar ayuda no reduce una puntuación del jugador. |
| Repetición automática de variantes | Frecuencia con que se repite la misma variante para g y l cuando había alternativas; separar el botón «Repetir». |
| Tiempo de decisión del motor | Duración del cálculo del selector; no se usa como límite de tiempo para el jugador. |
| Cambios por contexto | Comprobar si z distintos producen decisiones distintas cuando los datos lo justifican. |

No hay resultados experimentales todavía. La comparación podrá mostrar ventajas, resultados similares o costes de la restricción de variedad.

## 13. Comprobaciones necesarias

Antes de integrar el modelo en la interfaz deberá verificarse:

1. Una respuesta adicional confirmada completa el reto aunque no coincida con g.
2. Una selección pendiente no aumenta el nivel ni genera una etiqueta 0.
3. «Repetir» reproduce u y conserva la observación abierta.
4. Pausar y reanudar conservan el mismo reto y observación.
5. «Ayuda» avanza como 0 → 1 → 2 → 3 → 3.
6. Una nueva ayuda en nivel 3 conserva el apoyo explícito y puede cambiar su variante.
7. Una etiqueta incrementa una sola vez el parámetro correspondiente.
8. Ninguna etiqueta procede únicamente de ausencia de interacción o salida.
9. Una variante excluida por repetición no se selecciona si hay otra disponible.
10. La falta de datos produce un criterio de desempate reproducible.
11. La falta de variantes recupera una pista base validada.
12. Los clics posteriores a RETO_RESUELTO no duplican el progreso ni las observaciones.
13. El modelo permanece congelado durante la evaluación comparativa.
14. El informe identifica los datos y resultados sintéticos.

Son criterios de aceptación del diseño. No se han implementado ni ejecutado como pruebas de un programa.

## 14. Texto para incorporar al documento técnico

El modelo principal será un sistema experto probabilístico para seleccionar variantes de asistencia. Las reglas del juego determinarán qué intervenciones son válidas y mantendrán los tres niveles progresivos de ayuda. El árbol ID3 proporcionará la ruta de atributos del hábitat de guía, mientras que el selector probabilístico elegirá la forma de comunicar la pista entre variantes verificadas de descripción, relación y pregunta.

El contexto incluirá el hábitat de guía, el nivel de ayuda que va a presentarse y el uso previo del botón «Repetir» durante el reto. Para cada contexto y variante se estimará, mediante un modelo Beta–Bernoulli, la probabilidad de una selección válida antes de una nueva ayuda entre los registros con resultado etiquetado. Las asociaciones pendientes y los registros interrumpidos no se utilizarán como resultados negativos y su proporción se informará por separado.

El agente elegirá la variante con mayor probabilidad estimada entre las alternativas permitidas, evitando la última variante de la misma pareja hábitat–nivel cuando exista otra disponible. El botón «Repetir» conservará su función de reproducción exacta. Las ocho opciones seguirán seleccionables y la matriz animal–hábitat aceptará cualquier asociación confirmada.

La viabilidad inicial se estudiará mediante simulaciones con parámetros explícitos, separando entrenamiento y evaluación. Los resultados permitirán analizar la selección de intervenciones y compararla con ID3 y una rotación sin aprendizaje. Su efectividad con jugadores reales y su valor pedagógico requerirán una evaluación posterior.

## 15. Referencias y estado del trabajo

- Cornell University. Estimating Probabilities from Data. CS4780, 2018. https://www.cs.cornell.edu/courses/cs4780/2018fa/lectures/lecturenote04.html
- Agrawal, S., y Goyal, N. (2012). Analysis of Thompson Sampling for the Multi-armed Bandit Problem. Proceedings of Machine Learning Research, 23, 39.1–39.26. https://proceedings.mlr.press/v23/agrawal12.html
- TP-TF-1ASI0404-Enunciado - 2026-20.pdf, requerimiento de modelo principal.
- baseline_id3_animales_habitats.md, consultado el 9 de octubre de 2026.
- formalizacion_agente_animales_habitats.md, consultado el 9 de octubre de 2026.
- matriz_animales_habitats_48.md, consultado el 9 de octubre de 2026.

Las referencias técnicas respaldan la estimación bayesiana y el muestreo de Thompson. El contexto elegido, las etiquetas de interacción, las variantes, las restricciones y su aplicación al juego son decisiones de diseño propias.

Esta entrega contiene la especificación del modelo principal. Todavía están pendientes el banco completo de variantes, el simulador, el entrenamiento, los resultados de comparación y la interfaz. El paso siguiente es definir la arquitectura que conectará estos componentes.

