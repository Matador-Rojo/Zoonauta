import { forwardRef, useState } from "react";
import type { Pictograma } from "../api/tipos";
import { resumenAlbum, type RegistroAlbum } from "../album";
import { useT } from "../i18n";
import { CERRAR_FUERA } from "./dialogos";
import { Icono } from "./Icono";
import { NumeroAnimado } from "./NumeroAnimado";

const POR_PAGINA_ALBUM = 9;

interface Props {
  registros: RegistroAlbum[];
  pictogramas?: Record<string, Pictograma>;
  reducido: boolean;
  onReiniciar: () => void;
  onCerrar: () => void;
}

/**
 * Pasaporte / Álbum persistente de expedición:
 * - Dos series de 5 estrellas (5 de animales y 5 de hábitats).
 * - Rejilla paginada 3×3 (máximo 9 hallazgos por página) con navegación izquierda / derecha.
 * - Botón discreto de reinicio en dos pasos en el pie izquierdo.
 */
export const Album = forwardRef<HTMLDialogElement, Props>(function Album(
  { registros, pictogramas, reducido, onReiniciar, onCerrar },
  ref,
) {
  const { t } = useT();
  const [pagina, setPagina] = useState(0);
  const [confirmandoReinicio, setConfirmandoReinicio] = useState(false);
  const { animalesUnicos, habitatsUnicos, medallasAnimales, medallasHabitats } = resumenAlbum(registros);

  const totalPaginas = Math.max(1, Math.ceil(registros.length / POR_PAGINA_ALBUM));
  const paginaActual = Math.min(pagina, totalPaginas - 1);
  const visibles = registros.slice(paginaActual * POR_PAGINA_ALBUM, (paginaActual + 1) * POR_PAGINA_ALBUM);

  return (
    <dialog
      ref={ref}
      className="album-dialogo"
      aria-labelledby="titulo-album"
      {...CERRAR_FUERA}
      onClose={() => {
        setConfirmandoReinicio(false);
        onCerrar();
      }}
    >
      <header className="pref-cabecera album-cabecera">
        <div>
          <p className="rotulo">{t("Tu pasaporte")}</p>
          <h2 id="titulo-album">{t("Mi álbum de expedición")}</h2>
          <p className="pref-subtitulo">{t("Cada animal que descubres guarda su sello en tu cuaderno.")}</p>
        </div>
        <form method="dialog">
          <button className="cerrar-dialogo" aria-label={t("Cerrar álbum")}>
            <Icono nombre="cerrar" />
          </button>
        </form>
      </header>

      <div className="album-contenido">
        <div className="album-resumen">
          <div className="album-dato">
            <strong>
              <NumeroAnimado valor={animalesUnicos} reducido={reducido} />
              <span> / 288</span>
            </strong>
            <span className="nota">{t("Animales descubiertos")}</span>
          </div>
          <div className="album-dato">
            <strong>
              <NumeroAnimado valor={habitatsUnicos} reducido={reducido} />
              <span> / 48</span>
            </strong>
            <span className="nota">{t("Hábitats explorados")}</span>
          </div>
        </div>

        <div className="album-medallas-bloques">
          <div className="album-medallas-seccion">
            <p className="album-seccion-titulo">{t("Estrellas de animales")}</p>
            <ul className="album-medallas" aria-label={t("Estrellas de animales")}>
              {medallasAnimales.map((m) => (
                <li key={m.id} className="album-medalla" data-obtenida={m.obtenida ? "true" : undefined}>
                  <span className="album-medalla-icono" aria-hidden="true">
                    {m.obtenida ? "★" : "☆"}
                  </span>
                  <span className="album-medalla-texto">
                    <strong>{t(m.titulo)}</strong>
                    <span>{t(m.meta)}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="album-medallas-seccion">
            <p className="album-seccion-titulo">{t("Estrellas de hábitats")}</p>
            <ul className="album-medallas" aria-label={t("Estrellas de hábitats")}>
              {medallasHabitats.map((m) => (
                <li
                  key={m.id}
                  className="album-medalla"
                  data-tipo="habitat"
                  data-obtenida={m.obtenida ? "true" : undefined}
                >
                  <span className="album-medalla-icono" aria-hidden="true">
                    {m.obtenida ? "★" : "☆"}
                  </span>
                  <span className="album-medalla-texto">
                    <strong>{t(m.titulo)}</strong>
                    <span>{t(m.meta)}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {registros.length === 0 ? (
          <div className="album-vacio">
            <p className="album-vacio-titulo">{t("Tu álbum todavía espera el primer sello.")}</p>
            <p className="nota">{t("Empieza una partida y encuentra el hogar de un animal para verlo aquí.")}</p>
          </div>
        ) : (
          <section className="album-lista-bloque" aria-label={t("Hallazgos sellados")}>
            <div className="diario-cabecera">
              <h3 className="diario-titulo">{t("Hallazgos sellados")}</h3>
              {totalPaginas > 1 && (
                <div className="diario-controles album-paginacion">
                  <span className="album-pagina-texto" aria-live="polite" aria-atomic="true">
                    {paginaActual + 1} / {totalPaginas}
                  </span>
                  <button
                    type="button"
                    className="diario-nav"
                    aria-label={t("Anteriores")}
                    disabled={paginaActual === 0}
                    onClick={() => setPagina((p) => Math.max(0, p - 1))}
                  >
                    <Icono nombre="anterior" />
                  </button>
                  <button
                    type="button"
                    className="diario-nav"
                    aria-label={t("Siguientes")}
                    disabled={paginaActual >= totalPaginas - 1}
                    onClick={() => setPagina((p) => Math.min(totalPaginas - 1, p + 1))}
                  >
                    <Icono nombre="flecha" />
                  </button>
                </div>
              )}
            </div>
            <ol className="album-rejilla">
              {visibles.map((r) => (
                <li key={`${r.animalId}-${r.habitatId}`} className="diario-tarjeta album-tarjeta">
                  <img
                    className="diario-habitat"
                    src={`/habitats/${r.habitatId}.webp`}
                    alt=""
                    draggable={false}
                    loading="lazy"
                  />
                  <span className="diario-animal">
                    {r.imagenAnimal ? (
                      <img
                        className="animal-ilustracion"
                        src={r.imagenAnimal}
                        alt=""
                        draggable={false}
                        loading="lazy"
                      />
                    ) : null}
                  </span>
                  <span className="diario-texto">
                    <strong>{pictogramas?.[r.pictogramaId]?.etiqueta ?? r.animalNombre}</strong>
                    <span>{pictogramas?.[`P_${r.habitatId}`]?.etiqueta ?? r.habitatNombre}</span>
                  </span>
                  <span className="diario-sello" aria-hidden="true">
                    ✓
                  </span>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>

      <footer className="pref-pie album-pie">
        <div className="album-pie-izq">
          {registros.length === 0 ? (
            <span className="nota">{t("Guardado automáticamente en este equipo.")}</span>
          ) : !confirmandoReinicio ? (
            <button type="button" className="album-reiniciar" onClick={() => setConfirmandoReinicio(true)}>
              {t("Reiniciar álbum")}
            </button>
          ) : (
            <div className="album-confirmar" role="group" aria-label={t("Confirmar reinicio del álbum")}>
              <span className="album-confirmar-texto">{t("¿Borrar todos los sellos?")}</span>
              <button
                type="button"
                className="album-confirmar-si"
                onClick={() => {
                  onReiniciar();
                  setConfirmandoReinicio(false);
                  setPagina(0);
                }}
              >
                {t("Sí, reiniciar")}
              </button>
              <button type="button" className="album-confirmar-no" onClick={() => setConfirmandoReinicio(false)}>
                {t("Cancelar")}
              </button>
            </div>
          )}
        </div>
        <form method="dialog">
          <button className="pref-volver">
            {t("Volver al juego")} <span aria-hidden="true">↗</span>
          </button>
        </form>
      </footer>
    </dialog>
  );
});
