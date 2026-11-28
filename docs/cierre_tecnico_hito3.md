# Cierre técnico del proyecto para el Hito 3 (Zoonauta)

## Alcance

Zoonauta es una aplicación web educativa accesible con pictogramas CAA y guía adaptativa local.
El servidor utiliza exclusivamente la biblioteca estándar de Python (`3.10+`, sin dependencias `pip`)
y puede ejecutarse en local (`127.0.0.1`) o desplegarse en web mediante WSGI (`codigo/interfaz/wsgi.py`)
o Docker (`Dockerfile` / `docker-compose.yml`). Sirve el frontend compilado (React 19 + TypeScript + Vite
en `codigo/interfaz/web6/`), las **8 voces grabadas completas** (`3 296` audios, `412` por voz en español,
portugués brasileño e inglés, con soporte nativo para AAC `.m4a`, MP3 y WAV), las portadas animadas 2K con
streaming por rangos HTTP (`206 Partial Content`) y el panel de observación `/revision`. No requiere Internet
ni APIs externas para jugar.

La aplicación dispone de:
- Dos modalidades (*Yo elijo* con orden híbrido aleatorio por biomas / alfabético y filtro *Por descubrir*; y
  *El agente elige*, que prioriza animales aún no descubiertos en el álbum).
- Catálogo ampliado de **288 animales** y **48 hábitats** (de 1 a 48 retos por partida, con 2, 4 u 8 opciones
  de hábitat), manteniendo además `--catalogo-original` (48 animales, 8 hábitats) para reproducir los
  experimentos del Hito 2.
- Preguntas y pistas pictográficas CAA sincronizadas con la voz, con cuatro políticas de guía seleccionables
  (`AGENTE_ADAPTATIVO` por defecto, `AGENTE_APRENDIDO` Beta-Bernoulli congelado, línea base `ID3_OPCIONES`
  y `PISTAS_PROGRESIVAS`).
- **3 idiomas completos** (*Español `es-419`*, *Português do Brasil `pt-BR`* y *English `en`*) y **8 voces
  grabadas completas** de ElevenLabs (`412` mensajes por voz):
  - **Español:** Marcela, Valeria, Gaby y Diego.
  - **Português (Brasil):** Roberta y Will.
  - **English:** Jessica y Mark.
- **3 temas visuales** con logotipo vectorial adaptativo (*Bosque de noche*, *Bosque de día* y *Alto contraste*
  WCAG AAA 21:1), **3 tamaños de texto** (*Pequeño*, *Normal*, *Grande*), *Reducir movimiento*, bloqueo
  opcional *Proteger Preferencias*, sonidos del bosque con celebración acústica reactiva a 5 familias de biomas,
  háptica suave, **Mi álbum de expedición** persistente en `localStorage` (2 series de 5 estrellas y rejilla
  paginada 3 × 3), repetición, pausa, salida, hallazgos de la partida, cierre y soporte instalable **PWA**.

## Relación con los requisitos finales

| Requisito | Implementación o evidencia | Límite |
|---|---|---|
| Partida completa en una interfaz funcional | `frontend/`, `codigo/interfaz/`, pruebas E2E Playwright (`--portada`, `--v6`, `--partidas-v6`, `--voz-v6`) y `verificar_copia_limpia` | Pensado para ejecución local y despliegue web Python (WSGI / Docker / PythonAnywhere) |
| Motor de IA (baseline + modelo principal) | `codigo/motores/id3.py`, `agente.py`, `aprendizaje6.py`, `guia.py` y `docs/agente/agente_6.md` | Entrenamiento y evaluación con jugadores sintéticos, no con usuarios reales |
| Pictogramas y voz multilingüe | 288 animales, 48 hábitats, pictogramas CAA, **3 idiomas completos** (`es-419`, `pt-BR`, `en`) y **8 voces completas de ElevenLabs** (`412` audios c/u · `3 296` total; AAC 32 kbps en `Zoonauta-Web.zip` y MP3 en el repositorio completo) | Voces verificadas automáticamente en cobertura total (`test_voz_grabada_cobertura`); la evaluación perceptual en aula requiere sesión con educadores |
| Accesibilidad de interfaz | 3 temas (incluido *Alto contraste* AAA 21:1), 3 tamaños de texto (*Pequeño / Normal / Grande*), movimiento reducido, *Proteger Preferencias*, navegación por teclado y `0` incidencias en `axe-core` | Las comprobaciones técnicas no sustituyen la validación humana con educadores |
| Repositorio organizado e íntegro | `codigo`, `frontend`, `datos`, `docs`, `assets`, `tests`, README en 3 idiomas y manifiesto SHA-256 (`verificar_paquete`: `correcto: true`) | El informe final, el PPT y el video demostrativo se entregan por separado para la sustentación |
| Manual, observatorio y casos de borde | `docs/manual_usuario.md`, panel `/revision` (exportación JSON/CSV/anonimizado), registros `.jsonl` y este archivo | Conviene verificar audio y pantalla en el equipo o enlace de sustentación |

## Despliegue y comprobación

Las instrucciones de inicio y despliegue se encuentran en `README.md`, `docs/manual_usuario.md` y
`docs/despliegue_hostinger.md`. Para comprobar el paquete completo:

```console
python -m codigo.nucleo.verificar_paquete
python -m codigo.nucleo.validar_textos_interfaz
python -m unittest discover -s tests -v
python -m codigo.poc.aceptacion
python -m codigo.nucleo.auditoria
```

Resultados verificados en la versión final:
- **126/126 pruebas Python** (`unittest discover -s tests`) en verde, incluyendo cobertura completa de voz en los 3 idiomas y las 8 voces (`test_voz_grabada_cobertura`, `test_idiomas_voz`, `test_catalogo_voz`).
- **8/8 casos de aceptación** (`codigo.poc.aceptacion`).
- **Auditoría estructural y traducciones** (`codigo.nucleo.auditoria`): `correcto: true`, `0` errores.
- **Verificación de integridad SHA-256** (`codigo.nucleo.verificar_paquete`): `correcto: true`, `0` errores.
- **8/8 pruebas Vitest** + TypeScript + ESLint + Prettier (`npm --prefix frontend run check`).
- **Smoke test del paquete web `Zoonauta-Web.zip`** (`HOSTINGER_AAC_SMOKE_OK`): arranque aislado, imágenes ligeras sin duplicados y streaming `audio/mp4` verificado en los 3 idiomas.

Pruebas del frontend y navegador (requieren Node 22+ en `frontend/`):

```console
npm --prefix frontend run check
python -m tests.ejecutar_navegador --portada --v6 --partidas-v6 --voz-v6
python -m tests.ejecutar_navegador --hito2 --hito3 --catalogo
```

Para comprobar una copia recién extraída del ZIP sin descargas:

```console
python -m tests.verificar_copia_limpia --carpeta RUTA_EXTRAIDA --salida RESULTADOS
```

No se deben incluir `.venv-voz`, `modelos_voz`, `registros`, `output`, `.shrink`, cookies ni
credenciales en el ZIP o el repositorio. El manifiesto enumera y verifica los recursos distribuibles
por tamaño y SHA-256.

## Casos de borde y comportamiento esperado

| Situación | Resultado esperado |
|---|---|
| Cantidad vacía, decimal o fuera de 1–48 | No inicia; presenta un aviso con instrucciones |
| Selección de un hábitat oculto | El servidor rechaza la acción; no aumenta el progreso |
| Doble clic o reenvío del mismo evento | No procesa dos veces el avance |
| Acción de una pantalla anterior | Recupera la vista actual y rechaza la acción obsoleta |
| Asociación pendiente | Da apoyo neutral, sin marcarla como error ni entrenar con una etiqueta inventada |
| Repetir | Conserva exactamente el mensaje y pictogramas; no cambia el progreso |
| Pausa y recarga del navegador | Conserva el reto mientras siga funcionando el servidor y la misma sesión |
| Reinicio del proceso servidor o pérdida de cookie | Inicia otra sesión; el progreso acumulado en *Mi álbum* se conserva localmente en el navegador |
| Voz no disponible o lectura cancelada | Conserva la interacción por texto e imágenes sin bloquear la partida |
| Pantalla pequeña (`320 px`) o zoom alto | Permite desplazamiento como último recurso sin aplastar imágenes ni controles |
| Reducir movimiento activo | Detiene el lienzo atmosférico `<BosqueVivo />` y las animaciones, mostrando las portadas 2K (`1672 × 941`) estáticas sin movimiento |
| Partida finalizada o álbum completado (`288/288`) | Presenta el resumen real y los hallazgos; al volver a jugar con el agente, mezcla nuevamente todo el catálogo sin bloquearse |

## Evaluación de uso con personas (alcance ético)

Antes de afirmar un impacto educativo medido en campo, se requiere una sesión autorizada y
acompañada por educadores de Kallpa. El observatorio `/revision` ofrece exportación anonimizada
sin nombres ni diagnósticos individuales. Los resultados de simulaciones sintéticas del Hito 2 y
del agente adaptativo evalúan propiedades algorítmicas y no deben presentarse como aprendizaje
humano comprobado.
