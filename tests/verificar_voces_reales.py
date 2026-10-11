"""Genera y comprueba WAV reales de las 14 voces (requiere preparar modelos)."""
from array import array
import hashlib
from importlib.metadata import version
import io
import json
import math
import platform
from time import perf_counter
import wave

from codigo.interfaz.idiomas import saludo
from codigo.interfaz.voz import MotorVoz
from codigo.nucleo.datos import RAIZ_PROYECTO


def main():
    motor = MotorVoz()
    resultados = []
    for voz in motor.configuracion()["voces"]:
        inicio = perf_counter()
        contenido = motor.sintetizar(voz["id"], saludo(voz["idioma"]), voz["idioma"])
        with wave.open(io.BytesIO(contenido)) as wav:
            assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
            frecuencia, frames = wav.getframerate(), wav.getnframes()
            muestras = array("h", wav.readframes(frames))
            rms = math.sqrt(sum(m * m for m in muestras) / len(muestras))
            assert frames > frecuencia / 2 and rms > 1
        assert contenido == motor.sintetizar(voz["id"], saludo(voz["idioma"]), voz["idioma"])
        fila = {"voz": voz["id"], "idioma": voz["idioma"], "texto": saludo(voz["idioma"]),
                "bytes_wav": len(contenido), "frecuencia_hz": frecuencia, "frames": frames,
                "duracion_segundos": round(frames / frecuencia, 3), "rms_pcm16": round(rms, 3),
                "generacion_segundos": round(perf_counter() - inicio, 3),
                "sha256_wav": hashlib.sha256(contenido).hexdigest(), "repeticion_identica": True}
        resultados.append(fila)
        print(f"Correcto: {voz['id']} ({fila['duracion_segundos']} s de audio)", flush=True)
    assert len(resultados) == 14
    documento = {"version": "3.8.0", "fecha": "2026-10-11", "plataforma": platform.system(),
                 "python": platform.python_version(),
                 "dependencias": {n: version(n) for n in ("piper-tts", "kokoro-onnx", "onnxruntime", "numpy")},
                 "alcance": "Síntesis local real y WAV PCM no silencioso. No certifica pronunciación ni reproducción audible en el equipo del usuario.",
                 "resultados": resultados}
    (RAIZ_PROYECTO / "docs/interfaz/revision_voces_locales.json").write_text(json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("14 voces locales comprobadas.", flush=True)


if __name__ == "__main__":
    main()
