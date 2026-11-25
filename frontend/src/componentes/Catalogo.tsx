import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { motion } from "motion/react";
import type { Vista } from "../api/tipos";
import { useT } from "../i18n";
import { Encabezado } from "./Encabezado";
import { Icono } from "./Icono";
import { Pictograma } from "./Pictograma";
import { moverLuzPuntero } from "./useLuzPuntero";

const POR_PAGINA = 6;
const normalizar = (texto: string, idioma: string) =>
  texto.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase(idioma).trim();

const RANGOS = [
  { id: "TODAS", etiqueta: "Todas", desde: "", hasta: "" },
  { id: "AC", etiqueta: "A–C", desde: "a", hasta: "c" },
  { id: "DG", etiqueta: "D–G", desde: "d", hasta: "g" },
  { id: "HL", etiqueta: "H–L", desde: "h", hasta: "l" },
  { id: "MP", etiqueta: "M–P", desde: "m", hasta: "p" },
  { id: "QZ", etiqueta: "Q–Z", desde: "q", hasta: "z" },
] as const;

type RangoId = (typeof RANGOS)[number]["id"] | "FALTANTES";

/** PRNG determinista por partida (FNV-1a + Mulberry32) para que el orden aleatorio
 *  cambie en cada partida nueva pero se mantenga estable al pasar páginas o recargar. */
function crearGenerador(semilla: string): () => number {
  let h = 2166136261;
  for (let i = 0; i < semilla.length; i++) {
    h ^= semilla.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  let estado = h >>> 0;
  return () => {
    estado = (estado + 0x6d2b79f5) | 0;
    let t = Math.imul(estado ^ (estado >>> 15), 1 | estado);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function mezclar<T>(items: T[], rand: () => number): T[] {
  const copia = [...items];
  for (let i = copia.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  return copia;
}

/**
 * En el banco de 288 animales, cada bloque consecutivo de 6 pertenece al mismo hábitat.
 * Intercalar rondas de los 48 bloques garantiza que cada página de 6 muestre 6 hábitats distintos.
 */
function barajarPorBiomas<T>(lista: T[], semilla: string): T[] {
  const rand = crearGenerador(semilla);
  if (lista.length < 12 || lista.length % POR_PAGINA !== 0) {
    return mezclar(lista, rand);
  }
  const bloques: T[][] = [];
  for (let i = 0; i < lista.length; i += POR_PAGINA) {
    bloques.push(mezclar(lista.slice(i, i + POR_PAGINA), rand));
  }
  const resultado: T[] = [];
  for (let ronda = 0; ronda < POR_PAGINA; ronda++) {
    const ordenBloques = mezclar(
      Array.from({ length: bloques.length }, (_, idx) => idx),
      rand,
    );
    for (const b of ordenBloques) {
      resultado.push(bloques[b][ronda]);
    }
  }
  return resultado;
}

export function Catalogo({
  vista,
  animalVolando = null,
  descubiertos,
  reducido = false,
  onElegir,
  onCambioPagina,
  controles,
}: {
  vista: Vista;
  animalVolando?: string | null;
  descubiertos?: Set<string>;
  reducido?: boolean;
  onElegir: (animalId: string) => void;
  onCambioPagina?: () => void;
  controles: React.ReactNode;
}) {
  const { t } = useT();
  const [consulta, setConsulta] = useState("");
  const [rango, setRango] = useState<RangoId>("TODAS");
  const [pagina, setPagina] = useState(0);
  const rejilla = useRef<HTMLDivElement>(null);
  const bloqueandoEmbla = useRef(false);
  const [emblaRef, emblaApi] = useEmblaCarousel({
    startIndex: 1,
    watchDrag: true,
    duration: 18,
  });

  const faltantesTotal = useMemo(() => {
    if (!descubiertos || descubiertos.size === 0) return vista.catalogo_animales.length;
    return vista.catalogo_animales.filter((a) => !descubiertos.has(a.id)).length;
  }, [vista.catalogo_animales, descubiertos]);

  // Orden aleatorio con biomas intercalados para «Todas» y «Por descubrir» (nuevo en cada partida).
  const catalogoAleatorio = useMemo(
    () => barajarPorBiomas(vista.catalogo_animales, vista.sesion_id || "zoonauta"),
    [vista.catalogo_animales, vista.sesion_id],
  );

  // Orden híbrido: aleatorio variado en «Todas»/«Por descubrir» y alfabético A–Z en búsqueda y letras.
  const animales = useMemo(() => {
    const q = normalizar(consulta, vista.idioma);
    const filtroRango = RANGOS.find((r) => r.id === rango);
    const usarAleatorio = !q && (rango === "TODAS" || rango === "FALTANTES");
    const base = usarAleatorio ? catalogoAleatorio : vista.catalogo_animales;
    const filtrados = base.filter((a) => {
      const nombre = normalizar(a.nombre, vista.idioma);
      if (q && !nombre.includes(q)) return false;
      if (!q && rango === "FALTANTES") {
        return !descubiertos?.has(a.id);
      }
      if (!q && filtroRango && filtroRango.desde) {
        const inicial = nombre.charAt(0);
        if (inicial < filtroRango.desde || inicial > filtroRango.hasta) return false;
      }
      return true;
    });
    if (usarAleatorio) return filtrados;
    return [...filtrados].sort((a, b) => a.nombre.localeCompare(b.nombre, vista.idioma, { sensitivity: "base" }));
  }, [consulta, rango, catalogoAleatorio, vista.catalogo_animales, vista.idioma, descubiertos]);

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

  const irA = useCallback(
    (paso: number, enfocar = true) => {
      const siguiente = Math.min(paginas - 1, Math.max(0, paginaActual + paso));
      if (siguiente === paginaActual) return;
      enfocarPrimero.current = enfocar;
      setPagina(siguiente);
      onCambioPagina?.();
    },
    [paginaActual, paginas, onCambioPagina],
  );

  // Sincroniza el gesto táctil/arrastre de Embla con la paginación accesible (solo 6 tarjetas en DOM).
  useEffect(() => {
    if (!emblaApi) return;
    const alSeleccionar = () => {
      if (bloqueandoEmbla.current) return;
      const idx = emblaApi.selectedScrollSnap();
      if (idx === 1) return;
      bloqueandoEmbla.current = true;
      const delta = idx === 2 ? 1 : -1;
      emblaApi.scrollTo(1, true);
      irA(delta, false);
      requestAnimationFrame(() => {
        bloqueandoEmbla.current = false;
      });
    };
    emblaApi.on("select", alSeleccionar);
    return () => {
      emblaApi.off("select", alSeleccionar);
    };
  }, [emblaApi, irA]);

  // Atajos de teclado: flechas izquierda/derecha pasan de página si no se está escribiendo.
  useEffect(() => {
    const alTecla = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      const destino = e.target as HTMLElement | null;
      if (destino && /^(INPUT|TEXTAREA|SELECT)$/.test(destino.tagName)) return;
      if (document.querySelector("dialog[open]")) return;
      if (e.key === "ArrowRight") {
        e.preventDefault();
        irA(1, false);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        irA(-1, false);
      }
    };
    window.addEventListener("keydown", alTecla);
    return () => window.removeEventListener("keydown", alTecla);
  }, [irA]);

  const filtrado = Boolean(consulta.trim()) || rango !== "TODAS";
  const totalTexto = filtrado
    ? t("{n} de {total} animales", { n: animales.length, total: vista.catalogo_animales.length })
    : t("{n} animales para explorar", { n: vista.catalogo_animales.length });

  return (
    <section className="pantalla catalogo-pantalla" aria-labelledby="titulo-pantalla">
      <Encabezado
        vista={vista}
        etiqueta="Explora los animales"
        titulo="Elige un animal"
        subtitulo="Toca el animal con el que quieres jugar."
        reducido={reducido}
      />
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
              if (e.target.value.trim()) setRango("TODAS");
              setPagina(0);
            }}
          />
        </label>
        <div className="catalogo-filtros" role="group" aria-label={t("Filtrar por letra inicial")}>
          {RANGOS.map((item) => (
            <button
              key={item.id}
              type="button"
              className="filtro-letra"
              aria-pressed={rango === item.id}
              onClick={() => {
                setConsulta("");
                setRango(item.id);
                setPagina(0);
                onCambioPagina?.();
              }}
            >
              {item.id === "TODAS" ? t(item.etiqueta) : item.etiqueta}
            </button>
          ))}
          <button
            type="button"
            className="filtro-letra filtro-faltantes"
            aria-pressed={rango === "FALTANTES"}
            onClick={() => {
              setConsulta("");
              setRango("FALTANTES");
              setPagina(0);
              onCambioPagina?.();
            }}
          >
            <span>{t("Por descubrir")}</span>
            <span className="filtro-faltantes-cuenta">{faltantesTotal}</span>
          </button>
        </div>
      </div>

      {animales.length === 0 ? (
        <p className="busqueda-vacia">
          {rango === "FALTANTES"
            ? t("¡Felicidades! Ya descubriste todos los animales del álbum.")
            : t("No encontramos ese animal. Prueba con otro nombre.")}
        </p>
      ) : (
        <>
          <div className="catalogo-carrusel" ref={emblaRef}>
            <div className="catalogo-pista">
              <div className="catalogo-diapositiva catalogo-fantasma" aria-hidden="true" />
              <div className="catalogo-diapositiva">
                <div
                  ref={rejilla}
                  id="catalogo-animales"
                  className="catalogo"
                  role="group"
                  aria-label={t("Animales de esta página")}
                  data-cantidad={visibles.length}
                >
                  {visibles.map((a, i) => {
                    const yaDescubierto = Boolean(descubiertos?.has(a.id));
                    return (
                      <motion.button
                        key={a.id}
                        type="button"
                        className="tarjeta-animal"
                        data-animal={a.id}
                        data-volando={animalVolando === a.id ? "true" : undefined}
                        data-descubierto={yaDescubierto ? "true" : undefined}
                        whileTap={{ scale: 0.965 }}
                        transition={{ type: "spring", stiffness: 420, damping: 28 }}
                        onPointerMove={moverLuzPuntero}
                        onClick={() => onElegir(a.id)}
                      >
                        <span className="tarjeta-numero" aria-hidden="true">
                          {String(paginaActual * POR_PAGINA + i + 1).padStart(2, "0")}
                        </span>
                        {yaDescubierto && (
                          <span className="tarjeta-sello" title={t("Ya descubierto")} aria-hidden="true">
                            ✓
                          </span>
                        )}
                        <span className="tarjeta-imagen">
                          <Pictograma id={a.pictograma_id} datos={vista.pictogramas[a.pictograma_id]} perezosa />
                        </span>
                        <span className="tarjeta-nombre">{a.nombre}</span>
                        <Icono nombre="flecha" className="tarjeta-flecha" />
                      </motion.button>
                    );
                  })}
                </div>
              </div>
              <div className="catalogo-diapositiva catalogo-fantasma" aria-hidden="true" />
            </div>
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
