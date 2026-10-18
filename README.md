# Zoonauta 4.4.0

Juego de animales y hábitats con pictogramas y una guía de inteligencia artificial.
Disponible en español y portugués brasileño, con voces locales Piper y Kokoro
y voces compatibles de Microsoft y Google del navegador.

![Pantalla principal actual de Zoonauta](docs/interfaz/3.8/inicio.webp)

## Cómo se juega

Pulsa **Comenzar** y escoge **Yo elijo** o **El agente elige**.
La guía lee «¿Quién elige el animal?» al abrir ese diálogo; al volver a la
portada o comenzar otra partida no se reproduce esa pregunta. Cerrar el diálogo
cancela la lectura.
El catálogo permite elegir cualquiera de los 48 animales, en ocho páginas de seis,
con búsqueda global por nombre. En modo agente, cada partida mezcla los 48 animales
y presenta tantos como hayas elegido en Preferencias (de 1 a 48; ocho por defecto).
No se repiten animales dentro de la partida y una nueva partida comienza con otro animal.
Pausar, repetir o recargar conserva el orden de la partida en curso.

El número de retos debe ser un entero del **1 al 48**. Si falta o no es válido,
Comenzar indica cómo corregirlo en Preferencias. Los avisos son tarjetas compactas
con fondo oscuro y borde según su tipo, abajo a la derecha. Los nuevos aparecen
debajo y los anteriores suben sin superponerse. Se muestran **hasta tres** a la vez;
si falta altura, se reduce la cantidad y se retiran los más antiguos, sin scroll
ni tarjetas cortadas. Cada tarjeta desaparece a los
**8 segundos** o se cierra con su **×** circular sobre la esquina superior derecha.
Créditos visuales, dentro de Preferencias, muestra la versión del programa.

En **Preferencias → Hábitats para elegir** se pueden configurar **2, 4 u 8 opciones**
(ocho por defecto). El educador elige la cantidad antes de comenzar. Cada reto incluye
el hábitat guía y al menos una alternativa pendiente; los demás se mezclan sin
duplicados. La respuesta válida no ocupa siempre la misma posición. Las opciones
permanecen estables al pedir pistas, repetir, pausar o recargar la partida.

Cada reto presenta el animal, una pregunta y los hábitats configurados. Las tarjetas usan paisajes
realistas generados específicamente para ellas, con composición central, nombre y
número del **01 al 08**. Las preguntas y pistas conservan sus secuencias de pictogramas,
con texto de apoyo y lectura en voz alta. Una selección pendiente ofrece una pista
nueva automáticamente, sin castigo. **Pista** usa un foco; **Repetir** conserva el
contenido, **Pausar** suspende el reto y **Salir** permite terminarlo.
El cierre presenta al robot guía despidiéndose con su cuaderno; al pausar,
el robot descansa sentado en un banco. Ambas imágenes mantienen el estilo de
caricatura y la transparencia, sin mostrar el último animal. El progreso indica
los retos realmente completados mediante texto y barra; **Comenzar otra partida**
vuelve a la portada en silencio. **Reanudar** conserva el animal y el reto.
No hay puntos competitivos ni límite de tiempo o intentos.

En computadora, el tablero aprovecha el ancho y la altura disponibles, con un
fondo continuo. El animal aparece grande y completo, con su nombre debajo; los
cuatro controles quedan bajo él en dos filas. La guía y los ocho hábitats se
alinean a la derecha, con pictogramas y etiquetas más grandes. El tablero cabe
sin scroll en las resoluciones probadas, incluidas 1024 × 768 y 1280 × 720.
La cabecera, el logo y Preferencias quedan en el inicio; el pie se oculta durante
el juego. En móvil se apila el contenido. Una ventana muy baja permite scroll
para conservar imágenes, nombres y controles completos.

Los 95 recursos educativos activos son ilustraciones originales con transparencia:
48 animales, ocho símbolos de hábitat y 39 apoyos o controles. Cada animal tiene una
única caricatura. Los 33 apoyos de comunicación renovados en 3.8 siguen el mismo estilo
de la capibara aprobada: contornos definidos, colores naturales y sombreado suave.
Explorar y Buscar tienen representaciones distintas. Los pictogramas de preguntas,
pistas y controles se muestran sin recuadros blancos. Su comprensión CAA sigue
pendiente de evaluación con usuarios de Kallpa.

La portada conserva sus ocho paisajes y cambia de fondo cada diez segundos.
Pausar actúa al pulsarlo; play o las flechas reanudan y reinician el intervalo.
Preferencias y una pestaña inactiva suspenden temporalmente el carrusel.
La interfaz se adapta a móvil y permite selección con teclado.

## Cierre técnico e instrucciones de uso

Preferencias aprovecha el ancho de la pantalla: idioma y partida a la izquierda,
voz y ritmo a la derecha. En escritorio se muestran juntos; en ventanas pequeñas
se apilan y permiten desplazamiento para conservar los controles completos.
Tab y Mayús+Tab recorren los controles del diálogo; Escape lo cierra.

El [manual de usuario](docs/manual_usuario.md) explica el inicio y los controles.
El [cierre técnico del Hito 3](docs/cierre_tecnico_hito3.md) reúne ejecución,
casos de borde y límites de las comprobaciones. El informe, el video y la
evaluación con usuarios son entregables distintos de estas verificaciones.

La ampliación de los textos de audio y la integración de ElevenLabs quedan
pendientes de definir el contenido. Las voces disponibles permanecen sin cambios.

## Ejecutar el juego

Clona este repositorio o descarga y extrae su ZIP. Abre la terminal en la carpeta
que contiene `codigo`, `datos`, `docs`, `assets` y `tests`. Al extraer el ZIP en
Windows, esa carpeta puede quedar dentro de otra `Zoonauta-main`. Para jugar:

En Windows abre **iniciar_juego.bat**. En Linux/macOS ejecuta
`bash iniciar_juego.sh`. También puedes iniciarlo desde una terminal:

```console
py -3 -m codigo.interfaz.iniciar
```

En Linux/macOS utiliza `python3` en lugar de `py -3`. El iniciador prepara un
entorno aislado con Python 3.12, los motores y los modelos, y abre
http://127.0.0.1:8766. Puedes conservar tu Python 3.14: el juego prepara su propia
versión compatible. Mantén la terminal abierta; Ctrl+C detiene el servidor.

La primera preparación requiere Internet y descarga unos **656 MB de modelos**,
además de Python y las dependencias que falten. Las descargas se verifican por
huella y tamaño. Si se interrumpen, vuelve a abrir el iniciador: conserva los
archivos completos comprobados. Después puedes jugar y escuchar las voces locales sin
conexión, claves de API ni cuentas adicionales.

Si la preparación falla por la conexión o por restricciones del equipo, el juego
abre con los recursos disponibles. Para omitir todas las instalaciones y descargas,
abre **iniciar_sin_descargas.bat** en Windows, o ejecuta:

```console
py -3 -m codigo.interfaz.iniciar --sin-descargas
```

En Linux/macOS usa `python3`. Puedes elegir en Preferencias las voces locales ya
completas o las voces compatibles del navegador. Si no hay ninguna disponible,
puedes jugar con texto y pictogramas. Esta opción requiere Python, pero no los
paquetes de voz. Para preparar las voces más adelante, abre `iniciar_juego.bat`
con una conexión que permita las descargas. `--solo-preparar` sigue indicando un
error si no logra completar la instalación.

Para usar otro puerto:

```console
iniciar_juego.bat --puerto 8767
```

Para actualizar una copia descargada como ZIP, detén el servidor, descarga el ZIP
actual y extrae la nueva versión. Puedes copiar la carpeta `modelos_voz` de la
versión anterior para evitar descargarla otra vez; el iniciador la comprobará.
Un ZIP anterior no se actualiza automáticamente.

Antes de comenzar, abre **Preferencias → Idioma** en la portada para elegir Español o Português (Brasil). Cambian
los controles, los 48 nombres de animales, los ocho hábitats, las etiquetas de
pictogramas, las pistas, las confirmaciones y las voces. El selector conserva siete opciones
locales por idioma y añade las voces compatibles de Microsoft y Google del navegador,
agrupadas por proveedor; **Probar voz** reproduce una muestra. La selección
manual se conserva por idioma mientras la página está abierta. Las voces del navegador
no necesitan descargar modelos ni claves de API; algunas requieren Internet.
Se aceptan las regiones latinoamericanas del español (incluidos es-419 y es-US)
y pt-BR. No se presenta una voz es-ES como latinoamericana ni pt-PT como brasileña.
Su disponibilidad depende del navegador y de las voces instaladas.

| Idioma | Motor | Opciones |
|---|---|---|
| Español | Piper | Claude (México), Ald (México, media y ligera), Daniela (Argentina) |
| Español | Kokoro | Dora, Alex, Santa |
| Português (Brasil) | Piper | Cadu, Edresson, Faber, Jeff |
| Português (Brasil) | Kokoro | Dora, Alex, Santa |
| Español latinoamericano | Microsoft / Google | Las voces regionales que expone el navegador |
| Português (Brasil) | Microsoft / Google | Las voces pt-BR que expone el navegador |

Ald ofrece dos variantes del mismo hablante. El ZIP contiene el catálogo y el
instalador; los pesos grandes se descargan al preparar el juego. Consulta
[la guía de voces](docs/interfaz/alternativas_voz.md) y
[la guía de interfaz](docs/guia_interfaz.md).

## Inteligencia artificial y revisión

La interfaz carga el modelo sintético contextual R01 de
`docs/experimentos/hito2/entrenamiento/modelos`, congelado, elegido como primera
réplica y no por su rendimiento. El núcleo comparte las asociaciones y transiciones
con consola y simulador. Las interacciones manuales se registran sin modificar los
parámetros del modelo. La selección aleatoria del animal es independiente de la
política que escoge las pistas. Consola y simulador conservan su orden reproducible.

El agente probabilístico utiliza el historial del reto: tras una selección pendiente,
prioriza un atributo que distinga el paisaje elegido del hábitat guía. Tras dos
selecciones pendientes ofrece el apoyo explícito. **Repetir** conserva exactamente
el mensaje; si después se solicita otra pista, puede reformularlo una vez antes de
avanzar. En cada nivel prioriza variantes todavía no presentadas en ese reto y evita
la repetición inmediata cuando hay alternativas. Estas reglas son observables en
`/revision`; complementan el selector entrenado y no suponen aprendizaje en vivo.

Para revisar y exportar los registros de la sesión, abre
http://127.0.0.1:8766/revision en el mismo navegador.

Otros comandos desde esta carpeta, que contiene codigo, datos, docs, assets y tests:

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 2
python -m codigo.interfaz.servidor --politica ID3 --puerto 8001
python -m codigo.interfaz.servidor --politica ROTACION --puerto 8002
python -m codigo.poc.consola --modalidad AGENTE --retos 2
python -m codigo.entrenamiento.experimento --salida resultados_nuevos
python -m codigo.entrenamiento.evaluar_demo --entrenamiento 15360 --salida resultados_nuevos/demo
python -m codigo.nucleo.auditoria --salida resultados_nuevos/auditoria.json
python -m codigo.nucleo.verificar_paquete
python -m codigo.poc.aceptacion
python -m unittest discover -s tests -v
```

ID3 construye el árbol calculando ganancias. La evaluación del protocolo actual
utilizó datos sintéticos: **276 480 retos de entrenamiento y 155 520 de evaluación**,
con tres condiciones, seis réplicas y las políticas ID3, rotación y probabilística,
separadas por tamaño del panel. Las semillas de entrenamiento y evaluación son
distintas; los parámetros permanecen congelados al evaluar.
Los resultados y las curvas de evolución se conservan en
[evaluacion_demo.json](docs/experimentos/hito2/evaluacion_demo.json).
El entrenamiento ampliado utiliza 15 360 retos por condición y réplica, frente a
los 1 920 iniciales. Conserva las semillas, el prefijo del entrenamiento y la
separación de la evaluación. El error medio frente a las probabilidades artificiales
pasó de 0,104 a 0,053. Todas las distribuciones tienen observaciones; 81 de las
2 592 distribuciones de las 18 réplicas siguen teniendo menos de diez etiquetas.
Las tres últimas variaciones medias son inferiores a 0,01 en cada réplica. Este
diagnóstico de estabilidad media no prueba convergencia general ni precisión de
cada variante. La primera réplica contextual sigue fijada como modelo del demo;
no se eligió una semilla por sus resultados de evaluación.
El [diagnóstico](docs/experimentos/hito2/diagnostico_entrenamiento.json) conserva
la comparación y sus límites. Para reproducirlo:

```console
python -m codigo.entrenamiento.diagnosticar --antes docs/experimentos/hito2/antecedentes_1920 --despues docs/experimentos/hito2 --salida resultados_nuevos/diagnostico.json
```

El simulador no modela el efecto cognitivo del número de opciones: resultados iguales
entre tamaños comprueban el flujo, no que los tres tamaños sean igual de accesibles.
Las ejecuciones anteriores de `docs/experimentos` son antecedentes.

La ayuda automática ante selecciones pendientes está activa en la interfaz y en
`evaluar_demo`. El comando histórico `experimento` usa ayuda explícita salvo que se
indique `--ayuda-automatica`; admite `--opciones 2`, `4` u `8`. La consola también
admite `--opciones`. Las 315 relaciones pendientes conservan su estado y no se
consideran errores. La auditoría comprueba referencias registradas, secuencias y
traducciones; no sustituye la revisión biológica ni la validación con usuarios.

La verificación del manifiesto acepta exclusivamente la conversión LF → CRLF de
los iniciadores BAT declarada en `.gitattributes`; comprueba el resto de su contenido
y todos los demás archivos por tamaño y SHA-256. Una copia recién extraída puede
probarse sin instalar voces ni reutilizar el entorno local:

```console
python -m tests.verificar_copia_limpia --carpeta ruta_de_la_copia_extraida --salida resultados_nuevos/copia_limpia
```

La prueba ejecuta el iniciador real con `--sin-descargas`, suprime únicamente la
apertura de una ventana y comprueba partidas completas en ambas modalidades con
2, 4 y 8 opciones. Requiere Python y una carpeta sin `.venv-voz` ni `modelos_voz`.

La revisión local pasó **96 pruebas Python**, los ocho casos de aceptación de
consola y **47 casos de navegador**: 20 de revisión general, seis del modo 2/4/8
en ambos idiomas, cinco de voces controladas y 16 de Preferencias y teclado.
Las [evidencias del cierre](docs/experimentos/hito3/revision_cierre.json) conservan
el alcance técnico y los pasos que requieren evaluación humana.
El comprobador general libera los
contextos entre escenarios conservando la cookie de la partida; mantiene todas
las comprobaciones. Comprueba transiciones, repetición, pausa, duplicados,
traducciones, transparencia, cierre, teclado, móvil, progreso real y los 48 animales
sin repeticiones. [Revisión del agente](docs/experimentos/hito2/revision_codigo.json).
La copia pública descargada también completó seis partidas sin instalar voces.
Las evidencias anteriores de síntesis real de las 14 voces permanecen en
`docs/interfaz/revision_voces_locales.json`; no certifican pronunciación o escucha
en otros dispositivos. Los documentos V1/V2 y sus resultados son antecedentes.

## Imágenes y documentación

Las ilustraciones y paisajes son imágenes sintéticas generadas con la herramienta
integrada de imágenes, no fotografías de ejemplares o lugares específicos.
Las rutas, prompts, transparencia y huellas de integridad se documentan en:

- [Animales](datos/imagenes_animales_ia.json).
- [Persona y agente](datos/imagenes_modalidad_ia.json).
- [Robot de despedida y pausa](datos/imagenes_cierre_pausa_ia.json).
- [Símbolos de hábitat y controles](datos/imagenes_habitats_controles_ia.json).
- [Apoyos de preguntas y pistas, versión 3.8](datos/imagenes_apoyos_ia.json).
- [Paisajes centrados de las tarjetas](datos/imagenes_paisajes_tarjetas_ia.json).

Los 19 WebP decorativos utilizados (ocho fondos de inicio, un atlas, ocho paisajes
de tarjetas y dos ilustraciones del robot) son adicionales al banco de 95 pictogramas.
Los créditos de ARASAAC y de los SVG del prototipo se mantienen como antecedentes;
esos recursos no son las imágenes activas. Las ilustraciones originales se ofrecen
bajo CC BY-NC-SA 4.0. Consulta [créditos](docs/creditos_pictogramas.md),
[guía de interfaz](docs/guia_interfaz.md) y [diseño visual](docs/interfaz/diseno_visual.md).
