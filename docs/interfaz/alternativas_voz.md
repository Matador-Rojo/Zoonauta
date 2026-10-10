# Voces locales de Zoonauta 3.4

Piper y Kokoro están integrados. El servidor del equipo genera WAV a partir de
la respuesta preparada por la guía; no utiliza un proveedor remoto de voz.

## Catálogo incluido

| Idioma | Motor | Nombre | Modelo / identificador |
|---|---|---|---|
| Español, México | Piper | Claude | es_MX-claude-high |
| Español, México | Piper | Ald, calidad media | es_MX-ald-medium |
| Español, México | Piper | Ald, ligera | es_MX-ald-x_low |
| Español, Argentina | Piper | Daniela | es_AR-daniela-high |
| Español | Kokoro | Dora | ef_dora |
| Español | Kokoro | Alex | em_alex |
| Español | Kokoro | Santa | em_santa |
| Português (Brasil) | Piper | Cadu | pt_BR-cadu-medium |
| Português (Brasil) | Piper | Edresson | pt_BR-edresson-low |
| Português (Brasil) | Piper | Faber | pt_BR-faber-medium |
| Português (Brasil) | Piper | Jeff | pt_BR-jeff-medium |
| Português (Brasil) | Kokoro | Dora | pf_dora |
| Português (Brasil) | Kokoro | Alex | pm_alex |
| Português (Brasil) | Kokoro | Santa | pm_santa |

Son 14 opciones: siete por idioma. Ald media y ligera son variantes del mismo
hablante. Se incorporaron todos los modelos MX/AR y BR del índice Piper fijado en
`datos/voces_locales.json`, y las tres voces de cada idioma del pack Kokoro v1.0.
El catálogo fija revisiones, tamaños y huellas; no cambia al actualizarse un índice
externo. Las voces del navegador se retiraron del selector y del reproductor.

## Preparación y uso

Abre `iniciar_juego.bat` en Windows o `bash iniciar_juego.sh` en Linux/macOS.
Se crea `.venv-voz` con Python 3.12 y los paquetes de `requirements_voz.txt`.
El iniciador usa uv para preparar una versión compatible aunque el Python
principal sea 3.14. Después descarga y verifica 26 archivos, unos 656 MB de
modelos y fichas, en `modelos_voz`. Las dependencias y Python se descargan aparte
si faltan. La carpeta de modelos y el entorno no se suben a GitHub.

La primera preparación requiere Internet. Después la generación es local y
funciona sin conexión ni claves. Los archivos completos verificados se conservan
si una descarga se interrumpe. Para preparar sin abrir el navegador:

```console
py -3 -m codigo.interfaz.iniciar --solo-preparar
```

En Preferencias selecciona el idioma, una voz y Probar voz. El ritmo modifica
la reproducción conservando el tono. Silenciar, pausar, salir, cambiar de voz o
idioma y comenzar otra acción detienen el audio anterior. Repetir reutiliza el
mismo texto y, mientras esté en la caché, el mismo WAV. Cambiar de idioma o probar
una voz no registra una acción del agente ni modifica su modelo.

Si se inicia directamente el servidor con un Python sin estos paquetes, el juego
con texto y pictogramas sigue disponible; Preferencias indica cómo preparar las
voces. Para jugar con voz utiliza el iniciador o el Python de `.venv-voz`.

## Implementación y verificación

Piper usa piper-tts 1.3.0. Kokoro usa kokoro-onnx 0.4.9 y el modelo ONNX int8 v1.0
con pack voices-v1.0. La generación se serializa, mantiene como máximo dos modelos
cargados y limita la caché de WAV a 128 respuestas y 32 MiB. Se adaptan los tipos
de entrada al contrato ONNX: este modelo requiere speed float32 y el motor
kokoro-onnx lo entrega como int32 en exportaciones input_ids.

La API solo lee la respuesta actual o el saludo fijo; comprueba sesión, reto,
revisión e idioma. No acepta texto libre del navegador. Una respuesta de audio
que llega después de pausar o cambiar de pantalla se descarta.

`tests/verificar_voces_reales.py` generó muestras de las 14 opciones con los motores
reales en Linux/Python 3.12, comprobó WAV PCM mono no silencioso y repetición
idéntica. Resultados: `revision_voces_locales.json`. También se resolvieron y
descargaron los 32 paquetes binarios compatibles con Windows x64/Python 3.12;
esto comprueba disponibilidad de paquetes, no una ejecución nativa en Windows.
Edresson emitió un aviso por el fonema de nasalización en la muestra; produjo
un WAV no silencioso. Las pruebas no certifican naturalidad ni pronunciación.

Para repetir la comprobación real en Windows:

```console
.venv-voz\Scripts\python.exe -m tests.verificar_voces_reales
```

## Fuentes y licencias

Las fichas MODEL_CARD de las ocho voces Piper se descargan junto a los modelos;
conservan la procedencia y licencia del corpus de cada voz. El motor Piper publica
GPL-3.0. Kokoro-82M publica los pesos con Apache-2.0; el motor kokoro-onnx publica
MIT. Las licencias de motores, modelos y pictogramas son independientes.

- [Piper: motor oficial y API](https://github.com/OHF-Voice/piper1-gpl).
- [Piper: modelos y fichas](https://huggingface.co/rhasspy/piper-voices).
- [Kokoro-82M: modelo y voces](https://huggingface.co/hexgrad/Kokoro-82M).
- [Kokoro: motor ONNX](https://github.com/thewh1teagle/kokoro-onnx).
- [Kokoro: release fijado de modelos](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1).
- [uv: Python gestionado](https://docs.astral.sh/uv/guides/install-python/).
