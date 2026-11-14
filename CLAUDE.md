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

## Comandos verificados (Windows, 2026-11-13)

```bash
python -m codigo.nucleo.verificar_paquete          # 1017 archivos, "correcto": true
PYTHONUTF8=1 python -m unittest discover -s tests -q   # 100 pruebas
python -m tests.ejecutar_navegador --hito2         # 6 casos (Pista/Repetir 2/4/8)
python -m tests.ejecutar_navegador --portada       # hoy: 48 fondos; pasar a 8 en la 6.0
python -m tests.ejecutar_navegador --catalogo      # 16 casos
python -m tests.ejecutar_navegador --hito3         # 16 casos (Preferencias, teclado)
python -m tests.ejecutar_navegador                 # 20 casos (recorrido general)
py -3 -m codigo.interfaz.iniciar --sin-descargas   # juego en http://127.0.0.1:8766
```

Entorno necesario para las pruebas de navegador (no hay Playwright en el repo):

- `PLAYWRIGHT_MODULE=<ruta absoluta a node_modules/playwright-core>`
- `CHROMIUM_EXECUTABLE="C:/Program Files/Google/Chrome/Application/chrome.exe"`
- `INTERFAZ_SALIDA=<carpeta temporal>` para no escribir capturas en `output/`.

Detalles del entorno:

- Sin `PYTHONUTF8=1`, `test_consola_jugador_recorrido_completo` falla en Windows: la
  consola hija escribe en cp1252 y la prueba lee UTF-8.
- El repo local usa `core.autocrlf=input`; con `true` cinco textos salen en CRLF y
  `verificar_paquete` falla.
- Nueve JSON de `datos/` y `docs/` están confirmados con CRLF pese a `eol=lf` y aparecen
  como modificados. No incluirlos en commits sin decisión explícita.

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

## Portada 6.0 (decidido)

Exactamente ocho fondos, en este orden: H01 Selva tropical húmeda, H09 Sabana seca,
H17 Desierto cálido, H22 Hielo marino polar, H20 Alta montaña rocosa, H37 Arrecife de
coral, H21 Cueva terrestre (estática), H25 Lago de agua dulce. Reutilizar los WebP de
`fondos/catalogo/`. El catálogo jugable conserva los 48 hábitats.
