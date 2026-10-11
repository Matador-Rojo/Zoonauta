# Zoonauta: contexto para continuar en Codex

Fecha del traspaso: 10 de octubre de 2026.
Repositorio: https://github.com/Matador-Rojo/Zoonauta
Versión funcional de referencia: **3.4.0**, commit `3d71aaa6e03b50bd091ce823f08da61d265c6e94`.

Este archivo resume las decisiones tomadas con el usuario y el estado del proyecto. Al continuar, comprueba la versión actual del repositorio: puede haber cambios posteriores a este punto de referencia.

## 1. Qué estamos construyendo

Zoonauta es un juego de animales por hábitat para el trabajo parcial del curso de Inteligencia Artificial. El ejercicio original se refería a PictoChef; el usuario eligió **Zoonauta** como nombre de este proyecto.

El jugador relaciona animales con hábitats y recibe preguntas, pistas y confirmaciones mediante pictogramas, texto y voz. El objetivo del agente es guiar la interacción y seleccionar asistencia apropiada. El usuario descartó los puntos competitivos. El progreso indica retos completados.

El usuario pidió expresamente **48 animales y ocho hábitats**, para tener variedad suficiente:

| ID | Hábitat |
|---|---|
| H01 | Selva tropical |
| H02 | Sabana |
| H03 | Desierto cálido |
| H04 | Mar |
| H05 | Bosque templado |
| H06 | Agua dulce |
| H07 | Regiones polares |
| H08 | Alta montaña |

Se mantienen dos modalidades de inicio. En `JUGADOR` (Yo elijo), el jugador elige un animal del catálogo completo. En `AGENTE` (El agente elige), el sistema prepara el siguiente escenario del banco. El jugador selecciona el hábitat por clic o toque; también hay navegación con teclado. No supongas que existen entrada por voz, reconocimiento de imágenes u otras modalidades que no estén implementadas.

## 2. Reglas educativas y estado

Una partida contiene N retos, configurable entre 1 y 48 antes de comenzar. Las ocho opciones de hábitat se mantienen disponibles mientras el reto está activo. Un animal puede practicarse de nuevo en otro reto.

- Hay tres niveles de ayuda: `0 → 1 → 2 → 3 → 3`. Una nueva ayuda de nivel 3 puede variar su presentación; `Repetir` reproduce exactamente el contenido educativo actual.
- Pausar y reanudar conserva el animal, el nivel, la pista y el progreso. No hay reloj ni límite de intentos o ayudas.
- Cualquier hábitat confirmado para el animal resuelve el reto, aunque sea diferente del hábitat de guía usado para las pistas.
- La matriz contiene **384 relaciones: 69 válidas, 315 pendientes y cero incorrectas verificadas**. Una pendiente recibe un mensaje neutral y no aumenta el nivel ni se etiqueta como un fracaso para entrenar.
- Por ejemplo, la capibara `A31` tiene asociaciones confirmadas con `H01`, `H02` y `H06`. Su guía usa agua dulce; las otras dos también se aceptan.
- Después de resolver, `Continuar` abre el siguiente reto o el cierre. Los clics duplicados no incrementan otra vez el progreso.
- Las fases son `INICIO`, `SELECCION_ANIMAL`, `PRESENTACION`, `ESPERANDO_RESPUESTA`, `RETO_RESUELTO`, `PAUSADA`, `COMPLETADA` y `ABANDONADA`.

La especificación formal está en `docs/diseno/formalizacion_agente_animales_habitats.md`. El modelo principal refina el diseño inicial añadiendo variantes de ayuda y observaciones. Los documentos de diseño V1 describen su etapa de propuesta; expresiones como «todavía no implementado» en esos antecedentes no describen automáticamente la versión 3.4.

## 3. Qué inteligencia artificial utiliza

El núcleo comparte reglas y datos entre la consola, el simulador y la interfaz. La guía combina:

1. **Reglas expertas** para las fases, asociaciones y límites de asistencia.
2. **ID3**, construido con entropía y ganancia de información a partir de ocho perfiles didácticos de hábitat, para la ruta de atributos de las pistas.
3. Un selector **Beta–Bernoulli** para elegir entre variantes verificadas de ayuda según hábitat, nivel y uso previo de `Repetir`.

La política `PROBABILISTICO` de la partida elige la mayor media posterior `alpha / (alpha + beta)` entre variantes elegibles. Evita la última variante del mismo hábitat y nivel cuando hay alternativas. No genera contenido libre ni utiliza un modelo de lenguaje para inventar pistas. Thompson Sampling pertenece a la exploración del entrenamiento sintético; no es la política congelada que el jugador usa en la interfaz.

También se conservan `ID3` con V1 fija y `ROTACION` como políticas de comparación. El entrenamiento se ejecuta por separado. En las sesiones del juego, los parámetros quedan congelados: cambiar idioma, voz o interfaz no entrena el modelo.

El modelo predeterminado de la interfaz es `docs/experimentos/modelos/SIM_CONTEXTUAL_R01.json`, primera réplica contextual por orden, elegida sin buscar la de mejor rendimiento. Su SHA-256 es `ee2bcd397ae18de09f5b4ed83c3244ceacc0c757146276a7b086534c62cc05e9`.

Las evidencias incluyen 18 modelos sintéticos, 34 560 retos de entrenamiento y 51 840 de evaluación, con semillas separadas. No proceden de jugadores reales. Conserva los resultados de `docs/experimentos/`; un experimento nuevo debe tener su propia carpeta.

Para explicar el algoritmo de forma sencilla: «Usé ID3 y probabilidades para que el agente elija qué pista darle al jugador».

## 4. Interfaz acordada con el usuario

La aplicación tiene un servidor local Python y una interfaz HTML/CSS/JavaScript que se abre en el navegador. No es una web pública desplegada ni necesita Streamlit.

El usuario pidió una presentación moderna. Sus referencias visuales fueron https://motionsites.ai/, https://www.scrolltide.co/ y https://sceneai.art/. Sirven como inspiración; no se pidió copiar una página. El usuario quiere **imágenes estáticas**, sin vídeos ni GIF.

La portada ocupa una sola pantalla, sin desplazamiento vertical ni secciones de eslóganes. Se retiraron «Elige. Explora. Conecta.» y «Ocho paisajes. Muchos hogares.». Hay ocho fondos fotográficos coherentes, incluyendo una selva renovada sin el guacamayo anterior. Cambian cada **10 segundos**, con nombre y contador `01 / 08` sincronizados. Hay controles para avanzar, retroceder y pausar. La navegación manual pausa el carrusel; Preferencias abierta y la pestaña oculta lo detienen temporalmente. Con movimiento reducido comienza pausado.

Los botones de modalidad y Preferencias comparten una paleta verde oscura con acentos lima. Conserva la dirección visual actual al hacer cambios. La restricción de una pantalla corresponde a la portada: el catálogo de 48 animales y el tablero pueden desplazarse en móvil. No escondas opciones para reducir su altura.

El catálogo tiene búsqueda por nombre sin distinguir mayúsculas ni tildes. El tablero separa animal, guía y hábitats; muestra cuatro columnas de hábitats en escritorio y dos en móvil. Las fotografías son decoración; no sustituyen los pictogramas ni validan asociaciones.

Hay **95 pictogramas educativos**: 28 PNG ARASAAC sin modificación y 67 SVG propios, con créditos y huellas. Los nueve WebP decorativos utilizados son ocho fondos y un atlas. Consulta `docs/creditos_pictogramas.md`, `datos/fuentes_pictogramas.json` y `docs/interfaz/diseno_visual.md`.

## 5. Idiomas y voces: ya implementados

En Preferencias se elige **Español** o **Português (Brasil)**. Cambian controles, animales, hábitats, etiquetas de pictogramas, pistas, mensajes y contextos de confirmación. Los IDs del núcleo, asociaciones y registros siguen siendo canónicos. Cambiar idioma conserva la partida y no cambia sus parámetros.

El usuario pidió retirar las cuatro voces anteriores del navegador y agregar Piper de México y Argentina, Kokoro y portugués brasileño. Actualmente hay **14 opciones: siete por idioma**:

| Idioma | Motor | Opciones |
|---|---|---|
| Español | Piper | Claude MX high; Ald MX medium; Ald MX x_low; Daniela AR high |
| Español | Kokoro | Dora `ef_dora`; Alex `em_alex`; Santa `em_santa` |
| Português (Brasil) | Piper | Cadu medium; Edresson low; Faber medium; Jeff medium |
| Português (Brasil) | Kokoro | Dora `pf_dora`; Alex `pm_alex`; Santa `pm_santa` |

Ald ofrece dos calidades del mismo hablante. La elección manual se conserva por idioma mientras la página está abierta. `Probar voz` lee un saludo fijo. El juego sintetiza el texto preparado por el núcleo; el endpoint no acepta texto libre arbitrario del cliente.

Se usa audio WAV generado localmente, sin claves de API ni cuentas de pago. El usuario descartó la opción de voz que figuraba como «pendiente de activación». No reintroduzcas ese proveedor ni las voces antiguas como sustitución automática.

Las acciones nuevas, pausa, salida y cambios de idioma, voz o velocidad cancelan la lectura anterior. Las respuestas de audio antiguas se descartan. La recarga no reproduce voz automáticamente. Sin preparar modelos, el juego puede seguir con texto y pictogramas.

`requirements_voz.txt` fija 32 dependencias, incluyendo `piper-tts==1.3.0` y `kokoro-onnx==0.4.9`. El adaptador `SesionONNXTipada` conserva tipos compatibles con el modelo Kokoro usado. No actualices versiones o exportaciones a ciegas: hay pruebas reales de estas combinaciones.

`datos/voces_locales.json` fija 26 archivos con tamaños y huellas, unos **656 MB**. Los pesos se descargan en `modelos_voz/`, excluido de Git. El instalador conserva archivos completos verificados si una descarga se interrumpe. Las comprobaciones de hash y descarga están en `codigo/interfaz/preparar_voces.py`. Los detalles y las licencias están en `docs/interfaz/alternativas_voz.md`.

## 6. Cómo ejecutarlo

Trabaja desde la carpeta raíz que contiene `codigo`, `datos`, `docs`, `assets` y `tests`.

En Windows, abre `iniciar_juego.bat`, o ejecuta:

```console
py -3 -m codigo.interfaz.iniciar
```

En Linux/macOS:

```console
bash iniciar_juego.sh
```

El iniciador prepara Python 3.12 aislado mediante uv en `.venv-voz`, instala las dependencias y descarga los modelos. El usuario tiene Python 3.14; no necesita reemplazarlo. La primera preparación requiere Internet para Python, dependencias y pesos. Después la síntesis es local.

Se abre `http://127.0.0.1:8766`. Mantén la terminal abierta; Ctrl+C detiene el servidor. El puerto 8766 se eligió tras problemas con el 8000 en Windows. Puedes usar `iniciar_juego.bat --puerto 8767` o `python3 -m codigo.interfaz.iniciar --solo-preparar` para preparar sin abrir el servidor.

Para revisar la interfaz sin descargar voces:

```console
python -m codigo.interfaz.servidor --puerto 8766
```

Abre la dirección local manualmente. El núcleo y el servidor usan la biblioteca estándar; la voz necesita sus dependencias y pesos. Una copia nueva en Codex no incluye automáticamente el entorno ni los modelos preparados en el equipo del usuario.

La partida vive en memoria, vinculada a una cookie. Recargar conserva la sesión mientras exista el servidor; reiniciarlo no restaura automáticamente una partida desde los registros. `/revision` es la página técnica del mismo navegador. Los registros manuales se guardan en `registros/interfaz/`, excluido de Git, con origen `INTERFAZ_MANUAL`; no se piden datos personales.

## 7. Dónde está cada parte

| Ruta | Responsabilidad |
|---|---|
| `codigo/nucleo/` | Datos, estado, gestor de transiciones y registro. |
| `codigo/motores/id3.py` | Construcción del árbol ID3. |
| `codigo/motores/guia.py` | Políticas de elección de ayudas y modelo congelado. |
| `codigo/respuestas/generador.py` | Respuestas educativas preparadas. |
| `codigo/entrenamiento/` | Simulación, aprendizaje y comparación. |
| `codigo/interfaz/servicio.py` | Sesión web y adaptación de acciones al núcleo. |
| `codigo/interfaz/servidor.py` | Servidor local y endpoints HTTP. |
| `codigo/interfaz/idiomas.py` | Traducción de la presentación. |
| `codigo/interfaz/voz.py` | Síntesis Piper/Kokoro y caché de WAV. |
| `codigo/interfaz/iniciar.py` | Preparación del entorno e inicio. |
| `codigo/interfaz/web/` | HTML, CSS, JavaScript y fondos locales. |
| `datos/` | Catálogos, asociaciones, ayudas, configuración y metadatos. |
| `datos/traducciones_pt_BR.json` | Traducciones brasileñas. |
| `assets/pictogramas/` | Imágenes educativas. |
| `docs/guia_interfaz.md` | Guía actual de funcionamiento y demostración. |
| `docs/diseno/` | Formalización, arquitectura y diseño inicial del modelo. |
| `docs/experimentos/` | Resultados sintéticos ya ejecutados. |
| `docs/interfaz/` | Diseño, capturas y evidencias de navegador y voz. |
| `tests/` | Pruebas del núcleo, aprendizaje, web, idiomas y voz. |
| `datos/manifest.json` | Tamaños y SHA-256 de los archivos del proyecto; excluye el propio manifest. |

## 8. Verificación anterior y cómo repetirla

La versión 3.4.0 tiene evidencia de **49 pruebas Python**, ocho casos de aceptación, 14 casos de interfaz en Chromium, síntesis real de las 14 voces y dos pruebas con reproductor nativo: español con Piper y portugués con Kokoro.

Los 14 casos generales de interfaz usan respuesta WAV y reproductor controlados para comprobar la lógica. Las dos pruebas nativas de audio comprobaron además WAV, decodificación y avance de reproducción real. Se verificaron vistas móviles, teclado, neutralidad, repetición, pausa, traducciones y congelación del modelo.

Comprobaciones del núcleo y adaptador:

```console
python -m unittest discover -s tests -v
python -m codigo.poc.aceptacion
```

Interfaz, con Node, Playwright y Chromium instalados para las pruebas:

```console
python -m tests.ejecutar_navegador
```

Voces reales, después de preparar el entorno. En Windows:

```console
.venv-voz\Scripts\python.exe -m tests.verificar_voces_reales
.venv-voz\Scripts\python.exe -m tests.ejecutar_navegador --audio-real
```

En Linux/macOS usa `.venv-voz/bin/python`. Estos verificadores pueden actualizar JSON y capturas de evidencia; revisa sus cambios y el manifest si se incluyen en un commit.

Las evidencias están en `docs/interfaz/revision_navegador.json`, `docs/interfaz/revision_voces_locales.json` y `docs/interfaz/revision_audio_navegador.json`. El entorno y la síntesis se ejecutaron en Linux. Se comprobó disponibilidad de las 32 dependencias para Windows x64/Python 3.12; eso no equivale a haber ejecutado todo nativamente en Windows.

Las comprobaciones de WAV no certifican pronunciación, naturalidad o escucha en el dispositivo del usuario. Tampoco hay validación CAA o eficacia pedagógica con personas. Mantén estos límites al explicar resultados.

## 9. Qué queda pendiente

El código, los datos, la interfaz bilingüe y las voces locales están implementados en esta versión. No se debe afirmar que toda la entrega académica está terminada.

El usuario dejó el **documento académico para después**. El informe final, la presentación PPT y el video siguen pendientes. Hay especificaciones y guías para apoyarlos, pero no son el informe final. La última captura del enunciado compartida indicaba cuatro archivos obligatorios: **informe, PPT, demo y video**, con un envío por grupo. Al preparar la entrega, revisa el enunciado completo del Campus; no inventes formatos, plazos, duración o criterios a partir de este resumen. También se mencionó explicar el objetivo del producto y su relación con Kallpa.

Falta confirmar en el equipo del usuario la preparación, reproducción y preferencia de voces. Cualquier evaluación con usuarios debe distinguirse de la simulación ya ejecutada.

La petición actual es trasladar el proyecto y su contexto a Codex. Aún no se ha elegido una nueva modificación funcional. Al comenzar allí, resume brevemente lo entendido y los pendientes; continúa con la siguiente indicación concreta del usuario. No conviertas el traspaso en una reescritura de la interfaz, un nuevo entrenamiento o la redacción del informe aplazado.
