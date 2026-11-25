import { forwardRef, useState } from "react";
import type { Idioma, VozGrabadaInfo } from "../api/tipos";
import { useT } from "../i18n";
import { IDIOMAS_CON_VOZ } from "../voz";
import { CERRAR_FUERA } from "./dialogos";
import { Icono } from "./Icono";

export type TemaVisual = "noche" | "dia" | "contraste";
export type EscalaTexto = "pequeno" | "normal" | "grande";

export interface ValoresPreferencias {
  retos: string;
  opciones: number;
  vozActiva: boolean;
  vozGrabada: string;
  velocidad: number;
  sonidoBosque: boolean;
  protegerPreferencias: boolean;
  movimientoReducido: boolean | null;
  tema: TemaVisual;
  escala: EscalaTexto;
}

interface Props {
  idioma: Idioma;
  valores: ValoresPreferencias;
  enInicio: boolean;
  /** Mensajes con grabación de la voz de Zoonauta en el idioma actual. */
  grabadas: number;
  /** Voces grabadas disponibles para el idioma actual. */
  vocesDisponibles: VozGrabadaInfo[];
  sistemaReduce: boolean;
  puedeInstalar?: boolean;
  onInstalar?: () => void;
  onCambio: (cambios: Partial<ValoresPreferencias>) => void;
  onIdioma: (idioma: Idioma) => void;
  onProbarVoz: () => void;
  onCerrar: () => void;
}

/**
 * Preferencias «Tu expedición / A tu manera.»: controles y textos de la 5.0 con el diseño
 * aprobado en la maqueta «Bosque de luz». Modal nativo con cabecera y pie fijos y contenido
 * desplazable solo si no cabe (Modern Web Guidance: dialog, light-dismiss-a-dialog,
 * prevent-page-scroll-under-modal-dialog, animate-to-from-top-layer, switch).
 */
export const Preferencias = forwardRef<HTMLDialogElement, Props>(function Preferencias(
  {
    idioma,
    valores,
    enInicio,
    grabadas,
    vocesDisponibles,
    sistemaReduce,
    puedeInstalar = false,
    onInstalar,
    onCambio,
    onIdioma,
    onProbarVoz,
    onCerrar,
  },
  ref,
) {
  const { t } = useT();
  const [hayMas, setHayMas] = useState(false);
  const hayVoz = grabadas > 0;
  const vozHabilitada = IDIOMAS_CON_VOZ.includes(idioma) && hayVoz;
  const opcionesVoz: VozGrabadaInfo[] = !vozHabilitada
    ? []
    : vocesDisponibles.length > 0
      ? vocesDisponibles
      : [
          idioma === "en"
            ? { id: "mark", etiqueta: "Mark · ElevenLabs", cantidad: grabadas }
            : idioma === "pt-BR"
              ? { id: "roberta", etiqueta: "Roberta · ElevenLabs", cantidad: grabadas }
              : { id: "marcela", etiqueta: "Marcela · ElevenLabs", cantidad: grabadas },
        ];
  const vozActual = opcionesVoz.some((v) => v.id === valores.vozGrabada)
    ? valores.vozGrabada
    : (opcionesVoz[0]?.id ?? "");
  const vozActiva = vozHabilitada && valores.vozActiva;
  const etiquetaVoz =
    idioma === "en" ? "Voz en inglés" : idioma === "pt-BR" ? "Voz en portugués brasileño" : "Voz en español";
  const notaVoz = !vozHabilitada
    ? idioma === "en"
      ? "La voz en inglés todavía no está disponible."
      : idioma === "pt-BR"
        ? "La voz en portugués todavía no está disponible."
        : "Faltan las grabaciones de la voz de Zoonauta en assets/voz/grabada."
    : "Voz grabada de Zoonauta. Funciona en este equipo, sin Internet.";

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
            <option value="en">English</option>
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
          {/* Voces grabadas disponibles en español (Marcela, Valeria). En pt-BR queda bloqueado. */}
          <div className="pref-campo" data-apagado={!vozActiva || undefined}>
            <label htmlFor="pref-voces">{t(etiquetaVoz)}</label>
            <select
              id="pref-voces"
              value={vozHabilitada ? vozActual : ""}
              disabled={!vozActiva || !hayVoz}
              aria-describedby="nota-voz"
              onChange={(e) => onCambio({ vozGrabada: e.target.value })}
            >
              {vozHabilitada ? (
                opcionesVoz.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.etiqueta}
                  </option>
                ))
              ) : (
                <option value="">{t("Sin voces disponibles")}</option>
              )}
            </select>
            <p id="nota-voz" className="nota" role="status">
              {t(notaVoz)}
            </p>
          </div>
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

        <div className="pref-sonido">
          <label className="interruptor">
            <span className="interruptor-texto">
              <span className="interruptor-titulo">{t("Sonidos del bosque")}</span>
              <span className="nota">{t("Ambiente suave y tonos de aviso.")}</span>
            </span>
            <input
              type="checkbox"
              role="switch"
              {...{ switch: "" }}
              checked={valores.sonidoBosque}
              onChange={(e) => onCambio({ sonidoBosque: e.target.checked })}
            />
          </label>
          <label className="interruptor">
            <span className="interruptor-texto">
              <span className="interruptor-titulo">{t("Proteger Preferencias")}</span>
              <span className="nota">{t("Mantener pulsado para abrir.")}</span>
            </span>
            <input
              type="checkbox"
              role="switch"
              {...{ switch: "" }}
              checked={valores.protegerPreferencias}
              onChange={(e) => onCambio({ protegerPreferencias: e.target.checked })}
            />
          </label>
        </div>

        <fieldset className="pref-grupo pref-pantalla">
          <legend>{t("Pantalla")}</legend>
          <label className="interruptor">
            <span className="interruptor-texto">
              <span className="interruptor-titulo">{t("Reducir movimiento")}</span>
              {sistemaReduce && (valores.movimientoReducido ?? true) && (
                <span className="nota" id="nota-movimiento">
                  {t("Tu equipo ya pide reducir el movimiento.")}
                </span>
              )}
            </span>
            <input
              type="checkbox"
              role="switch"
              {...{ switch: "" }}
              checked={valores.movimientoReducido ?? sistemaReduce}
              aria-describedby={sistemaReduce && (valores.movimientoReducido ?? true) ? "nota-movimiento" : undefined}
              onChange={(e) => onCambio({ movimientoReducido: e.target.checked })}
            />
          </label>
          <div className="pref-fila-doble">
            <div className="pref-campo">
              <label htmlFor="pref-tema">{t("Aspecto visual")}</label>
              <select
                id="pref-tema"
                value={valores.tema}
                onChange={(e) => onCambio({ tema: e.target.value as TemaVisual })}
              >
                <option value="noche">{t("Bosque de noche")}</option>
                <option value="dia">{t("Bosque de día")}</option>
                <option value="contraste">{t("Alto contraste")}</option>
              </select>
            </div>
            <div className="pref-campo">
              <label htmlFor="pref-escala">{t("Tamaño de texto")}</label>
              <select
                id="pref-escala"
                value={valores.escala}
                onChange={(e) => onCambio({ escala: e.target.value as EscalaTexto })}
              >
                <option value="pequeno">{t("Pequeño")}</option>
                <option value="normal">{t("Normal")}</option>
                <option value="grande">{t("Grande")}</option>
              </select>
            </div>
          </div>
        </fieldset>
      </div>

      <footer className="pref-pie">
        <details className="pref-creditos">
          <summary>{t("Créditos visuales")}</summary>
          <div className="pref-creditos-caja">
            <p className="pref-version">
              Zoonauta <span>6.0.0</span>
            </p>
            <p>{t("Ilustraciones de animales, pictogramas y paisajes originales generados con IA.")}</p>
          </div>
        </details>
        <div className="pref-pie-acciones">
          {puedeInstalar && onInstalar && (
            <button type="button" className="boton-secundario pref-instalar" onClick={onInstalar}>
              <Icono nombre="descargar" />
              <span>{t("Instalar app")}</span>
            </button>
          )}
          <form method="dialog">
            <button className="pref-volver">
              {t("Volver al juego")} <span aria-hidden="true">↗</span>
            </button>
          </form>
        </div>
      </footer>
    </dialog>
  );
});
