import type { TipoAccion, Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Pictograma } from "./Pictograma";
import { Controles, TiraPictogramas } from "./Reto";

// Pausa y cierre reutilizan las ilustraciones existentes del robot.
export function Cierre({ vista, onAccion }: { vista: Vista; onAccion: (tipo: TipoAccion) => void }) {
  const { t } = useT();
  const pausa = vista.fase === "PAUSADA";
  const titulo = pausa ? "Tomamos una pausa" : vista.fase === "COMPLETADA" ? "¡Terminamos!" : "Partida terminada";
  const { completados, total } = vista.progreso;
  return (
    <section className="pantalla cierre" data-estado={vista.fase} aria-labelledby="titulo-pantalla">
      <figure className="cierre-visual">
        <img
          src={`/ilustraciones/${pausa ? "robot_pausa" : "robot_despedida"}.webp`}
          // Proporciones reales (1:1 y 2:3) para reservar el espacio y evitar saltos.
          width={pausa ? 640 : 427}
          height={640}
          alt={t("Tu guía")}
          draggable={false}
        />
        <figcaption>{t(pausa ? "A tu ritmo" : "Gracias por jugar")}</figcaption>
      </figure>
      <div className="cierre-contenido">
        <h1 id="titulo-pantalla" tabIndex={-1}>
          {t(titulo)}
        </h1>
        <p className="introduccion">{t(vista.respuesta.texto_apoyo)}</p>
        <TiraPictogramas ids={vista.respuesta.pictogramas} vista={vista} />
        <div className="cierre-resumen">
          <strong>
            {completados} / {total}
          </strong>
          <span>{t("Retos completados")}</span>
          <progress max={total} value={completados} aria-label={t("Progreso de la partida")} />
        </div>
        {pausa ? (
          <Controles vista={vista} onAccion={onAccion} />
        ) : (
          <button type="button" className="boton-principal" onClick={() => onAccion("nueva_partida")}>
            <Pictograma id="P_INICIAR" datos={vista.pictogramas.P_INICIAR} />
            <span>{t("Comenzar otra partida")}</span>
          </button>
        )}
      </div>
    </section>
  );
}
