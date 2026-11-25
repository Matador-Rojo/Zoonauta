# Cierre técnico del proyecto para el Hito 3 (Zoonauta 6.0)

## Alcance

Zoonauta 6.0 (*Atlas Bioluminiscente*) es una aplicación web local con entrada digital
accesible (CAA). El servidor utiliza la biblioteca estándar de Python y escucha en
`127.0.0.1`, sirviendo el frontend compilado (React 19 + TypeScript + Vite en
`codigo/interfaz/web6/`), las 412 grabaciones de voz en español (`assets/voz/grabada/es-419/`),
las portadas 2K con streaming por rangos HTTP (`206 Partial Content`) y el panel de
revisión `/revision`. No requiere Internet ni instalar dependencias externas para jugar:
basta Python 3.10 o posterior.

La aplicación dispone de las dos modalidades (*El agente elige* y *Yo elijo*), partidas
de 1 a 48 animales del catálogo ampliado (288 animales y 48 hábitats), 2/4/8 opciones de
hábitat, preguntas y pistas pictográficas sincronizadas con la voz, cuatro políticas de
guía seleccionables (`AGENTE_ADAPTATIVO` por defecto, `AGENTE_APRENDIDO` Beta-Bernoulli
congelado, línea base `ID3_OPCIONES` y `PISTAS_PROGRESIVAS`), tres aspectos visuales
(*Bosque de noche*, *Bosque de día* y *Alto contraste* 21:1), tamaño de texto grande,
sonidos del bosque opcionales, repetición, pausa, salida, hallazgos de la partida, cierre
y soporte PWA.

## Relación con los requisitos finales

| Requisito | Implementación o evidencia | Límite |
|---|---|---|
| Partida completa en una interfaz funcional | `frontend/`, `codigo/interfaz/`, pruebas E2E Playwright y `verificar_copia_limpia` | Ejecución local en `127.0.0.1` (sin despliegue en nube pública) |
| Motor de IA (baseline + modelo principal) | `codigo/motores/id3.py`, `agente.py`, `aprendizaje6.py` y `docs/agente/agente_6.md` | Entrenamiento y evaluación con jugadores sintéticos, no con usuarios reales |
| Pictogramas y voz | 288 animales, 48 hábitats, pictogramas CAA y **tres voces completas de ElevenLabs en español (Marcela, Valeria y Gaby — `5vkxOzoz40FrElmLP4P7`, 412 grabaciones cada una)** | En `pt-BR` la voz permanece bloqueada mientras no existan grabaciones en portugués |
| Accesibilidad de interfaz | 3 temas (incluido *Alto contraste* AAA 21:1), texto grande, movimiento reducido, teclado y `0` incidencias en `axe-core` | Las comprobaciones técnicas no sustituyen la validación humana con educadores |
| Repositorio organizado e íntegro | `codigo`, `frontend`, `datos`, `docs`, `assets`, `tests` y manifiesto SHA-256 (`verificar_paquete`) | Los documentos PDF finales y el video demostrativo se añaden para la entrega formal |
| Manual, observatorio y casos de borde | `docs/manual_usuario.md`, panel `/revision` (exportación JSON/CSV/anonimizado) y este archivo | Conviene verificar audio y pantalla en el equipo de sustentación |

## Despliegue y comprobación

Las instrucciones de inicio se encuentran en el `README.md` y en `docs/manual_usuario.md`.
Para comprobar el paquete completo:

```console
python -m codigo.nucleo.verificar_paquete
python -m codigo.nucleo.validar_textos_interfaz
python -m unittest discover -s tests -v
python -m codigo.poc.aceptacion
python -m codigo.nucleo.auditoria
```

Pruebas del frontend (requieren Node 22+ en `frontend/`):

```console
npm --prefix frontend run check
python -m tests.ejecutar_navegador --portada
python -m tests.ejecutar_navegador --v6
python -m tests.ejecutar_navegador --partidas-v6
python -m tests.ejecutar_navegador --voz-v6
python -m tests.ejecutar_navegador --hito2
python -m tests.ejecutar_navegador --hito3
python -m tests.ejecutar_navegador --catalogo
```

Para comprobar una copia recién extraída del ZIP sin descargas:

```console
python -m tests.verificar_copia_limpia --carpeta RUTA_EXTRAIDA --salida RESULTADOS
```

No se deben incluir `.venv-voz`, `modelos_voz`, `registros`, `output`, `.shrink`, cookies
ni credenciales en el ZIP o el repositorio. El manifiesto enumera y verifica los recursos
distribuibles por tamaño y SHA-256.

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
| Reinicio del proceso servidor o pérdida de cookie | Inicia otra sesión; no restaura una partida anterior |
| Voz no disponible o lectura cancelada | Conserva la interacción por texto e imágenes; informa del problema cuando corresponde |
| Pantalla pequeña o zoom alto | Permite desplazamiento como último recurso sin aplastar imágenes ni controles |
| Reducir movimiento activo | Desmonta los videos de portada y muestra las imágenes estáticas `1672 × 941` sin animaciones |
| Partida finalizada | Presenta el robot, el resumen real y los hallazgos de la partida |

## Evaluación de uso con personas (alcance ético)

Antes de afirmar un impacto educativo medido en campo, se requiere una sesión autorizada
y acompañada por educadores de Kallpa. El observatorio `/revision` ofrece exportación
anonimizada sin nombres ni diagnósticos individuales. Los resultados de simulaciones
sintéticas del Hito 2 y 6.0 evalúan propiedades algorítmicas y no deben presentarse como
aprendizaje humano comprobado.
