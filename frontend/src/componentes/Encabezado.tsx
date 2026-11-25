import type { Vista } from "../api/tipos";
import { useT } from "../i18n";
import { NumeroAnimado } from "./NumeroAnimado";
import { SenderoProgreso } from "./SenderoProgreso";

/** Rótulo, título de la pantalla y avance real de la partida (el servidor es la fuente). */
export function Encabezado({
  vista,
  titulo,
  subtitulo,
  etiqueta,
  reducido = false,
}: {
  vista: Vista;
  titulo: string;
  subtitulo?: string;
  etiqueta?: string;
  reducido?: boolean;
}) {
  const { t } = useT();
  const { completados, total } = vista.progreso;
  const plantilla = t("{n} de {total} completados", { n: "__N__", total });
  const partes = plantilla.split("__N__");
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
        <span className="progreso-texto">
          {partes[0]}
          <NumeroAnimado valor={completados} reducido={reducido} />
          {partes[1] ?? ""}
        </span>
        <SenderoProgreso completados={completados} total={total} etiquetaAria={t("Progreso de la partida")} />
      </div>
    </header>
  );
}
