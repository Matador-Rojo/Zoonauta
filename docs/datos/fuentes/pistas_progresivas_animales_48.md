# Animales y hábitats: estrategia y catálogo de pistas progresivas

Diseño propuesto · Versión 1 · 9 de octubre de 2026

Este archivo desarrolla la estrategia de ayuda del juego y contiene tres pistas para cada uno de sus 48 animales: 144 mensajes. Se basa en la matriz de asociaciones animal–hábitat ya preparada. Las pistas guían hacia una asociación confirmada; no afirman que sea la única posible.

## 1. Propósito de la ayuda

El agente acompañará al jugador cuando solicite ayuda o cuando seleccione una asociación que se haya validado como incorrecta. La ayuda aumentará de forma gradual y mantendrá disponibles las ocho opciones de hábitat. Se usará el mismo comportamiento en las modalidades «inicia el agente» e «inicia el jugador».

Tres niveles permiten pasar de una orientación general a una indicación explícita. El tercer nivel es una respuesta con apoyo: revela una opción válida, pero el jugador sigue realizando la selección. Se registrará el nivel usado para distinguir una resolución independiente de una resolución con ayuda, sin quitar puntos ni bloquear al jugador.

## 2. Niveles de ayuda

| Nivel | Qué muestra | Qué permite hacer |
|---|---|---|
| 0: sin ayuda | Pictograma y nombre del animal; pregunta «¿Dónde puede vivir este animal?»; ocho hábitats. | Responder, pedir ayuda, repetir la pregunta, pausar o salir. |
| 1: pista general | Una frase breve sobre un lugar donde puede vivir el animal, con un pictograma de apoyo pertinente. | Intentar relacionar una característica general con las opciones. |
| 2: pista concreta | Una frase que describa rasgos más específicos del entorno; apoyo visual que coincida con esa frase. | Distinguir mejor la opción orientada por las pistas. |
| 3: opción explícita | Nombre y pictograma de un hábitat confirmado; frase «Una opción es…». | Seleccionar esa opción entre las ocho, o elegir otra asociación confirmada. |

No se ocultan, retiran ni desactivan opciones al aumentar la ayuda. El nivel 3 puede mostrar una tarjeta de apoyo junto al animal; no selecciona la respuesta automáticamente ni avanza por el jugador. Los pictogramas de apoyo descritos aquí quedan especificados como contenido visual por preparar, no como imágenes ya creadas.

## 3. Cuándo cambia el nivel

| Evento | Respuesta del agente | Nivel después del evento |
|---|---|---|
| Comienza un reto nuevo | Presenta el animal, la pregunta y las ocho opciones. | 0 |
| El jugador pulsa «Ayuda» | Muestra la siguiente pista. | Sube uno, hasta un máximo de 3. |
| El jugador pulsa «Repetir» | Reproduce otra vez la pregunta o la pista que está en pantalla. | Se mantiene. |
| Selección confirmada como válida | Confirma y explica brevemente la asociación elegida. Habilita «Continuar». | Se conserva como registro del reto resuelto. |
| Selección confirmada como incorrecta | Dice «Probemos otra opción» y muestra la siguiente pista. | Sube uno, hasta un máximo de 3. |
| Selección pendiente de validación | Evita afirmar que está mal. Ofrece explorar una asociación confirmada. | Se mantiene; sube solo si el jugador pide ayuda. |
| Nueva ayuda después de llegar al nivel 3 | Repite la opción de apoyo. | 3 |
| El jugador permanece sin tocar la pantalla | Espera; no interpreta el tiempo como un error. | Se mantiene. |
| El jugador pulsa «Continuar» tras resolver | Abre el siguiente reto conforme a la modalidad y reinicia la ayuda. | 0 |
| El jugador pausa o sale | Conserva o finaliza el reto según la navegación que se defina. | No incrementa la ayuda ni cuenta un error. |

Cada evento produce como máximo un avance de nivel. Pulsar «Ayuda» no es un error. Usar «Repetir» no aumenta la dificultad ni cambia el criterio de evaluación. No hay tiempo límite ni máximo de intentos en este diseño básico.

La matriz actual distingue asociaciones confirmadas y pendientes; no contiene todavía una lista de relaciones verificadas como incorrectas. Por ello, el comportamiento de «respuesta incorrecta» queda definido para cuando existan esos casos validados. No se deben convertir las celdas «?» en errores para activar esta transición.

## 4. Mensajes de respuesta

| Situación | Mensaje propuesto |
|---|---|
| Respuesta válida | «¡Sí! [Animal] puede vivir en [hábitat].» |
| Respuesta válida con contexto | «¡Sí! [Animal] puede vivir en [hábitat]. [Explicación breve del contexto].» |
| Relación validada como incorrecta | «Probemos otra opción. [Siguiente pista].» |
| Relación pendiente | «Vamos a explorar un lugar que conocemos para este animal. Puedes pedir una pista.» |
| Ayuda solicitada | Mostrar la pista del nivel correspondiente, sin un texto adicional innecesario. |
| Nivel 3 | «Una opción es [hábitat]. Toca su pictograma.» |
| Reto resuelto | Mantener la confirmación y mostrar el botón «Continuar». |

La respuesta pendiente recibe un tratamiento neutral y no reduce un puntaje ni cuenta como un error. Las decisiones y asociaciones pendientes se registrarán para su revisión en el desarrollo del proyecto; ese registro técnico no se presenta como una tarea para el jugador.

## 5. Respuestas múltiples y dirección de las pistas

En una pregunta general, todas las asociaciones confirmadas del animal se aceptan como válidas. El hábitat de referencia se usa como destino de las pistas iniciales de este catálogo, para tener una secuencia coherente y fácil de revisar. Si el jugador selecciona otra asociación confirmada, el reto termina con una respuesta válida: no tiene que regresar a la opción hacia la que apuntaban las pistas.

Por ejemplo, las pistas de la capibara orientan hacia agua dulce. Si el jugador selecciona selva tropical o sabana, se acepta la respuesta con una explicación sobre el agua accesible en ese entorno. El tercer nivel siempre dice «Una opción»; evita «La única respuesta» o frases que nieguen los otros hábitats confirmados.

Para un reto con escenario específico, el texto, la imagen del contexto y la evaluación deben corresponder al mismo escenario. Este catálogo cubre inicialmente las preguntas generales animal–hábitat.

## 6. Aplicación en las dos modalidades

### Inicia el agente

1. El agente presenta un animal del catálogo y pregunta dónde puede vivir.
2. El jugador ve las ocho opciones de hábitat y el botón «Ayuda».
3. El agente responde a la selección o entrega una pista según los eventos definidos.
4. Tras una respuesta válida, el jugador pulsa «Continuar» para avanzar al siguiente reto.

### Inicia el jugador

1. El jugador elige un animal en el panel de 48 opciones, con desplazamiento si es necesario.
2. El agente confirma el animal y pregunta dónde puede vivir.
3. Se presentan las ocho opciones y se usa la misma secuencia de ayuda.
4. Tras una respuesta válida, «Continuar» permite elegir otro animal.

Elegir el animal al comenzar no equivale a responder el reto. Las pistas y el nivel de ayuda se reinician cuando empieza un reto nuevo en cualquiera de las dos modalidades.

## 7. Presentación accesible de la ayuda

- Mostrar una sola pista nueva a la vez y mantener a la vista el animal actual.
- Usar frases breves en español y pictogramas que representen el contenido de la frase.
- Mantener el mismo orden y ubicación de las ocho opciones durante el reto.
- Ofrecer «Ayuda», «Repetir», «Continuar» y «Pausa/Salir» con icono y texto claros.
- Permitir reproducción de la pregunta y las pistas mediante voz; ofrecer control de repetición y sonido.
- Usar pictogramas grandes y contraste suficiente; no comunicar la corrección solo mediante color o sonido.
- Dar al jugador tiempo para leer, escuchar y seleccionar, sin activar ayuda por inactividad.
- Evitar frases como «Fallaste» o mensajes que asignen valor personal al desempeño.

Estos criterios se revisarán con pruebas de uso; no se afirma que el prototipo ya haya sido validado con sus beneficiarios.

## 8. Catálogo: tres pistas por cada animal

Las frases son propuestas de interfaz basadas en las asociaciones de referencia confirmadas. Las primeras dos pistas son descripciones de un entorno posible; la tercera indica explícitamente una opción válida. Las fuentes ecológicas son las mismas de la matriz y se incluyen al final para conservar la trazabilidad.

### H01: Selva tropical

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A01 | Jaguar | Puede vivir en un lugar con muchos árboles. | Busca un bosque cálido y húmedo, con mucha vegetación. | Una opción es la selva tropical. Toca su pictograma. |
| A02 | Orangután de Borneo | Puede vivir en un lugar con muchos árboles. | Busca un bosque cálido y húmedo, con mucha vegetación. | Una opción es la selva tropical. Toca su pictograma. |
| A03 | Gorila occidental | Puede vivir en un lugar con muchos árboles. | Busca un bosque cálido y húmedo, con mucha vegetación. | Una opción es la selva tropical. Toca su pictograma. |
| A04 | Perezoso de dos dedos de Hoffmann | Puede vivir en un lugar con muchos árboles. | Busca un bosque cálido y húmedo, con mucha vegetación. | Una opción es la selva tropical. Toca su pictograma. |
| A05 | Guacamayo rojo | Puede vivir en un lugar con muchos árboles. | Busca un bosque cálido y húmedo, con mucha vegetación. | Una opción es la selva tropical. Toca su pictograma. |
| A06 | Rana dardo azul | Puede vivir en un lugar con muchos árboles. | Busca un bosque cálido y húmedo, con mucha vegetación. | Una opción es la selva tropical. Toca su pictograma. |

### H02: Sabana

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A07 | León africano | Puede vivir en un lugar abierto, con mucho pasto. | Busca una llanura cálida, con árboles separados. | Una opción es la sabana. Toca su pictograma. |
| A08 | Jirafa reticulada | Puede vivir en un lugar abierto, con mucho pasto. | Busca una llanura cálida, con árboles separados. | Una opción es la sabana. Toca su pictograma. |
| A09 | Cebra de llanura | Puede vivir en un lugar abierto, con mucho pasto. | Busca una llanura cálida, con árboles separados. | Una opción es la sabana. Toca su pictograma. |
| A10 | Elefante africano de sabana | Puede vivir en un lugar abierto, con mucho pasto. | Busca una llanura cálida, con árboles separados. | Una opción es la sabana. Toca su pictograma. |
| A11 | Guepardo | Puede vivir en un lugar abierto, con mucho pasto. | Busca una llanura cálida, con árboles separados. | Una opción es la sabana. Toca su pictograma. |
| A12 | Avestruz común | Puede vivir en un lugar abierto, con mucho pasto. | Busca una llanura cálida, con árboles separados. | Una opción es la sabana. Toca su pictograma. |

### H03: Desierto cálido

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A13 | Dromedario | Puede vivir en un lugar muy seco. | Busca un terreno con poca vegetación, donde puede hacer mucho calor. | Una opción es el desierto cálido. Toca su pictograma. |
| A14 | Zorro fénec | Puede vivir en un lugar muy seco. | Busca un terreno con poca vegetación, donde puede hacer mucho calor. | Una opción es el desierto cálido. Toca su pictograma. |
| A15 | Suricata | Puede vivir en un lugar muy seco. | Busca un terreno con poca vegetación, donde puede hacer mucho calor. | Una opción es el desierto cálido. Toca su pictograma. |
| A16 | Tortuga del desierto de Mojave | Puede vivir en un lugar muy seco. | Busca un terreno con poca vegetación, donde puede hacer mucho calor. | Una opción es el desierto cálido. Toca su pictograma. |
| A17 | Monstruo de Gila | Puede vivir en un lugar muy seco. | Busca un terreno con poca vegetación, donde puede hacer mucho calor. | Una opción es el desierto cálido. Toca su pictograma. |
| A18 | Jerbo egipcio menor | Puede vivir en un lugar muy seco. | Busca un terreno con poca vegetación, donde puede hacer mucho calor. | Una opción es el desierto cálido. Toca su pictograma. |

### H04: Mar

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A19 | Delfín nariz de botella | Puede vivir en agua salada. | Busca una gran extensión de agua con olas. | Una opción es el mar. Toca su pictograma. |
| A20 | Ballena azul | Puede vivir en agua salada. | Busca una gran extensión de agua con olas. | Una opción es el mar. Toca su pictograma. |
| A21 | Tiburón blanco | Puede vivir en agua salada. | Busca una gran extensión de agua con olas. | Una opción es el mar. Toca su pictograma. |
| A22 | Mantarraya gigante | Puede vivir en agua salada. | Busca una gran extensión de agua con olas. | Una opción es el mar. Toca su pictograma. |
| A23 | Pulpo común | Puede vivir en agua salada. | Busca una gran extensión de agua con olas. | Una opción es el mar. Toca su pictograma. |
| A24 | Tortuga verde | Puede vivir en agua salada. | Busca una gran extensión de agua con olas. | Una opción es el mar. Toca su pictograma. |

### H05: Bosque templado

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A25 | Oso pardo | Puede vivir en un lugar con muchos árboles. | Busca un bosque donde las estaciones cambian el paisaje. | Una opción es el bosque templado. Toca su pictograma. |
| A26 | Lobo gris | Puede vivir en un lugar con muchos árboles. | Busca un bosque donde las estaciones cambian el paisaje. | Una opción es el bosque templado. Toca su pictograma. |
| A27 | Zorro rojo | Puede vivir en un lugar con muchos árboles. | Busca un bosque donde las estaciones cambian el paisaje. | Una opción es el bosque templado. Toca su pictograma. |
| A28 | Ardilla roja euroasiática | Puede vivir en un lugar con muchos árboles. | Busca un bosque donde las estaciones cambian el paisaje. | Una opción es el bosque templado. Toca su pictograma. |
| A29 | Corzo europeo | Puede vivir en un lugar con muchos árboles. | Busca un bosque donde las estaciones cambian el paisaje. | Una opción es el bosque templado. Toca su pictograma. |
| A30 | Jabalí | Puede vivir en un lugar con muchos árboles. | Busca un bosque donde las estaciones cambian el paisaje. | Una opción es el bosque templado. Toca su pictograma. |

### H06: Agua dulce

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A31 | Capibara o ronsoco | Necesita tener agua cerca. | Busca un río o una laguna con vegetación en sus orillas. | Una opción es el agua dulce. Toca su pictograma. |
| A32 | Ajolote mexicano | Vive dentro del agua. | Busca un lago o una laguna. | Una opción es el agua dulce. Toca su pictograma. |
| A33 | Delfín rosado amazónico | Vive en el agua de la Amazonía. | Busca un río o un bosque inundado. | Una opción es el agua dulce. Toca su pictograma. |
| A34 | Nutria gigante | Puede vivir en ríos y lagunas. | Busca agua con vegetación en sus orillas. | Una opción es el agua dulce. Toca su pictograma. |
| A35 | Castor norteamericano | Necesita un lugar con agua y árboles cerca. | Busca un río, arroyo, lago o estanque. | Una opción es el agua dulce. Toca su pictograma. |
| A36 | Cocodrilo del Nilo | Puede vivir en ríos y humedales. | Busca un río o una zona inundada con vegetación. | Una opción es el agua dulce. Toca su pictograma. |

### H07: Regiones polares

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A37 | Oso polar | Puede vivir en una región muy fría. | Busca una región del extremo norte o sur del planeta. | Una opción es las regiones polares. Toca su pictograma. |
| A38 | Zorro ártico | Puede vivir en una región muy fría. | Busca una región del extremo norte o sur del planeta. | Una opción es las regiones polares. Toca su pictograma. |
| A39 | Pingüino emperador | Puede vivir en una región muy fría. | Busca hielo y mar en el extremo sur del planeta. | Una opción es las regiones polares. Toca su pictograma. |
| A40 | Morsa | Puede vivir en una región muy fría. | Busca hielo y mar en el extremo norte del planeta. | Una opción es las regiones polares. Toca su pictograma. |
| A41 | Búho nival | Puede vivir en una región muy fría. | Busca una llanura fría, con pocos árboles, en el extremo norte. | Una opción es las regiones polares. Toca su pictograma. |
| A42 | Liebre ártica | Puede vivir en una región muy fría. | Busca una llanura fría, con pocos árboles, en el extremo norte. | Una opción es las regiones polares. Toca su pictograma. |

### H08: Alta montaña

| ID | Animal | Pista 1: general | Pista 2: concreta | Pista 3: explícita |
|---|---|---|---|---|
| A43 | Vicuña | Puede vivir en un lugar alto y frío. | Busca montañas altas con pastizales. | Una opción es la alta montaña. Toca su pictograma. |
| A44 | Yak salvaje | Puede vivir en un lugar alto y frío. | Busca montañas altas con pastizales. | Una opción es la alta montaña. Toca su pictograma. |
| A45 | Leopardo de las nieves | Puede vivir en un lugar alto y frío. | Busca montañas altas con rocas. | Una opción es la alta montaña. Toca su pictograma. |
| A46 | Cóndor andino | Puede vivir cerca de montañas altas. | Busca montañas con grandes paredes de roca. | Una opción es la alta montaña. Toca su pictograma. |
| A47 | Cabra de las Rocosas | Puede vivir en un lugar alto. | Busca montañas altas con pendientes rocosas. | Una opción es la alta montaña. Toca su pictograma. |
| A48 | Chinchilla de cola corta | Puede vivir en un lugar alto. | Busca montañas altas con rocas y poca vegetación. | Una opción es la alta montaña. Toca su pictograma. |

## 9. Ejemplo de un reto con ayuda

Animal: jirafa reticulada. Pregunta inicial: «¿Dónde puede vivir la jirafa?».

1. Se muestran los ocho hábitats y el botón «Ayuda».
2. Al pedir ayuda por primera vez, el agente dice: «Puede vivir en un lugar abierto, con mucho pasto».
3. Al pedir ayuda de nuevo, dice: «Busca una llanura cálida, con árboles separados».
4. Al solicitar el tercer nivel, dice: «Una opción es sabana. Toca su pictograma», junto a una tarjeta de apoyo de sabana.
5. El jugador selecciona sabana. El agente confirma: «¡Sí! La jirafa puede vivir en la sabana».
6. El jugador pulsa «Continuar». El nuevo reto comienza en nivel 0.

En todos los pasos se conservan las ocho opciones. No se selecciona ni se avanza automáticamente.

## 10. Datos que deberá recordar el agente

| Dato | Propósito |
|---|---|
| Modalidad de inicio | Determinar quién elige el animal del reto. |
| Animal actual | Consultar asociaciones y pistas del animal elegido. |
| Hábitat de guía | Mantener coherencia entre las tres pistas. |
| Asociaciones confirmadas | Aceptar cualquiera de las respuestas válidas del animal. |
| Nivel de ayuda: 0, 1, 2 o 3 | Entregar la pista siguiente o repetir la última. |
| Última selección y resultado | Responder como válida, incorrecta validada o pendiente. |
| Estado del reto | Distinguir entre esperando respuesta, resuelto y pausado. |
| Nivel usado al resolver | Registrar si el jugador resolvió sin ayuda o con apoyo. |

Estos datos se formalizarán posteriormente como variables de estado, acciones y transiciones del agente. Las reglas de ayuda no sustituyen la definición ni la evaluación del algoritmo de inteligencia artificial del proyecto.

## 11. Texto para el documento: estrategia de guía del agente

El agente utilizará una estrategia de ayuda progresiva organizada en tres niveles. En el primer nivel presentará una pista general sobre un entorno posible del animal; en el segundo ofrecerá una descripción más concreta; y en el tercero mostrará el nombre y el pictograma de una opción de hábitat válida. El jugador podrá solicitar ayuda y repetir los mensajes. Las ocho opciones de hábitat permanecerán visibles y seleccionables durante todo el reto, sin tiempo límite ni penalizaciones por solicitar apoyo.

El agente comprobará las selecciones mediante la base de asociaciones animal–hábitat. Aceptará cualquiera de las relaciones confirmadas, incluso si difiere del hábitat hacia el que orientan las pistas. Una asociación validada como incorrecta generará una invitación a intentar otra opción y el siguiente nivel de ayuda. Las relaciones pendientes de comprobación recibirán una respuesta neutral y no se contarán automáticamente como errores. Tras resolver un reto, el jugador decidirá cuándo continuar y el nivel de ayuda volverá a cero para el siguiente animal. La misma estrategia se aplicará tanto cuando inicie la partida el agente como cuando la inicie el jugador.

## 12. Fuentes ecológicas del catálogo

Fuente de trabajo: matriz_animales_habitats_48.md, versión consultada el 9 de octubre de 2026. Las fuentes siguientes respaldan las asociaciones de hábitat; no se presentan como evidencia de que estas pistas o reglas pedagógicas hayan sido evaluadas experimentalmente.

| ID | Animal | Fuentes |
|---|---|---|
| A01 | Jaguar | [Fuente 1](https://animaldiversity.org/accounts/Panthera_onca/) |
| A02 | Orangután de Borneo | [Fuente 1](https://animaldiversity.org/accounts/Pongo_pygmaeus/) |
| A03 | Gorila occidental | [Fuente 1](https://animaldiversity.org/accounts/Gorilla_gorilla/) |
| A04 | Perezoso de dos dedos de Hoffmann | [Fuente 1](https://animaldiversity.org/accounts/Choloepus_hoffmanni/) |
| A05 | Guacamayo rojo | [Fuente 1](https://animaldiversity.org/accounts/Ara_macao/) |
| A06 | Rana dardo azul | [Fuente 1](https://aqua.org/explore/animals/blue-poison-dart-frog) |
| A07 | León africano | [Fuente 1](https://animaldiversity.org/accounts/Panthera_leo/) |
| A08 | Jirafa reticulada | [Fuente 1](https://giraffeconservation.org/giraffe-species/reticulated-giraffe/); [Fuente 2](https://animals.sandiegozoo.org/animals/giraffe) |
| A09 | Cebra de llanura | [Fuente 1](https://animals.sandiegozoo.org/animals/zebra) |
| A10 | Elefante africano de sabana | [Fuente 1](https://animals.sandiegozoo.org/animals/elephant) |
| A11 | Guepardo | [Fuente 1](https://animaldiversity.org/accounts/Acinonyx_jubatus/) |
| A12 | Avestruz común | [Fuente 1](https://animaldiversity.org/accounts/Struthio_camelus/); [Fuente 2](https://animals.sandiegozoo.org/animals/ostrich) |
| A13 | Dromedario | [Fuente 1](https://animaldiversity.org/accounts/Camelus_dromedarius/) |
| A14 | Zorro fénec | [Fuente 1](https://animaldiversity.org/accounts/Vulpes_zerda/) |
| A15 | Suricata | [Fuente 1](https://animaldiversity.org/accounts/Suricata_suricatta/) |
| A16 | Tortuga del desierto de Mojave | [Fuente 1](https://animaldiversity.org/accounts/Gopherus_agassizii/) |
| A17 | Monstruo de Gila | [Fuente 1](https://animaldiversity.org/accounts/Heloderma_suspectum/) |
| A18 | Jerbo egipcio menor | [Fuente 1](https://animaldiversity.org/accounts/Jaculus_jaculus/) |
| A19 | Delfín nariz de botella | [Fuente 1](https://animaldiversity.org/accounts/Tursiops_truncatus/) |
| A20 | Ballena azul | [Fuente 1](https://animaldiversity.org/accounts/Balaenoptera_musculus/) |
| A21 | Tiburón blanco | [Fuente 1](https://animaldiversity.org/accounts/Carcharodon_carcharias/) |
| A22 | Mantarraya gigante | [Fuente 1](https://animaldiversity.org/accounts/Manta_birostris/) |
| A23 | Pulpo común | [Fuente 1](https://animaldiversity.org/accounts/Octopus_vulgaris/) |
| A24 | Tortuga verde | [Fuente 1](https://animaldiversity.org/accounts/Chelonia_mydas/) |
| A25 | Oso pardo | [Fuente 1](https://animaldiversity.org/accounts/Ursus_arctos/) |
| A26 | Lobo gris | [Fuente 1](https://animaldiversity.org/accounts/Canis_lupus/); [Fuente 2](https://explorer.natureserve.org/Taxon/ELEMENT_GLOBAL.2.105212/Canis_lupus) |
| A27 | Zorro rojo | [Fuente 1](https://animaldiversity.org/accounts/Vulpes_vulpes/); [Fuente 2](https://home.nps.gov/bela/learn/nature/red-fox.htm) |
| A28 | Ardilla roja euroasiática | [Fuente 1](https://animaldiversity.org/accounts/Sciurus_vulgaris/) |
| A29 | Corzo europeo | [Fuente 1](https://www.woodlandtrust.org.uk/trees-woods-and-wildlife/animals/mammals/roe-deer/) |
| A30 | Jabalí | [Fuente 1](https://animaldiversity.org/accounts/Sus_scrofa/) |
| A31 | Capibara o ronsoco | [Fuente 1](https://animaldiversity.org/accounts/Hydrochoerus_hydrochaeris/); [Fuente 2](https://www.worldwildlife.org/resources/facts/are-capybaras-rodents-and-5-other-capybara-facts/) |
| A32 | Ajolote mexicano | [Fuente 1](https://animals.sandiegozoo.org/animals/axolotl) |
| A33 | Delfín rosado amazónico | [Fuente 1](https://animaldiversity.org/accounts/Inia_geoffrensis/) |
| A34 | Nutria gigante | [Fuente 1](https://animaldiversity.org/accounts/Pteronura_brasiliensis/); [Fuente 2](https://www.iucnosgbull.org/Volume14/Schenck_et_al_1997.html) |
| A35 | Castor norteamericano | [Fuente 1](https://animaldiversity.org/accounts/Castor_canadensis/) |
| A36 | Cocodrilo del Nilo | [Fuente 1](https://seaworld.org/animals/facts/reptiles/nile-crocodile/) |
| A37 | Oso polar | [Fuente 1](https://animaldiversity.org/accounts/Ursus_maritimus/) |
| A38 | Zorro ártico | [Fuente 1](https://animaldiversity.org/accounts/Vulpes_lagopus/) |
| A39 | Pingüino emperador | [Fuente 1](https://animaldiversity.org/accounts/Aptenodytes_forsteri/) |
| A40 | Morsa | [Fuente 1](https://animaldiversity.org/accounts/Odobenus_rosmarus/) |
| A41 | Búho nival | [Fuente 1](https://animaldiversity.org/accounts/Nyctea_scandiaca/) |
| A42 | Liebre ártica | [Fuente 1](https://animaldiversity.org/accounts/Lepus_arcticus/) |
| A43 | Vicuña | [Fuente 1](https://animaldiversity.org/accounts/Vicugna_vicugna/) |
| A44 | Yak salvaje | [Fuente 1](https://animaldiversity.org/accounts/Bos_grunniens/) |
| A45 | Leopardo de las nieves | [Fuente 1](https://animals.sandiegozoo.org/animals/snow-leopard) |
| A46 | Cóndor andino | [Fuente 1](https://animaldiversity.org/accounts/Vultur_gryphus/) |
| A47 | Cabra de las Rocosas | [Fuente 1](https://animaldiversity.org/accounts/Oreamnos_americanus/); [Fuente 2](https://www.adfg.alaska.gov/index.cfm?adfg=goat.printerfriendly) |
| A48 | Chinchilla de cola corta | [Fuente 1](https://animaldiversity.org/accounts/Chinchilla_chinchilla/) |
