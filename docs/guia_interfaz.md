# Zoonauta: interfaz digital con pictogramas y voz

Versión 3.3.0.

## 1. Qué está implementado

La interfaz convierte clics o toques en eventos del mismo `GestorPartida` utilizado
por la consola y el simulador. El navegador presenta las respuestas preparadas por
el generador; la evaluación de asociaciones y la selección de ayudas las hace el núcleo.

| Elemento | Comportamiento disponible |
|---|---|
| Inicio del jugador | Muestra los 48 animales, todos seleccionables. |
| Inicio del agente | Prepara automáticamente el escenario siguiente. |
| Búsqueda | Filtra los 48 animales por nombre, sin distinguir mayúsculas o tildes. |
| Reto | Muestra el animal, la pregunta o pista y los ocho hábitats. |
| Progreso | Indica retos completados mediante texto y una barra accesible. |
| Ayuda | Solicita una nueva pista: niveles 1, 2 y 3; después conserva 3. |
| Repetir | Recupera la misma respuesta educativa, su secuencia y su texto de voz. |
| Pausar y reanudar | Suspende la interacción, detiene la voz y conserva el reto. |
| Selección confirmada | Acepta cualquiera de los hábitats confirmados del animal. |
| Selección pendiente | Da una respuesta neutral y conserva el reto. |
| Continuar | Abre otro reto o presenta el cierre cuando se completó N. |
| Preferencias | Permite N entre 1 y 48 antes del inicio, voz y velocidad. |
| Revisión técnica | Página aparte con modelo, estado, decisiones y exportación JSON. |

Los ocho hábitats permanecen en los retos activos. Tras resolver se ven desactivados
para evitar completar dos veces. La pausa ofrece Reanudar y Salir. No hay puntos
competitivos, reloj ni tope de ayudas para jugar.

## 2. Ejecutarlo

Descarga y extrae el ZIP actual de GitHub, o clona el repositorio. Abre una terminal en la carpeta
que contiene `codigo`, `datos`, `docs`, `assets` y `tests`. Utiliza Python 3.10 o superior.
En Windows puede ser necesario entrar en una segunda carpeta `Zoonauta-main`.

```console
python -m codigo.interfaz.servidor --abrir
```

Abre http://127.0.0.1:8000 si el navegador no se abre automáticamente. En Windows
puedes usar `py` en lugar de `python`. Mantén la terminal abierta mientras juegas.
Ctrl+C detiene el servidor y cierra las observaciones abiertas sin etiqueta.
También se incluyen `iniciar_juego.bat` y `iniciar_juego.sh`.

La aplicación usa la biblioteca estándar de Python y HTML/CSS/JavaScript.
Esta elección concreta la propuesta de interfaz: no utiliza Streamlit.
Todos los recursos visuales están incluidos; no se descargan durante la partida.

Si el puerto está ocupado o Windows muestra `WinError 10013`, prueba otro puerto:

```console
py -m codigo.interfaz.servidor --abrir --puerto 8765
```

La dirección será http://127.0.0.1:8765. Una copia ZIP anterior no recibe cambios:
detén el servidor y descarga y extrae la versión actual para ver el rediseño.
Para comparar variantes:

```console
python -m codigo.interfaz.servidor --politica ID3 --puerto 8001
python -m codigo.interfaz.servidor --politica ROTACION --puerto 8002
python -m codigo.interfaz.servidor --politica PROBABILISTICO --puerto 8003
```

Para cargar otro modelo congelado utiliza `--parametros RUTA`. El predeterminado
es `docs/experimentos/modelos/SIM_CONTEXTUAL_R01.json`: primera réplica contextual
del entrenamiento sintético, sin escoger una réplica por su rendimiento.
Las selecciones manuales se registran y no actualizan α o β.

## 3. Voz

La lectura ofrece dos fuentes. Las voces del dispositivo usan Web Speech API,
filtradas a español. Google español tiene prioridad sobre las voces locales cuando
está disponible. Preferencias permite elegir otra voz, cambiar el ritmo, silenciar
la guía y escuchar una muestra. La disponibilidad de estas voces depende del navegador
y del sistema. El ZIP no instala voces ni incluye grabaciones.

La fuente opcional de OpenAI usa `gpt-audio-1.5` mediante Chat Completions con
salida de audio MP3. Se ofrecen Marin, Cedar y Coral. Para activarla en Windows:

```console
py -m codigo.interfaz.servidor --abrir --puerto 8766 --voz-openai
```

Introduce una clave de API de tu cuenta en la terminal, en la entrada oculta.
No se guarda en archivos ni se envía al navegador. También puede configurarse
`OPENAI_API_KEY` antes de iniciar el servidor; sin la variable o la entrada privada,
las opciones de OpenAI permanecen pendientes de activación y se usa el dispositivo.
Para otros sistemas sustituye `py` por `python`.
Puedes crear la clave en https://platform.openai.com/api-keys.
La API necesita conexión, acceso al modelo y saldo, y factura el uso en la cuenta.

El servidor toma el texto de la respuesta vigente o la muestra fija de Probar voz;
el navegador no puede solicitar locuciones de texto arbitrario. Las instrucciones
piden una lectura cálida en español latinoamericano. La transcripción devuelta debe
conservar las mismas palabras; se permiten diferencias de puntuación y mayúsculas.
Si cambia las palabras, se descarta el audio y se recurre al dispositivo. Esta
comprobación utiliza la transcripción del proveedor y no una auditoría independiente
del sonido generado.

Las locuciones válidas se conservan en memoria por modelo, voz y texto (hasta 128
entradas y 32 MB). Repetir reutiliza los mismos bytes mientras sigan en esa caché;
reiniciar el servidor o expulsar una entrada exige generar de nuevo. Cambiar el ritmo
modifica la reproducción, sin otra petición de generación.
Pausar, Salir, cambiar de voz o iniciar otra acción cancela la lectura y la petición
del navegador. Una respuesta tardía no comienza a sonar. Una petición que ya llegó
al proveedor puede terminar y consumir API aunque se haya cancelado su reproducción.
Recargar conserva la partida mientras exista la sesión y no reproduce audio automáticamente.
Ante un fallo de OpenAI se indica el problema y se intenta la voz española del dispositivo.

GPT-Live-1 sirve para conversaciones continuas, escuchando y hablando simultáneamente.
Esta actividad usa respuestas preparadas y una selección de pictogramas; la integración
de audio se limita a narrarlas. No solicita micrófono ni modifica el agente del curso.
La documentación oficial anuncia la retirada de los modelos TTS anteriores el
6 de enero de 2027; esta integración usa GPT-Audio-1.5, sin esa dependencia.

Documentación oficial consultada el 10 de octubre de 2026:

- [GPT-Live-1](https://developers.openai.com/api/docs/models/gpt-live-1).
- [GPT-Audio-1.5](https://developers.openai.com/api/docs/models/gpt-audio-1.5).
- [Audio en Chat Completions](https://developers.openai.com/api/docs/guides/audio-chat-completions).
- [Referencia de Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).
- [Deprecaciones](https://developers.openai.com/api/docs/deprecations).

La prueba automatizada usa API, audio y síntesis simulados. No se realizó una llamada
real a OpenAI porque este entorno no tiene una clave configurada. La naturalidad,
pronunciación y calidad audible deben probarse en el equipo del usuario.

## 4. Recursos visuales y presentación

Hay 95 imágenes: 48 animales, ocho hábitats y 39 apoyos o controles. Se utilizaron
28 PNG originales ARASAAC y 67 SVG originales. Los 20 animales con ilustración
propia incluyen rasgos específicos, como el ajolote, la rana azul o el zorro ártico.
Cada recurso conserva ruta, procedencia, licencia y SHA-256.

Los PNG genéricos representan la clase del animal; no acreditan una identificación
de subespecie. Se mantiene el nombre preciso del banco. Los SVG son esquemáticos.
La revisión técnica comprobó carga, legibilidad y correspondencia de etiquetas.
La comprensión CAA de las secuencias requiere validación posterior con usuarios.

Las tarjetas combinan imagen y nombre; los botones son grandes. Los paneles de
ayuda y los nombres de hábitats tienen texto oscuro sobre fondos claros; el catálogo
y los controles usan texto claro sobre fondos oscuros. Hay foco visible para teclado, botones nativos y un
diálogo de preferencias. En escritorio los hábitats tienen cuatro columnas; en
pantallas estrechas pasan a dos y se recorren desplazando la página.
No se elimina ninguna opción para adaptar la interfaz al móvil.

La versión 3.3 muestra una sola portada que ocupa la altura de la pantalla, sin
sección inferior ni scroll vertical. Ocho fotografías locales cambian cada 10 segundos,
con nombre y contador sincronizados. El paisaje inicial de selva se sustituyó por
una escena sin animales, coherente con los otros siete. Hay controles para avanzar,
retroceder y pausar; la navegación manual pausa el cambio automático. El carrusel
se detiene con Preferencias abierta o con la pestaña oculta. Si el dispositivo pide
movimiento reducido, empieza pausado. Este cambio decorativo no emite eventos del juego.

Los botones de modalidad usan formas redondeadas e iconos lineales. Preferencias
comparte el verde oscuro, las líneas suaves y los acentos lima. Los créditos visuales
están disponibles en Preferencias y en el pie de las pantallas del juego.
El catálogo mantiene la búsqueda por nombre sin cambiar el modelo o la partida.
El tablero conserva los ocho hábitats y los pictogramas originales sobre superficies
claras, separados de sus fondos decorativos. Las pantallas con 48 animales y los
retos pueden desplazarse verticalmente para conservar todas sus opciones.

No se usan vídeos, GIF ni canvas. Los ocho fondos y el atlas se generaron con la
herramienta integrada imagegen y se codificaron como WebP sin alterar su contenido.
Son elementos decorativos adicionales a los 95 pictogramas, sin autoridad para validar
asociaciones del banco. El mapa SVG anterior se conserva como antecedente.
Las referencias, los prompts y las rutas están en `docs/interfaz/diseno_visual.md`
y `docs/interfaz/fondos_generados.json`. La terminal y el pie del juego indican 3.3.

## 5. Estado y registros

Una cookie vincula el navegador con el gestor en memoria. Recargar conserva la
partida mientras el servidor siga activo y exista la cookie. Reiniciar el servidor
o abrir otro navegador inicia otra sesión. Los registros guardados no reconstruyen
automáticamente una partida anterior.

Cada acción lleva identificador de evento, sesión, reto y revisión de pantalla.
El adaptador serializa las acciones de una sesión. Un duplicado no ejecuta otra
acción; una entrada de una vista antigua devuelve la pantalla actual.
Consultar el estado no llama al motor ni abre otra observación.

Los registros se guardan en `registros/interfaz/`, separados por sesión, con origen
`INTERFAZ_MANUAL`. No se solicitan datos personales. Se puede cambiar la carpeta
con `--registros RUTA`. El servidor se ejecuta solo en el equipo local.

Abre http://127.0.0.1:8000/revision en el mismo navegador para inspeccionar y
descargar el JSON de la sesión. Esta página no aparece en el recorrido del jugador.
Actualizar allí solo consulta el registro.

## 6. Recorrido para la demostración

1. Abre Preferencias, selecciona un reto y prueba una voz española disponible.
2. Pulsa Yo elijo y muestra el catálogo completo de 48 animales.
3. Selecciona Capibara o ronsoco. Aparecen los ocho hábitats.
4. Pulsa Ayuda y Repetir. Se conserva la pista, secuencia y texto de voz.
5. Pulsa Pausar y Reanudar. El reto y la ayuda siguen vigentes.
6. Selecciona Desierto cálido: aparece una respuesta neutral por asociación pendiente.
7. Selecciona Selva tropical: es una asociación adicional confirmada y resuelve el reto,
   aunque el hábitat de guía de la capibara sea Agua dulce.
8. Pulsa Continuar para cerrar. Comienza otra partida con El agente elige.
9. Abre `/revision` para mostrar que el modelo permanece congelado.

## 7. Verificación realizada

Pasaron 40 pruebas de Python: 19 del núcleo, siete de aprendizaje, nueve del
adaptador web y cinco de voz. Se ejecutaron trece casos en Chromium 145.0.7632.6.

| Comprobación en navegador | Resultado |
|---|---|
| Ambos inicios, 48 animales, ocho opciones y recorrido completo | Correcto |
| Búsqueda, tildes, caso vacío y restauración sin cambiar el estado | Correcto |
| Recarga sin repetir eventos ni audio | Correcto |
| Texto exacto para voz, idioma español y cancelación | Correcto con síntesis controlada |
| Decodificación de los 95 PNG/SVG y los nueve WebP decorativos | Correcto |
| Móvil 390 × 844: inicio, preferencias y partida | Correcto |
| Teclado, barra de progreso y movimiento reducido | Correcto |
| Inicio en una pantalla: 320 × 568, 390 × 844, 650 × 390, 844 × 390, 768 × 900, 1024 × 600, 1024 × 768, 1280 × 720 y 1920 × 1080 | Correcto |
| Carrusel de ocho fondos: contador, pausa, navegación y Preferencias | Correcto |
| Prioridad de Google español sobre voces locales | Correcto |
| Audio OpenAI: reproducción, ritmo, cancelación tardía y respaldo | Correcto con servicio y reproductor simulados |
| Ausencia de voz española: aviso y juego operativo | Correcto |
| Revisión técnica separada y modelo congelado | Correcto |

La prueba de voz intercepta el sintetizador y simula el proveedor y el reproductor;
no verifica sonido audible ni comprensión en otro dispositivo. La inspección
de las capturas no constituye una certificación de accesibilidad.

Evidencias: `docs/interfaz/revision_navegador.json` y ocho capturas de inicio,
catálogo, reto de escritorio, revisión de animales, reto móvil, inicio móvil y
preferencias en móvil, incluido un inicio panorámico a 1920 px de ancho.
También se comprobó el inicio del servidor, una sesión HTTP y su cierre con Ctrl+C.

```console
python -m unittest discover -s tests -v
```

La prueba de navegador es opcional y requiere Node, Playwright y Chromium.
No son dependencias necesarias para jugar. Para preparar y ejecutar esa prueba:

```console
npm install --no-save playwright
npx playwright install chromium
python -m tests.ejecutar_navegador
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
| `codigo/interfaz/voz.py` | Voz OpenAI opcional, lectura verificada y caché. |
| `codigo/interfaz/web/paisajes.webp` | Atlas estático de los ocho paisajes decorativos. |
| `codigo/interfaz/crear_svg.py` | Fuente editable de las ilustraciones propias. |
| `codigo/interfaz/preparar_recursos.py` | Regeneración de recursos; innecesaria para jugar. |
| `assets/pictogramas/` | 28 PNG y 67 SVG listos para presentar. |
| `datos/pictogramas.json` | IDs simbólicos, imágenes y créditos. |
| `datos/fuentes_pictogramas.json` | Metadatos y descargas ARASAAC usadas. |
| `tests/test_voz.py` | Límites HTTP, fidelidad, caché y fallos de voz sin API real. |
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
como secuencias de pictogramas con texto de apoyo y síntesis de voz española.
Se permite pedir ayuda, repetir el contenido, pausar, reanudar y continuar,
sin puntos competitivos ni límites de tiempo o intentos.

El adaptador web transmite eventos identificados por sesión, reto y revisión,
evitando duplicados y acciones de pantallas anteriores. El gestor conserva la
autoridad sobre las transiciones, las asociaciones confirmadas y el progreso.
El modelo probabilístico se carga congelado y registra las interacciones manuales
sin actualizar sus parámetros. La revisión técnica se realiza en una página aparte.

Se incorporaron 95 recursos visuales con rutas, créditos y huellas de integridad.
Las pruebas de Python y los recorridos en navegador verificaron el funcionamiento,
incluidos repetición, pausa, respuesta neutral y vista móvil. La voz depende de
las voces españolas del dispositivo o de una configuración opcional de OpenAI.
Se probó con un sintetizador, un proveedor y un reproductor controlados; no se
verificó la calidad audible de una voz real de OpenAI.
La comprensión CAA y la eficacia pedagógica requieren evaluación con usuarios;
los experimentos de aprendizaje siguen siendo exclusivamente sintéticos.
