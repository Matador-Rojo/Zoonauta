"""Adaptador WSGI sin dependencias externas para PythonAnywhere, Gunicorn y Hostinger.

Uso en PythonAnywhere (/var/www/<usuario>_pythonanywhere_com_wsgi.py):
    import sys
    sys.path.insert(0, '/home/<usuario>/Zoonauta-Web')
    from codigo.interfaz.wsgi import application
"""
from __future__ import annotations

from email.message import Message
from http import HTTPStatus
import io
from pathlib import Path

from codigo.interfaz.servidor import Manejador, NucleoServidor
from codigo.interfaz.servicio import MODELO_DEMO
from codigo.motores.agente import POLITICA_AGENTE
from codigo.nucleo.datos import RAIZ_PROYECTO


class _EstadoWSGI(NucleoServidor):
    def __init__(self, *, registros: Path | None = None, politica: str = "PROBABILISTICO",
                 parametros=MODELO_DEMO, ampliado: bool = True, agente: str = POLITICA_AGENTE,
                 modelo_agente=None):
        self._inicializar_estado(registros=registros, politica=politica, parametros=parametros,
                                 ampliado=ampliado, agente=agente, modelo_agente=modelo_agente)


def _cabeceras_desde_environ(environ: dict) -> Message:
    cab = Message()
    for clave, valor in environ.items():
        if clave.startswith("HTTP_"):
            nombre = clave[5:].replace("_", "-").title()
            cab[nombre] = str(valor)
    if environ.get("CONTENT_TYPE"):
        cab["Content-Type"] = str(environ["CONTENT_TYPE"])
    if environ.get("CONTENT_LENGTH"):
        cab["Content-Length"] = str(environ["CONTENT_LENGTH"])
    if "Host" not in cab and environ.get("SERVER_NAME"):
        puerto = str(environ.get("SERVER_PORT", ""))
        esquema = str(environ.get("wsgi.url_scheme", "http"))
        defecto = (esquema == "http" and puerto == "80") or (esquema == "https" and puerto == "443")
        cab["Host"] = environ["SERVER_NAME"] if (not puerto or defecto) else f"{environ['SERVER_NAME']}:{puerto}"
    if "X-Forwarded-Proto" not in cab and environ.get("wsgi.url_scheme"):
        cab["X-Forwarded-Proto"] = str(environ["wsgi.url_scheme"])
    return cab


class _ManejadorWSGI(Manejador):
    """Reutiliza toda la lógica de Manejador sobre una petición WSGI en memoria."""

    def __init__(self, estado: _EstadoWSGI, environ: dict):
        self.server = estado  # type: ignore[assignment]
        self.command = str(environ.get("REQUEST_METHOD", "GET")).upper()
        ruta = str(environ.get("PATH_INFO", "/") or "/")
        consulta = str(environ.get("QUERY_STRING", ""))
        self.path = f"{ruta}?{consulta}" if consulta else ruta
        self.headers = _cabeceras_desde_environ(environ)
        largo = int(environ.get("CONTENT_LENGTH") or 0)
        flujo = environ.get("wsgi.input")
        cuerpo = flujo.read(largo) if (flujo is not None and largo > 0) else b""
        self.rfile = io.BytesIO(cuerpo)
        self.wfile = io.BytesIO()
        self._codigo = 200
        self._cabeceras_salida: list[tuple[str, str]] = []
        self.nueva_cookie = None

    def send_response(self, code: int, message: str | None = None):
        self._codigo = int(code)

    def send_header(self, keyword: str, value: str):
        self._cabeceras_salida.append((str(keyword), str(value)))

    def end_headers(self):
        pass

    def ejecutar(self) -> tuple[str, list[tuple[str, str]], bytes]:
        if self.command == "GET":
            self.do_GET()
        elif self.command == "HEAD":
            self.do_GET()
            return self._estado_http(), self._cabeceras_salida, b""
        elif self.command == "POST":
            self.do_POST()
        else:
            self._enviar({"error": "Método no permitido."}, codigo=405)
        return self._estado_http(), self._cabeceras_salida, self.wfile.getvalue()

    def _estado_http(self) -> str:
        try:
            frase = HTTPStatus(self._codigo).phrase
        except ValueError:
            frase = "OK"
        return f"{self._codigo} {frase}"


def crear_aplicacion(*, registros: Path | None = None, ampliado: bool = True,
                     agente: str = POLITICA_AGENTE, modelo_agente=None):
    """Construye una aplicación WSGI callable lista para PythonAnywhere o Gunicorn."""
    carpeta_reg = registros if registros is not None else (RAIZ_PROYECTO / "registros/interfaz")
    estado = _EstadoWSGI(registros=carpeta_reg, ampliado=ampliado, agente=agente,
                         modelo_agente=modelo_agente)

    def application(environ, start_response):
        manejador = _ManejadorWSGI(estado, environ)
        status, headers, body = manejador.ejecutar()
        start_response(status, headers)
        return [body]

    application.estado = estado  # type: ignore[attr-defined]
    return application


_APLICACION_POR_DEFECTO = None


def application(environ, start_response):
    """Punto de entrada WSGI estándar con carga diferida del banco de datos."""
    global _APLICACION_POR_DEFECTO
    if _APLICACION_POR_DEFECTO is None:
        _APLICACION_POR_DEFECTO = crear_aplicacion()
    return _APLICACION_POR_DEFECTO(environ, start_response)
