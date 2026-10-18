# Zoonauta: interfaz digital con pictogramas y voz

Versión 4.4.0.

## 1. Qué está implementado

La interfaz convierte clics o toques en eventos del mismo `GestorPartida` utilizado
por la consola y el simulador. El navegador presenta las respuestas preparadas por
el generador; la evaluación de asociaciones y la selección de ayudas las hace el núcleo.

| Elemento | Comportamiento disponible |
|---|---|
| Portada | Un único botón principal Comenzar abre la elección de modalidad. Volver al inicio o Escape cierran esa elección sin iniciar la partida. |
| Inicio del jugador | Muestra seis animales por página; ocho páginas permiten elegir cualquiera de los 48. |
| Inicio del agente | Mezcla los 48 animales al preparar cada partida, sin repeticiones; el primer animal cambia al comenzar otra partida. |
| Búsqueda | Filtra los 48 animales por nombre, sin distinguir mayúsculas o tildes. |
| Páginas | Anteriores y Siguientes recorren los resultados sin modificar el reto ni el progreso. Buscar vuelve a la primera página; pausar y reanudar conservan la página. |
| Pictogramas educativos | Preguntas, pistas, tarjetas y retratos usan las mismas caricaturas originales transparentes. Los apoyos siguen el estilo de la capibara aprobada; los hábitats tienen paisaje, nombre y número 01–08. |
| Reto | Muestra el animal, la pregunta o pista y 2, 4 u 8 hábitats según Preferencias. |
| Progreso | Indica retos completados mediante texto y una barra accesible. |
| Pista | Solicita una nueva pista. El modelo probabilístico considera la elección y las ayudas anteriores; ID3 y rotación conservan la secuencia base. |
| Repetir | Recupera la misma respuesta educativa, su secuencia y su texto de voz. |
| Pausar y reanudar | Suspende la interacción, detiene la voz y conserva el reto. |
| Selección confirmada | Acepta cualquiera de los hábitats confirmados del animal. |
| Selección pendiente | Da una respuesta neutral con una nueva pista automática, sin penalización; conserva el reto y permite repetir esa pista. |
| Continuar | Abre otro reto o presenta el cierre cuando se completó N. |
| Preferencias | Disponible solo en la portada: permite N entre 1 y 48, 2/4/8 hábitats antes del inicio, idioma, voz y velocidad. |
| Avisos | Tarjetas de hasta 260 px con fondo oscuro y borde por tipo. Hasta tres visibles, menos si falta altura; las nuevas se añaden abajo y se retiran las más antiguas, sin scroll ni recortes. Cada una dura ocho segundos y tiene una × circular sobre la esquina, accesible por teclado. Comenzar valida un entero del 1 al 48 antes de abrir modalidad. |
| Revisión técnica | Página aparte con modelo, estado, decisiones y exportación JSON. |

Las opciones elegidas al preparar el reto permanecen estables en los retos activos. Tras resolver se ven desactivados
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

Preferencias, en la portada antes de comenzar, permite elegir español o portugués brasileño. Se traducen los
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

El banco activo tiene 95 WebP transparentes: 48 animales, ocho símbolos de hábitat
y 39 apoyos o controles. Se usa una sola caricatura por animal en todas las pantallas.
Los 33 apoyos renovados de comunicación siguen el mismo estilo de la capibara
aprobada, con contornos definidos, colores naturales y sombreado suave.
Explorar utiliza un mapa con brújula y Buscar una lupa: sus imágenes son diferentes.
Se mantienen los identificadores y las secuencias de preguntas y pistas del núcleo.
Cada recurso conserva procedencia, prompt, transparencia y SHA-256 en los archivos
`datos/imagenes_*_ia.json`. La comprensión CAA requiere evaluación con usuarios.

En el tablero, las preguntas y pistas usan imágenes de 84–140 px según el espacio,
con etiquetas de 14 px; los controles mantienen imágenes de 56 px y texto de 17 px.
Las imágenes no llevan recuadros blancos. Iniciar y Salir
también conservan transparencia en el cierre y en los botones.
Hay foco visible para teclado, botones nativos y un diálogo de preferencias.

Las tarjetas de hábitat presentan ocho paisajes realistas propios, con el elemento
principal centrado, nombre y número 01–08 arriba a la derecha. En escritorio ocupan
la columna derecha, debajo de la guía y con su mismo ancho: cuatro columnas y dos
filas de tarjetas que se ajustan a la altura disponible. El tablero utiliza el
ancho completo, con márgenes laterales de 20–48 px, y un fondo continuo hasta el
borde inferior. El animal ocupa un área de imagen de al menos 200 × 180 px en las
resoluciones de escritorio probadas, conserva sus proporciones y muestra su nombre
debajo con texto de 24–30 px. Pista, Repetir, Pausar y Salir quedan debajo en una
cuadrícula de dos columnas. La cabecera, el logo y Preferencias se muestran
solo en inicio; el pie se oculta durante el juego.
Los símbolos de hábitat se usan en las secuencias educativas, sin superponerse a
las fotografías sintéticas de las tarjetas. No se elimina ninguna opción en móvil.

La portada conserva los ocho fondos locales, el logo y su composición. Cambia cada
diez segundos; la pausa se activa solo mediante el botón. Play o las flechas reanudan
y reinician el intervalo. Preferencias y una pestaña inactiva suspenden el carrusel;
movimiento reducido elimina las animaciones. Comenzar abre el diálogo de modalidad.
La portada no requiere desplazamiento vertical. El tablero de escritorio se
verificó sin scroll en 1024 × 768, 1280 × 720, 1366 × 768, 1440 × 900, 1920 × 988 y 1920 × 1080,
incluidas las pistas más largas. En móvil y pantallas estrechas, el contenido se
apila y puede desplazarse; se conservan los ocho hábitats y todos los controles.
Una ventana de menos de 660 px de alto permite desplazamiento para conservar el
animal, su nombre y las opciones completos, también al aumentar el zoom.
El catálogo conserva su paginación y puede desplazarse.
La pausa conserva el animal y el orden del reto, y muestra al robot guía sentado
en un banco. En el cierre, el robot se despide con su cuaderno; no se muestra el
último animal. Ambas imágenes son WebP transparentes locales, independientes del
banco de 95 pictogramas. El progreso real se muestra mediante texto y barra accesible.
Comenzar otra partida vuelve a la portada en silencio. La pregunta «¿Quién
elige el animal?» solo se lee al abrir la elección de modalidad, en el idioma
seleccionado; cerrar ese diálogo cancela la lectura.

No se usan vídeos, GIF ni recursos externos para mostrar imágenes.
Los paisajes se generan con IA y son decorativos; no validan asociaciones del banco.
Los créditos y metadatos de ARASAAC y los SVG anteriores son históricos.
La captura de portada actual está en `docs/interfaz/3.8/inicio.webp`.
Créditos visuales en Preferencias muestra Zoonauta 4.4. La terminal identifica la versión 4.4.0. El pie no ocupa espacio durante la partida.

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
4. Pulsa Pista y Repetir. Se conserva la pista, secuencia y texto de voz.
5. Pulsa Pausar y Reanudar. El reto y la ayuda siguen vigentes.
6. Selecciona Desierto cálido: aparece una respuesta neutral y la siguiente pista
   automáticamente. Pulsa Repetir para escuchar el mismo contenido.
7. Selecciona Selva tropical: es una asociación adicional confirmada y resuelve el reto,
   aunque el hábitat de guía de la capibara sea Agua dulce.
8. Pulsa Continuar para cerrar. Comienza otra partida con Comenzar y después El agente elige.
9. Abre `/revision` para mostrar que el modelo permanece congelado.

## 7. Verificación realizada

La versión 4.4 pasó 72 pruebas Python, 20 recorridos de interfaz y cinco casos
de voces Microsoft/Google controladas en Chrome. También pasaron los ocho casos
de aceptación de consola. Se recorrieron dos partidas de 48 animales sin repetir
y se comprobó que una nueva partida cambia el primero, mientras pausar conserva
el orden. Los 95 recursos activos se verificaron como WebP con alpha real;
los nuevos apoyos se revisaron sobre superficies claras y oscuras.
Las secuencias y controles, incluido Iniciar, se muestran sin fondos ni bordes.
La revisión actual está en `docs/interfaz/4.4/revision.json`. La captura de
portada conservada en `docs/interfaz/3.8/inicio.webp` sigue representando el inicio.
Las evidencias de síntesis real de las 14 voces pertenecen a revisiones anteriores
y no se repitieron para este cambio visual y de selección.

| Comprobación | Resultado |
|---|---|
| Ambas modalidades, 48 animales, ocho opciones, repetición, pausa y cierre | Correcto |
| Traducción de mensajes, 72 pistas y contextos de las 69 asociaciones confirmadas | Correcto |
| Cambio de idioma sin modificar estado, observaciones, registros o modelo | Correcto |
| Búsqueda de nombres en ambos idiomas, sin distinguir tildes o mayúsculas | Correcto |
| Recarga sin repetir acciones o audio, idioma de sesión conservado | Correcto |
| 14 opciones locales, muestras, elección por idioma, ritmo y silencio | Correcto con API y reproductor controlados |
| Modelos ausentes, idiomas inválidos y descarte de audio obsoleto | Correcto |
| 95 pictogramas, nueve paisajes de portada y ocho paisajes de tarjetas decodificados | Correcto |
| Móvil, teclado, progreso accesible y movimiento reducido | Correcto |
| Inicio español y portugués, de 320 × 568 a 1920 × 1080, sin scroll vertical | Correcto |
| Ocho fondos: contador, cambio cada 10 segundos, pausa y Preferencias | Correcto |
| Encabezados de revisión técnica localizados, registros originales conservados | Correcto |
| Síntesis real de las 14 opciones: WAV mono PCM no silencioso, repetición en caché | Correcto en revisión anterior |
| Audio real de Piper español y Kokoro portugués: WAV, decodificación y avance de reproducción nativa | Correcto en revisión anterior |
| Preparación aislada y resolución de paquetes para Windows x64/Python 3.12 | Revisión anterior: preparación en Linux y disponibilidad de ruedas Windows |

Evidencia anterior y capturas: `interfaz/revisiones/2026-10-10-apoyos/`.
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
| `codigo/interfaz/crear_svg.py` | Generador SVG histórico del prototipo. |
| `codigo/interfaz/preparar_recursos.py` | Preparación histórica del prototipo; innecesaria para jugar. |
| `assets/pictogramas/` | Símbolos, apoyos y controles actuales en WebP transparente. |
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

## Historial del reto y evaluación del agente

En la política probabilística, la primera selección pendiente orienta una pista hacia
un atributo que distinga esa elección del hábitat guía. Tras dos selecciones
pendientes se presenta una opción explícita. Repetir conserva el contenido; una
nueva petición después de repetir puede ofrecer otra formulación antes de avanzar.
Se priorizan variantes no vistas en ese nivel del reto y se conserva el historial
al pausar o recargar. El historial se limpia al continuar a otro reto.

El panel reducido incluye el hábitat guía y una alternativa pendiente. El núcleo
rechaza selecciones de tarjetas no visibles. Cambiar la cantidad solo se permite
al iniciar una partida; el educador decide el apoyo, sin reducir opciones automáticamente.

`python -m codigo.entrenamiento.evaluar_demo --salida resultados_nuevos/demo`
entrena con semillas separadas y compara las tres políticas en los tres tamaños.
Los resultados son sintéticos; las curvas de evolución y su cobertura no prueban
convergencia general ni comprensión humana. `python -m codigo.nucleo.auditoria`
comprueba referencias y coherencia de las secuencias sin cambiar relaciones pendientes.
