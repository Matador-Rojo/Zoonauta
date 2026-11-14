import { useCallback, useEffect, useRef, useState } from "react";
import type { Elemento, Modalidad, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Icono } from "./Icono";
import { Pictograma } from "./Pictograma";

// Los ocho paisajes de la portada 6.0, en el orden decidido. Solo cambian la
// presentación: el catálogo jugable conserva los 48 hábitats.
export const PAISAJES_PORTADA = ["H01", "H09", "H17", "H22", "H20", "H37", "H21", "H25"] as const;
const INTERVALO_MS = 10_000;

interface Props {
  vista: Vista;
  movimientoReducido: boolean;
  dialogoAbierto: boolean;
  onComenzar: (modalidad: Modalidad) => void;
  onAbrirModalidad: () => void;
  onCerrarModalidad: () => void;
}

export function Portada({ vista, movimientoReducido, dialogoAbierto, onComenzar, onAbrirModalidad, onCerrarModalidad }: Props) {
  const { t } = useT();
  const paisajes = PAISAJES_PORTADA
    .map((id) => vista.opciones_habitat.find((h) => h.id === id))
    .filter((h): h is Elemento => Boolean(h));
  const [{ indice, previo }, setPosicion] = useState({ indice: 0, previo: -1 });
  const [pausado, setPausado] = useState(false);
  const [focoDentro, setFocoDentro] = useState(false);
  const [visible, setVisible] = useState(() => document.visibilityState === "visible");
  const [anuncio, setAnuncio] = useState("");
  const selector = useRef<HTMLDialogElement>(null);
  const total = paisajes.length;
  const actual = paisajes[indice % Math.max(total, 1)];

  // La rotación automática se detiene con Reducir movimiento, con la pausa,
  // con un diálogo abierto, con la pestaña oculta o con el foco en el carrusel.
  const rota = !movimientoReducido && !pausado && !dialogoAbierto && visible && !focoDentro && total > 1;
  useEffect(() => {
    if (!rota) return;
    const temporizador = window.setInterval(() => setPosicion(({ indice: i }) => ({ indice: (i + 1) % total, previo: i })), INTERVALO_MS);
    return () => window.clearInterval(temporizador);
  }, [rota, total]);

  useEffect(() => {
    const alCambiar = () => setVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", alCambiar);
    return () => document.removeEventListener("visibilitychange", alCambiar);
  }, []);

  const mover = useCallback((paso: number) => {
    const nuevo = (indice + paso + total) % total;
    setPosicion({ indice: nuevo, previo: indice });
    // Solo se anuncian los cambios que pide la persona, no la rotación automática.
    setAnuncio(t("Paisaje {n} de {total}", { n: nuevo + 1, total }) + ": " + paisajes[nuevo]?.nombre);
  }, [indice, total, paisajes, t]);

  const abrirSelector = () => {
    selector.current?.showModal();
    onAbrirModalidad();
  };

  const n = vista.catalogo_animales.length;
  const nHabitats = vista.opciones_habitat.length;

  return (
    <section className="portada" aria-labelledby="titulo-pantalla">
      <div className="portada-fondo" aria-hidden="true">
        {paisajes.map((h, i) => {
          const esActual = i === indice;
          const esSiguiente = i === (indice + 1) % total;
          // Se montan el paisaje actual, el anterior (para el fundido) y el siguiente (precarga).
          if (!esActual && !esSiguiente && i !== previo) return null;
          return (
            <div key={h.id} className="portada-capa" data-habitat={h.id}
              data-estado={esActual ? "actual" : i === previo ? "previo" : "siguiente"}>
              <img src={`/fondos/catalogo/${h.id}.webp`} alt="" width={1920} height={1080} draggable={false}
                fetchPriority={esActual && i === 0 ? "high" : esActual ? undefined : "low"} />
              <span className="ambiente" />
            </div>
          );
        })}
        <div className="portada-sombra" />
      </div>

      <div className="portada-contenido">
        <div className="portada-texto">
          <p className="etiqueta">{t("El mundo está esperando")}</p>
          <h1 id="titulo-pantalla" tabIndex={-1}>
            <span>{t("Cada animal.")}</span> <em>{t("Su mundo.")}</em>
          </h1>
          <p className="introduccion">
            {t("{animales} animales. {habitats} hábitats. Descubre dónde viven con pictogramas y una guía que te acompaña.", { animales: n, habitats: nHabitats })}
          </p>
          <div className="entrada">
            <button type="button" className="boton-principal" aria-haspopup="dialog" onClick={abrirSelector}>
              <Icono nombre="reproducir" />
              <span>{t("Comenzar")}</span>
              <Icono nombre="flecha" className="flecha" />
            </button>
            <p className="nota"><Icono nombre="reloj" /><span>{t("Sin reloj. Con ayuda. A tu ritmo.")}</span></p>
          </div>
        </div>

        <section className="carrusel" aria-roledescription="carousel" aria-label={t("Paisajes de la portada")}
          onFocus={() => setFocoDentro(true)}
          onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocoDentro(false); }}>
          <p className="carrusel-nombre">
            <strong>{actual?.nombre}</strong>
            <span className="carrusel-contador">{indice + 1} / {total}</span>
          </p>
          <div className="carrusel-controles">
            <button type="button" className="control-redondo" aria-label={t("Paisaje anterior")} onClick={() => mover(-1)}>
              <Icono nombre="anterior" />
            </button>
            {!movimientoReducido && (
              // La etiqueta cambia entre Pausar y Reanudar; sin aria-pressed (Modern Web Guidance, motion).
              <button type="button" className="control-redondo" aria-label={t(pausado ? "Reanudar paisajes" : "Pausar paisajes")}
                onClick={() => setPausado((p) => !p)}>
                <Icono nombre={pausado ? "reproducir" : "pausa"} />
              </button>
            )}
            <button type="button" className="control-redondo" aria-label={t("Siguiente paisaje")} onClick={() => mover(1)}>
              <Icono nombre="flecha" />
            </button>
          </div>
          <p className="solo-lectores" role="status" aria-live="polite">{anuncio}</p>
        </section>
      </div>

      <dialog ref={selector} className="selector-modalidad" aria-labelledby="titulo-modalidad"
        onClose={onCerrarModalidad}>
        <h2 id="titulo-modalidad">{t("¿Quién elige el animal?")}</h2>
        <div className="opciones-modalidad">
          {([["JUGADOR", "Yo elijo", "P_JUGADOR"], ["AGENTE", "El agente elige", "P_AGENTE"]] as const).map(([modo, etiqueta, picto], i) => (
            <button key={modo} type="button" className="opcion-modalidad" autoFocus={i === 0}
              onClick={() => { selector.current?.close(); onComenzar(modo); }}>
              <Pictograma id={picto} datos={vista.pictogramas[picto]} />
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
