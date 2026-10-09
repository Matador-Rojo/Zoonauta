"""Servidor local sin dependencias. Ejecutar: python -m codigo.interfaz.servidor."""
from __future__ import annotations

import argparse
import json
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit
from uuid import uuid4
import webbrowser

from codigo.interfaz.servicio import ConflictoVista, MODELO_DEMO, SesionWeb
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO


class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, direccion, *, registros=None, politica="PROBABILISTICO",
                 parametros=MODELO_DEMO):
        self.banco = BancoDatos()
        for p in self.banco.pictogramas.values():
            archivo = p.get("archivo_imagen")
            if not archivo or not (RAIZ_PROYECTO / archivo).is_file():
                raise ValueError(f"Falta el recurso visual {p['id']}.")
        self.sesiones = {}
        self.lock = RLock()
        self.registros, self.politica, self.parametros = registros, politica, parametros
        super().__init__(direccion, Manejador)


class Manejador(BaseHTTPRequestHandler):
    server: Servidor

    def log_message(self, formato, *args):
        # No se imprimen cookies, identificadores ni contenido educativo.
        if args and str(args[1] if len(args) > 1 else "").startswith("5"):
            super().log_message(formato, *args)

    def _sesion(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        sid = cookie["habitats"].value if "habitats" in cookie else None
        with self.server.lock:
            if sid not in self.server.sesiones:
                sid = uuid4().hex
                self.server.sesiones[sid] = SesionWeb(self.server.banco,
                    self.server.registros, self.server.politica, self.server.parametros)
                self.nueva_cookie = f"habitats={sid}; HttpOnly; SameSite=Strict; Path=/"
            return self.server.sesiones[sid]

    def _enviar(self, contenido, tipo="application/json; charset=utf-8", codigo=200):
        if not isinstance(contenido, bytes):
            contenido = json.dumps(contenido, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        if getattr(self, "nueva_cookie", None):
            self.send_header("Set-Cookie", self.nueva_cookie)
        self.end_headers()
        self.wfile.write(contenido)

    def do_GET(self):
        ruta = urlsplit(self.path).path
        fijos = {"/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/estilos.css": ("estilos.css", "text/css; charset=utf-8"),
            "/revision": ("revision.html", "text/html; charset=utf-8"),
            "/revision.js": ("revision.js", "text/javascript; charset=utf-8")}
        if ruta in fijos:
            archivo, mime = fijos[ruta]
            self._enviar((Path(__file__).parent / "web" / archivo).read_bytes(), mime)
        elif ruta == "/api/vista":
            self._enviar(self._sesion().vista())
        elif ruta == "/api/revision":
            self._enviar(self._sesion().revision_tecnica())
        elif ruta.startswith("/media/"):
            picto = self.server.banco.pictogramas.get(ruta.removeprefix("/media/"))
            if not picto:
                return self._enviar({"error": "Recurso no encontrado."}, codigo=404)
            archivo = (RAIZ_PROYECTO / picto["archivo_imagen"]).resolve()
            if not archivo.is_relative_to(RAIZ_PROYECTO / "assets"):
                return self._enviar({"error": "Recurso no permitido."}, codigo=404)
            mime = "image/svg+xml" if archivo.suffix == ".svg" else "image/png"
            self._enviar(archivo.read_bytes(), mime)
        else:
            self._enviar({"error": "Ruta no encontrada."}, codigo=404)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/accion":
            return self._enviar({"error": "Ruta no encontrada."}, codigo=404)
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            return self._enviar({"error": "Origen no permitido."}, codigo=403)
        sesion = self._sesion()
        try:
            longitud = int(self.headers.get("Content-Length", "0"))
            if not 0 < longitud <= 8192:
                raise ValueError("Tamaño de acción no válido.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("La acción debe ser JSON.")
            entrada = json.loads(self.rfile.read(longitud))
            self._enviar(sesion.actuar(entrada))
        except ConflictoVista as e:
            self._enviar({"error": str(e), "vista": sesion.vista()}, codigo=409)
        except (ValueError, TypeError, KeyError) as e:
            self._enviar({"error": str(e), "vista": sesion.vista()}, codigo=400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--abrir", action="store_true")
    parser.add_argument("--politica", choices=["ID3", "ROTACION", "PROBABILISTICO"], default="PROBABILISTICO")
    parser.add_argument("--parametros", type=Path, default=MODELO_DEMO)
    parser.add_argument("--registros", type=Path, default=RAIZ_PROYECTO / "registros/interfaz")
    args = parser.parse_args()
    servidor = Servidor(("127.0.0.1", args.puerto), registros=args.registros,
                         politica=args.politica, parametros=args.parametros)
    url = f"http://127.0.0.1:{servidor.server_port}"
    print(f"Zoonauta: {url}\nRevisión técnica: {url}/revision\nCtrl+C para detener.", flush=True)
    if args.abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        # Las ayudas abiertas al detener el servidor se cierran sin etiqueta.
        for sesion in list(servidor.sesiones.values()):
            with sesion.lock:
                if sesion.gestor.estado.fase not in TERMINALES:
                    sesion.gestor.procesar(sesion.gestor.crear_evento("salir"))
        servidor.server_close()


if __name__ == "__main__":
    main()
