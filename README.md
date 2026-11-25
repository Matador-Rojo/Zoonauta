# Zoonauta

Juego educativo de animales y hábitats con pictogramas CAA y una guía de inteligencia artificial.
Disponible en **español (`es-419`)**, **portugués brasileño (`pt-BR`)** e **inglés (`en`)**, con
**8 voces grabadas completas** (ElevenLabs, 412 mensajes por voz) para jugar sin Internet ni APIs externas.

![Portada de Zoonauta](docs/interfaz/portada_zoonauta.webp)

Zoonauta reúne **288 animales**, **48 hábitats**, pistas adaptativas guiadas por un agente local,
**Mi álbum de expedición** persistente, tres temas visuales accesibles y soporte completo como
**PWA** y servidor **WSGI** para despliegue web.

## Cómo se juega

La portada «Bosque de luz» resume el juego en una frase: *Elige un animal. Sigue las pistas y
descubre dónde vive.* Pulsa **Comenzar** y escoge **Yo elijo** o **El agente elige**. La guía lee
«¿Quién elige el animal?» al abrir ese selector.

- **Yo elijo:** explora los **288 animales** en páginas de 6 con orden híbrido:
  - En **Todas** y **Por descubrir**, el catálogo usa un orden aleatorio variado por biomas
    (garantizando 6 hábitats distintos por página y renovándose en cada partida).
  - En los filtros alfabéticos (`A–C` a `Q–Z`) y en el buscador por nombre, ordena de la `A` a la `Z`.
  - Los animales ya resueltos muestran su sello `✓` y el filtro **Por descubrir** muestra cuántos faltan.
- **El agente elige:** prioriza automáticamente los animales que aún no has descubierto en tu álbum;
  al completar los 288, vuelve a mezclar todo el catálogo de forma continua y sin bloqueos. Puedes elegir
  entre **1 y 48 retos** por partida (8 por defecto).

Cada reto presenta el animal a la izquierda con **Pista**, **Repetir**, **Pausar** y **Salir** debajo;
a la derecha, la guía con su frase y sus pictogramas CAA, y los hábitats para elegir (**2, 4 u 8** según
Preferencias). Si transcurren unos segundos sin acción, el botón **Pista** ofrece una invitación visual sutil.
Al pedir **Pista** o elegir un hábitat no confirmado, el **agente de la guía** selecciona la ayuda que mejor
distingue las opciones visibles, sin penalizaciones ni límite de tiempo (ver [El agente adaptativo](#el-agente-adaptativo)).
Al acertar, el hábitat se marca con `✓`, se guarda el sello en **Mi álbum** y **Continuar** pasa al siguiente reto.
No hay puntos, reloj ni límite de intentos.

Las opciones de hábitat priorizan la claridad cognitiva para niños y personas con discapacidad intelectual:
incluyen siempre el hábitat principal y los secundarios documentados, y completan el panel con hábitats
claramente distintos entre sí. Cualquier hábitat secundario documentado también resuelve el reto.

### Mi álbum de expedición

Cada usuario dispone de su propio álbum guardado localmente en su navegador (`localStorage`), de modo que
cada persona empieza en cero y conserva su progreso de forma independiente:

- **Dos series de 5 estrellas:**
  - *Estrellas de animales:* `1`, `20`, `80`, `160` y `288` animales descubiertos.
  - *Estrellas de hábitats:* `1`, `5`, `15`, `30` y `48` hábitats explorados.
- **Rejilla paginada 3 × 3** (9 hallazgos por página con navegación `←` / `→`) con traducción automática
  de nombres al cambiar de idioma.
- Botón discreto **Reiniciar álbum** en dos pasos para comenzar una colección desde cero cuando se desee.

### Pantalla completa, identidad visual y accesibilidad

Cada pantalla se adapta a escritorio (`1440 × 900`), portátil (`1280 × 720`) y móvil (`390 × 844` y `320 px`)
sin desplazamiento innecesario. La interfaz incluye **tres temas visuales** en tiempo real con un
**logotipo vectorial adaptativo** (zorro y estrella):

- **Bosque de noche** *(predeterminado)*: observatorio bioluminiscente con acento cian/turquesa, tipografía
  editorial serif (`Fraunces Variable`) y lectura accesible (`Atkinson Hyperlegible Next`), ambas locales.
- **Bosque de día:** tema claro editorial cálido con acento verde selva y portada diurna.
- **Alto contraste (WCAG AAA 21:1):** negro puro (`#000000`) y blanco puro (`#ffffff`) con relieve sólido
  nítido, logotipo monocromo blanco y cero efectos decorativos distractores.

Cada tema cuenta con su **portada animada 2K** (`assets/portada/*.mp4`) y versión estática de alta nitidez
cuando está activo **Reducir movimiento**. Además, el juego incluye manifiesto y *service worker* para
instalarlo como **PWA** (*Instalar app* en Preferencias).

## Preferencias, idiomas y voces

**Preferencias** («Tu expedición · A tu manera.») se abre sobre cualquier pantalla y también puede protegerse
con pulsación prolongada (**Proteger Preferencias**):

- **Idioma:** **Español**, **Português (Brasil)** o **English**. Traduce en vivo interfaz, botones,
  los 288 animales, los 48 hábitats, etiquetas CAA, pistas, confirmaciones y el álbum.
- **La partida:** cantidad de retos (`1` a `48`) y hábitats por reto (`2`, `4` u `8`).
- **Voz:** *Una guía con voz*, selector de narrador según idioma, ritmo de lectura (*Despacio*, *Natural*,
  *Más ágil*) y **Probar voz**:
  - **Español (`es-419`):** Marcela, Valeria, Gaby y Diego *(4 voces × 412 audios)*
  - **Português (`pt-BR`):** Roberta y Will *(2 voces × 412 audios)*
  - **English (`en`):** Mark y Jessica *(2 voces × 412 audios)*
- **Sonidos del bosque:** paisaje suave durante el juego, celebración acústica reactiva al bioma
  (5 familias sonoras: mar, agua dulce, bosque, montaña y sabana), música serena en pausa, fanfarria de
  victoria y háptica suave en dispositivos compatibles. Se atenúan automáticamente mientras habla la guía.
- **Pantalla:** *Aspecto visual* (*Bosque de noche*, *Bosque de día*, *Alto contraste*), **Tamaño de texto**
  (*Pequeño*, *Normal*, *Grande*) y *Reducir movimiento*.

Las **8 voces** (`3 296` audios en total) cubren el 100 % de los mensajes del juego sin unir fragmentos y
funcionan sin Internet. El servidor soporta nativamente **AAC (`.m4a` / `audio/mp4`)** —usado a 32 kbps mono
en el paquete web liviano— así como **MP3** y **WAV**.

## Estructura del proyecto

- **`codigo/motores/` y `codigo/entrenamiento/`** *(modelos de IA)*: baseline `ID3` (`id3.py`), agente adaptativo (`agente.py`), selector probabilístico Beta-Bernoulli (`aprendizaje6.py`, `bayes.py`), simulador, entrenamiento y evaluación reproducible.
- **`codigo/nucleo/`, `codigo/respuestas/` y `codigo/interfaz/`** *(backend)*: espacio de estados y gestor de reglas (`estado.py`, `gestor.py`), generador CAA, servidor HTTP con soporte `206 Partial Content` para video, adaptador **WSGI** (`wsgi.py`) sin dependencias externas y panel `/revision`.
- **`frontend/`** *(frontend)*: aplicación React 19 + TypeScript + Vite compilada en `codigo/interfaz/web6/`.
- **`datos/` y `assets/`**: catálogo validado (288 animales, 48 hábitats, rasgos, pistas, traducciones `pt-BR` y `en`, manifiesto SHA-256), ilustraciones, pictogramas, grabaciones de voz y portadas 2K.
- **`docs/` y `tests/`**: documentación técnica, experimentos reproducibles y pruebas automatizadas.

Documentación de referencia: [manual de usuario](docs/manual_usuario.md),
[contrato de identidad visual](docs/interfaz/6.0/identidad.md),
[accesibilidad y rendimiento](docs/interfaz/6.0/accesibilidad_rendimiento.md) y
[cierre técnico](docs/cierre_tecnico_hito3.md).

## Ejecutar el juego

### En equipo local (Windows / Linux / macOS)

Requiere únicamente **Python 3.10 o posterior** (sin dependencias externas para ejecutar el servidor):

- **Windows:** abre `iniciar_juego.bat` o ejecuta:
  ```console
  py -3 -m codigo.interfaz.iniciar
  ```
- **Linux / macOS:** ejecuta `bash iniciar_juego.sh` o:
  ```console
  python3 -m codigo.interfaz.iniciar
  ```

El iniciador abre `http://127.0.0.1:8766` y la revisión técnica está disponible en `/revision`.
Para indicar otro puerto:

```console
py -3 -m codigo.interfaz.servidor --puerto 8080
```

### Despliegue web (Hostinger / WSGI / Docker)

- **Paquete web (`Zoonauta-Web.zip`, ~71 MB):** incluye la app compilada, imágenes ligeras optimizadas
  y las 8 voces completas en **AAC 32 kbps (`.m4a`)**, listo para subir a un servidor web Python.
- **WSGI (`codigo.interfaz.wsgi:application`):** compatible con Gunicorn, Passenger/Hostinger y PythonAnywhere
  sin dependencias adicionales.
- **Docker:** `Dockerfile` y `docker-compose.yml` incluidos en la raíz del proyecto.

## Inteligencia artificial y revisión

### El agente adaptativo

En la partida principal (288 animales, 48 hábitats) un agente local decide qué pista ofrecer en cada turno
sin usar Internet ni APIs externas. Evalúa el animal, los hábitats visibles, las selecciones previas,
las ayudas ya mostradas y las repeticiones. Combina las 3 pistas progresivas por hábitat con 32 ayudas breves
por rasgo, afirmando únicamente rasgos documentados y evitando repetir características compartidas con un
hábitat ya intentado.

También están disponibles `--agente AGENTE_APRENDIDO` (modelo Beta-Bernoulli entrenado fuera de línea y
congelado), `--agente ID3_OPCIONES` (ganancia de información sobre las opciones visibles) y
`--agente PISTAS_PROGRESIVAS` (secuencia fija nivel 1 → 2 → 3). El detalle técnico y las evaluaciones
se encuentran en [docs/agente/agente_6.md](docs/agente/agente_6.md).

### Catálogo experimental (48 animales, 8 hábitats)

Con `--catalogo-original` la interfaz conserva el banco experimental original y las políticas `PROBABILISTICO`,
`ID3` y `ROTACION` para reproducir los experimentos de evaluación.

### Comandos útiles y pruebas

```console
python -m unittest discover -s tests -v
python -m unittest tests.test_voz_grabada_cobertura tests.test_interfaz tests.test_idiomas_voz tests.test_catalogo_voz
python -m codigo.nucleo.verificar_paquete
python -m codigo.nucleo.auditoria --salida resultados_nuevos/auditoria.json
python -m codigo.poc.aceptacion
npm --prefix frontend run check
npm --prefix frontend run build
```

**Verificación:** pruebas unitarias Python (incluyendo cobertura completa de las 8 voces en `es`,
`pt-BR` y `en` recorriendo los 288 animales), **8 pruebas Vitest** (TypeScript + ESLint + Prettier),
pruebas de navegador Playwright con `axe-core`, verificación de integridad SHA-256 (`verificar_paquete`)
y smoke test del paquete web descomprimido con audios `audio/mp4` en los tres idiomas.

## Créditos e imágenes

Las ilustraciones de animales, pictogramas de apoyo y paisajes son recursos originales generados con IA
documentados en `datos/imagenes_*_ia.json` y se ofrecen bajo licencia **CC BY-NC-SA 4.0**. Los créditos
históricos de ARASAAC y del prototipo inicial se conservan en [docs/creditos_pictogramas.md](docs/creditos_pictogramas.md).
