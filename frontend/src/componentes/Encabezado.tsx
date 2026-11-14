import type { Vista } from "../api/tipos";
import { useT } from "../i18n";

export function Encabezado({
  vista,
  etiqueta,
  titulo,
  subtitulo,
}: {
  vista: Vista;
  etiqueta: string;
  titulo: string;
  subtitulo?: string;
}) {
  const { t } = useT();
  const { completados, total } = vista.progreso;
  return (
    <header className="encabezado-pantalla">
      <div>
        <p className="etiqueta">{t(etiqueta)}</p>
        <h1 id="titulo-pantalla" tabIndex={-1}>
          {t(titulo)}
        </h1>
        {subtitulo && <p className="subtitulo">{t(subtitulo)}</p>}
      </div>
      <div className="progreso">
        <span>{t("{n} de {total} completados", { n: completados, total })}</span>
        <progress max={total} value={completados} aria-label={t("Progreso de la partida")} />
      </div>
    </header>
  );
}
