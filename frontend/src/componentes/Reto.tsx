import type { TipoAccion, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Encabezado } from "./Encabezado";
import { Pictograma, useContenidoListo } from "./Pictograma";

const CONTROLES: Partial<Record<string, [string, string, string]>> = {
  ayuda: ["Pista", "P_AYUDA", "destacada"],
  repetir: ["Repetir", "P_REPETIR", ""],
  pausar: ["Pausar", "P_PAUSAR", ""],
  reanudar: ["Reanudar", "P_REANUDAR", ""],
  continuar: ["Continuar", "P_CONTINUAR", "continuar"],
  salir: ["Salir", "P_SALIR", "salir"],
};

export function Controles({ vista, onAccion }: { vista: Vista; onAccion: (tipo: TipoAccion) => void }) {
  const { t } = useT();
  return (
    <nav className="controles" aria-label={t("Controles de la partida")}>
      {vista.controles_disponibles.map((tipo) => {
        const control = CONTROLES[tipo];
        if (!control) return null;
        const [texto, picto, variante] = control;
        return (
          <button key={tipo} type="button" className={`control ${variante}`.trim()} data-control={tipo}
            onClick={() => onAccion(tipo as TipoAccion)}>
            <Pictograma id={picto} datos={vista.pictogramas[picto]} />
            <span>{t(texto)}</span>
          </button>
        );
      })}
    </nav>
  );
}

export function Guia({ vista }: { vista: Vista }) {
  const { t } = useT();
  // Texto y pictogramas cambian juntos cuando las imágenes nuevas están listas.
  const respuesta = useContenidoListo(vista.respuesta, vista.pictogramas);
  const tono = respuesta.tipo_respuesta === "CONFIRMACION" ? "confirmacion"
    : respuesta.tipo_respuesta === "NEUTRAL" ? "neutral" : "";
  return (
    <section className={`guia ${tono}`.trim()} aria-labelledby="mensaje">
      <p className="guia-cabecera"><img src="/zoonauta-logo.svg" alt="" width={28} height={28} />{t("Tu guía")}</p>
      <h2 id="mensaje" tabIndex={-1}>{t(respuesta.texto_apoyo)}</h2>
      <div className="secuencia" aria-label={t("Secuencia de pictogramas")}>
        {respuesta.pictogramas.map((id, i) => (
          <figure key={`${i}-${id}`} className="simbolo">
            <Pictograma id={id} datos={vista.pictogramas[id]} />
            <figcaption>{vista.pictogramas[id]?.etiqueta}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

export function Reto({ vista, onAccion }: {
  vista: Vista;
  onAccion: (tipo: TipoAccion, payload?: Record<string, unknown>) => void;
}) {
  const { t } = useT();
  const resuelto = vista.fase === "RETO_RESUELTO";
  const animal = vista.animal;
  return (
    <section className="pantalla reto-pantalla" aria-labelledby="titulo-pantalla">
      <Encabezado vista={vista} etiqueta="Encuentra su hábitat"
        titulo={resuelto ? "¡Encontraste un lugar!" : "Elige un hábitat"} />
      <div className="tablero">
        <aside className="panel-animal">
          {animal && (
            <div className="animal-actual">
              <p className="etiqueta">{t("Tu animal")}</p>
              <div className="animal-retrato">
                <Pictograma id={animal.pictograma_id} datos={vista.pictogramas[animal.pictograma_id]} />
              </div>
              <strong>{animal.nombre}</strong>
            </div>
          )}
          <Controles vista={vista} onAccion={onAccion} />
        </aside>
        <Guia vista={vista} />
        <div className="habitats-panel">
          {vista.fase === "ESPERANDO_RESPUESTA" && <p className="instruccion">{t("Toca un lugar donde pueda vivir.")}</p>}
          <div className="habitats" data-cantidad={vista.opciones_habitat.length} aria-label={t("Hábitats para elegir")}>
            {vista.opciones_habitat.map((h) => (
              <button key={h.id} type="button" className="tarjeta-habitat" data-habitat={h.id}
                disabled={!vista.seleccion_habilitada}
                onClick={() => onAccion("seleccionar_habitat", { habitat_id: h.id })}>
                <img className="paisaje" src={`/habitats/${h.id}.webp`} alt="" draggable={false} loading="lazy" />
                <span>{h.nombre}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
