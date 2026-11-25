import { useEffect, useState } from "react";
import { motion } from "motion/react";
import type { TipoAccion, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Encabezado } from "./Encabezado";
import { LogoZoonauta } from "./LogoZoonauta";
import { Pictograma, useContenidoListo } from "./Pictograma";
import { moverLuzPuntero, moverTiltTarjeta, resetTiltTarjeta } from "./useLuzPuntero";

const CONFETI_ACIERTO = [
  { id: 0, dx: -82, dy: -56, r: -140, s: 1.05, d: 0, tipo: "estrella" },
  { id: 1, dx: 78, dy: -62, r: 160, s: 0.95, d: 0.03, tipo: "hoja" },
  { id: 2, dx: -96, dy: 8, r: -95, s: 0.9, d: 0.06, tipo: "punto" },
  { id: 3, dx: 92, dy: 14, r: 120, s: 1.1, d: 0.02, tipo: "estrella" },
  { id: 4, dx: -48, dy: -82, r: -180, s: 0.85, d: 0.07, tipo: "hoja" },
  { id: 5, dx: 46, dy: -84, r: 150, s: 0.9, d: 0.05, tipo: "punto" },
  { id: 6, dx: -64, dy: 58, r: -110, s: 0.85, d: 0.09, tipo: "hoja" },
  { id: 7, dx: 66, dy: 54, r: 135, s: 0.95, d: 0.07, tipo: "estrella" },
  { id: 8, dx: 0, dy: -92, r: 90, s: 1.05, d: 0.04, tipo: "estrella" },
  { id: 9, dx: -26, dy: -68, r: -75, s: 0.78, d: 0.08, tipo: "punto" },
  { id: 10, dx: 28, dy: -64, r: 85, s: 0.82, d: 0.06, tipo: "hoja" },
  { id: 11, dx: -74, dy: -24, r: -130, s: 0.86, d: 0.05, tipo: "hoja" },
  { id: 12, dx: 74, dy: -22, r: 145, s: 0.88, d: 0.08, tipo: "punto" },
  { id: 13, dx: 12, dy: 62, r: 110, s: 0.8, d: 0.1, tipo: "estrella" },
] as const;

type Grupo = "ayuda" | "partida";

// Orden y grupo fijos: las ayudas (Pista, Repetir) a un lado y la partida (Pausar,
// Reanudar, Continuar, Salir) al otro, siempre en el mismo sitio.
const CONTROLES: Partial<Record<string, { texto: string; picto: string; grupo: Grupo }>> = {
  ayuda: { texto: "Pista", picto: "P_AYUDA", grupo: "ayuda" },
  repetir: { texto: "Repetir", picto: "P_REPETIR", grupo: "ayuda" },
  continuar: { texto: "Continuar", picto: "P_CONTINUAR", grupo: "partida" },
  reanudar: { texto: "Reanudar", picto: "P_REANUDAR", grupo: "partida" },
  pausar: { texto: "Pausar", picto: "P_PAUSAR", grupo: "partida" },
  salir: { texto: "Salir", picto: "P_SALIR", grupo: "partida" },
};

export function Controles({
  vista,
  hablando = false,
  invitarPista = false,
  onAccion,
}: {
  vista: Vista;
  hablando?: boolean;
  invitarPista?: boolean;
  onAccion: (tipo: TipoAccion) => void;
}) {
  const { t } = useT();
  const disponibles = Object.keys(CONTROLES).filter((tipo) => vista.controles_disponibles.includes(tipo));
  const boton = (tipo: string) => {
    const { texto, picto } = CONTROLES[tipo]!;
    return (
      <motion.button
        key={tipo}
        type="button"
        className="control"
        data-control={tipo}
        data-hablando={tipo === "repetir" && hablando ? "true" : undefined}
        data-invitar={tipo === "ayuda" && invitarPista ? "true" : undefined}
        whileTap={{ scale: 0.96 }}
        transition={{ type: "spring", stiffness: 420, damping: 28 }}
        onClick={() => onAccion(tipo as TipoAccion)}
      >
        <Pictograma id={picto} datos={vista.pictogramas[picto]} />
        <span>{t(texto)}</span>
      </motion.button>
    );
  };
  return (
    <nav className="controles" aria-label={t("Controles de la partida")}>
      <div className="controles-grupo" data-grupo="ayuda">
        {disponibles.filter((tipo) => CONTROLES[tipo]!.grupo === "ayuda").map(boton)}
      </div>
      <div className="controles-grupo" data-grupo="partida">
        {disponibles.filter((tipo) => CONTROLES[tipo]!.grupo === "partida").map(boton)}
      </div>
    </nav>
  );
}

/** Tira de frase: los pictogramas en orden de lectura, como en un tablero CAA. */
export function TiraPictogramas({
  ids,
  vista,
  indiceActivo = -1,
}: {
  ids: string[];
  vista: Vista;
  indiceActivo?: number;
}) {
  const { t } = useT();
  return (
    <ol className="tira" aria-label={t("Secuencia de pictogramas")}>
      {ids.map((id, i) => {
        const activo = indiceActivo === i;
        return (
          <motion.li
            key={`${i}-${id}`}
            className="tira-celda"
            data-activo={activo ? "true" : undefined}
            animate={activo ? { y: -5, scale: 1.07 } : { y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 420, damping: 20 }}
          >
            <Pictograma id={id} datos={vista.pictogramas[id]} />
            <span>{vista.pictogramas[id]?.etiqueta}</span>
          </motion.li>
        );
      })}
    </ol>
  );
}

export function Guia({
  vista,
  fotoHabitat,
  hablando = false,
  progresoVoz = 0,
}: {
  vista: Vista;
  fotoHabitat?: string | null;
  hablando?: boolean;
  progresoVoz?: number;
}) {
  const { t } = useT();
  // Texto y pictogramas cambian juntos cuando las imágenes nuevas están listas.
  const respuesta = useContenidoListo(vista.respuesta, vista.pictogramas);
  const indiceActivo =
    hablando && respuesta.pictogramas.length > 0
      ? Math.min(respuesta.pictogramas.length - 1, Math.floor(progresoVoz * respuesta.pictogramas.length))
      : -1;
  const tono =
    respuesta.tipo_respuesta === "CONFIRMACION"
      ? "confirmacion"
      : respuesta.tipo_respuesta === "NEUTRAL"
        ? "neutral"
        : respuesta.tipo_respuesta === "AYUDA"
          ? "ayuda"
          : "";
  return (
    <section
      className={`guia ${tono}`.trim()}
      data-tipo={respuesta.tipo_respuesta}
      data-hablando={hablando ? "true" : undefined}
      aria-labelledby="mensaje"
    >
      <p className="guia-cabecera">
        <span className="guia-emblema">
          <LogoZoonauta size={30} />
        </span>
        <span>{t("Tu guía")}</span>
        <span className="guia-onda" aria-hidden="true">
          <i />
          <i />
          <i />
          <i />
          <i />
        </span>
      </p>
      <h2 id="mensaje" tabIndex={-1}>
        {t(respuesta.texto_apoyo)}
      </h2>
      <TiraPictogramas ids={respuesta.pictogramas} vista={vista} indiceActivo={indiceActivo} />
      {fotoHabitat && (
        // El hábitat acertado, a la vista junto a la frase que lo nombra.
        <img className="guia-foto" src={`/habitats/${fotoHabitat}.webp`} alt="" draggable={false} />
      )}
    </section>
  );
}

export function Reto({
  vista,
  hablando = false,
  progresoVoz = 0,
  reducido = false,
  onAccion,
}: {
  vista: Vista;
  hablando?: boolean;
  progresoVoz?: number;
  reducido?: boolean;
  onAccion: (tipo: TipoAccion, payload?: Record<string, unknown>) => void;
}) {
  const { t } = useT();
  const resuelto = vista.fase === "RETO_RESUELTO";
  const animal = vista.animal;
  // Último hábitat pulsado en este reto: al resolverse es el acertado; si devuelve NEUTRAL,
  // aplica un micro-vaivén amable para indicar que seguimos explorando.
  const [pulsado, setPulsado] = useState<{ reto: string | null; id: string; intento: number } | null>(null);
  const [invitarPista, setInvitarPista] = useState(false);
  const elegido = resuelto && pulsado && pulsado.reto === vista.reto_id ? pulsado.id : null;
  const exploradoNeutral =
    !resuelto && vista.respuesta.tipo_respuesta === "NEUTRAL" && pulsado && pulsado.reto === vista.reto_id
      ? pulsado
      : null;

  // Empujoncito gentil (Pok Pok / Sago Mini): tras 12 s sin actividad en espera, Pista respira con suavidad.
  useEffect(() => {
    if (reducido || resuelto || hablando || vista.fase !== "ESPERANDO_RESPUESTA") {
      return;
    }
    let id = window.setTimeout(() => setInvitarPista(true), 12000);
    const reiniciar = () => {
      setInvitarPista(false);
      window.clearTimeout(id);
      id = window.setTimeout(() => setInvitarPista(true), 12000);
    };
    window.addEventListener("pointerdown", reiniciar, { passive: true });
    window.addEventListener("keydown", reiniciar, { passive: true });
    return () => {
      window.clearTimeout(id);
      window.removeEventListener("pointerdown", reiniciar);
      window.removeEventListener("keydown", reiniciar);
      setInvitarPista(false);
    };
  }, [reducido, resuelto, hablando, vista.fase, vista.reto_id, vista.revision]);

  const tonoAnimal =
    vista.respuesta.tipo_respuesta === "CONFIRMACION"
      ? "confirmacion"
      : vista.respuesta.tipo_respuesta === "AYUDA"
        ? "ayuda"
        : vista.respuesta.tipo_respuesta === "NEUTRAL"
          ? "neutral"
          : "";

  return (
    <section
      className="pantalla reto-pantalla"
      data-resuelto={resuelto ? "true" : undefined}
      aria-labelledby="titulo-pantalla"
    >
      <Encabezado
        vista={vista}
        etiqueta="Encuentra su hábitat"
        titulo={resuelto ? "¡Encontraste un lugar!" : "Elige un hábitat"}
        reducido={reducido}
      />
      <div className="tablero">
        {animal && (
          <motion.figure
            key={animal.id}
            className="animal-actual"
            data-animal={animal.id}
            data-tono={tonoAnimal || undefined}
            initial={reducido ? false : { opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}
            onPointerMove={moverLuzPuntero}
          >
            <span className="animal-foco" aria-hidden="true" />
            <span className="rotulo">{t("Tu animal")}</span>
            <Pictograma id={animal.pictograma_id} datos={vista.pictogramas[animal.pictograma_id]} />
            <figcaption>
              <strong>{animal.nombre}</strong>
            </figcaption>
          </motion.figure>
        )}
        <Guia vista={vista} fotoHabitat={elegido} hablando={hablando} progresoVoz={progresoVoz} />
      </div>
      <section className="habitats-panel" aria-labelledby="titulo-habitats">
        <h2 id="titulo-habitats" className="instruccion">
          {t(vista.fase === "ESPERANDO_RESPUESTA" ? "Toca un lugar donde pueda vivir." : "Hábitats para elegir")}
        </h2>
        <div
          className="habitats"
          role="group"
          aria-labelledby="titulo-habitats"
          data-cantidad={vista.opciones_habitat.length}
          data-resuelto={elegido ? "true" : undefined}
        >
          {vista.opciones_habitat.map((h) => {
            const esElegido = elegido === h.id;
            const esNeutral = exploradoNeutral?.id === h.id;
            return (
              <motion.button
                key={h.id}
                type="button"
                className={`tarjeta-habitat${esElegido ? " elegido" : ""}`}
                data-habitat={h.id}
                disabled={!vista.seleccion_habilitada}
                animate={
                  reducido
                    ? undefined
                    : esNeutral
                      ? { x: [0, -6, 6, -3, 0] }
                      : esElegido
                        ? { scale: [1, 1.022, 1] }
                        : { x: 0, scale: 1 }
                }
                whileTap={reducido || !vista.seleccion_habilitada ? undefined : { scale: 0.968 }}
                transition={
                  esNeutral ? { duration: 0.36, ease: "easeOut" } : { type: "spring", stiffness: 380, damping: 26 }
                }
                onPointerMove={moverTiltTarjeta}
                onPointerLeave={resetTiltTarjeta}
                onClick={() => {
                  setPulsado((prev) => ({
                    reto: vista.reto_id,
                    id: h.id,
                    intento: (prev?.intento ?? 0) + 1,
                  }));
                  onAccion("seleccionar_habitat", { habitat_id: h.id });
                }}
              >
                <img className="paisaje" src={`/habitats/${h.id}.webp`} alt="" draggable={false} loading="lazy" />
                <span>{h.nombre}</span>
                {esElegido && (
                  <>
                    <motion.b
                      className="insignia"
                      aria-hidden="true"
                      initial={reducido ? false : { opacity: 0, scale: 0.6 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ type: "spring", stiffness: 440, damping: 18 }}
                    >
                      ✓
                    </motion.b>
                    {!reducido && (
                      <span className="destellos-acierto" aria-hidden="true">
                        {CONFETI_ACIERTO.map((p) => (
                          <motion.i
                            key={p.id}
                            className={`destello-pieza destello-${p.tipo}`}
                            initial={{ opacity: 0.96, x: 0, y: 0, scale: 0.5, rotate: 0 }}
                            animate={{ opacity: 0, x: p.dx, y: p.dy, scale: p.s, rotate: p.r }}
                            transition={{ duration: 0.85, delay: p.d, ease: [0.22, 1, 0.36, 1] }}
                          />
                        ))}
                      </span>
                    )}
                  </>
                )}
              </motion.button>
            );
          })}
        </div>
      </section>
      {/* Después de los hábitats: así el orden del foco coincide con el visual en móvil. */}
      <Controles vista={vista} hablando={hablando} invitarPista={invitarPista} onAccion={onAccion} />
    </section>
  );
}
