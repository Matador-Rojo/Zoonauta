import { useRef } from "react";
import type { Modalidad, Vista } from "../api/tipos";
import { useT } from "../i18n";
import fondo960 from "../recursos/bosque-de-luz-960.webp";
import fondo1672 from "../recursos/bosque-de-luz-1672.webp";
import { CERRAR_FUERA, useCerrarFuera } from "./dialogos";
import { Icono } from "./Icono";
import { Pictograma } from "./Pictograma";

/**
 * Portada «Bosque de luz» (decidida por el propietario el 2026-11-14).
 * El fondo está aprobado: no se sustituye ni se le aplican filtros, capas ni animaciones;
 * conserva su encuadre y su velo oscuro (copia WebP del PNG original en assets/portada/).
 * La portada ocupa exactamente la vista y no lleva pictogramas. Comenzar abre
 * «¿Quién elige el animal?» (Yo elijo / El agente elige), como en la 5.0.
 */
interface Props {
  vista: Vista;
  onComenzar: (modalidad: Modalidad) => void;
  onAbrirModalidad: () => void;
  onCerrarModalidad: () => void;
}

export function Portada({ vista, onComenzar, onAbrirModalidad, onCerrarModalidad }: Props) {
  const { t } = useT();
  const selector = useRef<HTMLDialogElement>(null);
  useCerrarFuera(selector);

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
    <section className="portada" aria-labelledby="titulo-pantalla">
      <img
        className="portada-paisaje"
        src={fondo1672}
        srcSet={`${fondo960} 960w, ${fondo1672} 1672w`}
        sizes="max(100vw, 177.7vh)"
        width={1672}
        height={941}
        alt=""
        draggable={false}
        fetchPriority="high"
        decoding="async"
      />
      <div className="portada-velo" aria-hidden="true" />

      <div className="portada-bienvenida">
        <p className="portada-introduccion">{t("Un bosque que cobra vida")}</p>
        <h1 id="titulo-pantalla" tabIndex={-1}>
          {t("Descubre el")} <span>{t("bosque de luz.")}</span>
        </h1>
        <p className="portada-descripcion">{t("Elige un animal. Sigue las pistas y descubre dónde vive.")}</p>
        <button
          type="button"
          className="portada-comenzar"
          aria-haspopup="dialog"
          onClick={abrirSelector}
          onPointerEnter={precargarSelector}
          onFocus={precargarSelector}
          onTouchStart={precargarSelector}
        >
          <Icono nombre="reproducir" />
          <span>{t("Comenzar")}</span>
        </button>
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
              onClick={() => {
                selector.current?.close();
                onComenzar(modo);
              }}
            >
              {/* Diferida: el diálogo cerrado no debe descargar ~1 MB al abrir la portada. */}
              <Pictograma id={picto} datos={vista.pictogramas[picto]} perezosa />
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
