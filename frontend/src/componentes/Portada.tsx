import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import type { Elemento, Modalidad, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Icono } from "./Icono";
import { Pictograma } from "./Pictograma";

/**
 * Los ocho paisajes de la portada 6.0, en el orden decidido. Solo cambian la
 * presentación: el catálogo jugable conserva los 48 hábitats.
 *
 * `fx`/`fy` fijan el punto de la foto que se conserva al recortarla en pantallas
 * con otra proporción. `efectos` son luces hechas con CSS. `capas` son imágenes con
 * transparencia (fondos/capas, ver procedencia.json) superpuestas a la foto en su
 * posición exacta: `caja` = [izquierda, arriba, derecha, abajo] en píxeles de 1920×1080.
 * Las capas forman parte de la escena (también con movimiento reducido); solo su
 * movimiento es opcional. Nada mueve la cámara, hace zoom ni destella (ver portada.css).
 */
type Capa = { nombre: string; caja: readonly [number, number, number, number] };
export const PAISAJES_PORTADA: readonly {
  id: string;
  fx: number;
  fy: number;
  efectos: readonly string[];
  capas: readonly Capa[];
}[] = [
  {
    id: "H01",
    fx: 0.86,
    fy: 0.5,
    efectos: ["cascada"],
    capas: [
      { nombre: "niebla", caja: [25, 12, 981, 526] },
      { nombre: "hojas", caja: [1480, 670, 1920, 1080] },
    ],
  },
  { id: "H09", fx: 0.92, fy: 0.6, efectos: ["sol"], capas: [{ nombre: "hierba", caja: [80, 893, 1774, 1080] }] },
  { id: "H17", fx: 0.88, fy: 0.5, efectos: ["luz-calida"], capas: [] },
  { id: "H22", fx: 0.9, fy: 0.55, efectos: ["reflejo-frio"], capas: [] },
  { id: "H20", fx: 0.88, fy: 0.4, efectos: [], capas: [{ nombre: "nubes", caja: [189, 282, 1178, 480] }] },
  {
    id: "H37",
    fx: 0.9,
    fy: 0.55,
    efectos: ["rayos", "ondas-luz"],
    capas: [{ nombre: "algas", caja: [909, 840, 1853, 1080] }],
  },
  { id: "H21", fx: 0.8, fy: 0.5, efectos: [], capas: [] },
  { id: "H25", fx: 0.65, fy: 0.55, efectos: ["agua"], capas: [] },
];

/** Posición de una capa en porcentajes de la escena 1920×1080. */
function estiloCapa([x1, y1, x2, y2]: Capa["caja"]): CSSProperties {
  return {
    left: `${(x1 / 1920) * 100}%`,
    top: `${(y1 / 1080) * 100}%`,
    width: `${((x2 - x1) / 1920) * 100}%`,
    height: `${((y2 - y1) / 1080) * 100}%`,
  };
}
export const ORDEN_PORTADA = PAISAJES_PORTADA.map((p) => p.id);
const INTERVALO_MS = 10_000;

interface Props {
  vista: Vista;
  movimientoReducido: boolean;
  dialogoAbierto: boolean;
  onComenzar: (modalidad: Modalidad) => void;
  onAbrirModalidad: () => void;
  onCerrarModalidad: () => void;
}

function Foto({
  id,
  prioridad,
  clase,
  onLoad,
}: {
  id: string;
  prioridad?: "high" | "low";
  clase?: string;
  onLoad?: () => void;
}) {
  return (
    <img
      className={clase}
      src={`/fondos/catalogo/${id}.webp`}
      alt=""
      width={1920}
      height={1080}
      draggable={false}
      srcSet={`/fondos/portada/${id}-960.webp 960w, /fondos/catalogo/${id}.webp 1920w`}
      sizes="max(100vw, 177.78vh)"
      fetchPriority={prioridad}
      decoding="async"
      onLoad={onLoad}
    />
  );
}

export function Portada({
  vista,
  movimientoReducido,
  dialogoAbierto,
  onComenzar,
  onAbrirModalidad,
  onCerrarModalidad,
}: Props) {
  const { t } = useT();
  const paisajes = PAISAJES_PORTADA.flatMap((p) => {
    const habitat = vista.opciones_habitat.find((h) => h.id === p.id);
    return habitat ? [{ ...p, habitat } as const] : [];
  });
  const [{ indice, previo }, setPosicion] = useState({ indice: 0, previo: -1 });
  const [pausado, setPausado] = useState(false);
  const [focoDentro, setFocoDentro] = useState(false);
  const [punteroDentro, setPunteroDentro] = useState(false);
  const [visible, setVisible] = useState(() => document.visibilityState === "visible");
  const [anuncio, setAnuncio] = useState("");
  // El siguiente paisaje se precarga solo cuando el primero ya cargó, para no competir
  // con él por la red (LCP en móvil).
  const [primeroCargado, setPrimeroCargado] = useState(false);
  const selector = useRef<HTMLDialogElement>(null);
  const total = paisajes.length;
  const actual: Elemento | undefined = paisajes[indice]?.habitat;

  // La rotación automática se detiene con Reducir movimiento, con la pausa, con un
  // diálogo abierto, con la pestaña oculta y mientras el foco o el puntero están en
  // los controles del carrusel (para leer y decidir sin que cambie).
  const rota =
    !movimientoReducido && !pausado && !dialogoAbierto && visible && !focoDentro && !punteroDentro && total > 1;
  useEffect(() => {
    if (!rota) return;
    const temporizador = window.setInterval(
      () => setPosicion(({ indice: i }) => ({ indice: (i + 1) % total, previo: i })),
      INTERVALO_MS,
    );
    return () => window.clearInterval(temporizador);
  }, [rota, total, indice]);

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

  useEffect(() => {
    const alCambiar = () => setVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", alCambiar);
    return () => document.removeEventListener("visibilitychange", alCambiar);
  }, []);

  const irA = useCallback(
    (nuevo: number) => {
      if (nuevo === indice) return;
      setPosicion({ indice: nuevo, previo: indice });
      // Solo se anuncian los cambios que pide la persona, no la rotación automática.
      setAnuncio(t("Paisaje {n} de {total}", { n: nuevo + 1, total }) + ": " + paisajes[nuevo]?.habitat.nombre);
    },
    [indice, total, paisajes, t],
  );

  const abrirSelector = () => {
    selector.current?.showModal();
    onAbrirModalidad();
  };

  return (
    <section
      className="portada"
      aria-labelledby="titulo-pantalla"
      data-ambiente={pausado || !visible ? "pausado" : "activo"}
    >
      <div className="portada-fondo" aria-hidden="true">
        {paisajes.map((p, i) => {
          const esActual = i === indice;
          const esSiguiente = i === (indice + 1) % total;
          // Se montan el paisaje actual, el anterior (para el fundido) y el siguiente (precarga).
          if (!esActual && !esSiguiente && i !== previo) return null;
          if (esSiguiente && !esActual && i !== previo && !primeroCargado) return null;
          const estado = esActual ? "actual" : i === previo ? "previo" : "siguiente";
          return (
            <div key={p.id} className="portada-capa" data-habitat={p.id} data-estado={estado}>
              {/* La escena recorta la foto como object-fit: cover, y los efectos se colocan
                  sobre ella en porcentajes de la foto, sea cual sea la pantalla. */}
              <div className="escena" style={{ "--fx": p.fx, "--fy": p.fy } as CSSProperties}>
                <Foto
                  id={p.id}
                  prioridad={esActual ? (i === 0 ? "high" : undefined) : "low"}
                  onLoad={esActual ? () => setPrimeroCargado(true) : undefined}
                />
                {p.capas.map((capa) => (
                  <img
                    key={capa.nombre}
                    className={`capa capa-${capa.nombre}`}
                    src={`/fondos/capas/${p.id}-${capa.nombre}.webp`}
                    alt=""
                    draggable={false}
                    decoding="async"
                    fetchPriority={esActual ? undefined : "low"}
                    style={estiloCapa(capa.caja)}
                  />
                ))}
                {esActual &&
                  p.efectos.map((efecto) =>
                    // El agua mueve una copia recortada de la misma foto (ya en caché).
                    efecto === "agua" ? (
                      <Foto key={efecto} id={p.id} clase={`efecto efecto-${efecto}`} />
                    ) : (
                      <span key={efecto} className={`efecto efecto-${efecto}`} />
                    ),
                  )}
              </div>
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
            {t(
              "{animales} animales. {habitats} hábitats. Descubre dónde viven con pictogramas y una guía que te acompaña.",
              { animales: vista.catalogo_animales.length, habitats: vista.opciones_habitat.length },
            )}
          </p>
          <div className="entrada">
            <button
              type="button"
              className="boton-principal"
              aria-haspopup="dialog"
              onClick={abrirSelector}
              onPointerEnter={precargarSelector}
              onFocus={precargarSelector}
              onTouchStart={precargarSelector}
            >
              <Icono nombre="reproducir" />
              <span>{t("Comenzar")}</span>
              <Icono nombre="flecha" className="flecha" />
            </button>
            <p className="nota">
              <Icono nombre="reloj" />
              <span>{t("Sin reloj. Con ayuda. A tu ritmo.")}</span>
            </p>
          </div>
        </div>

        <section
          className="carrusel"
          aria-roledescription="carousel"
          aria-label={t("Paisajes de la portada")}
          onFocus={() => setFocoDentro(true)}
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocoDentro(false);
          }}
          onPointerEnter={() => setPunteroDentro(true)}
          onPointerLeave={() => setPunteroDentro(false)}
        >
          <div className="carrusel-cabecera">
            <p className="carrusel-nombre">
              <span className="carrusel-contador">
                {indice + 1} / {total}
              </span>
              <strong>{actual?.nombre}</strong>
            </p>
            <div className="carrusel-controles">
              <button
                type="button"
                className="control-redondo"
                aria-label={t("Paisaje anterior")}
                onClick={() => irA((indice - 1 + total) % total)}
              >
                <Icono nombre="anterior" />
              </button>
              {!movimientoReducido && (
                // La etiqueta cambia entre Pausar y Reanudar; sin aria-pressed (Modern Web Guidance, motion).
                // Detiene a la vez la rotación y el movimiento ambiental (WCAG 2.2.2).
                <button
                  type="button"
                  className="control-redondo"
                  aria-label={t(pausado ? "Reanudar paisajes" : "Pausar paisajes")}
                  onClick={() => setPausado((x) => !x)}
                >
                  <Icono nombre={pausado ? "reproducir" : "pausa"} />
                </button>
              )}
              <button
                type="button"
                className="control-redondo"
                aria-label={t("Siguiente paisaje")}
                onClick={() => irA((indice + 1) % total)}
              >
                <Icono nombre="flecha" />
              </button>
            </div>
          </div>
          <nav className="carrusel-marcas" aria-label={t("Elige un paisaje")}>
            {paisajes.map((p, i) => (
              <button
                key={p.id}
                type="button"
                className="marca-paisaje"
                aria-label={p.habitat.nombre}
                aria-current={i === indice ? "true" : undefined}
                onClick={() => irA(i)}
              />
            ))}
          </nav>
          <p className="solo-lectores" role="status" aria-live="polite">
            {anuncio}
          </p>
        </section>
      </div>

      <dialog
        ref={selector}
        className="selector-modalidad"
        aria-labelledby="titulo-modalidad"
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
