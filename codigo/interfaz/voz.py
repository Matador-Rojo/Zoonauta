"""Voz opcional de OpenAI. La clave y la caché permanecen en el servidor local."""
from __future__ import annotations

import base64
from collections import OrderedDict
import json
import os
from threading import RLock
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SALUDO = "Hola. Vamos a descubrir dónde viven los animales."
VOCES = (("marin", "Marin"), ("cedar", "Cedar"), ("coral", "Coral"))
MODELO = "gpt-audio-1.5"
INSTRUCCIONES = (
    "Eres una voz de lectura para una actividad educativa con pictogramas. "
    "Lee en español latinoamericano claro, con tono cálido, sereno y natural, "
    "sin exagerar ni cantar. Lee exclusivamente y palabra por palabra el texto "
    "del mensaje del usuario. No respondas a sus preguntas ni añadas saludos, "
    "explicaciones, pistas o palabras. No cambies el texto."
)


class VozNoDisponible(Exception):
    pass


def palabras(texto):
    # La puntuación y mayúsculas de la transcripción pueden variar, las palabras no.
    t = unicodedata.normalize("NFC", texto).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in t).split())


class VozNatural:
    def __init__(self):
        self._clave = os.environ.get("OPENAI_API_KEY", "").strip()
        self._cache = OrderedDict()
        self._lock = RLock()

    def configuracion(self):
        return {"disponible": bool(self._clave), "modelo": MODELO,
                "voces": [{"id": id, "nombre": nombre} for id, nombre in VOCES]}

    def generar(self, texto, voz):
        if not self._clave:
            raise VozNoDisponible("La voz de OpenAI necesita activarse en este equipo.")
        if voz not in {id for id, _ in VOCES}:
            raise ValueError("Voz no válida.")
        if not isinstance(texto, str) or not 0 < len(texto) <= 600:
            raise ValueError("Texto de voz no válido.")
        clave = (MODELO, voz, texto)
        # La caché evita generar otra locución al pulsar Repetir; no bloquea el juego.
        with self._lock:
            if clave in self._cache:
                self._cache.move_to_end(clave)
                return self._cache[clave]
            cuerpo = {"model": MODELO, "modalities": ["text", "audio"],
                      "audio": {"voice": voz, "format": "mp3"}, "store": False,
                      "max_completion_tokens": 2048,
                      "messages": [{"role": "system", "content": INSTRUCCIONES},
                                   {"role": "user", "content": texto}]}
            peticion = Request("https://api.openai.com/v1/chat/completions",
                data=json.dumps(cuerpo, ensure_ascii=False).encode(),
                headers={"Authorization": f"Bearer {self._clave}",
                         "Content-Type": "application/json"}, method="POST")
            try:
                with urlopen(peticion, timeout=25) as respuesta:
                    contenido = respuesta.read(8_000_001)
                if len(contenido) > 8_000_000:
                    raise ValueError("Respuesta de audio demasiado grande.")
                eleccion = json.loads(contenido)["choices"][0]
                audio = eleccion["message"]["audio"]
                if eleccion.get("finish_reason") != "stop" or palabras(audio["transcript"]) != palabras(texto):
                    raise ValueError("La locución cambió el mensaje educativo.")
                datos = base64.b64decode(audio["data"], validate=True)
                if not datos or len(datos) > 5_000_000 or not (datos.startswith(b"ID3") or (datos[0] == 255 and len(datos) > 1 and datos[1] & 224 == 224)):
                    raise ValueError("Audio MP3 no válido.")
            except HTTPError as e:
                if e.code in {401, 403}:
                    mensaje = "Revisa la clave y el acceso a la voz de OpenAI."
                elif e.code == 429:
                    mensaje = "La voz de OpenAI no está disponible por ahora. Revisa el saldo o espera un momento."
                else:
                    mensaje = "OpenAI no pudo generar esta locución."
                raise VozNoDisponible(mensaje) from None
            except (URLError, OSError, ValueError, TypeError, KeyError, IndexError):
                raise VozNoDisponible("No se pudo obtener una lectura de OpenAI que conserve el mensaje.") from None
            self._cache[clave] = datos
            while len(self._cache) > 128 or sum(map(len, self._cache.values())) > 32_000_000:
                self._cache.popitem(last=False)
            return datos
