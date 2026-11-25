import { useEffect, useRef, useState } from "react";
import type { TemaVisual } from "./Preferencias";

const SOLAPE_SEGUNDOS = 1.4;

interface RespuestaPortada {
  video?: string | null;
  videos?: Partial<Record<TemaVisual, string | null>>;
}

/**
 * Portada cinematográfica en video real con bucle invisible (doble reproductor en fundido cruzado):
 * - Reproduce el video 2K correspondiente al tema activo (noche, día o alto contraste)
 *   si existe en assets/portada/ (descubierto vía /api/portada).
 * - Cuando faltan ~1,4 s para el final, el segundo reproductor arranca desde 0 y hace un fundido
 *   cruzado suave sobre el primero, eliminando cualquier salto visual al reiniciar el bucle.
 * - Con «Reducir movimiento» se desmonta por completo y queda la imagen WebP estática del tema.
 */
export function PortadaViva({
  tema,
  poster,
  reducido,
  onVideoActivo,
}: {
  tema: TemaVisual;
  poster: string;
  reducido: boolean;
  onVideoActivo?: (activo: boolean) => void;
}) {
  const [videos, setVideos] = useState<Partial<Record<TemaVisual, string | null>>>({});
  const [activo, setActivo] = useState<0 | 1>(0);
  const [listoUrl, setListoUrl] = useState<string | null>(null);
  const ref0 = useRef<HTMLVideoElement>(null);
  const ref1 = useRef<HTMLVideoElement>(null);
  const activoRef = useRef<0 | 1>(0);
  const cambiando = useRef(false);

  const videoUrl = videos[tema] ?? null;
  const listo = Boolean(videoUrl && listoUrl === videoUrl);

  useEffect(() => {
    activoRef.current = activo;
  }, [activo]);

  useEffect(() => {
    if (reducido) {
      onVideoActivo?.(false);
      return;
    }
    let vigente = true;
    fetch("/api/portada", { headers: { Accept: "application/json" } })
      .then((r): Promise<RespuestaPortada> => (r.ok ? (r.json() as Promise<RespuestaPortada>) : Promise.resolve({})))
      .then((d) => {
        if (!vigente) return;
        const mapa: Partial<Record<TemaVisual, string | null>> = d.videos ?? { noche: d.video ?? null };
        setVideos(mapa);
      })
      .catch(() => {
        if (vigente) setVideos({});
      });
    return () => {
      vigente = false;
    };
  }, [reducido, onVideoActivo]);

  useEffect(() => {
    onVideoActivo?.(!reducido && Boolean(videoUrl));
  }, [reducido, videoUrl, onVideoActivo]);

  useEffect(() => {
    if (reducido || !videoUrl) return;
    const v0 = ref0.current;
    const v1 = ref1.current;
    if (!v0 || !v1) return;

    cambiando.current = false;
    activoRef.current = 0;

    const alVisibilidad = () => {
      const actual = activoRef.current === 0 ? v0 : v1;
      if (document.hidden) {
        v0.pause();
        v1.pause();
      } else {
        void actual.play().catch(() => undefined);
      }
    };
    document.addEventListener("visibilitychange", alVisibilidad);
    v1.pause();
    v0.currentTime = 0;
    void v0.play().catch(() => undefined);

    return () => {
      document.removeEventListener("visibilitychange", alVisibilidad);
      v0.pause();
      v1.pause();
    };
  }, [reducido, videoUrl]);

  const alAvanzar = (indice: 0 | 1) => {
    if (indice !== activoRef.current || cambiando.current) return;
    const actual = indice === 0 ? ref0.current : ref1.current;
    const siguiente = indice === 0 ? ref1.current : ref0.current;
    if (!actual || !siguiente || !Number.isFinite(actual.duration) || actual.duration <= SOLAPE_SEGUNDOS * 2) return;

    const restante = actual.duration - actual.currentTime;
    if (restante <= SOLAPE_SEGUNDOS) {
      cambiando.current = true;
      siguiente.currentTime = 0;
      void siguiente
        .play()
        .then(() => {
          setActivo(indice === 0 ? 1 : 0);
          window.setTimeout(() => {
            actual.pause();
            actual.currentTime = 0;
            cambiando.current = false;
          }, SOLAPE_SEGUNDOS * 1000);
        })
        .catch(() => {
          cambiando.current = false;
        });
    }
  };

  const alTerminar = (indice: 0 | 1) => {
    if (indice !== activoRef.current || cambiando.current) return;
    const v = indice === 0 ? ref0.current : ref1.current;
    if (v) {
      v.currentTime = 0;
      void v.play().catch(() => undefined);
    }
  };

  if (reducido || !videoUrl) return null;

  return (
    <div key={videoUrl} className="portada-viva-capa" data-listo={listo ? "true" : undefined} aria-hidden="true">
      <video
        ref={ref0}
        className="portada-video"
        data-visible={activo === 0 ? "true" : "false"}
        src={videoUrl}
        poster={poster}
        muted
        playsInline
        preload="auto"
        onPlaying={() => {
          setActivo(0);
          setListoUrl(videoUrl);
        }}
        onTimeUpdate={() => alAvanzar(0)}
        onEnded={() => alTerminar(0)}
      />
      <video
        ref={ref1}
        className="portada-video"
        data-visible={activo === 1 ? "true" : "false"}
        src={videoUrl}
        poster={poster}
        muted
        playsInline
        preload="auto"
        onTimeUpdate={() => alAvanzar(1)}
        onEnded={() => alTerminar(1)}
      />
    </div>
  );
}
