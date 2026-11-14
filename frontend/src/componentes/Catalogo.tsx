import { useEffect, useMemo, useRef, useState } from "react";
import type { Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Icono } from "./Icono";
import { Pictograma } from "./Pictograma";
import { Encabezado } from "./Encabezado";

const POR_PAGINA = 6;
const normalizar = (texto: string, idioma: string) =>
  texto.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase(idioma).trim();

export function Catalogo({
  vista,
  onElegir,
  controles,
}: {
  vista: Vista;
  onElegir: (animalId: string) => void;
  controles: React.ReactNode;
}) {
  const { t } = useT();
  const [consulta, setConsulta] = useState("");
  const [pagina, setPagina] = useState(0);
  const rejilla = useRef<HTMLDivElement>(null);

  const animales = useMemo(() => {
    const q = normalizar(consulta, vista.idioma);
    return vista.catalogo_animales.filter((a) => normalizar(a.nombre, vista.idioma).includes(q));
  }, [consulta, vista.catalogo_animales, vista.idioma]);
  const paginas = Math.max(1, Math.ceil(animales.length / POR_PAGINA));
  const paginaActual = Math.min(pagina, paginas - 1);
  const visibles = animales.slice(paginaActual * POR_PAGINA, (paginaActual + 1) * POR_PAGINA);

  // Tras cambiar de página con los botones, el foco pasa al primer animal de la página
  // nueva (cuando React ya la pintó), sin desplazar la página.
  const enfocarPrimero = useRef(false);
  useEffect(() => {
    if (!enfocarPrimero.current) return;
    enfocarPrimero.current = false;
    rejilla.current?.querySelector("button")?.focus({ preventScroll: true });
  }, [paginaActual]);
  const irA = (paso: number) => {
    enfocarPrimero.current = true;
    setPagina(paginaActual + paso);
  };

  const totalTexto = consulta.trim()
    ? t("{n} de {total} animales", { n: animales.length, total: vista.catalogo_animales.length })
    : t("{n} animales para explorar", { n: vista.catalogo_animales.length });

  return (
    <section className="pantalla catalogo-pantalla" aria-labelledby="titulo-pantalla">
      <Encabezado vista={vista} titulo="Elige un animal" subtitulo="Toca el animal con el que quieres jugar." />
      <div className="catalogo-barra">
        <p className="catalogo-total" aria-live="polite" aria-atomic="true">
          {totalTexto}
        </p>
        <label className="busqueda">
          <Icono nombre="buscar" />
          <input
            type="search"
            value={consulta}
            autoComplete="off"
            placeholder={t("Busca un animal…")}
            aria-label={t("Buscar animal")}
            onChange={(e) => {
              setConsulta(e.target.value);
              setPagina(0);
            }}
          />
        </label>
      </div>

      {animales.length === 0 ? (
        <p className="busqueda-vacia">{t("No encontramos ese animal. Prueba con otro nombre.")}</p>
      ) : (
        <>
          <div
            ref={rejilla}
            id="catalogo-animales"
            className="catalogo"
            role="group"
            aria-label={t("Animales de esta página")}
          >
            {visibles.map((a) => (
              <button
                key={a.id}
                type="button"
                className="tarjeta-animal"
                data-animal={a.id}
                onClick={() => onElegir(a.id)}
              >
                <span className="tarjeta-imagen">
                  <Pictograma id={a.pictograma_id} datos={vista.pictogramas[a.pictograma_id]} />
                </span>
                <span className="tarjeta-nombre">{a.nombre}</span>
              </button>
            ))}
          </div>
          <nav className="paginacion" aria-label={t("Páginas de animales")}>
            <button
              type="button"
              className="boton-secundario"
              aria-controls="catalogo-animales"
              disabled={paginaActual === 0}
              onClick={() => irA(-1)}
            >
              <Icono nombre="anterior" />
              <span>{t("Anteriores")}</span>
            </button>
            <span className="paginacion-estado" aria-live="polite" aria-atomic="true">
              {t("Página {pagina} de {total}", { pagina: paginaActual + 1, total: paginas })}
            </span>
            <button
              type="button"
              className="boton-secundario"
              aria-controls="catalogo-animales"
              disabled={paginaActual >= paginas - 1}
              onClick={() => irA(1)}
            >
              <span>{t("Siguientes")}</span>
              <Icono nombre="flecha" />
            </button>
          </nav>
        </>
      )}
      {controles}
    </section>
  );
}
