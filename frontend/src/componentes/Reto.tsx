import { useState } from "react";
import type { TipoAccion, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Encabezado } from "./Encabezado";
import { Pictograma, useContenidoListo } from "./Pictograma";

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

export function Controles({ vista, onAccion }: { vista: Vista; onAccion: (tipo: TipoAccion) => void }) {
  const { t } = useT();
  const disponibles = Object.keys(CONTROLES).filter((tipo) => vista.controles_disponibles.includes(tipo));
  const boton = (tipo: string) => {
    const { texto, picto } = CONTROLES[tipo]!;
    return (
      <button
        key={tipo}
        type="button"
        className="control"
        data-control={tipo}
        onClick={() => onAccion(tipo as TipoAccion)}
      >
        <Pictograma id={picto} datos={vista.pictogramas[picto]} />
        <span>{t(texto)}</span>
      </button>
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
export function TiraPictogramas({ ids, vista }: { ids: string[]; vista: Vista }) {
  const { t } = useT();
  return (
    <ol className="tira" aria-label={t("Secuencia de pictogramas")}>
      {ids.map((id, i) => (
        <li key={`${i}-${id}`} className="tira-celda">
          <Pictograma id={id} datos={vista.pictogramas[id]} />
          <span>{vista.pictogramas[id]?.etiqueta}</span>
        </li>
      ))}
    </ol>
  );
}

export function Guia({ vista, fotoHabitat }: { vista: Vista; fotoHabitat?: string | null }) {
  const { t } = useT();
  // Texto y pictogramas cambian juntos cuando las imágenes nuevas están listas.
  const respuesta = useContenidoListo(vista.respuesta, vista.pictogramas);
  const tono =
    respuesta.tipo_respuesta === "CONFIRMACION"
      ? "confirmacion"
      : respuesta.tipo_respuesta === "NEUTRAL"
        ? "neutral"
        : "";
  return (
    <section className={`guia ${tono}`.trim()} aria-labelledby="mensaje">
      <p className="guia-cabecera">
        <img src="/zoonauta-logo.svg" alt="" width={32} height={32} />
        {t("Tu guía")}
      </p>
      <h2 id="mensaje" tabIndex={-1}>
        {t(respuesta.texto_apoyo)}
      </h2>
      <TiraPictogramas ids={respuesta.pictogramas} vista={vista} />
      {fotoHabitat && (
        // El hábitat acertado, a la vista junto a la frase que lo nombra.
        <img className="guia-foto" src={`/habitats/${fotoHabitat}.webp`} alt="" draggable={false} />
      )}
    </section>
  );
}

export function Reto({
  vista,
  onAccion,
}: {
  vista: Vista;
  onAccion: (tipo: TipoAccion, payload?: Record<string, unknown>) => void;
}) {
  const { t } = useT();
  const resuelto = vista.fase === "RETO_RESUELTO";
  const animal = vista.animal;
  // Último hábitat pulsado en este reto: al resolverse es el acertado. Tras recargar la
  // página no se conoce y simplemente no se destaca nada (sin atenuar las demás).
  const [pulsado, setPulsado] = useState<{ reto: string | null; id: string } | null>(null);
  const elegido = resuelto && pulsado && pulsado.reto === vista.reto_id ? pulsado.id : null;
  return (
    <section className="pantalla reto-pantalla" aria-labelledby="titulo-pantalla">
      <Encabezado
        vista={vista}
        etiqueta="Encuentra su hábitat"
        titulo={resuelto ? "¡Encontraste un lugar!" : "Elige un hábitat"}
      />
      <div className="tablero">
        {animal && (
          <figure className="animal-actual">
            <span className="rotulo">{t("Tu animal")}</span>
            <Pictograma id={animal.pictograma_id} datos={vista.pictogramas[animal.pictograma_id]} />
            <figcaption>
              <strong>{animal.nombre}</strong>
            </figcaption>
          </figure>
        )}
        <Guia vista={vista} fotoHabitat={elegido} />
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
          {vista.opciones_habitat.map((h) => (
            <button
              key={h.id}
              type="button"
              className={`tarjeta-habitat${elegido === h.id ? " elegido" : ""}`}
              data-habitat={h.id}
              disabled={!vista.seleccion_habilitada}
              onClick={() => {
                setPulsado({ reto: vista.reto_id, id: h.id });
                onAccion("seleccionar_habitat", { habitat_id: h.id });
              }}
            >
              <img className="paisaje" src={`/habitats/${h.id}.webp`} alt="" draggable={false} loading="lazy" />
              <span>{h.nombre}</span>
              {elegido === h.id && (
                <b className="insignia" aria-hidden="true">
                  ✓
                </b>
              )}
            </button>
          ))}
        </div>
      </section>
      {/* Después de los hábitats: así el orden del foco coincide con el visual en móvil. */}
      <Controles vista={vista} onAccion={onAccion} />
    </section>
  );
}
