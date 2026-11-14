# Zoonauta — instrucciones para Claude Code

Juego educativo sobre animales y hábitats (curso de IA, UPC 2026-2) para personas que
pueden necesitar apoyos visuales, pictográficos y auditivos. Base estable: Zoonauta
5.0.0 (`main`, 1a0b3a5). Trabajo actual: modernización 6.0 en la rama
`experimental/zoonauta-v6-modern-web`. Responder al propietario en español.

## Reglas permanentes

- Commits pequeños por función en la rama experimental. Sin `reset --hard`, `clean -fd`
  ni reescritura de historial. Pedir autorización antes de push, merge a `main` o
  cualquier despliegue público.
- No tocar la carpeta de origen `C:\Users\adria\Downloads\Zoonauta` (sin `.git`).
- Conservar sin reemplazar: pictogramas, ilustraciones de animales, logo, créditos e
  imágenes del robot (pausa y cierre). No generar un robot nuevo ni fotos de animales.
- Conservar IDs, referencias, nombres científicos, traducciones, procedencia y las
  asociaciones educativas (288 animales, 48 hábitats, 144 pistas, 31 asociaciones
  secundarias). Las asociaciones biológicas solo cambian con fuente y revisión humana.
  No dar por correcto contenido educativo generado por IA.
- No inventar funciones (menús, cuentas, logros, modos). Conservar Yo elijo / El agente
  elige, búsqueda y paginación del catálogo, 2/4/8 opciones, Pista, Repetir, Pausar,
  Reanudar y Salir. El servidor Python es la autoridad de reglas y progreso.
- Sin 3D, dioramas, WebGL de escenarios, zoom continuo, parallax intenso ni destellos.
  Todo movimiento es ambiental, leve y desactivable (control propio + `prefers-reduced-motion`).
- Audio siempre bajo control del usuario: una sola voz a la vez; cancelar la lectura
  anterior al cambiar de mensaje o pausar. Conservar Piper, Kokoro y Web Speech API.
- Voces (decidido 2026-11-14): por ahora solo español. En español se ofrecen todas las voces
  descargadas (Piper y Kokoro, más las grabaciones es-419) y las del navegador. En pt-BR la voz
  queda bloqueada: cero voces y controles desactivados, aunque existan modelos pt-BR. Más
  idiomas de voz llegarán después; no borrar modelos ni `datos/voces_locales.json`.
- ElevenLabs u otro servicio externo: esperar autorización antes de consumir créditos o
  enviar textos. Claves solo en el entorno del servidor o de generación, nunca en el
  frontend ni en el repositorio.
- Traducciones por ID; revisión humana en ambos idiomas. No sustituir es-419 por es-ES ni
  pt-BR por pt-PT.
- No instalar en bloque la lista de 47 repositorios del plan; evaluar versión, licencia,
  mantenimiento y compatibilidad con Windows antes de cada dependencia.
- Consultar Modern Web Guidance (GoogleChrome/modern-web-guidance) al implementar
  diálogos, foco, formularios, movimiento, imágenes y rendimiento, y registrar qué
  recomendación se aplicó y cómo se probó.
- Informes académicos: fuera de alcance por ahora.
- Si se cambia un archivo listado en `datos/manifest.json`, actualizar su `bytes` y
  `sha256` en el mismo commit.

## Modelos, advisor y calidad (decidido 2026-11-14)

- Modelo principal: Sonnet (`.claude/settings.json`). Advisor: Fable (`advisorModel`). Para que
  el advisor funcione, el propietario debe haber aceptado una vez `/model fable` (créditos de uso).
  Subagentes en `.claude/agents/`: `investigador` (Haiku, solo lectura) y `revisor` (Opus).
- **Consulta al advisor siempre en estos tres momentos**, y solo en ellos:
  1. antes de fijar un plan o una arquitectura cuando haya más de una opción real;
  2. cuando un error se repite o una prueba falla por segunda vez;
  3. antes de dar un trabajo por terminado.
- **Antes de dar algo por terminado**, pasa por `revisor` si el cambio es grande.
- **«Mejorar» debe superar lo anterior**, en lo que se ve y en lo que se mide. Igualar o empeorar
  no es mejorar y no se presenta como mejora.
- Cambios visuales: compáralos con la versión anterior en capturas lado a lado y di qué es mejor
  y qué es peor. Avisa siempre que quites un rasgo que existía.
- La identidad visual del propietario manda sobre cualquier guía genérica de diseño. Desde el
  2026-11-14 la 6.0 entera es azul noche con acento cian/turquesa (botones, foco, brillos),
  titular serif grande sobre la portada «Bosque de luz». La 5.0 en `/` conserva su verde y lima.
  Contrato completo en `docs/interfaz/6.0/identidad.md`. Ante la duda, pregunta.
- Antes de rediseñar una pieza, captúrala en la 5.0 y parte de ella (controles, textos,
  estructura); no la imagines de cero. Leer `referencias-externas/LEEME.md` y aplicar sus guías.
- Búsquedas y lecturas amplias: delégalas en `investigador`.
- Cambios visuales: ejecuta `python -m tests.comparar_versiones --salida <carpeta temporal>` (5.0
  izquierda, 6.0 derecha, escritorio y móvil), MIRA las imágenes y contrasta con
  `docs/interfaz/6.0/identidad.md`. Al cerrar cualquier cambio sigue el skill `/cerrar-cambio`.
- Hook `.claude/hooks/proteger_git.py` (probado en `tests/test_hook_git.py`): bloquea
  `git add -A/.`, `commit -a`, `reset --hard`, `clean`, `push`, `stash`, `restore` y
  `checkout --`. Los cambios sin confirmar del propietario no se tocan ni se confirman.

## Comandos verificados (Windows, 2026-11-13)

```bash
python -m codigo.nucleo.verificar_paquete          # 1017 archivos, "correcto": true
PYTHONUTF8=1 python -m unittest discover -s tests -q   # 100 pruebas
python -m tests.ejecutar_navegador --hito2         # 6 casos (Pista/Repetir 2/4/8)
python -m tests.ejecutar_navegador --portada       # portada 6.0 (/v6/): 8 paisajes, 7 casos + axe
python -m tests.ejecutar_navegador --portada-5     # portada 5.0 (/): 48 fondos
python -m tests.ejecutar_navegador --catalogo      # 16 casos
python -m tests.ejecutar_navegador --hito3         # 16 casos (Preferencias, teclado)
python -m tests.ejecutar_navegador                 # 20 casos (recorrido general)
python -m tests.ejecutar_navegador --partidas-v6    # 4 partidas completas con teclado (6.0)
python -m tests.ejecutar_navegador --voz-v6         # cadena de voz 6.0 con audio simulado
python -m tests.lighthouse_v6 --salida <carpeta>      # Lighthouse en 4 pantallas × 2 dispositivos
py -3 -m codigo.interfaz.iniciar --sin-descargas   # juego en http://127.0.0.1:8766
```

Herramientas de prueba: `cd frontend && npm ci` instala Playwright core, axe-core y
Lighthouse fijados; `ejecutar_navegador` los usa por defecto junto con el Chrome del
sistema (variables `PLAYWRIGHT_MODULE`, `AXE_SOURCE`, `CHROMIUM_EXECUTABLE` las
sustituyen). `INTERFAZ_SALIDA=<carpeta temporal>` evita escribir capturas en `output/`.

```bash
cd frontend && npm run check        # tsc + ESLint 10 + Prettier + Vitest
cd frontend && npm run mwg -- search "toggle switch"   # Modern Web Guidance (CLI 1.0.0)
python -m uv tool run ruff@0.15.0 check codigo tests    # 18 avisos de base (ver ruff.toml)
python -m uv tool run --python 3.12 pip-audit@2.10.0 -r requirements_voz.txt --disable-pip --no-deps
python -m codigo.nucleo.actualizar_manifiesto [--incluir RUTA]  # tras compilar o editar
python -m codigo.interfaz.preparar_imagenes_ligeras            # si cambia un pictograma, paisaje o robot (Pillow)
python -m codigo.nucleo.validar_catalogo                      # integridad del catálogo ampliado (0 errores)
python -m codigo.nucleo.validar_textos_interfaz               # traducciones de interfaz 5.0 y 6.0
python -m codigo.nucleo.hoja_revision_traducciones            # docs/traducciones/revision_es_pt.csv
```

Flujo de Modern Web Guidance: `search` → `retrieve` → aplicar y verificar → cerrar la
entrega con una sección «Modern Web Guidance» (id de guía, decisión y cita breve).
Skills del proyecto en `.claude/skills/` (frontend-design, webapp-testing).

Detalles del entorno:

- Sin `PYTHONUTF8=1`, `test_consola_jugador_recorrido_completo` falla en Windows: la
  consola hija escribe en cp1252 y la prueba lee UTF-8.
- El repo local usa `core.autocrlf=input`; con `true` cinco textos salen en CRLF y
  `verificar_paquete` falla.
- Nueve JSON de `datos/` y `docs/` están confirmados con CRLF pese a `eol=lf` y aparecen
  como modificados. No incluirlos en commits sin decisión explícita.

## Frontend 6.0 (React + TypeScript + Vite, decidido 2026-11-13)

- Código en `frontend/`; el compilado va a `codigo/interfaz/web6/` y se versiona, para que
  `iniciar_juego.bat` funcione sin Node. Python lo sirve en `/v6/`; la 5.0 sigue en `/`
  hasta que el propietario apruebe el cambio.
- `cd frontend && npm ci && npm run build` (tsc + vite). Tras compilar, los nombres con
  hash cambian: actualizar `datos/manifest.json` (quitar los antiguos, añadir los nuevos).
- Desarrollo: servidor Python en 8766 + `npm run dev` (Vite reenvía `/api`, `/media`, etc.).
- `python -m tests.ejecutar_navegador --v6` — recorrido completo del prototipo (10 casos).
- CSS nativo y controles HTML nativos (`<dialog>` con `showModal`, `<select>`, switches
  `role="switch"`). Sin Tailwind, shadcn, Motion ni Embla mientras no aporten algo concreto.
- Textos nuevos sin traducción revisada: `TEXTOS_NUEVOS_PENDIENTES` en `frontend/src/i18n.ts`.

## Mapa del proyecto

- `codigo/interfaz/servidor.py` — HTTP y API (`/api/vista`, `/api/accion`, `/api/idioma`,
  `/api/voz`, `/api/voz/cancelar`, `/api/revision`, `/revision`). Acciones con
  `evento_id`, `revision`, `sesion_id`, `reto_id`.
- `codigo/interfaz/iniciar.py` — iniciador (uv, Python 3.12 gestionado, modelos de voz).
  `iniciar_juego.bat` / `iniciar_sin_descargas.bat` lo llaman.
- `codigo/interfaz/web/` — frontend actual (`index.html`, `app.js`, `estilos.css`,
  `expedicion.css`, `fondos/catalogo/H01..H48.webp` de 1920×1080).
- `codigo/nucleo/` — estado, gestor de sesión, catálogo, registro, auditoría, manifiesto.
- `codigo/motores/` — `guia.py` (pistas progresivas del catálogo ampliado, ambas
  modalidades) e `id3.py` (catálogo original: ID3, rotación y política probabilística,
  `--catalogo-original`).
- `codigo/entrenamiento/`, `codigo/poc/` — experimentos, simulador, consola, aceptación.
- `datos/expedicion/` — catálogo ampliado (animales, hábitats, pictogramas, pistas).
- `datos/*.json` — catálogo original, traducciones pt-BR, voces, procedencia de imágenes.
- `assets/` — pictogramas, ilustraciones y robot. `datos/manifest.json` — huellas.
- Locales, fuera de Git: `.venv-voz/`, `modelos_voz/`, `registros/`, `output/`,
  `resultados_nuevos/`.

## Portada 6.0 (decidido 2026-11-14, sustituye al carrusel de ocho fondos)

Un único fondo aprobado: «Bosque de luz» (ciervo y búho bajo la luna,
`prototipo-bosque-de-luz/bosque-de-luz-ciervo.png`). No se sustituye, ni se le aplican
filtros, animaciones o capas; conserva su encuadre y su velo oscuro. La portada ocupa
exactamente la vista, sin desplazamiento; Preferencias se abre encima sin empujar nada.
**Sin pictogramas en la portada.** Textos: «Descubre el bosque de luz.» y «Elige un animal.
Sigue las pistas y descubre dónde vive.». Comenzar abre «¿Quién elige el animal?». El
catálogo jugable conserva los 48 hábitats. Los ocho paisajes y capas del carrusel anterior
siguen en `fondos/` sin uso en la 6.0.
