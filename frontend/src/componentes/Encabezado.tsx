import type { Vista } from "../api/tipos";
import { useT } from "../i18n";

/** Rótulo, título de la pantalla y avance real de la partida (el servidor es la fuente). */
export function Encabezado({
  vista,
  titulo,
  subtitulo,
  etiqueta,
}: {
  vista: Vista;
  titulo: string;
  subtitulo?: string;
  etiqueta?: string;
}) {
  const { t } = useT();
  const { completados, total } = vista.progreso;
  return (
    <header className="encabezado-pantalla">
      <div className="encabezado-texto">
        {etiqueta && <p className="rotulo">{t(etiqueta)}</p>}
        <h1 id="titulo-pantalla" tabIndex={-1}>
          {t(titulo)}
        </h1>
        {subtitulo && <p className="subtitulo">{t(subtitulo)}</p>}
      </div>
      <div className="progreso">
        <span className="progreso-texto">{t("{n} de {total} completados", { n: completados, total })}</span>
        <progress max={total} value={completados} aria-label={t("Progreso de la partida")} />
      </div>
    </header>
  );
}
