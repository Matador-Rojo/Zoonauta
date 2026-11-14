import { forwardRef, useState } from "react";
import type { Idioma } from "../api/tipos";
import { useT } from "../i18n";
import { IDIOMAS_CON_VOZ, SOLO_VOZ_GRABADA, type OpcionVoz } from "../voz";
import { CERRAR_FUERA } from "./dialogos";
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
  /** Mensajes con grabación de la voz de Zoonauta en el idioma actual. */
  grabadas: number;
  sistemaReduce: boolean;
  onCambio: (cambios: Partial<ValoresPreferencias>) => void;
  onIdioma: (idioma: Idioma) => void;
  onProbarVoz: () => void;
  onCerrar: () => void;
}

const MOTORES = [
  ["google", "Google"],
  ["microsoft", "Microsoft"],
  ["piper", "Piper"],
  ["kokoro", "Kokoro"],
] as const;
const CALIDAD: Record<string, string> = {
  high: "Calidad alta",
  medium: "Calidad media",
  low: "Calidad baja",
  x_low: "Ligera",
};

/**
 * Preferencias «Tu expedición / A tu manera.»: controles y textos de la 5.0 con el diseño
 * aprobado en la maqueta «Bosque de luz». Modal nativo con cabecera y pie fijos y contenido
 * desplazable solo si no cabe (Modern Web Guidance: dialog, light-dismiss-a-dialog,
 * prevent-page-scroll-under-modal-dialog, animate-to-from-top-layer, switch).
 */
export const Preferencias = forwardRef<HTMLDialogElement, Props>(function Preferencias(
  { idioma, valores, enInicio, voces, grabadas, sistemaReduce, onCambio, onIdioma, onProbarVoz, onCerrar },
  ref,
) {
  const { t } = useT();
  const [hayMas, setHayMas] = useState(false);
  const region = (codigo: string) => {
    if (codigo === "419") return t("Latinoamérica");
    try {
      return new Intl.DisplayNames([idioma], { type: "region" }).of(codigo) ?? codigo;
    } catch {
      return codigo;
    }
  };
  const vozHabilitada = IDIOMAS_CON_VOZ.includes(idioma);
  const hayVoz = SOLO_VOZ_GRABADA ? grabadas > 0 : voces.some((v) => v.disponible);
  const vozActiva = vozHabilitada && valores.vozActiva;
  const elegida = voces.find((v) => v.id === valores.vozId);
  const notaVoz = !vozHabilitada
    ? "La voz en portugués todavía no está disponible."
    : SOLO_VOZ_GRABADA
      ? hayVoz
        ? "Voz grabada de Zoonauta. Funciona en este equipo, sin Internet."
        : "Faltan las grabaciones de la voz de Zoonauta en assets/voz/grabada."
      : !hayVoz
        ? "No hay voces preparadas para este idioma. Abre iniciar_juego.bat para descargar los modelos."
        : elegida?.nativa
          ? elegida.local
            ? "Voz del navegador instalada en este equipo. No requiere descargar modelos."
            : "Voz del navegador. Puede necesitar Internet; no requiere descargar modelos."
          : "Las voces se reproducen en este equipo, sin conexión después de preparar los modelos.";
  const notaNavegador = voces.some((v) => v.nativa)
    ? "Microsoft y Google: se muestran las voces compatibles que ofrece tu navegador."
    : "Este navegador no ofrece voces de Microsoft o Google para esta región. Puedes usar Piper o Kokoro.";

  // Retos: se escribe libremente y se ajusta de 1 a 48 al salir o con − / +.
  const numero = Number.parseInt(valores.retos, 10);
  const fijarRetos = (n: number) => onCambio({ retos: String(Math.min(48, Math.max(1, Number.isNaN(n) ? 8 : n))) });

  // Aviso «hay más abajo» mientras quede contenido por ver (móvil y pantallas bajas).
  const medir = (el: HTMLElement | null) => {
    if (!el) return;
    setHayMas(el.scrollTop + el.clientHeight < el.scrollHeight - 4);
  };

  return (
    <dialog
      ref={ref}
      className="preferencias"
      aria-labelledby="titulo-preferencias"
      {...CERRAR_FUERA}
      onClose={onCerrar}
      onToggle={(e) => medir(e.currentTarget.querySelector<HTMLElement>(".pref-contenido"))}
    >
      <header className="pref-cabecera">
        <div>
          <p className="rotulo">{t("Tu expedición")}</p>
          <h2 id="titulo-preferencias">{t("A tu manera.")}</h2>
          <p className="pref-subtitulo">{t("Un ritmo cómodo. Una voz que te acompañe.")}</p>
        </div>
        <form method="dialog">
          <button className="cerrar-dialogo" aria-label={t("Cerrar Preferencias")}>
            <Icono nombre="cerrar" />
          </button>
        </form>
      </header>

      <div className="pref-contenido" data-mas={hayMas || undefined} onScroll={(e) => medir(e.currentTarget)}>
        <div className="pref-campo pref-idioma">
          <label htmlFor="pref-idioma">{t("Idioma")}</label>
          <select id="pref-idioma" value={idioma} onChange={(e) => onIdioma(e.target.value as Idioma)}>
            <option value="es">Español</option>
            <option value="pt-BR">Português (Brasil)</option>
          </select>
        </div>

        <fieldset className="pref-grupo pref-partida" disabled={!enInicio}>
          <legend>{t("La partida")}</legend>
          <div className="pref-campo">
            <label htmlFor="pref-retos">{t("¿Cuántos animales quieres explorar?")}</label>
            <div className="paso-a-paso">
              <button
                type="button"
                className="paso"
                aria-label={t("Uno menos")}
                aria-controls="pref-retos"
                disabled={!enInicio || numero <= 1}
                onClick={() => fijarRetos((Number.isNaN(numero) ? 8 : numero) - 1)}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M6 12h12" />
                </svg>
              </button>
              <input
                id="pref-retos"
                type="text"
                inputMode="numeric"
                autoComplete="off"
                value={valores.retos}
                aria-describedby="nota-retos"
                onChange={(e) => onCambio({ retos: e.target.value.trim() })}
                onBlur={() => fijarRetos(numero)}
                onKeyDown={(e) => {
                  if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
                  e.preventDefault();
                  fijarRetos((Number.isNaN(numero) ? 8 : numero) + (e.key === "ArrowUp" ? 1 : -1));
                }}
              />
              <button
                type="button"
                className="paso"
                aria-label={t("Uno más")}
                aria-controls="pref-retos"
                disabled={!enInicio || numero >= 48}
                onClick={() => fijarRetos((Number.isNaN(numero) ? 8 : numero) + 1)}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M6 12h12M12 6v12" />
                </svg>
              </button>
            </div>
            <p id="nota-retos" className="nota">
              {t("De 1 a 48. Se aplica al comenzar; todos los animales siguen disponibles.")}
            </p>
          </div>
          <div className="pref-campo">
            <label htmlFor="pref-opciones">{t("Hábitats para elegir")}</label>
            <select
              id="pref-opciones"
              value={valores.opciones}
              aria-describedby="nota-opciones"
              onChange={(e) => onCambio({ opciones: Number(e.target.value) })}
            >
              {[2, 4, 8].map((n) => (
                <option key={n} value={n}>
                  {t(`${n} hábitats`)}
                </option>
              ))}
            </select>
            <p id="nota-opciones" className="nota">
              {t("Menos opciones para empezar. Se aplica a la próxima partida.")}
            </p>
          </div>
        </fieldset>

        <fieldset className="pref-grupo pref-voz">
          <legend>{t("Voz")}</legend>
          <label className="interruptor">
            <span className="interruptor-texto">
              <span className="interruptor-titulo">{t("Una guía con voz")}</span>
              <span className="nota">{t("Leer las respuestas en voz alta.")}</span>
            </span>
            <input
              type="checkbox"
              role="switch"
              {...{ switch: "" }}
              checked={vozActiva}
              disabled={!vozHabilitada}
              onChange={(e) => onCambio({ vozActiva: e.target.checked })}
            />
          </label>
          {SOLO_VOZ_GRABADA ? (
            // Una sola voz por ahora: Marcela (ElevenLabs). En pt-BR el selector queda bloqueado.
            <div className="pref-campo" data-apagado={!vozActiva || undefined}>
              <label htmlFor="pref-voces">
                {t(idioma === "pt-BR" ? "Voz en portugués brasileño" : "Voz en español")}
              </label>
              <select
                id="pref-voces"
                value={vozHabilitada ? "marcela" : ""}
                disabled={!vozActiva || !hayVoz}
                aria-describedby="nota-voz"
                onChange={() => undefined}
              >
                {vozHabilitada ? (
                  <option value="marcela">Marcela · ElevenLabs</option>
                ) : (
                  <option value="">{t("Sin voces disponibles")}</option>
                )}
              </select>
              <p id="nota-voz" className="nota" role="status">
                {t(notaVoz)}
              </p>
            </div>
          ) : (
            <div className="pref-campo" data-apagado={!vozActiva || undefined}>
              <label htmlFor="pref-voces">
                {t(idioma === "pt-BR" ? "Voz en portugués brasileño" : "Voz en español")}
              </label>
              <select
                id="pref-voces"
                value={vozHabilitada ? valores.vozId : ""}
                disabled={!vozActiva || !hayVoz}
                aria-describedby="nota-voz nota-navegador"
                onChange={(e) => onCambio({ vozId: e.target.value })}
              >
                {!vozHabilitada && <option value="">{t("Sin voces disponibles")}</option>}
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
              <p id="nota-voz" className="nota" role="status">
                {t(notaVoz)}
              </p>
              {vozHabilitada && (
                <p id="nota-navegador" className="nota">
                  {t(notaNavegador)}
                </p>
              )}
            </div>
          )}
          <div className="pref-campo" data-apagado={!vozActiva || undefined}>
            <label htmlFor="pref-velocidad">{t("Ritmo de lectura")}</label>
            <select
              id="pref-velocidad"
              value={valores.velocidad}
              disabled={!vozActiva}
              onChange={(e) => onCambio({ velocidad: Number(e.target.value) })}
            >
              <option value={0.8}>{t("Despacio")}</option>
              <option value={0.95}>{t("Natural")}</option>
              <option value={1.1}>{t("Más ágil")}</option>
            </select>
          </div>
          <button
            type="button"
            className="boton-secundario pref-probar"
            disabled={!vozActiva || !hayVoz}
            onClick={onProbarVoz}
          >
            <Icono nombre="reproducir" />
            <span>{t("Probar voz")}</span>
          </button>
        </fieldset>

        <fieldset className="pref-grupo pref-pantalla">
          <legend>{t("Pantalla")}</legend>
          <label className="interruptor">
            <span className="interruptor-texto">
              <span className="interruptor-titulo">{t("Reducir movimiento")}</span>
              {sistemaReduce && (
                <span className="nota" id="nota-movimiento">
                  {t("Tu equipo ya pide reducir el movimiento.")}
                </span>
              )}
            </span>
            <input
              type="checkbox"
              role="switch"
              {...{ switch: "" }}
              checked={valores.movimientoReducido || sistemaReduce}
              disabled={sistemaReduce}
              aria-describedby={sistemaReduce ? "nota-movimiento" : undefined}
              onChange={(e) => onCambio({ movimientoReducido: e.target.checked })}
            />
          </label>
        </fieldset>
      </div>

      <footer className="pref-pie">
        <details className="pref-creditos">
          <summary>{t("Créditos visuales")}</summary>
          <div className="pref-creditos-caja">
            <p className="pref-version">
              Zoonauta <span>6.0</span>
            </p>
            <p>{t("Ilustraciones de animales, pictogramas y paisajes originales generados con IA.")}</p>
          </div>
        </details>
        <form method="dialog">
          <button className="pref-volver">
            {t("Volver al juego")} <span aria-hidden="true">↗</span>
          </button>
        </form>
      </footer>
    </dialog>
  );
});
