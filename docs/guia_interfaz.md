# Zoonauta: interfaz digital con pictogramas y voz

Versión 3.4.0.

## 1. Qué está implementado

La interfaz convierte clics o toques en eventos del mismo `GestorPartida` utilizado
por la consola y el simulador. El navegador presenta las respuestas preparadas por
el generador; la evaluación de asociaciones y la selección de ayudas las hace el núcleo.

| Elemento | Comportamiento disponible |
|---|---|
| Portada | Un único botón principal Comenzar abre la elección de modalidad. Volver al inicio o Escape cierran esa elección sin iniciar la partida. |
| Inicio del jugador | Muestra seis animales por página; ocho páginas permiten elegir cualquiera de los 48. |
| Inicio del agente | Prepara automáticamente el escenario siguiente. |
| Búsqueda | Filtra los 48 animales por nombre, sin distinguir mayúsculas o tildes. |
| Páginas | Anteriores y Siguientes recorren los resultados sin modificar el reto ni el progreso. Buscar vuelve a la primera página; pausar y reanudar conservan la página. |
| Pictogramas educativos | Preguntas y pistas usan los recursos originales; las tarjetas y retratos conservan los animales fotorrealistas. Los símbolos de hábitat son grandes y centrados. |
| Reto | Muestra el animal, la pregunta o pista y los ocho hábitats. |
| Progreso | Indica retos completados mediante texto y una barra accesible. |
| Ayuda | Solicita una nueva pista: niveles 1, 2 y 3; después conserva 3. |
| Repetir | Recupera la misma respuesta educativa, su secuencia y su texto de voz. |
| Pausar y reanudar | Suspende la interacción, detiene la voz y conserva el reto. |
| Selección confirmada | Acepta cualquiera de los hábitats confirmados del animal. |
| Selección pendiente | Da una respuesta neutral con una nueva pista automática, sin penalización; conserva el reto y permite repetir esa pista. |
| Continuar | Abre otro reto o presenta el cierre cuando se completó N. |
| Preferencias | Permite N entre 1 y 48 antes del inicio, idioma, voz y velocidad. |
| Revisión técnica | Página aparte con modelo, estado, decisiones y exportación JSON. |

Los ocho hábitats permanecen en los retos activos. Tras resolver se ven desactivados
para evitar completar dos veces. La pausa ofrece Reanudar y Salir. No hay puntos
competitivos, reloj ni tope de ayudas para jugar.

## 2. Ejecutarlo

Descarga y extrae el ZIP actual de GitHub, o clona el repositorio. En Windows
abre `iniciar_juego.bat` desde la carpeta que contiene `codigo`, `datos`, `docs`,
`assets` y `tests`. Al extraer el ZIP puede haber dos carpetas Zoonauta-main.
En Linux/macOS ejecuta `bash iniciar_juego.sh`.

```console
py -3 -m codigo.interfaz.iniciar
```

En Linux/macOS usa `python3` en lugar de `py -3`. El iniciador prepara Python 3.12,
las dependencias y los modelos de voz. Después abre http://127.0.0.1:8766.
Mantén la terminal abierta; Ctrl+C detiene el servidor y cierra las observaciones
abiertas sin etiqueta. Puedes pasar `--puerto 8767` si necesitas otro puerto.

El núcleo y el servidor HTTP usan la biblioteca estándar; la síntesis local añade
las dependencias ONNX de `requirements_voz.txt`. La interfaz utiliza HTML/CSS/JS,
sin Streamlit. Todos los recursos visuales están incluidos. La preparación inicial
de voz requiere Internet; los modelos y las imágenes están disponibles localmente
durante la partida. Las voces remotas del navegador pueden necesitar conexión.

Si falla la preparación de voz, el iniciador abre el juego con los recursos
disponibles y conserva los archivos verificados. Para redes restringidas o equipos
de la universidad, abre `iniciar_sin_descargas.bat` en Windows o ejecuta
`py -3 -m codigo.interfaz.iniciar --sin-descargas` (`python3` en Linux/macOS).
No instala paquetes ni descarga modelos: reutiliza el entorno local si existe,
o el Python con el que se abrió el iniciador. Las voces que estén completas y las
voces compatibles del navegador permanecen disponibles en Preferencias; el juego
puede usarse con texto y pictogramas si no hay voces. Para completar las voces
después, vuelve al iniciador normal con conexión. `--solo-preparar` requiere que
la preparación termine correctamente y no abre el juego.

Para comparar políticas con el entorno ya preparado, utiliza su ejecutable Python:

```console
.venv-voz\Scripts\python.exe -m codigo.interfaz.servidor --abrir --politica ID3 --puerto 8767
.venv-voz\Scripts\python.exe -m codigo.interfaz.servidor --abrir --politica ROTACION --puerto 8768
```

En Linux/macOS usa `.venv-voz/bin/python`. Para cargar otro modelo congelado
utiliza `--parametros RUTA`. El predeterminado es
`docs/experimentos/modelos/SIM_CONTEXTUAL_R01.json`: primera réplica contextual
del entrenamiento sintético, sin escoger una réplica por su rendimiento.
Las selecciones manuales se registran y no actualizan α o β.

## 3. Idiomas y voces

Preferencias permite elegir español o portugués brasileño. Se traducen los
controles, los 48 animales, los ocho hábitats, las 95 etiquetas de pictogramas,
las 72 variantes de pistas y los mensajes, incluidos los contextos de confirmación.
Los identificadores de recursos, las asociaciones y los registros originales
siguen siendo los del núcleo. El cambio no modifica la revisión de la partida,
las observaciones, el progreso ni los parámetros del modelo.

Hay siete opciones locales de voz por idioma. Piper: Claude y Ald (media/ligera) de México,
Daniela de Argentina; Cadu, Edresson, Faber y Jeff de Brasil. Kokoro: Dora, Alex y
Santa para cada idioma. También se agregan las voces de Microsoft y Google que
el navegador ofrece en español latinoamericano o portugués brasileño. Se muestra
su región real; no se mezclan es-ES ni pt-PT con esas opciones. No requieren
descargas de modelos ni claves de API, pero algunas necesitan Internet.
Piper y Kokoro generan WAV local; las voces del navegador utilizan Web Speech API.
Todos leen el texto preparado por la guía. Probar voz lee un saludo fijo.
El selector conserva la elección manual por idioma mientras la página esté abierta.

Abre `iniciar_juego.bat` o `bash iniciar_juego.sh`. Se prepara Python 3.12 en un
entorno aislado, compatible aunque tengas Python 3.14, y se descargan unos 656 MB
de modelos además de las dependencias. Después funciona sin conexión, claves ni
cuentas adicionales. El puerto predeterminado del iniciador es 8766.
Detalles, versiones, licencias y catálogo: [Voces locales](interfaz/alternativas_voz.md).

Pausar, Salir, cambiar de voz, ritmo o idioma y comenzar otra acción cancelan
la lectura anterior. Repetir conserva el texto y reutiliza su WAV en caché.
Recargar conserva el idioma y la partida mientras exista la sesión, y no
reproduce audio automáticamente. Sin modelos preparados se indica cómo
instalarlos; el juego continúa con texto y pictogramas.

## 4. Recursos visuales y presentación

Hay 95 imágenes: 48 animales, ocho hábitats y 39 apoyos o controles. Se utilizaron
28 PNG originales ARASAAC y 67 SVG originales. Los 20 animales con ilustración
propia incluyen rasgos específicos, como el ajolote, la rana azul o el zorro ártico.
Cada recurso conserva ruta, procedencia, licencia y SHA-256.

Los PNG genéricos representan la clase del animal; no acreditan una identificación
de subespecie. Se mantiene el nombre preciso del banco. Los SVG son esquemáticos.
La revisión técnica comprobó carga, legibilidad y correspondencia de etiquetas.
La comprensión CAA de las secuencias requiere validación posterior con usuarios.

Las tarjetas combinan el pictograma original, el recorte fotorrealista y el nombre.
Los controles incorporan pictogramas de 56 px sobre una superficie blanca.
Las preguntas y pistas usan símbolos de 96 px en escritorio y 84 px en móvil;
los hábitats, de 96–112 px. Los paneles usan texto claro sobre verde oscuro,
con fondo blanco en cada pictograma. Hay foco visible para teclado, botones nativos y un
diálogo de preferencias. En escritorio los hábitats tienen cuatro columnas; en
pantallas estrechas pasan a dos y se recorren desplazando la página.
No se elimina ninguna opción para adaptar la interfaz al móvil.

La versión 3.3 muestra una sola portada que ocupa la altura de la pantalla, sin
sección inferior ni scroll vertical. Ocho fotografías locales cambian cada 10 segundos,
con nombre y contador sincronizados. El paisaje inicial de selva se sustituyó por
una escena sin animales, coherente con los otros siete. Hay controles para avanzar,
retroceder y pausar; play o cualquiera de las flechas reanuda el cambio automático
y reinicia el intervalo de 10 segundos. La pausa solo se activa con el botón central.
El carrusel empieza en marcha, incluso con movimiento reducido, que elimina las animaciones.
Se detiene temporalmente con Preferencias abierta o con la pestaña oculta.
Este cambio decorativo no emite eventos del juego.

Los botones de modalidad usan formas redondeadas y los pictogramas de jugador y agente. Preferencias
comparte el verde oscuro, las líneas suaves y los acentos lima. Los créditos visuales
están disponibles en Preferencias y en el pie de las pantallas del juego.
El catálogo mantiene la búsqueda por nombre sin cambiar el modelo o la partida.
El catálogo, el tablero y el cierre comparten la paleta y el cuidado visual de la portada.
Los 48 animales se muestran mediante recortes fotorrealistas con transparencia, generados
con IA, en catálogo, retratos y decoración del cierre. Cada tarjeta de selección añade el
pictograma original correspondiente. Las secuencias educativas usan únicamente los pictogramas originales.
El tablero muestra los ocho paisajes realistas locales como imagen principal y
un pictograma pequeño de apoyo en la esquina. Pista (foco), Repetir, Pausar y Salir
usan las nuevas ilustraciones; la acción interna de solicitud de pista se conserva.
La pausa conserva el animal; el cierre muestra los retos realmente completados, también
cuando se sale antes de terminar. Pausa, cierre completo y salida anticipada muestran
las secuencias emitidas por el sistema. Los 95 pictogramas originales se conservan en el banco.
Las páginas con seis animales y los
retos pueden desplazarse verticalmente para conservar todas sus opciones.

No se usan vídeos, GIF ni canvas. Los ocho fondos y el atlas se generaron con la
herramienta integrada imagegen y se codificaron como WebP sin alterar su contenido.
Los recortes nuevos se generaron individualmente con la misma herramienta; sus prompts,
archivos, dimensiones, transparencia y huellas están en `datos/imagenes_animales_ia.json`.
Son imágenes sintéticas, no fotografías reales, y no modifican las asociaciones o el modelo.
La revisión del rediseño está en `docs/interfaz/revisiones/2026-10-10-redisenio/`:
55 pruebas Python, ocho casos de aceptación, 19 recorridos de interfaz y transparencia
comprobada en los 48 recortes. Las verificaciones previas permanecen en sus archivos originales.
Son elementos decorativos adicionales a los 95 pictogramas, sin autoridad para validar
asociaciones del banco. El mapa SVG anterior se conserva como antecedente.
Las referencias, los prompts y las rutas están en `docs/interfaz/diseno_visual.md`
y `docs/interfaz/fondos_generados.json`. La terminal indica 3.4.0; el pie del juego identifica la familia 3.4.

## 5. Estado y registros

Una cookie vincula el navegador con el gestor en memoria. Recargar conserva la
partida mientras el servidor siga activo y exista la cookie. Reiniciar el servidor
o abrir otro navegador inicia otra sesión. Los registros guardados no reconstruyen
automáticamente una partida anterior.

Cada acción lleva identificador de evento, sesión, reto y revisión de pantalla.
El adaptador serializa las acciones de una sesión. Un duplicado no ejecuta otra
acción; una entrada de una vista antigua devuelve la pantalla actual.
Consultar el estado no llama al motor ni abre otra observación.

La interfaz activa `ayuda_en_pendiente` en el gestor compartido. Una selección
pendiente cierra la observación anterior sin etiqueta, elige la siguiente pista
y abre su observación. El nivel llega hasta 3; posteriores selecciones pendientes
pueden presentar otra variante de ese nivel. No incrementa progreso ni actualiza
el modelo. Repetir y reanudar conservan la respuesta completa, incluido el mensaje
neutral. Consola y simulador conservan el protocolo anterior de ayuda explícita.

Los registros se guardan en `registros/interfaz/`, separados por sesión, con origen
`INTERFAZ_MANUAL`. No se solicitan datos personales. Se puede cambiar la carpeta
con `--registros RUTA`. El servidor se ejecuta solo en el equipo local.

Abre http://127.0.0.1:8766/revision en el mismo navegador para inspeccionar y
descargar el JSON de la sesión. Esta página no aparece en el recorrido del jugador.
Actualizar allí solo consulta el registro.

## 6. Recorrido para la demostración

1. Abre Preferencias, selecciona un reto y prueba una voz española disponible.
2. Pulsa Comenzar y luego Yo elijo. Muestra las páginas de seis animales y la búsqueda global.
3. Busca Capibara o ronsoco y selecciónala. Aparecen los ocho hábitats.
4. Pulsa Ayuda y Repetir. Se conserva la pista, secuencia y texto de voz.
5. Pulsa Pausar y Reanudar. El reto y la ayuda siguen vigentes.
6. Selecciona Desierto cálido: aparece una respuesta neutral y la siguiente pista
   automáticamente. Pulsa Repetir para escuchar el mismo contenido.
7. Selecciona Selva tropical: es una asociación adicional confirmada y resuelve el reto,
   aunque el hábitat de guía de la capibara sea Agua dulce.
8. Pulsa Continuar para cerrar. Comienza otra partida con Comenzar y después El agente elige.
9. Abre `/revision` para mostrar que el modelo permanece congelado.

## 7. Verificación realizada

La revisión actual pasó 68 pruebas Python y 21 casos de navegador en Edge
155.0.4283.45: 17 de interfaz y cuatro de voces Microsoft/Google controladas.
Incluye las 315 asociaciones pendientes: producen una pista automática sin
resolver el reto ni penalizar, con parámetros congelados. También comprueba
duplicados, repetición, pausa, niveles 1–3 y traducción de la respuesta compuesta.
Los ocho casos de aceptación de consola siguen pasando con su protocolo original.
Las pruebas anteriores de síntesis real de 14 voces y reproducción nativa se
conservan como evidencia de esa etapa; no se repitieron en este ajuste.

| Comprobación | Resultado |
|---|---|
| Ambas modalidades, 48 animales, ocho opciones, repetición, pausa y cierre | Correcto |
| Traducción de mensajes, 72 pistas y contextos de las 69 asociaciones confirmadas | Correcto |
| Cambio de idioma sin modificar estado, observaciones, registros o modelo | Correcto |
| Búsqueda de nombres en ambos idiomas, sin distinguir tildes o mayúsculas | Correcto |
| Recarga sin repetir acciones o audio, idioma de sesión conservado | Correcto |
| 14 opciones locales, muestras, elección por idioma, ritmo y silencio | Correcto con API y reproductor controlados |
| Modelos ausentes, idiomas inválidos y descarte de audio obsoleto | Correcto |
| 95 pictogramas y nueve WebP decorativos decodificados | Correcto |
| Móvil, teclado, progreso accesible y movimiento reducido | Correcto |
| Inicio español y portugués, de 320 × 568 a 1920 × 1080, sin scroll vertical | Correcto |
| Ocho fondos: contador, cambio cada 10 segundos, pausa y Preferencias | Correcto |
| Encabezados de revisión técnica localizados, registros originales conservados | Correcto |
| Síntesis real de las 14 opciones: WAV mono PCM no silencioso, repetición en caché | Correcto |
| Audio real de Piper español y Kokoro portugués: WAV, decodificación y avance de reproducción nativa | Correcto |
| Preparación aislada y resolución de paquetes para Windows x64/Python 3.12 | Correcto; ejecución de preparación en Linux, disponibilidad de ruedas Windows |

Evidencia actual y capturas: `interfaz/revisiones/2026-10-10-apoyos/`.
Evidencias anteriores: `interfaz/revision_navegador.json`,
`interfaz/revision_voces_locales.json`, `interfaz/revision_audio_navegador.json`
y doce capturas, incluidas las pantallas en portugués. Las pruebas de PCM y del
reproductor no certifican pronunciación ni escucha humana en otro equipo.
Las capturas tampoco constituyen certificación de accesibilidad o comprensión CAA.

```console
python -m unittest discover -s tests -v
```

Las pruebas de navegador requieren Node, Playwright y Chromium, que no son
necesarios para jugar:

```console
npm install --no-save playwright
npx playwright install chromium
python -m tests.ejecutar_navegador
python -m tests.ejecutar_navegador --voces-navegador
.venv-voz\Scripts\python.exe -m tests.verificar_voces_reales
.venv-voz\Scripts\python.exe -m tests.ejecutar_navegador --audio-real
```

Referencia: [Playwright Library](https://playwright.dev/docs/library).

## 8. Organización

| Ubicación | Contenido |
|---|---|
| `codigo/interfaz/servicio.py` | Eventos y vistas sobre el gestor compartido. |
| `codigo/interfaz/servidor.py` | Servidor local y entrega de recursos. |
| `codigo/interfaz/web/` | Pantallas, estilos, captura y adaptador de voz. |
| `codigo/interfaz/web/mundo.svg` | Antecedente: mapa decorativo de la versión 3.1. |
| `codigo/interfaz/web/portada-selva.webp` | Selva renovada del carrusel de la versión 3.3. |
| `codigo/interfaz/web/fondos/` | Siete fondos adicionales del carrusel. |
| `codigo/interfaz/web/paisajes.webp` | Atlas estático de los ocho paisajes decorativos. |
| `codigo/interfaz/crear_svg.py` | Fuente editable de las ilustraciones propias. |
| `codigo/interfaz/preparar_recursos.py` | Regeneración de recursos; innecesaria para jugar. |
| `assets/pictogramas/` | 28 PNG y 67 SVG listos para presentar. |
| `datos/pictogramas.json` | IDs simbólicos, imágenes y créditos. |
| `datos/fuentes_pictogramas.json` | Metadatos y descargas ARASAAC usadas. |
| `docs/interfaz/alternativas_voz.md` | Catálogo, preparación y verificación de las voces locales. |
| `tests/test_interfaz.py` | Concurrencia, repetición, límites y congelación. |
| `tests/ejecutar_navegador.py` | Servidor de prueba y ejecución de Playwright. |
| `tests/verificar_interfaz.cjs` | Recorridos de navegador y capturas. |

Los resultados sintéticos V2 permanecen en `docs/experimentos`. Sus informes y
las especificaciones V1 son antecedentes con el alcance de esa etapa. No se
repitieron ni se atribuyeron a jugadores por construir esta interfaz.

## 9. Texto para incorporar al documento técnico

Se implementó un prototipo digital de selección por clic o toque, conectado al
núcleo compartido de la consola y el simulador. La interfaz presenta 48 animales,
ocho hábitats y ambas modalidades de inicio. Las respuestas preparadas se muestran
como secuencias de pictogramas con texto de apoyo y síntesis de voz en español
o portugués brasileño.
Las selecciones no confirmadas ofrecen una pista automática sin castigo; se
permite pedir más ayuda, repetir el contenido, pausar, reanudar y continuar,
sin puntos competitivos ni límites de tiempo o intentos.

El adaptador web transmite eventos identificados por sesión, reto y revisión,
evitando duplicados y acciones de pantallas anteriores. El gestor conserva la
autoridad sobre las transiciones, las asociaciones confirmadas y el progreso.
El modelo probabilístico se carga congelado y registra las interacciones manuales
sin actualizar sus parámetros. La revisión técnica se realiza en una página aparte.

Se incorporaron 95 recursos visuales con rutas, créditos y huellas de integridad.
Las pruebas de Python y los recorridos en navegador verificaron el funcionamiento,
incluidos repetición, pausa, respuesta neutral, idiomas y vista móvil. La voz se
genera en el equipo mediante Piper y Kokoro. Se comprobaron WAV reales de las
14 opciones; la calidad audible en el equipo del usuario requiere escucharlas.
La comprensión CAA y la eficacia pedagógica requieren evaluación con usuarios;
los experimentos de aprendizaje siguen siendo exclusivamente sintéticos.
