# Fase 5 (voces) — en pausa por decisión del propietario (2026-11-14)

## Hecho

- Frontend 6.0: estado de la voz en Preferencias (sin voces, voz del navegador local o
  en línea, voces locales sin conexión) con los textos ya traducidos de 5.0.
- Un fallo de red al leer muestra el aviso traducido, no el error técnico del navegador.
- `python -m tests.ejecutar_navegador --voz-v6`: 8 casos con audio simulado (grabación
  primero, voz alternativa con el mensaje completo, una sola voz, velocidad, pausa que
  cancela, interruptor, fallo de red, sin grabaciones no se piden).
- Entorno local de voces preparado en esta copia (`modelos_voz/`, `.venv-voz/`, fuera de Git):
  14 voces disponibles.

## Hallazgo pendiente de decisión: Kokoro en español usa pronunciación de España

`codigo/interfaz/voz.py` llama a Kokoro con `lang="es"`, que en espeak-ng es el español
peninsular (distinción /θ/). Comprobado con el fonemizador:

| Variante | «zorro» | «cerca» | «océano» |
|---|---|---|---|
| `es` (actual) | /θoro/ | /θeɾka/ | /oθeano/ |
| `es-419` | /soro/ | /seɾka/ | /oseano/ |

`datos/voces_locales.json` ya declara esas voces como región `ES`, y la interfaz las muestra
como «España». Propuesta para cuando se retome: usar `lang="es-419"` y decidir la etiqueta
(el timbre de las voces Kokoro sigue siendo el original). No se ha cambiado nada.

## Siguiente al retomar

1. Comparación objetiva de las 14 voces y de las grabaciones ElevenLabs (síntesis +
   transcripción con faster-whisper): inteligibilidad, latencia y duración.
2. Decidir el cambio de Kokoro a `es-419`.
3. Grabaciones ElevenLabs: las coordina la sesión «Catálogo de voces» (voz Marcela,
   Eleven v4; falta el `voice_id` y decidir si los MP3 van a Git).
