import { useRef } from "react";
import { motion } from "motion/react";
import type { Modalidad, Vista } from "../api/tipos";
import { useT } from "../i18n";
import altoContraste960 from "../recursos/alto-contraste-960.webp";
import altoContraste1672 from "../recursos/alto-contraste-1672.webp";
import bosqueDia960 from "../recursos/bosque-de-dia-960.webp";
import bosqueDia1672 from "../recursos/bosque-de-dia-1672.webp";
import fondo960 from "../recursos/bosque-de-luz-960.webp";
import fondo1672 from "../recursos/bosque-de-luz-1672.webp";
import { CERRAR_FUERA, useCerrarFuera } from "./dialogos";
import { Icono } from "./Icono";
import { Pictograma } from "./Pictograma";
import { PortadaViva } from "./PortadaViva";
import type { TemaVisual } from "./Preferencias";
import { moverLuzPuntero } from "./useLuzPuntero";

const FONDOS_TEMA: Record<TemaVisual, { grande: string; mediano: string }> = {
  noche: { grande: fondo1672, mediano: fondo960 },
  dia: { grande: bosqueDia1672, mediano: bosqueDia960 },
  contraste: { grande: altoContraste1672, mediano: altoContraste960 },
};

/**
 * Portada cinematográfica de Zoonauta 6.0 con tres mundos sincronizados al tema visual:
 * - Bosque de noche: ciervo y búho bajo la luna («Bosque de luz»).
 * - Bosque de día: jaguar y guacamayo rojo en selva soleada.
 * - Alto contraste: lobo ártico y búho nival bajo aurora boreal.
 * Cada tema muestra su imagen WebP de carga instantánea y su video 2K en bucle invisible
 * (desactivable al instante con «Reducir movimiento»).
 */
interface Props {
  vista: Vista;
  tema: TemaVisual;
  reducido: boolean;
  onVideoActivo?: (activo: boolean) => void;
  onComenzar: (modalidad: Modalidad) => void;
  onAbrirModalidad: () => void;
  onCerrarModalidad: () => void;
}

export function Portada({
  vista,
  tema,
  reducido,
  onVideoActivo,
  onComenzar,
  onAbrirModalidad,
  onCerrarModalidad,
}: Props) {
  const { t } = useT();
  const selector = useRef<HTMLDialogElement>(null);
  useCerrarFuera(selector);
  const fondo = FONDOS_TEMA[tema];

  // Los pictogramas del selector pesan ~500 KB cada uno: se piden solo cuando hay
  // intención de pulsar Comenzar (puntero o foco), sin competir con la carga inicial.
  const precargado = useRef(false);
  const precargarSelector = () => {
    if (precargado.current) return;
    precargado.current = true;
    for (const id of ["P_JUGADOR", "P_AGENTE"]) {
      const imagen = new Image();
      imagen.src = vista.pictogramas[id]?.imagen ?? "";
    }
  };

  const abrirSelector = () => {
    selector.current?.showModal();
    onAbrirModalidad();
  };

  return (
    <section className="portada" data-tema={tema} aria-labelledby="titulo-pantalla">
      <img
        className="portada-paisaje"
        src={fondo.grande}
        srcSet={`${fondo.mediano} 960w, ${fondo.grande} 1672w`}
        sizes="max(100vw, 177.7vh)"
        width={1672}
        height={941}
        alt=""
        draggable={false}
        fetchPriority="high"
        decoding="async"
      />
      <PortadaViva tema={tema} poster={fondo.grande} reducido={reducido} onVideoActivo={onVideoActivo} />
      <div className="portada-velo" aria-hidden="true" />

      <div className="portada-bienvenida">
        <motion.p
          className="portada-introduccion"
          initial={reducido ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
        >
          {t("Un bosque que cobra vida")}
        </motion.p>
        <motion.h1
          id="titulo-pantalla"
          tabIndex={-1}
          initial={reducido ? false : { opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.52, delay: 0.06, ease: [0.22, 1, 0.36, 1] }}
        >
          {t("Descubre el")} <span>{t("bosque de luz.")}</span>
        </motion.h1>
        <motion.p
          className="portada-descripcion"
          initial={reducido ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.48, delay: 0.13, ease: [0.22, 1, 0.36, 1] }}
        >
          {t("Elige un animal. Sigue las pistas y descubre dónde vive.")}
        </motion.p>
        <motion.button
          type="button"
          className="portada-comenzar"
          aria-haspopup="dialog"
          initial={reducido ? false : { opacity: 0, y: 14, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.48, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          whileHover={reducido ? undefined : { scale: 1.028 }}
          whileTap={reducido ? undefined : { scale: 0.965 }}
          onClick={abrirSelector}
          onPointerEnter={precargarSelector}
          onPointerMove={moverLuzPuntero}
          onFocus={precargarSelector}
          onTouchStart={precargarSelector}
        >
          <span className="comenzar-icono" aria-hidden="true">
            <Icono nombre="reproducir" />
          </span>
          <span>{t("Comenzar")}</span>
        </motion.button>
      </div>

      <dialog
        ref={selector}
        className="selector-modalidad"
        aria-labelledby="titulo-modalidad"
        {...CERRAR_FUERA}
        onClose={onCerrarModalidad}
      >
        <h2 id="titulo-modalidad">{t("¿Quién elige el animal?")}</h2>
        <div className="opciones-modalidad">
          {(
            [
              ["JUGADOR", "Yo elijo", "P_JUGADOR"],
              ["AGENTE", "El agente elige", "P_AGENTE"],
            ] as const
          ).map(([modo, etiqueta, picto], i) => (
            <button
              key={modo}
              type="button"
              className="opcion-modalidad"
              autoFocus={i === 0}
              onPointerMove={moverLuzPuntero}
              onClick={() => {
                selector.current?.close();
                onComenzar(modo);
              }}
            >
              {/* Diferida: el diálogo cerrado no debe descargar ~1 MB al abrir la portada. */}
              <span className="opcion-modalidad-escena">
                <Pictograma id={picto} datos={vista.pictogramas[picto]} perezosa />
              </span>
              <span>{t(etiqueta)}</span>
            </button>
          ))}
        </div>
        <form method="dialog">
          <button className="boton-secundario">{t("Volver al inicio")}</button>
        </form>
      </dialog>
    </section>
  );
}
