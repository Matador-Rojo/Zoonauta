"""Servidor local sin dependencias. Ejecutar: python -m codigo.interfaz.servidor."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit
from uuid import uuid4
import webbrowser

from codigo.interfaz.servicio import ConflictoVista, MODELO_DEMO, POLITICAS_6, SesionWeb
from codigo.motores.agente import POLITICA_AGENTE
from codigo.motores.aprendizaje6 import POLITICA_APRENDIDA, MotorAgenteAprendido
from codigo.interfaz import idiomas, voz_grabada
from codigo.nucleo.datos import BancoDatos, RAIZ_PROYECTO
from codigo.nucleo.estado import TERMINALES

CACHE_MEDIOS = "public, max-age=604800"
CACHE_VOZ = "private, max-age=86400"
TIPOS_COMPRIMIBLES = (
    "application/json",
    "text/html",
    "text/javascript",
    "text/css",
    "image/svg+xml",
    "application/manifest+json",
)
TTL_SESION_SEG = 7200
MAX_SESIONES = 500

FONDOS_PORTADA = {f"H{i:02}.webp" for i in range(1, 49)}
FONDOS_HISTORICOS = {f"H0{i}.webp" for i in range(2, 9)}
# Versiones de 960 px de los ocho paisajes de la portada 6.0 (derivadas de fondos/catalogo).
FONDOS_PORTADA_960 = {f"{h}-{ancho}.webp" for h in ("H01", "H09", "H17", "H22", "H20", "H37", "H21", "H25")
                     for ancho in (960, 160)}
# Capas con transparencia superpuestas a cinco paisajes (ver fondos/capas/procedencia.json).
CAPAS_PORTADA = {f"{c}.webp" for c in ("H01-hojas", "H01-niebla", "H09-hierba", "H20-nubes", "H37-algas")}
WEB6 = (Path(__file__).parent / "web6").resolve()
TIPOS_V6 = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".webp": "image/webp",
            ".woff2": "font/woff2"}


def _ligeros(carpeta: str) -> dict[str, Path]:
    indice = RAIZ_PROYECTO / "assets" / carpeta / "indice.json"
    if not indice.is_file():
        return {}
    return {clave: RAIZ_PROYECTO / "assets" / carpeta / f"{clave}.webp"
            for clave in json.loads(indice.read_text("utf-8"))["items"]}


def _ligero_o_original(ligeros: dict[str, Path], clave: str, original: Path) -> Path:
    copia = ligeros.get(clave)
    return copia if copia is not None and copia.is_file() else original


# Precarga del primer paisaje (y su capa) en index.html de la 6.0: solo se envía
# cuando la sesión está en la portada (en otras pantallas descargaría 338 KB inútiles).
PRECARGA_PORTADA = re.compile(rb"\s*<!-- portada:inicio.*?<!-- portada:fin -->", re.S)


class NucleoServidor:
    """Estado compartido del juego (banco, recursos ligeros y sesiones), reusable en HTTP y WSGI."""

    def _inicializar_estado(self, *, registros=None, politica="PROBABILISTICO",
                            parametros=MODELO_DEMO, ampliado=True, agente=POLITICA_AGENTE,
                            modelo_agente=None):
        self.banco = BancoDatos(ampliado=ampliado)
        # Copias ligeras (ver preparar_imagenes_ligeras): pictogramas, paisajes de las
        # tarjetas y robot. Si falta alguna, se sirve el original.
        self.pictogramas_ligeros = _ligeros("pictogramas_ligeros")
        self.paisajes_ligeros = _ligeros("paisajes_ligeros")
        self.ilustraciones_ligeras = _ligeros("ilustraciones_ligeras")
        for p in self.banco.pictogramas.values():
            archivo = p.get("archivo_imagen")
            ligero = self.pictogramas_ligeros.get(p["id"])
            tiene_original = bool(archivo and (RAIZ_PROYECTO / archivo).is_file())
            tiene_ligero = bool(ligero is not None and ligero.is_file())
            if not (tiene_original or tiene_ligero):
                raise ValueError(f"Falta el recurso visual {p['id']}.")
        self.imagenes_habitat = {f"{h}.webp": (RAIZ_PROYECTO / datos["paisaje"]
            if ampliado else RAIZ_PROYECTO / f"assets/paisajes/{h}.webp")
            for h, datos in self.banco.habitats.items()}
        for nombre, archivo in self.imagenes_habitat.items():
            clave = nombre.removesuffix(".webp")
            ligero = self.paisajes_ligeros.get(clave)
            if not (archivo.is_file() or (ligero is not None and ligero.is_file())):
                raise ValueError("Falta un paisaje del catálogo.")
        self.imagenes_animal = {f"{a['id']}.webp": (
            a["pictograma_id"],
            RAIZ_PROYECTO / self.banco.pictogramas[a["pictograma_id"]]["archivo_imagen"],
        ) for a in self.banco.animales.values()}
        self.sesiones = {}
        self.ultimo_acceso: dict[str, float] = {}
        self.lock = RLock()
        self.registros, self.politica, self.parametros = registros, politica, parametros
        self.agente, self.modelo_agente = agente, modelo_agente
        if agente == POLITICA_APRENDIDA:
            MotorAgenteAprendido(self.banco, modelo_agente)  # falla al arrancar, no en la primera partida


class Servidor(NucleoServidor, ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, direccion, *, registros=None, politica="PROBABILISTICO",
                 parametros=MODELO_DEMO, ampliado=True, agente=POLITICA_AGENTE, modelo_agente=None):
        self._inicializar_estado(registros=registros, politica=politica, parametros=parametros,
                                 ampliado=ampliado, agente=agente, modelo_agente=modelo_agente)
        super().__init__(direccion, Manejador)


class Manejador(BaseHTTPRequestHandler):
    server: Servidor

    def log_message(self, formato, *args):
        # No se imprimen cookies, identificadores ni contenido educativo.
        if args and str(args[1] if len(args) > 1 else "").startswith("5"):
            super().log_message(formato, *args)

    def _es_https(self) -> bool:
        proto = self.headers.get("X-Forwarded-Proto", "").split(",")[0].strip().lower()
        return proto == "https"

    def _origen_valido(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        hosts = {
            h.split(",")[0].strip().lower()
            for h in (self.headers.get("Host", ""), self.headers.get("X-Forwarded-Host", ""))
            if h and h.strip()
        }
        permitidos = {f"{esquema}://{host}" for esquema in ("http", "https") for host in hosts}
        return origin.rstrip("/").lower() in permitidos

    def _limpiar_sesiones(self, ahora: float):
        expiradas = [k for k, t in self.server.ultimo_acceso.items() if ahora - t > TTL_SESION_SEG]
        for k in expiradas:
            self.server.sesiones.pop(k, None)
            self.server.ultimo_acceso.pop(k, None)
        while len(self.server.sesiones) >= MAX_SESIONES and self.server.ultimo_acceso:
            mas_vieja = min(self.server.ultimo_acceso, key=self.server.ultimo_acceso.get)
            self.server.sesiones.pop(mas_vieja, None)
            self.server.ultimo_acceso.pop(mas_vieja, None)

    def _sesion(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            pass
        sid = cookie["habitats"].value if "habitats" in cookie else None
        ahora = time.monotonic()
        with self.server.lock:
            if sid not in self.server.sesiones:
                self._limpiar_sesiones(ahora)
                sid = uuid4().hex
                self.server.sesiones[sid] = SesionWeb(self.server.banco,
                    self.server.registros, self.server.politica, self.server.parametros,
                    agente=self.server.agente, modelo_agente=self.server.modelo_agente)
                seguro = "; Secure" if self._es_https() else ""
                self.nueva_cookie = f"habitats={sid}; HttpOnly; SameSite=Strict; Path=/{seguro}"
            self.server.ultimo_acceso[sid] = ahora
            return self.server.sesiones[sid]

    def _enviar(self, contenido, tipo="application/json; charset=utf-8", codigo=200,
                cache="no-store", etag=False):
        if not isinstance(contenido, bytes):
            contenido = json.dumps(contenido, ensure_ascii=False).encode()
        tag = None
        if etag and codigo == 200:
            tag = f'"{hashlib.sha256(contenido).hexdigest()[:16]}"'
            if self.headers.get("If-None-Match") == tag:
                self.send_response(304)
                self.send_header("ETag", tag)
                self.send_header("Cache-Control", cache)
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                return
        comprimido = False
        if (codigo == 200 and len(contenido) >= 512
                and tipo.startswith(TIPOS_COMPRIMIBLES)
                and "gzip" in self.headers.get("Accept-Encoding", "").lower()):
            contenido = gzip.compress(contenido, compresslevel=6)
            comprimido = True
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", cache)
        if tag:
            self.send_header("ETag", tag)
        if comprimido:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self'; media-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; worker-src 'self'; manifest-src 'self'; frame-ancestors 'none'")
        if getattr(self, "nueva_cookie", None):
            self.send_header("Set-Cookie", self.nueva_cookie)
        self.end_headers()
        try:
            self.wfile.write(contenido)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # El navegador puede cancelar una descarga al pausar la lectura.
            pass

    def _enviar_v6(self, ruta):
        """Interfaz 6.0 compilada con Vite (frontend/ → web6/). No requiere Node para jugar."""
        if ruta in ("/v6", "/v6/"):
            archivo = WEB6 / "index.html"
        else:
            archivo = (WEB6 / ruta.removeprefix("/v6/")).resolve()
            if not archivo.is_relative_to(WEB6 / "assets"):
                return self._enviar({"error": "Ruta no encontrada."}, codigo=404)
        mime = TIPOS_V6.get(archivo.suffix)
        if not mime or not archivo.is_file():
            return self._enviar({"error": "Ruta no encontrada."}, codigo=404)
        if archivo.name == "index.html":
            contenido = archivo.read_bytes()
            if self._sesion().vista()["fase"] != "INICIO":
                contenido = PRECARGA_PORTADA.sub(b"", contenido)
            return self._enviar(contenido, mime)
        # Los compilados llevan una huella en el nombre: pueden guardarse para siempre.
        self._enviar(archivo.read_bytes(), mime, cache="public, max-age=31536000, immutable")

    def do_GET(self):
        ruta = urlsplit(self.path).path
        # Desde el 2026-11-14 la 6.0 es la versión principal («/»); la 5.0 sigue en «/v5/».
        # Las dos comparten API y sesión; sus recursos usan rutas absolutas.
        fijos = {"/v5": ("index.html", "text/html; charset=utf-8"),
            "/v5/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/estilos.css": ("estilos.css", "text/css; charset=utf-8"),
            "/expedicion.css": ("expedicion.css", "text/css; charset=utf-8"),
            "/mundo.svg": ("mundo.svg", "image/svg+xml"),
            "/zoonauta-logo.svg": ("zoonauta-logo.svg", "image/svg+xml"),
            "/portada-selva.webp": ("portada-selva.webp", "image/webp"),
            "/paisajes.webp": ("paisajes.webp", "image/webp"),
            "/revision": ("revision.html", "text/html; charset=utf-8"),
            "/revision.css": ("revision.css", "text/css; charset=utf-8"),
            "/revision.js": ("revision.js", "text/javascript; charset=utf-8"),
            "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"),
            "/sw.js": ("sw.js", "text/javascript; charset=utf-8")}
        if ruta in fijos:
            archivo, mime = fijos[ruta]
            ruta_web = Path(__file__).parent / "web" / archivo
            if not ruta_web.is_file():
                return self._enviar({"error": "Ruta no encontrada."}, codigo=404)
            es_media = archivo.endswith((".svg", ".webp"))
            self._enviar(ruta_web.read_bytes(), mime, cache=CACHE_MEDIOS if es_media else "no-store", etag=es_media)
        elif ruta == "/healthz":
            self._enviar({"ok": True, "sesiones": len(self.server.sesiones)})
        elif ruta == "/":
            self._enviar_v6("/v6/")
        elif ruta in ("/v6", "/v6/") or ruta.startswith("/v6/assets/"):
            self._enviar_v6(ruta)
        elif ruta.startswith("/animales/") and ruta.removeprefix("/animales/") in self.server.imagenes_animal:
            picto_id, original = self.server.imagenes_animal[ruta.removeprefix("/animales/")]
            archivo = _ligero_o_original(self.server.pictogramas_ligeros, picto_id, original)
            self._enviar(archivo.read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta.startswith("/fondos/capas/") and ruta.removeprefix("/fondos/capas/") in CAPAS_PORTADA:
            self._enviar((Path(__file__).parent / "web" / ruta.lstrip("/")).read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta.startswith("/fondos/portada/") and ruta.removeprefix("/fondos/portada/") in FONDOS_PORTADA_960:
            self._enviar((Path(__file__).parent / "web" / ruta.lstrip("/")).read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta.startswith("/fondos/catalogo/") and ruta.removeprefix("/fondos/catalogo/") in FONDOS_PORTADA:
            self._enviar((Path(__file__).parent / "web" / ruta.lstrip("/")).read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta.startswith("/fondos/") and ruta.removeprefix("/fondos/") in FONDOS_HISTORICOS:
            self._enviar((Path(__file__).parent / "web" / ruta.lstrip("/")).read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta.startswith("/habitats/") and ruta.removeprefix("/habitats/") in self.server.imagenes_habitat:
            nombre = ruta.removeprefix("/habitats/")
            archivo = _ligero_o_original(self.server.paisajes_ligeros, nombre.removesuffix(".webp"),
                                         self.server.imagenes_habitat[nombre])
            self._enviar(archivo.read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta in ("/ilustraciones/robot_despedida.webp", "/ilustraciones/robot_pausa.webp"):
            nombre = ruta.removeprefix("/ilustraciones/")
            archivo = _ligero_o_original(self.server.ilustraciones_ligeras, nombre.removesuffix(".webp"),
                                         RAIZ_PROYECTO / "assets" / "ilustraciones" / nombre)
            self._enviar(archivo.read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
        elif ruta == "/api/vista":
            self._enviar(self._sesion().vista())
        elif ruta == "/api/revision":
            self._enviar(self._sesion().revision_tecnica())
        elif ruta == "/api/idiomas":
            self._enviar(
                {"es": {}, "pt-BR": idiomas.PORTUGUES["interfaz"], "en": idiomas.INGLES["interfaz"]},
                cache=CACHE_MEDIOS,
                etag=True,
            )
        elif ruta == "/api/voz/config":
            # Voces grabadas de Zoonauta (sin voces sintetizadas).
            # «voces» se mantiene (vacía) por compatibilidad con los clientes 5.0 y 6.0.
            self._enviar({
                "voces": [],
                "grabadas": voz_grabada.disponibles(self.server.banco),
                "voces_grabadas": voz_grabada.voces_disponibles(self.server.banco),
            })
        elif ruta.startswith("/media/"):
            picto = self.server.banco.pictogramas.get(ruta.removeprefix("/media/"))
            if not picto:
                return self._enviar({"error": "Recurso no encontrado."}, codigo=404)
            ligero = self.server.pictogramas_ligeros.get(picto["id"])
            if ligero is not None and ligero.is_file():
                return self._enviar(ligero.read_bytes(), "image/webp", cache=CACHE_MEDIOS, etag=True)
            archivo = (RAIZ_PROYECTO / picto["archivo_imagen"]).resolve()
            if not archivo.is_relative_to(RAIZ_PROYECTO / "assets"):
                return self._enviar({"error": "Recurso no permitido."}, codigo=404)
            mime = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp"}[archivo.suffix]
            self._enviar(archivo.read_bytes(), mime, cache=CACHE_MEDIOS, etag=True)
        else:
            self._enviar({"error": "Ruta no encontrada."}, codigo=404)

    def do_POST(self):
        ruta = urlsplit(self.path).path
        if ruta not in {"/api/accion", "/api/idioma", "/api/voz/grabada"}:
            return self._enviar({"error": "Ruta no encontrada."}, codigo=404)
        if not self._origen_valido():
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
            if ruta == "/api/idioma":
                self._enviar({"vista": sesion.cambiar_idioma(entrada)})
            elif ruta == "/api/voz/grabada":
                # Grabación completa del mensaje exacto (nunca se unen audios). Sin ella, la 6.0
                # no lee ese mensaje; la 5.0 lo lee con una voz del navegador si la hay.
                if "texto" in entrada or "texto_voz" in entrada or entrada.get("prueba"):
                    raise ValueError("La voz solo puede leer contenido de la partida.")
                voz_id = entrada.get("voz")
                if voz_id is not None and not isinstance(voz_id, str):
                    raise ValueError("Identificador de voz no válido.")
                archivo = voz_grabada.buscar(
                    sesion.texto_voz(entrada), sesion.idioma, self.server.banco, voz=voz_id
                )
                if archivo is None:
                    self._enviar({"grabada": False}, codigo=404)
                else:
                    self._enviar(archivo.read_bytes(), voz_grabada.TIPOS[archivo.suffix], cache=CACHE_VOZ)
            else:
                self._enviar(sesion.actuar(entrada))
        except ConflictoVista as e:
            self._enviar({"error": idiomas.error(str(e), sesion.idioma), "vista": sesion.vista()}, codigo=409)
        except (ValueError, TypeError, KeyError) as e:
            self._enviar({"error": idiomas.error(str(e), sesion.idioma), "vista": sesion.vista()}, codigo=400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"),
                        help="Interfaz de escucha (usa 0.0.0.0 en servidor web/Docker).")
    parser.add_argument("--puerto", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--abrir", action="store_true")
    parser.add_argument("--catalogo-original", action="store_true",
                        help="Abre el banco experimental de 48 animales y ocho hábitats.")
    parser.add_argument("--politica", choices=["ID3", "ROTACION", "PROBABILISTICO"], default="PROBABILISTICO",
                        help="Política de guía para el catálogo original.")
    parser.add_argument("--parametros", type=Path, default=MODELO_DEMO,
                        help="Modelo de guía para el catálogo original.")
    parser.add_argument("--agente", choices=POLITICAS_6, default=POLITICA_AGENTE,
                        help="Quién elige las pistas con el catálogo ampliado (por defecto, el agente "
                             "adaptativo; ID3_OPCIONES y PISTAS_PROGRESIVAS sirven para comparar).")
    parser.add_argument("--modelo-agente", type=Path, default=None,
                        help="Con --agente AGENTE_APRENDIDO: modelo congelado (por defecto, el de "
                             "demostración entrenado con jugadores simulados).")
    parser.add_argument("--registros", type=Path, default=RAIZ_PROYECTO / "registros/interfaz")
    args = parser.parse_args()
    if args.modelo_agente and args.agente != POLITICA_APRENDIDA:
        parser.error("--modelo-agente solo se usa con --agente AGENTE_APRENDIDO.")
    servidor = Servidor((args.host, args.puerto), registros=args.registros,
                         politica=args.politica, parametros=args.parametros,
                         ampliado=not args.catalogo_original, agente=args.agente,
                         modelo_agente=args.modelo_agente)
    host_mostrar = "127.0.0.1" if args.host == "0.0.0.0" else args.host
    url = f"http://{host_mostrar}:{servidor.server_port}"
    print(f"Zoonauta 6.0.0: {url}  (5.0: {url}/v5/)\nCarpeta: {RAIZ_PROYECTO}\nRevisión técnica: {url}/revision\nCtrl+C para detener.", flush=True)
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
