# Animales y hábitats: diseño del baseline con ID3

Versión 1 · 9 de octubre de 2026

## 1. Técnica seleccionada y propósito

Se propone un árbol de decisión ID3 como baseline del motor de guía. El árbol organizará los atributos de las fichas de hábitat mediante ganancia de información y permitirá ordenar las pistas desde una característica general hasta una opción explícita.

ID3 construye un árbol a partir de ejemplos categóricos. En cada nodo selecciona el atributo que más reduce la entropía de las clases, divide los ejemplos según sus valores y repite el proceso en los subconjuntos restantes.

La aplicación de esta técnica al juego es una decisión de diseño: el árbol orienta hacia el hábitat de guía g, una asociación ya confirmada del animal. Las respuestas del jugador se evalúan con la función C(x,h) y la matriz de asociaciones. Si una respuesta distinta de g también está confirmada, se acepta y el reto se resuelve.

El baseline será determinista y explicable. No se le atribuye todavía personalización aprendida de interacciones reales.

## 2. Qué información utiliza

El motor dispone de:

| Entrada | Uso |
|---|---|
| Animal x | Recuperar el escenario y las asociaciones confirmadas del animal. |
| Hábitat de guía g = ref(x) | Elegir la ruta de pistas de una asociación válida. |
| Nivel de ayuda l | Distinguir pregunta inicial, pista general, pista concreta y opción explícita. |
| Fase y acción recibida | Determinar si corresponde evaluar, ayudar, repetir, esperar o confirmar. |
| Resultado C(x,h) | Aplicar la transición de respuesta válida, incorrecta validada o pendiente. |
| Perfil descriptivo de g | Recorrer el árbol construido mediante ID3. |
| Nodo actual del árbol | Continuar desde la pista ya proporcionada. |

La modalidad de inicio determina quién elige el animal. Una vez presentado el reto, el baseline funciona igual en ambas modalidades.

## 3. Datos iniciales para construir el árbol

El conjunto D contiene ocho perfiles de escena, uno por tarjeta de hábitat. La clase objetivo Y es el ID de esa tarjeta: H01–H08.

Estos perfiles son una configuración didáctica propuesta para representar las tarjetas. No son registros obtenidos de jugadores ni descripciones exhaustivas de todos los ecosistemas. Por ejemplo, una tarjeta polar puede representar hielo y un paisaje frío; eso no excluye la existencia de bosques o montañas en regiones polares.

Los atributos describen el rasgo principal y el contexto de la escena seleccionada. Las imágenes que se preparen deberán corresponder a esos perfiles. No se afirma que las imágenes ya estén creadas o que se hayan extraído atributos mediante visión computacional.

| Clase | Hábitat | Entorno principal | Temperatura | Tipo de agua | Vegetación | Ubicación |
|---|---|---|---|---|---|---|
| H01 | Selva tropical | Arbolado | Cálido | No es el rasgo principal | Abundante | Otra |
| H02 | Sabana | Abierto y cálido | Cálido | No es el rasgo principal | Abundante | Otra |
| H03 | Desierto cálido | Abierto y cálido | Cálido | No es el rasgo principal | Escasa | Otra |
| H04 | Mar | Acuático | Variable | Salada | Escasa | Otra |
| H05 | Bosque templado | Arbolado | Templado | No es el rasgo principal | Abundante | Otra |
| H06 | Agua dulce | Acuático | Variable | Dulce | Abundante | Otra |
| H07 | Regiones polares | Paisaje frío | Frío | No es el rasgo principal | Escasa | Polar |
| H08 | Alta montaña | Paisaje frío | Frío | No es el rasgo principal | Escasa | Montaña |

En «Ubicación», Otra significa que la escena propuesta no destaca una región polar ni una alta montaña. En «Tipo de agua», No es el rasgo principal significa que el agua no domina esa escena; no significa que el ecosistema carezca de agua.

El conjunto de perfiles es independiente de la matriz animal–hábitat. No se duplicarán estos ocho perfiles para presentar artificialmente un conjunto de 48 observaciones de aprendizaje. Los 48 animales usan las rutas del árbol mediante sus asociaciones de guía confirmadas.

## 4. Entropía y ganancia de información

La entropía mide la diversidad de clases en un conjunto de ejemplos:

$$
\operatorname{Ent}(D)=-\sum_{j=1}^{k}p_j\log_2(p_j)
$$

La ganancia de un atributo F es:

$$
\operatorname{Gain}(D,F)=
\operatorname{Ent}(D)
-\sum_{v\in\operatorname{Valores}(F)}
\frac{|D_v|}{|D|}
\operatorname{Ent}(D_v)
$$

D_v contiene los perfiles cuyo atributo F tiene el valor v.

En nuestro conjunto inicial hay ocho clases con un perfil cada una; para este cálculo todas tienen el mismo peso:

$$
\operatorname{Ent}(D)
=-8\left(\frac{1}{8}\log_2\frac{1}{8}\right)
=3\text{ bits}
$$

Al separar por Entorno principal aparecen cuatro grupos de dos perfiles. Cada grupo tiene una entropía de 1 bit:

$$
\operatorname{Ent}(D\mid\mathrm{Entorno})
=4\left(\frac{2}{8}\times1\right)=1
$$

Por tanto:

$$
\operatorname{Gain}(D,\mathrm{Entorno})=3-1=2\text{ bits}
$$

La comparación de todos los atributos es:

| Atributo | Entropía posterior ponderada, bits | Ganancia, bits |
|---|---:|---:|
| Entorno principal | 1,00 | 2,00 |
| Temperatura | 1,09 | 1,91 |
| Tipo de agua | 1,94 | 1,06 |
| Vegetación | 2,00 | 1,00 |
| Ubicación | 1,94 | 1,06 |

El atributo raíz seleccionado es Entorno principal, con ganancia de 2,00 bits. Los valores corresponden a esta configuración de perfiles; deberán recalcularse si se cambian los datos.

Una ganancia mayor indica una mejor separación de las tarjetas en este conjunto. No demuestra por sí sola que una pista sea más comprensible para una persona.

## 5. Construcción y rutas del árbol

Para construir el árbol se seguirá este procedimiento:

1. Calcular la entropía de las clases del conjunto actual.
2. Calcular la ganancia de cada atributo disponible.
3. Elegir el atributo con mayor ganancia.
4. Crear una rama por cada valor del atributo y repetir con cada subconjunto.
5. Detener una rama cuando todos sus perfiles pertenezcan a una misma clase.
6. Resolver empates con el orden fijo: Entorno principal, Temperatura, Tipo de agua, Vegetación y Ubicación.

Este criterio de empate permite reproducir el resultado. En la rama acuática, Tipo de agua y Vegetación tienen la misma ganancia; se elige Tipo de agua por ese orden.

| Valor de la raíz | Tarjetas del grupo | Atributo siguiente | Ganancia local | Resultados |
|---|---|---|---:|---|
| Arbolado | H01, H05 | Temperatura | 1,00 | Cálido → H01; Templado → H05. |
| Abierto y cálido | H02, H03 | Vegetación | 1,00 | Vegetación abundante → H02; Vegetación escasa → H03. |
| Acuático | H04, H06 | Tipo de agua | 1,00 | Agua salada → H04; Agua dulce → H06. |
| Paisaje frío | H07, H08 | Ubicación | 1,00 | Ubicación polar → H07; Ubicación de montaña → H08. |

Cada grupo tiene inicialmente 1 bit de entropía. El atributo siguiente separa los dos perfiles en hojas puras, cuya entropía es 0. Para estos datos, todas las rutas requieren dos atributos.

El árbol debe construirse calculando las ganancias. Dibujar manualmente estas rutas no equivale a ejecutar el aprendizaje ID3.

## 6. Uso del árbol para ofrecer ayuda

El agente conoce el hábitat g hacia el que orienta la ayuda. Al solicitar una pista, recorre una parte de la ruta de ese perfil:

- **Nivel 0:** presentar el animal y la pregunta general, sin revelar una característica del hábitat.
- **Nivel 1:** comunicar el valor de Entorno principal correspondiente a g.
- **Nivel 2:** comunicar el valor del atributo que diferencia las dos tarjetas de esa rama.
- **Nivel 3:** mostrar explícitamente el nombre y el pictograma de g.
- **Nuevas solicitudes después del nivel 3:** repetir el apoyo explícito.

El tercer nivel es una ayuda de interfaz sobre una hoja ya identificada; no constituye una nueva división del árbol.

El aprendizaje ID3 se ejecutará al preparar el baseline. Durante la interacción se recorre el árbol resultante. El agente no necesita volver a entrenarlo después de cada clic.

### Plantillas de pistas alineadas con los atributos

Las pistas anteriores siguen disponibles como banco base. Para la PoC de ID3 se añaden las siguientes plantillas de guía, alineadas con los atributos que selecciona el árbol. El cambio afecta al contenido de las pistas y conserva los tres niveles y las reglas de interacción acordadas.

| Hábitat de guía | Nivel 1: entorno | Nivel 2: atributo diferenciador | Nivel 3: apoyo explícito |
|---|---|---|---|
| Selva tropical | Busca un lugar con muchos árboles. | Busca un bosque cálido y húmedo. | Una opción es la selva tropical. Toca su pictograma. |
| Sabana | Busca un lugar abierto y cálido. | Busca mucho pasto y árboles separados. | Una opción es la sabana. Toca su pictograma. |
| Desierto cálido | Busca un lugar abierto y cálido. | Busca un lugar seco, con pocas plantas. | Una opción es el desierto cálido. Toca su pictograma. |
| Mar | Busca un lugar con mucha agua. | Busca agua salada. | Una opción es el mar. Toca su pictograma. |
| Bosque templado | Busca un lugar con muchos árboles. | Busca un bosque de clima templado. | Una opción es el bosque templado. Toca su pictograma. |
| Agua dulce | Busca un lugar con mucha agua. | Busca agua dulce, como la de un río. | Una opción es el agua dulce. Toca su pictograma. |
| Regiones polares | Busca un paisaje muy frío. | Busca el extremo norte o sur del planeta. | Las regiones polares son una opción. Toca su pictograma. |
| Alta montaña | Busca un paisaje muy frío. | Busca montañas altas. | Una opción es la alta montaña. Toca su pictograma. |

Estas frases son texto de apoyo para el diseño. En la interfaz deberán representarse mediante secuencias de pictogramas y podrán acompañarse de voz. Por ejemplo, «lugar abierto y cálido» se apoyará en pictogramas que comuniquen paisaje abierto y calor, no únicamente en un bloque de texto.

## 7. Estado auxiliar y compatibilidad con la formalización

Se añade un único dato al estado de ejecución: n, el nodo actual del árbol. El árbol aprendido es configuración del sistema. El estado extendido es:

$$
s_{\mathrm{ID3}}=(s,n)
$$

Inicialmente, al preparar un reto, n apunta a la raíz. Para explicar la ruta se puede obtener:

$$
K(n)=\{\text{clases de las hojas descendientes de }n\}
$$

K(n) es el conjunto de tarjetas compatibles con las pistas de la ruta de guía. No representa las respuestas válidas del animal ni una estimación de lo que piensa el jugador.

El conjunto V(x), usado para evaluar las respuestas, se conserva completo. Puede contener asociaciones ajenas a K(n). Por ejemplo, la ayuda de la capibara puede recorrer Agua dulce y dejar K = {H06}; una selección de Selva tropical seguirá siendo válida porque H01 ∈ V(A31).

| Evento | Comportamiento del baseline |
|---|---|
| Preparar un nuevo reto | Reiniciar n en la raíz y l = 0. |
| Pedir ayuda desde l = 0 | Emitir la pista de la raíz para el perfil g; avanzar n al nodo de la rama elegida y l = 1. |
| Pedir ayuda desde l = 1 | Emitir la pista del atributo secundario; avanzar n a la hoja de g y l = 2. |
| Pedir ayuda desde l = 2 | Mostrar la opción explícita; conservar n en la hoja y l = 3. |
| Pedir ayuda desde l = 3 | Repetir el apoyo explícito; conservar n y l. |
| Repetir | Reproducir el último mensaje; conservar n, l y el progreso. |
| Seleccionar una asociación válida | Confirmar y resolver el reto, cualquiera sea su relación con K(n). |
| Seleccionar una asociación pendiente | Responder de forma neutral; conservar n y l. |
| Seleccionar una asociación incorrecta validada | Avanzar un nivel de ayuda mediante la misma ruta, hasta 3. |
| Pausar y reanudar | Conservar y restaurar n junto a las demás variables. |
| Continuar hacia un nuevo reto | Reiniciar el nodo y el nivel para el animal siguiente. |

Las ocho opciones permanecen visibles y seleccionables mientras el reto esté activo. K(n) solo es un dato interno explicativo; no se utiliza para ocultar o desactivar tarjetas.

## 8. Ejemplo completo: jirafa reticulada

Se usa A08 y su hábitat de guía g = H02, Sabana.

La ruta del perfil es:

- Entorno principal = LLANURA_CALIDA.
- Vegetación = ABUNDANTE.
- Hoja = H02.

| Paso | Acción o intervención | Mensaje | K de la ruta | Entropía del subconjunto |
|---|---|---|---|---:|
| Inicio | Presentar el animal y la pregunta. | «¿Dónde puede vivir la jirafa?» | H01–H08 | 3,00 bits |
| Ayuda 1 | Comunicar el valor del atributo raíz. | «Busca un lugar abierto y cálido». | H02, H03 | 1,00 bit |
| Ayuda 2 | Comunicar el valor del atributo secundario. | «Busca mucho pasto y árboles separados». | H02 | 0,00 bits |
| Ayuda 3, si se solicita | Mostrar el nombre y el pictograma de la hoja. | «Una opción es la sabana. Toca su pictograma». | H02 | 0,00 bits |
| Selección válida del jugador | Evaluar H02 y confirmar. | «¡Sí! La jirafa puede vivir en la sabana». | El reto queda resuelto. | No se requiere otra pista. |

La secuencia puede detenerse antes si el jugador selecciona una asociación válida. Llegar a una hoja o a una entropía de 0 no completa el reto automáticamente: todavía debe existir una selección válida del jugador.

La reducción de entropía describe la separación matemática de las tarjetas de guía. No mide la comprensión del jugador.

## 9. Evaluación y control de las respuestas

C(x,h) sigue utilizando la matriz de asociaciones:

- Una relación confirmada se acepta.
- Una relación validada como incorrecta permite ofrecer la siguiente pista.
- Una relación pendiente recibe tratamiento neutral.

Actualmente la matriz contiene 69 asociaciones válidas y 315 pendientes. No se utilizarán las pendientes como ejemplos negativos para construir este árbol ni para evaluar al jugador.

El árbol aprende a organizar perfiles de tarjetas; no decide si una asociación biológica es verdadera ni inventa nuevas relaciones animal–hábitat.

## 10. Qué deberá mostrar la futura PoC

La simulación del baseline deberá permitir revisar:

1. La tabla de perfiles utilizada.
2. La entropía inicial de 3,00 bits.
3. Las ganancias de los cinco atributos y la elección de la raíz.
4. La ganancia del atributo elegido en cada una de las cuatro ramas.
5. Las rutas que terminan en las ocho clases.
6. Una partida que avance por ayudas, confirme una respuesta y conserve las ocho opciones.
7. Un caso en que se acepte una asociación adicional aunque no coincida con la hoja de guía.
8. Un caso pendiente que mantenga una respuesta neutral.
9. Una pausa y una repetición que conserven el nodo y el nivel.
10. La diferencia entre resolver el perfil de guía y recibir la selección válida del jugador.

Los cálculos de este documento se han comprobado sobre la tabla propuesta. Todavía no se ha creado ni ejecutado el notebook de la PoC.

Reconocer los mismos ocho perfiles empleados al construir el árbol es una verificación estructural. No se presentará como prueba de generalización a ecosistemas nuevos ni de efectividad con usuarios reales.

## 11. Alcance del baseline y continuidad del proyecto

Este baseline produce una secuencia explicable mediante cálculos de ganancia de información. Con la tabla actual, dos atributos separan las ocho tarjetas y el tercer nivel ofrece apoyo explícito.

La secuencia será la misma para un mismo perfil de guía. El modelo principal del proyecto podrá incorporar variantes de intervención e información de las interacciones para adaptar mejor la asistencia. Su diseño corresponde al paso siguiente; no está implementado en esta especificación.

## 12. Redacción para el documento técnico

El motor de guía utilizará como baseline un árbol de decisión ID3 construido sobre perfiles categóricos de las ocho tarjetas de hábitat. La clase objetivo será el identificador del hábitat representado y los atributos incluirán el entorno principal, la temperatura, el tipo de agua, la vegetación y la ubicación de la escena. El algoritmo calculará la entropía y seleccionará en cada nodo el atributo con mayor ganancia de información.

Durante un reto, el agente recorrerá la ruta correspondiente a una asociación de guía previamente confirmada del animal. La primera pista comunicará un rasgo general, la segunda ofrecerá una característica diferenciadora y la tercera mostrará una opción explícita. La selección del jugador se evaluará con la matriz animal–hábitat, aceptando cualquiera de sus asociaciones confirmadas. Las ocho opciones permanecerán disponibles y las relaciones pendientes no se considerarán automáticamente incorrectas.

Los perfiles utilizados son una configuración didáctica del banco de tarjetas. El baseline permite comprobar el razonamiento y la secuencia de ayuda; su efectividad pedagógica y la adaptación individual se evaluarán posteriormente.

## 13. Referencias

- Quinlan, J. R. (1986). Induction of decision trees. Machine Learning, 1, 81–106. https://doi.org/10.1007/BF00116251
- Singh, A. (2020). Decision Trees. Machine Learning 10-315, Carnegie Mellon University. https://www.cs.cmu.edu/~aarti/Class/10315_Fall20/lecs/DecisionTrees.pdf
- formalizacion_agente_animales_habitats.md, consultado el 9 de octubre de 2026.
- pistas_progresivas_animales_48.md, consultado el 9 de octubre de 2026.
- matriz_animales_habitats_48.md, base de asociaciones referenciada por la formalización.

Las referencias técnicas respaldan ID3 y su criterio de selección de atributos. La tabla de perfiles, sus cálculos y la aplicación de las pistas al juego son una propuesta de elaboración propia.
