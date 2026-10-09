# Animales y hábitats: datos preparados para la PoC

Versión 1.0.0 · 2026-10-09

## 1. Qué contiene el paquete

Los datos conservan los identificadores del diseño. La base de conocimiento y las ayudas pueden cargarse en la futura simulación textual. Este paquete no incluye el programa del juego, imágenes de pictogramas ni entrenamiento ejecutado.

| Archivo en /datos | Contenido |
|---|---|
| animales.json | 48 animales, referencia, asociaciones confirmadas y precisiones. |
| habitats.json | 8 categorías con definiciones y expresiones para los mensajes. |
| asociaciones.json | 384 relaciones: 69 válidas, 315 pendientes y ninguna incorrecta inventada. |
| escenarios.json | 48 escenarios; cada uno mantiene las ocho opciones y ambas modalidades. |
| perfiles_id3.json | 8 perfiles de escena y el orden de desempate de atributos. |
| variantes_ayuda.json | 72 plantillas: 8 hábitats × 3 niveles × 3 variantes. |
| pistas_originales.json | 144 pistas fuente, conservadas como banco aparte. |
| pictogramas.json | 95 identificadores y significados visuales; los archivos de imagen están pendientes. |
| mensajes_sistema.json | 9 mensajes de pregunta, navegación, confirmación y respuesta neutral. |
| parametros_iniciales.json | 144 distribuciones Beta(1,1), sin observaciones ni entrenamiento. |
| configuracion_poc.json | Configuración editable de demostración y reglas compartidas. |
| configuracion_simulador.json | 3 condiciones sintéticas explícitas para futuros experimentos. |
| casos_aceptacion.json | 8 recorridos esperados; todavía no ejecutados sobre un motor. |
| fuentes.json | 55 referencias URL conservadas de la matriz. |
| manifest.json | Inventario, procedencia y huellas SHA-256 de los archivos del paquete. |

Todos los JSON utilizan UTF-8 y tienen schema_version = 1.0.0. Las listas de registros se almacenan en items; las opciones de ejecución, en configuracion.

## 2. Cómo se conservan las asociaciones

Los estados de una relación se expresan como VALIDA, INCORRECTA o PENDIENTE. Las 315 relaciones pendientes conservan ese estado. No se transforman en ceros ni se utilizan como respuestas incorrectas.

Cada animal tiene una referencia para la guía, pero se aceptan todos sus hábitats confirmados. Las 48 referencias se distribuyen en seis animales por categoría y las 21 asociaciones adicionales también se conservan.

### Ejemplo: capibara o ronsoco

| Campo | Valor |
|---|---|
| Animal | A31 |
| Escenario | E31 |
| Guía | H06: Agua dulce |
| Respuestas confirmadas | H01: Selva tropical; H02: Sabana; H06: Agua dulce |
| Ejemplo pendiente | A31–H03: Desierto cálido |

Elegir H01 o H02 puede resolver este reto general aunque las pistas orienten a H06. Elegir H03 recibe tratamiento neutral con la base actual.

## 3. Variantes listas para la simulación textual

Cada hábitat tiene tres niveles y cada nivel tiene tres formas de intervención: V1, descripción; V2, relación con el animal; V3, pregunta breve. Las secuencias simbólicas cambian, además de sus palabras.

La variante V2 utiliza un slot llamado animal_actual. El generador lo sustituirá por el identificador visual del animal del reto; por ejemplo, P_A08. Los demás elementos se referencian por su ID en pictogramas.json.

Ejemplo AY_H02_L2_V2: «Este animal puede vivir en un lugar con mucho pasto y árboles separados».

| Orden | Elemento |
|---|---|
| 1 | animal_actual, por ejemplo P_A08 |
| 2 | P_VIVIR |
| 3 | P_PASTO_ABUNDANTE |
| 4 | P_ARBOLES_SEPARADOS |

El nivel 1 describe el entorno raíz; el nivel 2 diferencia la rama; el nivel 3 incluye explícitamente P_H01–P_H08. La revisión estructural comprobó esa progresión.

Las 144 pistas anteriores se conservan con su texto fuente. Se añadió una versión normalizada para corregir la concordancia de las seis frases de nivel 3 de regiones polares. El banco original aún necesita mapearse si se desea usarlo en el selector ID3; la PoC utilizará inicialmente las 72 variantes nuevas.

## 4. Estado de los pictogramas

Hay 95 definiciones: 48 animales, ocho hábitats y 39 apoyos o controles. Cada definición incluye etiqueta, significado y referencia. archivo_imagen, fuente_imagen y licencia se mantienen en null porque no se han incorporado imágenes.

El nivel de preparación es lógico y textual. Las 72 variantes están habilitadas para una simulación en texto, pero no se presentan como secuencias visuales ya creadas o validadas con jugadores. Las imágenes y su representación deberán revisarse al construir la interfaz.

## 5. Configuración inicial editable

La demostración propone ocho retos por partida, uno de referencia por categoría en el orden automático. N sigue siendo editable entre 1 y 48. El catálogo no cambia al modificar N: se conservan los 48 animales y las ocho opciones por reto.

La modalidad inicial del archivo es JUGADOR; también está disponible AGENTE. Las políticas comparables son ID3, ROTACION y PROBABILISTICO. Los casos de aceptación usan valores N = 1 o N = 2 cuando conviene aislar una transición.

## 6. Probabilidades y simulación

Los parámetros iniciales contienen 48 contextos —hábitat, nivel y uso previo de Repetir— con tres variantes cada uno. Las 144 distribuciones parten de Beta(1,1) y cero observaciones etiquetadas. La media inicial es 0,5; representa el prior elegido, no un resultado de usuarios.

Las condiciones SIM_UNIFORME, SIM_DIFERENCIAS y SIM_CONTEXTUAL contienen probabilidades artificiales declaradas. Todavía no han producido interacciones ni resultados. Servirán para estudiar el comportamiento del aprendizaje en el futuro simulador, con entrenamiento y evaluación separados.

Una señal y = 0 se simulará mediante una solicitud de nueva ayuda. No requiere inventar asociaciones biológicas incorrectas. Los casos pendientes y las salidas conservan un cierre sin etiqueta.

## 7. Qué se ha revisado

Se comprobaron los JSON, los IDs, las referencias entre archivos, las cantidades del catálogo, los estados de la matriz y las secuencias de las variantes. Cada escenario contiene las ocho opciones y admite ambas modalidades.

Sobre los perfiles se recalculó una entropía de 3 bits y la elección de entorno como raíz, con 2 bits de ganancia. Las cuatro ramas se separan con una ganancia local de 1 bit. Este cálculo revisa los datos; no sustituye la futura ejecución del aprendizaje ID3 en el notebook.

## 8. Cómo utilizar los archivos

Extrae el ZIP. La carpeta datos contiene los archivos que cargará el futuro núcleo de Python; docs contiene esta guía, la revisión de integridad y copias de las fuentes de trabajo utilizadas. Puedes abrir los JSON en VS Code para consultar los registros.

El paquete corresponde a la preparación de datos de la PoC. Los notebooks, el motor ejecutable y el prototipo digital se desarrollarán después.

## 9. Texto para incorporar al documento técnico

Se preparó una base estructurada en JSON con 48 animales, ocho categorías de hábitat y 48 escenarios generales. La matriz conserva 384 relaciones, de las cuales 69 están confirmadas y 315 permanecen pendientes. Estas últimas no se utilizarán como respuestas incorrectas. Cada escenario mantiene las ocho opciones disponibles y admite las modalidades de inicio por el agente o por el jugador.

El banco de asistencia contiene 72 plantillas parametrizadas, organizadas por hábitat, nivel y variante de presentación. Sus secuencias simbólicas se enlazan con un catálogo de identificadores visuales. También se conserva el banco previo de 144 pistas por animal. Los perfiles didácticos para ID3 y los parámetros iniciales del modelo probabilístico se almacenan por separado, distinguiendo el contenido del juego de las futuras observaciones de aprendizaje.

La preparación incluyó una revisión de integridad de identificadores, asociaciones, secuencias y formatos. El paquete está listo para la futura PoC textual. La incorporación de imágenes, la implementación del motor y la evaluación con jugadores corresponden a las siguientes etapas.

## 10. Catálogo completo de las 72 variantes

### H01: Selva tropical

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H01_L1_V1 | 1 | Descripcion | Busca un lugar con muchos árboles. |
| AY_H01_L1_V2 | 1 | Relacion | Este animal puede vivir en un lugar con muchos árboles. |
| AY_H01_L1_V3 | 1 | Pregunta | ¿Qué lugar tiene muchos árboles? |
| AY_H01_L2_V1 | 2 | Descripcion | Busca un bosque cálido y húmedo. |
| AY_H01_L2_V2 | 2 | Relacion | Este animal puede vivir en un bosque cálido y húmedo. |
| AY_H01_L2_V3 | 2 | Pregunta | ¿Qué bosque es cálido y húmedo? |
| AY_H01_L3_V1 | 3 | Descripcion | Una opción es la selva tropical. Toca su pictograma. |
| AY_H01_L3_V2 | 3 | Relacion | Este animal puede vivir en la selva tropical. Toca su pictograma. |
| AY_H01_L3_V3 | 3 | Pregunta | ¿Puedes señalar la selva tropical? |

### H02: Sabana

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H02_L1_V1 | 1 | Descripcion | Busca un lugar abierto y cálido. |
| AY_H02_L1_V2 | 1 | Relacion | Este animal puede vivir en un lugar abierto y cálido. |
| AY_H02_L1_V3 | 1 | Pregunta | ¿Qué lugar es abierto y cálido? |
| AY_H02_L2_V1 | 2 | Descripcion | Busca mucho pasto y árboles separados. |
| AY_H02_L2_V2 | 2 | Relacion | Este animal puede vivir en un lugar con mucho pasto y árboles separados. |
| AY_H02_L2_V3 | 2 | Pregunta | ¿Qué lugar tiene mucho pasto y árboles separados? |
| AY_H02_L3_V1 | 3 | Descripcion | Una opción es la sabana. Toca su pictograma. |
| AY_H02_L3_V2 | 3 | Relacion | Este animal puede vivir en la sabana. Toca su pictograma. |
| AY_H02_L3_V3 | 3 | Pregunta | ¿Puedes señalar la sabana? |

### H03: Desierto cálido

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H03_L1_V1 | 1 | Descripcion | Busca un lugar abierto y cálido. |
| AY_H03_L1_V2 | 1 | Relacion | Este animal puede vivir en un lugar abierto y cálido. |
| AY_H03_L1_V3 | 1 | Pregunta | ¿Qué lugar es abierto y cálido? |
| AY_H03_L2_V1 | 2 | Descripcion | Busca un lugar seco, con pocas plantas. |
| AY_H03_L2_V2 | 2 | Relacion | Este animal puede vivir en un lugar seco, con pocas plantas. |
| AY_H03_L2_V3 | 2 | Pregunta | ¿Qué lugar es seco y tiene pocas plantas? |
| AY_H03_L3_V1 | 3 | Descripcion | Una opción es el desierto cálido. Toca su pictograma. |
| AY_H03_L3_V2 | 3 | Relacion | Este animal puede vivir en el desierto cálido. Toca su pictograma. |
| AY_H03_L3_V3 | 3 | Pregunta | ¿Puedes señalar el desierto cálido? |

### H04: Mar

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H04_L1_V1 | 1 | Descripcion | Busca un lugar con mucha agua. |
| AY_H04_L1_V2 | 1 | Relacion | Este animal puede vivir en un entorno con mucha agua. |
| AY_H04_L1_V3 | 1 | Pregunta | ¿Qué lugar tiene mucha agua? |
| AY_H04_L2_V1 | 2 | Descripcion | Busca agua salada. |
| AY_H04_L2_V2 | 2 | Relacion | Este animal puede vivir en un entorno con agua salada. |
| AY_H04_L2_V3 | 2 | Pregunta | ¿Qué lugar tiene agua salada? |
| AY_H04_L3_V1 | 3 | Descripcion | Una opción es el mar. Toca su pictograma. |
| AY_H04_L3_V2 | 3 | Relacion | Este animal puede vivir en el mar. Toca su pictograma. |
| AY_H04_L3_V3 | 3 | Pregunta | ¿Puedes señalar el mar? |

### H05: Bosque templado

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H05_L1_V1 | 1 | Descripcion | Busca un lugar con muchos árboles. |
| AY_H05_L1_V2 | 1 | Relacion | Este animal puede vivir en un lugar con muchos árboles. |
| AY_H05_L1_V3 | 1 | Pregunta | ¿Qué lugar tiene muchos árboles? |
| AY_H05_L2_V1 | 2 | Descripcion | Busca un bosque de clima templado. |
| AY_H05_L2_V2 | 2 | Relacion | Este animal puede vivir en un bosque de clima templado. |
| AY_H05_L2_V3 | 2 | Pregunta | ¿Qué bosque tiene un clima templado? |
| AY_H05_L3_V1 | 3 | Descripcion | Una opción es el bosque templado. Toca su pictograma. |
| AY_H05_L3_V2 | 3 | Relacion | Este animal puede vivir en un bosque templado. Toca su pictograma. |
| AY_H05_L3_V3 | 3 | Pregunta | ¿Puedes señalar el bosque templado? |

### H06: Agua dulce

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H06_L1_V1 | 1 | Descripcion | Busca un lugar con mucha agua. |
| AY_H06_L1_V2 | 1 | Relacion | Este animal puede vivir en un entorno con mucha agua. |
| AY_H06_L1_V3 | 1 | Pregunta | ¿Qué lugar tiene mucha agua? |
| AY_H06_L2_V1 | 2 | Descripcion | Busca agua dulce, como la de un río. |
| AY_H06_L2_V2 | 2 | Relacion | Este animal puede vivir en un entorno de agua dulce, como un río. |
| AY_H06_L2_V3 | 2 | Pregunta | ¿Qué lugar tiene agua dulce, como la de un río? |
| AY_H06_L3_V1 | 3 | Descripcion | Una opción es el agua dulce. Toca su pictograma. |
| AY_H06_L3_V2 | 3 | Relacion | Este animal puede vivir en un entorno de agua dulce. Toca su pictograma. |
| AY_H06_L3_V3 | 3 | Pregunta | ¿Puedes señalar el agua dulce? |

### H07: Regiones polares

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H07_L1_V1 | 1 | Descripcion | Busca un paisaje muy frío. |
| AY_H07_L1_V2 | 1 | Relacion | Este animal puede vivir en un paisaje muy frío. |
| AY_H07_L1_V3 | 1 | Pregunta | ¿Qué paisaje es muy frío? |
| AY_H07_L2_V1 | 2 | Descripcion | Busca el extremo norte o sur del planeta. |
| AY_H07_L2_V2 | 2 | Relacion | Este animal puede vivir en el extremo norte o sur del planeta. |
| AY_H07_L2_V3 | 2 | Pregunta | ¿Qué lugar está en el extremo norte o sur del planeta? |
| AY_H07_L3_V1 | 3 | Descripcion | Las regiones polares son una opción. Toca su pictograma. |
| AY_H07_L3_V2 | 3 | Relacion | Este animal puede vivir en regiones polares. Toca su pictograma. |
| AY_H07_L3_V3 | 3 | Pregunta | ¿Puedes señalar las regiones polares? |

### H08: Alta montaña

| ID | Nivel | Forma | Mensaje |
|---|---:|---|---|
| AY_H08_L1_V1 | 1 | Descripcion | Busca un paisaje muy frío. |
| AY_H08_L1_V2 | 1 | Relacion | Este animal puede vivir en un paisaje muy frío. |
| AY_H08_L1_V3 | 1 | Pregunta | ¿Qué paisaje es muy frío? |
| AY_H08_L2_V1 | 2 | Descripcion | Busca montañas altas. |
| AY_H08_L2_V2 | 2 | Relacion | Este animal puede vivir en montañas altas. |
| AY_H08_L2_V3 | 2 | Pregunta | ¿Qué lugar tiene montañas altas? |
| AY_H08_L3_V1 | 3 | Descripcion | Una opción es la alta montaña. Toca su pictograma. |
| AY_H08_L3_V2 | 3 | Relacion | Este animal puede vivir en la alta montaña. Toca su pictograma. |
| AY_H08_L3_V3 | 3 | Pregunta | ¿Puedes señalar la alta montaña? |

## 11. Procedencia

Los animales, las asociaciones y sus referencias provienen de la matriz actual del proyecto. Las pistas fuente se importaron del catálogo actual y los perfiles se importaron del diseño ID3. Las variantes nuevas y la configuración de simulación desarrollan el modelo principal y la arquitectura acordados. fuentes.json conserva las URL citadas; esta etapa no constituye una nueva revisión de esas páginas.
