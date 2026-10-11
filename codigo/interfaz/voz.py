"""Síntesis local Piper/Kokoro, sin servicios externos durante la partida."""
from __future__ import annotations

from collections import OrderedDict
import importlib.util
import io
import json
from threading import RLock
import wave

from codigo.interfaz.preparar_voces import catalogo, directorio_voces


class VozNoDisponible(RuntimeError):
    pass


class LecturaCancelada(RuntimeError):
    """La lectura dejó de ser necesaria antes de terminar la síntesis."""


class ControlLecturasVoz:
    """Última lectura por página, independiente del estado educativo."""
    def __init__(self):
        self.lock = RLock()
        self.turnos = OrderedDict()

    def registrar(self, canal, turno):
        if (not isinstance(canal, str) or not 1 <= len(canal) <= 120
                or type(turno) is not int or not 0 <= turno < 2 ** 53):
            raise ValueError("Identificador de lectura no válido.")
        with self.lock:
            anterior = self.turnos.get(canal, -1)
            if turno < anterior:
                raise LecturaCancelada()
            self.turnos[canal] = turno
            self.turnos.move_to_end(canal)
            while len(self.turnos) > 8:
                self.turnos.popitem(last=False)

    def vigente(self, canal, turno):
        with self.lock:
            return self.turnos.get(canal) == turno


class SesionONNXTipada:
    """Ajusta las entradas al contrato del modelo ONNX descargado.

    kokoro-onnx 0.4.9 entrega speed como int32 en exportaciones input_ids,
    mientras que el modelo v1.0 int8 requiere float32.
    """
    def __init__(self, sesion):
        self.sesion = sesion

    def __getattr__(self, nombre):
        return getattr(self.sesion, nombre)

    def run(self, salidas, entradas, *args, **kwargs):
        import numpy as np
        tipos = {"tensor(float)": np.float32, "tensor(int64)": np.int64,
                 "tensor(int32)": np.int32, "tensor(float16)": np.float16}
        datos = dict(entradas)
        for entrada in self.sesion.get_inputs():
            if entrada.type in tipos and entrada.name in datos:
                datos[entrada.name] = np.asarray(datos[entrada.name], dtype=tipos[entrada.type])
        return self.sesion.run(salidas, datos, *args, **kwargs)


class MotorVoz:
    def __init__(self, raiz=None, *, max_cache_bytes=32 * 1024 * 1024, max_modelos=4):
        if type(max_modelos) is not int or max_modelos < 1:
            raise ValueError("El límite de modelos debe ser un entero positivo.")
        self.raiz = raiz or directorio_voces()
        self.catalogo = catalogo()
        self.voces = {v["id"]: v for v in self.catalogo["voces"]}
        self.archivos = {a["archivo"]: a for a in self.catalogo["archivos"]}
        self.lock = RLock()
        self.lock_cache = RLock()
        self.max_modelos = max_modelos
        self.modelos = OrderedDict()
        self.cache = OrderedDict()
        self.bytes_cache = 0
        self.max_cache_bytes = max_cache_bytes

    def _disponible(self, voz):
        modulo = "piper" if voz["motor"] == "piper" else "kokoro_onnx"
        if importlib.util.find_spec(modulo) is None:
            return False
        nombres = (["piper/" + voz["modelo"], "piper/" + voz["configuracion"]]
                   if voz["motor"] == "piper" else ["kokoro/" + voz["modelo"], "kokoro/" + voz["pack"]])
        return all((self.raiz / n).is_file() and (self.raiz / n).stat().st_size == self.archivos[n]["bytes"] for n in nombres)

    def configuracion(self):
        return {"voces": [{"id": v["id"], "nombre": v["nombre"], "motor": v["motor"],
                           "idioma": "pt-BR" if v["idioma"] == "pt-BR" or v["idioma"] == "pt" else "es",
                           "region": v["region"], "calidad": v.get("calidad", ""),
                           "disponible": self._disponible(v)} for v in self.voces.values()],
                "bytes_descarga": self.catalogo["bytes_descarga"]}

    def _modelo(self, voz):
        clave = (voz["motor"], voz["modelo"])
        if clave in self.modelos:
            self.modelos.move_to_end(clave)
            return self.modelos[clave]
        while len(self.modelos) >= self.max_modelos:
            self.modelos.popitem(last=False)
        import onnxruntime as ort
        opciones = ort.SessionOptions()
        # Cada modelo conserva su propio pool. Limitarlo evita la competencia
        # entre decenas de hilos al conservar varias voces en CPU.
        opciones.intra_op_num_threads = 2
        opciones.inter_op_num_threads = 1
        if voz["motor"] == "piper":
            from piper import PiperVoice
            from piper.config import PiperConfig
            configuracion = json.loads((self.raiz / "piper" / voz["configuracion"]).read_text(encoding="utf-8"))
            sesion = ort.InferenceSession(str(self.raiz / "piper" / voz["modelo"]),
                                         sess_options=opciones, providers=["CPUExecutionProvider"])
            # Constructor de piper-tts 1.3.0; load() no permite SessionOptions.
            modelo = PiperVoice(session=sesion, config=PiperConfig.from_dict(configuracion))
        else:
            from kokoro_onnx import Kokoro
            sesion = ort.InferenceSession(str(self.raiz / "kokoro" / voz["modelo"]),
                                         sess_options=opciones, providers=["CPUExecutionProvider"])
            modelo = Kokoro.from_session(sesion, str(self.raiz / "kokoro" / voz["pack"]))
            modelo.sess = SesionONNXTipada(sesion)
        self.modelos[clave] = modelo
        return modelo

    def _audio_cache(self, clave):
        with self.lock_cache:
            if clave in self.cache:
                self.cache.move_to_end(clave)
                return self.cache[clave]
        return None

    def sintetizar(self, voz_id: str, texto: str, idioma: str, *, vigente=None) -> bytes:
        voz = self.voces.get(voz_id) if isinstance(voz_id, str) else None
        if not voz or idioma != ("es" if voz["idioma"] == "es" else "pt-BR"):
            raise ValueError("Selecciona una voz válida para este idioma.")
        if not texto or len(texto) > 2000:
            raise ValueError("Texto de voz no válido.")
        def comprobar():
            if vigente is not None and not vigente():
                raise LecturaCancelada()

        comprobar()
        clave = (voz_id, texto)
        contenido = self._audio_cache(clave)
        if contenido is not None:
            return contenido
        with self.lock:
            # Las peticiones canceladas mientras esperaban no cargan modelos
            # ni generan WAV. Una inferencia ONNX ya iniciada debe terminar.
            comprobar()
            contenido = self._audio_cache(clave)
            if contenido is not None:
                return contenido
            if not self._disponible(voz):
                raise VozNoDisponible("No hay voces preparadas para este idioma. Abre iniciar_juego.bat para descargar los modelos.")
            try:
                modelo = self._modelo(voz)
                comprobar()
                archivo = io.BytesIO()
                if voz["motor"] == "piper":
                    with wave.open(archivo, "wb") as wav:
                        modelo.synthesize_wav(texto, wav)
                else:
                    import numpy as np
                    audio, frecuencia = modelo.create(texto, voice=voz["voz"], speed=1.0, lang="es" if idioma == "es" else "pt-br")
                    with wave.open(archivo, "wb") as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(frecuencia)
                        wav.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
                contenido = archivo.getvalue()
            except LecturaCancelada:
                raise
            except Exception as exc:
                self.modelos.pop((voz["motor"], voz["modelo"]), None)
                raise VozNoDisponible("No se pudo generar la voz. Puedes volver a pulsar Repetir.") from exc
            with self.lock_cache:
                if len(contenido) <= self.max_cache_bytes:
                    self.cache[clave] = contenido
                    self.bytes_cache += len(contenido)
                    while self.bytes_cache > self.max_cache_bytes or len(self.cache) > 128:
                        _, anterior = self.cache.popitem(last=False)
                        self.bytes_cache -= len(anterior)
            comprobar()
            return contenido
