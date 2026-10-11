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
from codigo.interfaz import idiomas
from codigo.interfaz.voz import LecturaCancelada, MotorVoz, VozNoDisponible
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO
from codigo.nucleo.estado import TERMINALES


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
        self.voz = MotorVoz()
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
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; media-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        if getattr(self, "nueva_cookie", None):
            self.send_header("Set-Cookie", self.nueva_cookie)
        self.end_headers()
        try:
            self.wfile.write(contenido)
        except (BrokenPipeError, ConnectionResetError):
            # El navegador puede cancelar una descarga al pausar la lectura.
            pass

    def do_GET(self):
        ruta = urlsplit(self.path).path
        fijos = {"/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/estilos.css": ("estilos.css", "text/css; charset=utf-8"),
            "/expedicion.css": ("expedicion.css", "text/css; charset=utf-8"),
            "/mundo.svg": ("mundo.svg", "image/svg+xml"),
            "/zoonauta-logo.svg": ("zoonauta-logo.svg", "image/svg+xml"),
            "/portada-selva.webp": ("portada-selva.webp", "image/webp"),
            "/paisajes.webp": ("paisajes.webp", "image/webp"),
            "/revision": ("revision.html", "text/html; charset=utf-8"),
            "/revision.js": ("revision.js", "text/javascript; charset=utf-8")}
        if ruta in fijos:
            archivo, mime = fijos[ruta]
            self._enviar((Path(__file__).parent / "web" / archivo).read_bytes(), mime)
        elif ruta.startswith("/animales/") and ruta.removeprefix("/animales/") in {f"A{i:02}.webp" for i in range(1, 49)}:
            self._enviar((RAIZ_PROYECTO / "assets" / "animales" / ruta.removeprefix("/animales/")).read_bytes(), "image/webp")
        elif ruta.startswith("/fondos/") and ruta.removeprefix("/fondos/") in {f"H0{i}.webp" for i in range(2, 9)}:
            self._enviar((Path(__file__).parent / "web" / ruta.lstrip("/")).read_bytes(), "image/webp")
        elif ruta.startswith("/habitats/") and ruta.removeprefix("/habitats/") in {f"H0{i}.webp" for i in range(1, 9)}:
            self._enviar((RAIZ_PROYECTO / "assets" / "paisajes" / ruta.removeprefix("/habitats/")).read_bytes(), "image/webp")
        elif ruta == "/api/vista":
            self._enviar(self._sesion().vista())
        elif ruta == "/api/revision":
            self._enviar(self._sesion().revision_tecnica())
        elif ruta == "/api/idiomas":
            self._enviar({"es": {}, "pt-BR": idiomas.PORTUGUES["interfaz"]})
        elif ruta == "/api/voz/config":
            self._enviar(self.server.voz.configuracion())
        elif ruta.startswith("/media/"):
            picto = self.server.banco.pictogramas.get(ruta.removeprefix("/media/"))
            if not picto:
                return self._enviar({"error": "Recurso no encontrado."}, codigo=404)
            archivo = (RAIZ_PROYECTO / picto["archivo_imagen"]).resolve()
            if not archivo.is_relative_to(RAIZ_PROYECTO / "assets"):
                return self._enviar({"error": "Recurso no permitido."}, codigo=404)
            mime = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp"}[archivo.suffix]
            self._enviar(archivo.read_bytes(), mime)
        else:
            self._enviar({"error": "Ruta no encontrada."}, codigo=404)

    def do_POST(self):
        ruta = urlsplit(self.path).path
        if ruta not in {"/api/accion", "/api/idioma", "/api/voz", "/api/voz/cancelar"}:
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
            if not isinstance(entrada, dict):
                raise ValueError("La entrada debe ser un objeto JSON.")
            if ruta == "/api/voz/cancelar":
                sesion.lecturas_voz.registrar(entrada.get("canal_voz"), entrada.get("turno_voz"))
                self._enviar({"cancelada": True})
            elif ruta == "/api/idioma":
                self._enviar({"vista": sesion.cambiar_idioma(entrada)})
            elif ruta == "/api/voz":
                if "texto" in entrada or "texto_voz" in entrada:
                    raise ValueError("La voz solo puede leer contenido de la partida.")
                texto = sesion.texto_voz(entrada)
                argumentos = {}
                if "canal_voz" in entrada or "turno_voz" in entrada:
                    canal, turno = entrada.get("canal_voz"), entrada.get("turno_voz")
                    sesion.lecturas_voz.registrar(canal, turno)
                    def vigente():
                        if not sesion.lecturas_voz.vigente(canal, turno):
                            return False
                        try:
                            sesion.texto_voz(entrada)
                        except ConflictoVista:
                            return False
                        return True
                    argumentos["vigente"] = vigente
                audio = self.server.voz.sintetizar(entrada.get("voz"), texto, entrada.get("idioma"), **argumentos)
                # La inferencia no mantiene el bloqueo de la partida. Comprobar
                # de nuevo evita entregar audio de una pantalla ya abandonada.
                if argumentos and not vigente():
                    raise LecturaCancelada()
                sesion.texto_voz(entrada)
                self._enviar(audio, "audio/wav")
            else:
                self._enviar(sesion.actuar(entrada))
        except LecturaCancelada:
            self._enviar({"cancelada": True}, codigo=409)
        except ConflictoVista as e:
            self._enviar({"error": idiomas.error(str(e), sesion.idioma), "vista": sesion.vista()}, codigo=409)
        except VozNoDisponible as e:
            mensaje = idiomas.PORTUGUES["interfaz"].get(str(e), str(e)) if sesion.idioma == "pt-BR" else str(e)
            self._enviar({"error": mensaje}, codigo=503)
        except (ValueError, TypeError, KeyError) as e:
            self._enviar({"error": idiomas.error(str(e), sesion.idioma), "vista": sesion.vista()}, codigo=400)


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
    print(f"Zoonauta 3.8.0: {url}\nCarpeta: {RAIZ_PROYECTO}\nRevisión técnica: {url}/revision\nCtrl+C para detener.", flush=True)
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
