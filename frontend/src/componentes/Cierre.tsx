import { useCallback, useEffect, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { motion } from "motion/react";
import type { TipoAccion, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Icono } from "./Icono";
import { NumeroAnimado } from "./NumeroAnimado";
import { Pictograma } from "./Pictograma";
import { Controles, TiraPictogramas } from "./Reto";
import { SenderoProgreso } from "./SenderoProgreso";
import { moverLuzPuntero } from "./useLuzPuntero";

export interface Hallazgo {
  animalId: string;
  animalNombre: string;
  pictogramaId: string;
  habitatId: string;
  habitatNombre: string;
}

const CELEBRACION_VICTORIA = [
  { id: 0, x: "7%", y: "16%", dy: -26, r: 95, d: 0, dur: 2.8, tipo: "estrella" },
  { id: 1, x: "18%", y: "74%", dy: -32, r: -110, d: 0.2, dur: 3.1, tipo: "hoja" },
  { id: 2, x: "33%", y: "12%", dy: -20, r: 120, d: 0.35, dur: 2.7, tipo: "luz" },
  { id: 3, x: "48%", y: "84%", dy: -28, r: -85, d: 0.15, dur: 3.3, tipo: "estrella" },
  { id: 4, x: "62%", y: "18%", dy: -24, r: 135, d: 0.45, dur: 2.9, tipo: "hoja" },
  { id: 5, x: "78%", y: "26%", dy: -22, r: -90, d: 0.25, dur: 3.0, tipo: "estrella" },
  { id: 6, x: "90%", y: "68%", dy: -26, r: 105, d: 0.55, dur: 2.8, tipo: "hoja" },
  { id: 7, x: "12%", y: "46%", dy: -18, r: 70, d: 0.3, dur: 3.2, tipo: "luz" },
  { id: 8, x: "84%", y: "52%", dy: -24, r: -120, d: 0.4, dur: 2.9, tipo: "estrella" },
  { id: 9, x: "44%", y: "38%", dy: -20, r: 85, d: 0.65, dur: 3.4, tipo: "hoja" },
  { id: 10, x: "26%", y: "30%", dy: -22, r: -75, d: 0.5, dur: 3.1, tipo: "estrella" },
  { id: 11, x: "70%", y: "78%", dy: -26, r: 115, d: 0.1, dur: 2.7, tipo: "luz" },
] as const;

// Pausa y cierre reutilizan las ilustraciones existentes del robot.
export function Cierre({
  vista,
  hallazgos = [],
  reducido = false,
  onAccion,
}: {
  vista: Vista;
  hallazgos?: Hallazgo[];
  reducido?: boolean;
  onAccion: (tipo: TipoAccion) => void;
}) {
  const { t } = useT();
  const pausa = vista.fase === "PAUSADA";
  const victoria = vista.fase === "COMPLETADA";
  const titulo = pausa ? "Tomamos una pausa" : victoria ? "¡Terminamos!" : "Partida terminada";
  const { completados, total } = vista.progreso;
  const mostrarAlbum = !pausa && hallazgos.length > 0;

  const [emblaRef, emblaApi] = useEmblaCarousel({
    align: "start",
    dragFree: true,
    containScroll: "trimSnaps",
  });
  const [puedeIzq, setPuedeIzq] = useState(false);
  const [puedeDer, setPuedeDer] = useState(false);

  const actualizarBotones = useCallback(() => {
    if (!emblaApi) return;
    setPuedeIzq(emblaApi.canScrollPrev());
    setPuedeDer(emblaApi.canScrollNext());
  }, [emblaApi]);

  useEffect(() => {
    if (!emblaApi || !mostrarAlbum) return;
    const id = requestAnimationFrame(actualizarBotones);
    emblaApi.on("select", actualizarBotones);
    emblaApi.on("reInit", actualizarBotones);
    emblaApi.on("scroll", actualizarBotones);
    return () => {
      cancelAnimationFrame(id);
      emblaApi.off("select", actualizarBotones);
      emblaApi.off("reInit", actualizarBotones);
      emblaApi.off("scroll", actualizarBotones);
    };
  }, [emblaApi, mostrarAlbum, hallazgos.length, actualizarBotones]);

  const desplazar = (dir: number) => {
    if (!emblaApi) return;
    if (dir < 0) emblaApi.scrollPrev();
    else emblaApi.scrollNext();
  };

  return (
    <section className="pantalla cierre" data-estado={vista.fase} aria-labelledby="titulo-pantalla">
      {victoria && !reducido && (
        <div className="celebracion-victoria" aria-hidden="true">
          {CELEBRACION_VICTORIA.map((p) => (
            <motion.span
              key={p.id}
              className={`victoria-pieza victoria-${p.tipo}`}
              style={{ left: p.x, top: p.y }}
              initial={{ opacity: 0, scale: 0.65, rotate: 0 }}
              animate={{
                opacity: [0, 0.92, 0.35, 0.88, 0],
                y: [0, p.dy, p.dy * 1.45],
                scale: [0.65, 1.15, 0.85],
                rotate: [0, p.r * 0.5, p.r],
              }}
              transition={{ duration: p.dur, delay: p.d, repeat: Infinity, repeatDelay: 0.35, ease: "easeInOut" }}
            />
          ))}
        </div>
      )}
      <motion.figure
        className="cierre-visual"
        initial={reducido || pausa ? false : { opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 320, damping: 26 }}
        onPointerMove={moverLuzPuntero}
      >
        <span className="rotulo">{t("Tu guía")}</span>
        {victoria && (
          <motion.span
            className="medalla-explorador"
            aria-hidden="true"
            initial={reducido ? false : { opacity: 0, scale: 0.7, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 380, damping: 20, delay: 0.12 }}
          >
            ★
          </motion.span>
        )}
        <img
          src={`/ilustraciones/${pausa ? "robot_pausa" : "robot_despedida"}.webp`}
          // Proporciones reales (1:1 y 2:3) para reservar el espacio y evitar saltos.
          width={pausa ? 640 : 427}
          height={640}
          alt={t("Tu guía")}
          draggable={false}
        />
        <figcaption>{t(pausa ? "A tu ritmo" : "Gracias por jugar")}</figcaption>
      </motion.figure>
      <div className="cierre-contenido">
        <p className="rotulo">{t("Tu expedición")}</p>
        <h1 id="titulo-pantalla" tabIndex={-1}>
          {t(titulo)}
        </h1>
        <p className="introduccion">{t(vista.respuesta.texto_apoyo)}</p>
        <TiraPictogramas ids={vista.respuesta.pictogramas} vista={vista} />
        <motion.div
          className="cierre-resumen"
          initial={reducido || pausa ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.36, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
        >
          <strong>
            <NumeroAnimado valor={completados} reducido={reducido} /> / {total}
          </strong>
          <span>{t("Retos completados")}</span>
          <SenderoProgreso completados={completados} total={total} etiquetaAria={t("Progreso de la partida")} />
        </motion.div>
        {mostrarAlbum && (
          <section className="diario-hallazgos" aria-labelledby="titulo-hallazgos">
            <div className="diario-cabecera">
              <h2 id="titulo-hallazgos" className="diario-titulo">
                {t("Hallazgos de esta partida")}
              </h2>
              {(puedeIzq || puedeDer) && (
                <div className="diario-controles">
                  <button
                    type="button"
                    className="diario-nav"
                    aria-label={t("Anteriores")}
                    disabled={!puedeIzq}
                    onClick={() => desplazar(-1)}
                  >
                    <Icono nombre="anterior" />
                  </button>
                  <button
                    type="button"
                    className="diario-nav"
                    aria-label={t("Siguientes")}
                    disabled={!puedeDer}
                    onClick={() => desplazar(1)}
                  >
                    <Icono nombre="flecha" />
                  </button>
                </div>
              )}
            </div>
            <div className="diario-marco" data-izq={puedeIzq || undefined} data-der={puedeDer || undefined}>
              <div className="diario-viewport" ref={emblaRef}>
                <ol className="diario-lista">
                  {hallazgos.map((h) => (
                    <li key={`${h.animalId}-${h.habitatId}`} className="diario-tarjeta">
                      <img
                        className="diario-habitat"
                        src={`/habitats/${h.habitatId}.webp`}
                        alt=""
                        draggable={false}
                        loading="lazy"
                      />
                      <span className="diario-animal">
                        <Pictograma id={h.pictogramaId} datos={vista.pictogramas[h.pictogramaId]} />
                      </span>
                      <span className="diario-texto">
                        <strong>{h.animalNombre}</strong>
                        <span>{h.habitatNombre}</span>
                      </span>
                      <span className="diario-sello" aria-hidden="true">
                        ✓
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </section>
        )}
        {pausa ? (
          <Controles vista={vista} onAccion={onAccion} />
        ) : (
          <button type="button" className="boton-principal" onClick={() => onAccion("nueva_partida")}>
            <Pictograma id="P_INICIAR" datos={vista.pictogramas.P_INICIAR} />
            <span>{t("Comenzar otra partida")}</span>
          </button>
        )}
        {!pausa && <p className="nota cierre-lema">{t("Sin reloj. Con ayuda. A tu ritmo.")}</p>}
      </div>
    </section>
  );
}
