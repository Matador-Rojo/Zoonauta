# Zoonauta: interfaz digital con pictogramas y voz

Versión 3.2.0.

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

Se usan `speechSynthesis` y `SpeechSynthesisUtterance` para leer el `texto_voz`
de la respuesta realmente emitida. Se filtran las voces disponibles a español y
se escucha `voiceschanged` cuando el dispositivo las carga después. Preferencias
permite elegir voz, velocidad, desactivar la lectura o probarla.

Repetir lee exactamente el texto educativo vigente. Pausar o Salir cancela la voz.
Recargar consulta la sesión y no vuelve a emitir una acción ni a leer una respuesta antigua.

La voz depende del navegador, del sistema y de las voces españolas instaladas.
Si falta una voz española o falla la síntesis, aparece un aviso. Texto y pictogramas
siguen disponibles. El ZIP no contiene voces instalables ni audio grabado. Algunos
servicios de voz pueden requerir conexión; el juego y las imágenes funcionan localmente.

Referencias técnicas consultadas el 9 de octubre de 2026:
[MDN, getVoices](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis/getVoices)
y [SpeechSynthesisUtterance](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisUtterance).

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

La versión 3.2 usa una escena de selva a todo el ancho del inicio, tipografía amplia
y una composición oscura con acentos lima. Una galería muestra los ocho paisajes
que aparecen también como fondos en las opciones de hábitat. Los pictogramas
originales siguen presentes sobre superficies claras y separados de las imágenes
decorativas. El tablero distingue el animal, la guía y la elección del hábitat.
La búsqueda del catálogo solo filtra la pantalla:
no emite eventos, cambia el modelo ni modifica el estado de la partida. Limpiar el
campo restaura los 48 animales. Hay un enlace para saltar directamente al juego.
No se usan vídeos, GIF, canvas ni animaciones automáticas. La portada y el atlas
de paisajes se generaron con la herramienta integrada imagegen y se codificaron
como WebP sin cambiar el contenido. Son composiciones decorativas, adicionales
a los 95 pictogramas. No se usan para validar las asociaciones del banco de datos.
El mapa SVG de la versión anterior se conserva como antecedente.
Las referencias, los prompts y las rutas están en `docs/interfaz/diseno_visual.md`.
El pie de página y la terminal indican 3.2 para distinguir la copia ejecutada.

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

Pasaron 35 pruebas de Python: 19 del núcleo, siete de aprendizaje y nueve del
adaptador web. Se ejecutaron diez casos en Chromium 145.0.7632.6.

| Comprobación en navegador | Resultado |
|---|---|
| Ambos inicios, 48 animales, ocho opciones y recorrido completo | Correcto |
| Búsqueda, tildes, caso vacío y restauración sin cambiar el estado | Correcto |
| Recarga sin repetir eventos ni audio | Correcto |
| Texto exacto para voz, idioma español y cancelación | Correcto con síntesis controlada |
| Decodificación de los 95 PNG/SVG y los dos WebP decorativos | Correcto |
| Móvil 390 × 844: inicio, preferencias y partida | Correcto |
| Teclado, barra de progreso y movimiento reducido | Correcto |
| Inicio y partida entre 320 y 1280 px sin desbordamiento horizontal | Correcto |
| Ausencia de voz española: aviso y juego operativo | Correcto |
| Revisión técnica separada y modelo congelado | Correcto |

La prueba de voz intercepta el sintetizador para comprobar qué se reproduce;
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
| `codigo/interfaz/web/portada-selva.webp` | Escena decorativa de portada de la versión 3.2. |
| `codigo/interfaz/web/paisajes.webp` | Atlas estático de los ocho paisajes decorativos. |
| `codigo/interfaz/crear_svg.py` | Fuente editable de las ilustraciones propias. |
| `codigo/interfaz/preparar_recursos.py` | Regeneración de recursos; innecesaria para jugar. |
| `assets/pictogramas/` | 28 PNG y 67 SVG listos para presentar. |
| `datos/pictogramas.json` | IDs simbólicos, imágenes y créditos. |
| `datos/fuentes_pictogramas.json` | Metadatos y descargas ARASAAC usadas. |
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
las voces españolas del dispositivo y se probó con un sintetizador controlado.
La comprensión CAA y la eficacia pedagógica requieren evaluación con usuarios;
los experimentos de aprendizaje siguen siendo exclusivamente sintéticos.
