# Zoonauta

Juego de animales y hábitats con pictogramas y guía de inteligencia artificial.

Versión 3.4.0. Español y portugués brasileño. Voces locales Piper y Kokoro,
más voces Microsoft y Google disponibles en el navegador.

![Inicio con paisajes de Zoonauta](docs/interfaz/01_inicio.png)

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

Abre **Preferencias → Idioma** para elegir Español o Português (Brasil). Cambian
los controles, los 48 nombres de animales, los ocho hábitats, las etiquetas de
pictogramas, las pistas, las confirmaciones y las voces. Puedes cambiar durante
una partida conservando su estado y progreso. El selector conserva siete opciones
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

El inicio ocupa una sola pantalla, sin desplazamiento vertical. Sus ocho fotografías
cambian cada 10 segundos; el nombre y el contador acompañan a cada fondo. Puedes
pausar con el botón central; play o cualquiera de las flechas reanuda el cambio y
reinicia los 10 segundos. El carrusel empieza en marcha. Preferencias y la pestaña
inactiva suspenden temporalmente el cambio; movimiento reducido elimina las animaciones.
La selva es ahora un paisaje sin el guacamayo y comparte el estilo de los otros siete.
La portada tiene un único botón Comenzar; después se elige Yo elijo o El agente elige
en un diálogo con pictogramas. Ambos diálogos usan la misma paleta oscura con acentos lima.
Puedes ver la [portada con Comenzar](docs/interfaz/revisiones/2026-10-10-inicio/inicio.webp)
y la [elección de modalidad](docs/interfaz/revisiones/2026-10-10-inicio/selector.webp).
El catálogo muestra el pictograma original de cada animal junto a su recorte fotorrealista
generado con IA y sin fondo, en ocho páginas de seis animales. Permite buscar en todo el catálogo, incluso sin tildes.
Las preguntas y pistas conservan los pictogramas originales del catálogo educativo;
los recortes fotorrealistas se usan en tarjetas, retratos y cierres. Los ocho hábitats
presentan pictogramas grandes y centrados, con los paisajes como apoyo de fondo.
Una selección sin asociación confirmada recibe un mensaje amable y una pista nueva
automáticamente, sin castigo. Repetir conserva esa pista. Los controles muestran los
pictogramas originales y las pantallas de pausa y cierre incluyen sus secuencias.
Las preguntas y pistas usan símbolos de 84–96 px; los hábitats, de 96–112 px.
El cierre presenta el progreso real y permite comenzar otra partida.
El progreso indica retos completados. Se adapta a móvil y admite
selección con teclado. No necesita vídeos, GIF ni recursos visuales externos.
Puedes ver la [pista automática](docs/interfaz/revisiones/2026-10-10-apoyos/pista.webp),
el [catálogo](docs/interfaz/revisiones/2026-10-10-apoyos/catalogo.webp) y
el [cierre](docs/interfaz/revisiones/2026-10-10-apoyos/cierre.webp).
Los archivos y prompts de los animales están en
[imagenes_animales_ia.json](datos/imagenes_animales_ia.json). Son imágenes sintéticas,
no fotografías de ejemplares reales. Los 95 pictogramas originales se conservan con sus créditos.

La interfaz carga el modelo sintético contextual R01, congelado, elegido por su
posición como primera réplica y no por su rendimiento. Para revisar los registros
de la sesión abre http://127.0.0.1:8766/revision en el mismo navegador.

Otros comandos desde esta carpeta, que contiene codigo, datos, docs, assets y tests:

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 2
python -m codigo.interfaz.servidor --politica ID3 --puerto 8001
python -m codigo.interfaz.servidor --politica ROTACION --puerto 8002
python -m codigo.poc.consola --modalidad AGENTE --retos 2
python -m codigo.entrenamiento.experimento --salida resultados_nuevos
python -m codigo.poc.aceptacion
python -m unittest discover -s tests -v
```

El núcleo conserva 48 animales, ocho opciones por reto y ambas modalidades.
No hay puntos competitivos ni límite de tiempo o intentos. ID3 construye el árbol
calculando ganancias. Se ejecutó aprendizaje probabilístico con interacciones
sintéticas y evaluación separada: 34 560 retos de entrenamiento, 51 840 de
evaluación. La revisión actual de accesibilidad está en
`docs/interfaz/revisiones/2026-10-10-apoyos/`: 68 pruebas Python, ocho casos de
aceptación del protocolo de consola y 21 casos de navegador, con voces controladas.
Las evidencias de síntesis real permanecen en `docs/interfaz/revision_voces_locales.json`.

La consola utiliza los priors originales salvo que indiques un modelo con
--parametros; conserva sus parámetros congelados durante la sesión.
La interfaz activa la ayuda automática ante selecciones pendientes; consola y
simulador conservan su protocolo de ayuda explícita para reproducir los experimentos anteriores.
El simulador y el informe no requieren paquetes externos. Volver a exportar
el PNG mediante --grafico requiere matplotlib; el gráfico ya está incluido.

Esta versión contiene el código, los datos, los modelos, la interfaz y sus imágenes.
Se comprobó síntesis real de las 14 opciones con WAV PCM no silencioso y
repetición idéntica desde caché. Esa prueba no certifica pronunciación ni sonido
audible en otros dispositivos. La comprensión CAA de las secuencias requiere validación
con usuarios. Los documentos V1/V2 son antecedentes; esta guía y la de interfaz
describen el estado actual. Los experimentos conservan su procedencia sintética.

Créditos: 28 PNG ARASAAC sin modificación, Sergio Palao, Gobierno de Aragón,
CC BY-NC-SA; 67 SVG originales del prototipo, CC BY-NC-SA 4.0.
Consulta `docs/creditos_pictogramas.md` y `datos/fuentes_pictogramas.json`.
La portada y los ocho paisajes son imágenes decorativas generadas con IA,
incluidas en nueve archivos WebP: ocho fondos de inicio y un atlas para el tablero. No forman parte de los 95 pictogramas educativos.
Las referencias visuales, los prompts y las rutas están en
`docs/interfaz/diseno_visual.md`. El mapa SVG anterior se conserva como antecedente.
