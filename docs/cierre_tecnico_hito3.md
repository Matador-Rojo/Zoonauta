# Cierre técnico del demo para el Hito 3

## Alcance

Zoonauta es una aplicación web local con entrada digital. El servidor utiliza la
biblioteca estándar de Python y escucha en `127.0.0.1`; no requiere un servidor
público para una demostración local. El iniciador abre el navegador y prepara
las dependencias opcionales de las voces. No se ha contratado ni publicado un
alojamiento web mediante este cierre.

La aplicación dispone de las dos modalidades, partidas de 1 a 48 animales, 2/4/8
hábitats, preguntas y pistas pictográficas, modelo probabilístico congelado,
baseline ID3, repetición, pausa, salida y cierre. El trabajo de este cierre mejora
Preferencias. Los textos de la futura producción de audio siguen pendientes de definir. No cambia la
política del agente ni vuelve a entrenar modelos.

## Relación con los requisitos finales

| Requisito | Implementación o evidencia | Límite |
|---|---|---|
| Partida completa en una interfaz funcional | `codigo/interfaz/`, recorridos de navegador y pruebas de copia limpia | Ejecución local; no es un servicio público |
| Pictogramas y voz | Recursos de `assets/`, síntesis local y voces compatibles del navegador | La migración a audios de ElevenLabs todavía no se ha realizado |
| Accesibilidad de interfaz | Pictogramas grandes, apoyos, teclado y Preferencias en dos columnas | Las comprobaciones técnicas no demuestran comprensión por los usuarios |
| Repositorio organizado | `codigo`, `datos`, `docs`, `assets`, `tests` y manifiesto con SHA-256 | El informe final y el video se incorporan por separado |
| Manual y casos de borde | `manual_usuario.md`, `guia_interfaz.md` y este archivo | Las condiciones del equipo deben probarse antes de la exposición |
| Evaluación e impacto | Resultados sintéticos reproducibles del Hito 2 | No hay resultados de una evaluación con usuarios de Kallpa |

## Despliegue y comprobación

Las instrucciones de inicio se encuentran en el README y la guía de interfaz.
Para comprobar el paquete sin generar voz:

```console
python -m codigo.nucleo.verificar_paquete
python -m unittest discover -s tests -v
python -m codigo.poc.aceptacion
python -m codigo.nucleo.auditoria
```

La revisión en Chrome usa Node, Playwright y un navegador instalado, únicamente
como dependencias de desarrollo:

```console
python -m tests.ejecutar_navegador
python -m tests.ejecutar_navegador --hito2
python -m tests.ejecutar_navegador --hito3
python -m tests.ejecutar_navegador --voces-navegador
```

Para una carpeta recién extraída sin modelos ni entorno de voz:

```console
python -m tests.verificar_copia_limpia --carpeta RUTA_EXTRAIDA --salida RESULTADOS
```

No se deben incluir `.venv-voz`, `modelos_voz`, `registros`, `output`, cookies ni
credenciales en el ZIP o el repositorio. El manifiesto enumera los recursos
distribuibles; los pesos opcionales de voz se preparan aparte.

## Casos de borde y comportamiento esperado

| Situación | Resultado esperado |
|---|---|
| Cantidad vacía, decimal o fuera de 1–48 | No inicia; presenta un aviso con instrucciones |
| Selección de un hábitat oculto | El servidor rechaza la acción; no aumenta el progreso |
| Doble clic o reenvío del mismo evento | No procesa dos veces el avance |
| Acción de una pantalla anterior | Recupera la vista actual y rechaza la acción obsoleta |
| Asociación pendiente | Da apoyo neutral, sin marcarla como error ni entrenar con una etiqueta inventada |
| Repetir | Conserva el contenido; no cambia la respuesta ni el progreso |
| Pausa y recarga del navegador | Conserva el reto mientras siga funcionando el servidor y la misma sesión |
| Reinicio del proceso servidor o pérdida de cookie | Inicia otra sesión; no restaura una partida anterior |
| Voz no disponible o lectura cancelada | Conserva la interacción por texto e imágenes; informa del problema cuando corresponde |
| Pantalla pequeña o zoom alto | Apila Preferencias y permite desplazamiento; no oculta controles para forzar un ajuste |
| Muchos avisos | Limita los visibles, retira los más antiguos y evita scroll en la pila |
| Partida finalizada | Presenta el robot y el progreso real; volver a la portada no lee la pregunta de modalidad |

## Producción de audio pendiente

El contenido de audio se ampliará antes de preparar las grabaciones. Este cierre
no publica un catálogo de locuciones ni incorpora audios de ElevenLabs.
La sustitución de voces requiere definir los textos, seleccionar las voces,
producir sus audios, comprobar su cobertura y revisar pronunciación y volumen.
Las voces disponibles y el comportamiento de lectura del juego permanecen sin cambios.

## Evaluación de uso pendiente

Antes de afirmar un impacto educativo, se necesita una sesión de evaluación
autorizada y acompañada por un educador. Conviene observar si se comprenden las
preguntas y pictogramas, si se distinguen las alternativas, si los controles se
encuentran y si repetir o pausar permite continuar. Registrar dificultades y
apoyos necesarios sin nombres, diagnósticos individuales ni grabaciones por defecto.
Los resultados de simulaciones no deben presentarse como aprendizaje humano.

El informe final, el video y la sustentación no se generan en este cierre de código.
