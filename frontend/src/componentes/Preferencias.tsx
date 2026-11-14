import { forwardRef } from "react";
import type { Idioma } from "../api/tipos";
import { useT } from "../i18n";
import type { OpcionVoz } from "../voz";
import { Icono } from "./Icono";

export interface ValoresPreferencias {
  retos: string;
  opciones: number;
  vozActiva: boolean;
  vozId: string;
  velocidad: number;
  movimientoReducido: boolean;
}

interface Props {
  idioma: Idioma;
  valores: ValoresPreferencias;
  enInicio: boolean;
  voces: OpcionVoz[];
  sistemaReduce: boolean;
  onCambio: (cambios: Partial<ValoresPreferencias>) => void;
  onIdioma: (idioma: Idioma) => void;
  onProbarVoz: () => void;
  onCerrar: () => void;
}

const MOTORES = [["google", "Google"], ["microsoft", "Microsoft"], ["piper", "Piper"], ["kokoro", "Kokoro"]] as const;
const CALIDAD: Record<string, string> = { high: "Calidad alta", medium: "Calidad media", low: "Calidad baja", x_low: "Ligera" };

// Diálogo modal nativo (Modern Web Guidance, dialog: showModal, sin role ni trampa de foco manual).
export const Preferencias = forwardRef<HTMLDialogElement, Props>(function Preferencias(
  { idioma, valores, enInicio, voces, sistemaReduce, onCambio, onIdioma, onProbarVoz, onCerrar }, ref,
) {
  const { t } = useT();
  const region = (codigo: string) => {
    if (codigo === "419") return t("Latinoamérica");
    try { return new Intl.DisplayNames([idioma], { type: "region" }).of(codigo) ?? codigo; } catch { return codigo; }
  };
  const hayVoz = voces.some((v) => v.disponible);
  return (
    <dialog ref={ref} className="preferencias" aria-labelledby="titulo-preferencias" onClose={onCerrar}>
      <div className="preferencias-cabecera">
        <div>
          <p className="etiqueta">{t("Tu expedición")}</p>
          <h2 id="titulo-preferencias">{t("A tu manera.")}</h2>
        </div>
        <form method="dialog">
          <button className="control-redondo" aria-label={t("Cerrar Preferencias")}><Icono nombre="cerrar" /></button>
        </form>
      </div>

      <div className="preferencias-columnas">
        <div className="preferencias-columna">
          <label className="campo">
            <span>{t("Idioma")}</span>
            <select value={idioma} onChange={(e) => onIdioma(e.target.value as Idioma)}>
              <option value="es">Español</option>
              <option value="pt-BR">Português (Brasil)</option>
            </select>
          </label>
          <label className="campo">
            <span>{t("Retos por partida")}</span>
            <input type="number" min={1} max={48} step={1} inputMode="numeric" value={valores.retos} disabled={!enInicio}
              aria-describedby="nota-retos" onChange={(e) => onCambio({ retos: e.target.value })} />
          </label>
          <p id="nota-retos" className="nota">{t("De 1 a 48. Se aplica al comenzar; todos los animales siguen disponibles.")}</p>
          <label className="campo">
            <span>{t("Hábitats para elegir")}</span>
            <select value={valores.opciones} disabled={!enInicio} aria-describedby="nota-opciones"
              onChange={(e) => onCambio({ opciones: Number(e.target.value) })}>
              {[2, 4, 8].map((n) => <option key={n} value={n}>{t(`${n} hábitats`)}</option>)}
            </select>
          </label>
          <p id="nota-opciones" className="nota">{t("Menos opciones para empezar. Se aplica a la próxima partida.")}</p>
          <label className="interruptor">
            <span>
              <span className="interruptor-titulo">{t("Reducir movimiento")}</span>
              <span className="nota" id="nota-movimiento">{t(sistemaReduce
                ? "Tu equipo ya pide reducir el movimiento. Las fotografías quedan fijas."
                : "Muestra fotografías fijas y cambia de paisaje solo con los botones.")}</span>
            </span>
            <input type="checkbox" role="switch" checked={valores.movimientoReducido || sistemaReduce}
              disabled={sistemaReduce} aria-describedby="nota-movimiento"
              onChange={(e) => onCambio({ movimientoReducido: e.target.checked })} />
          </label>
        </div>

        <div className="preferencias-columna">
          <label className="interruptor">
            <span>
              <span className="interruptor-titulo">{t("Una guía con voz")}</span>
              <span className="nota">{t("Leer las respuestas en voz alta.")}</span>
            </span>
            <input type="checkbox" role="switch" checked={valores.vozActiva}
              onChange={(e) => onCambio({ vozActiva: e.target.checked })} />
          </label>
          <label className="campo">
            <span>{t(idioma === "pt-BR" ? "Voz en portugués brasileño" : "Voz en español")}</span>
            <select value={valores.vozId} disabled={!hayVoz} onChange={(e) => onCambio({ vozId: e.target.value })}>
              {MOTORES.map(([motor, nombre]) => {
                const grupo = voces.filter((v) => v.motor === motor);
                if (!grupo.length) return null;
                return (
                  <optgroup key={motor} label={nombre}>
                    {grupo.map((v) => (
                      <option key={v.id} value={v.id} disabled={!v.disponible}>
                        {`${v.nombre} · ${region(v.region)}${v.calidad ? " · " + t(CALIDAD[v.calidad] ?? v.calidad) : ""}`}
                      </option>
                    ))}
                  </optgroup>
                );
              })}
            </select>
          </label>
          <label className="campo">
            <span>{t("Ritmo de lectura")}</span>
            <select value={valores.velocidad} onChange={(e) => onCambio({ velocidad: Number(e.target.value) })}>
              <option value={0.8}>{t("Despacio")}</option>
              <option value={0.95}>{t("Natural")}</option>
              <option value={1.1}>{t("Más ágil")}</option>
            </select>
          </label>
          <button type="button" className="boton-secundario" disabled={!hayVoz} onClick={onProbarVoz}>
            <Icono nombre="reproducir" /><span>{t("Probar voz")}</span>
          </button>
        </div>
      </div>

      <form method="dialog" className="preferencias-pie">
        <button className="boton-principal" autoFocus>{t("Volver al juego")}</button>
      </form>
    </dialog>
  );
});
