/* Service Worker de Zoonauta 6.0 (PWA instalable).
 * - Cache-first para los activos compilados con huella (/v6/assets/) y el logotipo.
 * - Network-first con respaldo en caché para imágenes de animales, hábitats y robot.
 * - Nunca intercepta /api/ ni la navegación HTML para preservar la autoridad del servidor Python. */
const CACHE = "zoonauta-v6.3-estaticos";
const INMUTABLES = ["/v6/assets/", "/zoonauta-logo.svg"];
const IMAGENES = ["/media/", "/animales/", "/habitats/", "/ilustraciones/"];

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((claves) => Promise.all(claves.filter((c) => c !== CACHE).map((c) => caches.delete(c))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (evento) => {
  const { request } = evento;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (INMUTABLES.some((p) => url.pathname.startsWith(p))) {
    evento.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const guardado = await cache.match(request);
        if (guardado) return guardado;
        const respuesta = await fetch(request);
        if (respuesta.ok) void cache.put(request, respuesta.clone());
        return respuesta;
      }),
    );
    return;
  }

  if (IMAGENES.some((p) => url.pathname.startsWith(p))) {
    evento.respondWith(
      caches.open(CACHE).then(async (cache) => {
        try {
          const respuesta = await fetch(request);
          if (respuesta.ok) void cache.put(request, respuesta.clone());
          return respuesta;
        } catch {
          const guardado = await cache.match(request);
          if (guardado) return guardado;
          throw new Error("Sin conexión");
        }
      }),
    );
  }
});
