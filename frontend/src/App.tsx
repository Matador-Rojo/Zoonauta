import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { MotionConfig, motion } from "motion/react";
import {
  cargarAlbum,
  limpiarAlbum,
  registrarHallazgoEnAlbum,
  resumenAlbum,
  type RegistroAlbum,
} from "./album";
import {
  cargarConfigVoz,
  cargarDiccionarios,
  cargarVista,
  enviarAccion,
  enviarIdioma,
} from "./api/cliente";
import type {
  Diccionarios,
  Idioma,
  Modalidad,
  TipoAccion,
  Vista,
  VozGrabadaInfo,
} from "./api/tipos";
import { Album } from "./componentes/Album";
import { BosqueVivo } from "./componentes/BosqueVivo";
import { Catalogo } from "./componentes/Catalogo";
import { Cierre, type Hallazgo } from "./componentes/Cierre";
import { useCerrarFuera } from "./componentes/dialogos";
import { Icono } from "./componentes/Icono";
import { LogoZoonauta } from "./componentes/LogoZoonauta";
import { Portada } from "./componentes/Portada";
import {
  Preferencias,
  type EscalaTexto,
  type TemaVisual,
  type ValoresPreferencias,
} from "./componentes/Preferencias";
import { Controles, Reto } from "./componentes/Reto";
import { vibrar } from "./haptica";
import { ContextoIdioma, crearTraductor } from "./i18n";
import { MotorSonido } from "./sonido";
import { GuiaVoz, type ContextoLectura } from "./voz";

const CLAVE_MOVIMIENTO = "zoonauta.movimientoReducido";
const CLAVE_TEMA = "zoonauta.tema";
const CLAVE_ESCALA = "zoonauta.escala";
const CLAVE_SONIDO = "zoonauta.sonidoBosque";
const CLAVE_VOZ = "zoonauta.vozGrabada";
const CLAVE_PROTEGER = "zoonauta.protegerPreferencias";

interface EventoInstalacionPwa extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const COLOR_TEMA: Record<TemaVisual, string> = {
  noche: "#04141f",
  dia: "#f3ede0",
  contraste: "#000000",
};

function leerLocal(clave: string): string | null {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
}

function guardarLocal(clave: string, valor: string | null) {
  try {
    if (valor === null) localStorage.removeItem(clave);
    else localStorage.setItem(clave, valor);
  } catch {
    /* almacenamiento no disponible */
  }
}

function movimientoInicial(): boolean | null {
  const guardado = leerLocal(CLAVE_MOVIMIENTO);
  if (guardado === "1") return true;
  if (guardado === "0") return false;
  return null;
}

function temaInicial(): TemaVisual {
  const guardado = leerLocal(CLAVE_TEMA);
  return guardado === "dia" || guardado === "contraste" ? guardado : "noche";
}

function escalaInicial(): EscalaTexto {
  const guardado = leerLocal(CLAVE_ESCALA);
  return guardado === "pequeno" || guardado === "grande" ? guardado : "normal";
}

// Preferencia del sistema, escuchada en vivo. Marca el valor inicial, pero la persona
// puede desactivar «Reducir movimiento» en Preferencias si desea ver las animaciones.
function useSistemaReduceMovimiento(): boolean {
  const [reduce, setReduce] = useState(
    () => matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    const consulta = matchMedia("(prefers-reduced-motion: reduce)");
    const alCambiar = () => setReduce(consulta.matches);
    consulta.addEventListener("change", alCambiar);
    return () => consulta.removeEventListener("change", alCambiar);
  }, []);
  return reduce;
}

export function App() {
  const [vista, setVista] = useState<Vista | null>(null);
  const [diccionarios, setDiccionarios] = useState<Diccionarios>({
    es: {},
    "pt-BR": {},
    en: {},
  });
  const [grabadas, setGrabadas] = useState<Partial<Record<Idioma, number>>>({});
  const [vocesGrabadas, setVocesGrabadas] = useState<
    Partial<Record<Idioma, VozGrabadaInfo[]>>
  >({});
  const [errorCarga, setErrorCarga] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [hablando, setHablando] = useState(false);
  const [progresoVoz, setProgresoVoz] = useState(0);
  const [hallazgos, setHallazgos] = useState<Hallazgo[]>([]);
  const [album, setAlbum] = useState<RegistroAlbum[]>(() => cargarAlbum());
  const [eventoInstalar, setEventoInstalar] =
    useState<EventoInstalacionPwa | null>(null);
  const [manteniendoPref, setManteniendoPref] = useState(false);
  const [animalVolando, setAnimalVolando] = useState<string | null>(null);
  const [videoPortadaActivo, setVideoPortadaActivo] = useState(false);
  const [prefs, setPrefs] = useState<ValoresPreferencias>(() => ({
    retos: "8",
    opciones: 8,
    vozActiva: true,
    vozGrabada: leerLocal(CLAVE_VOZ) || "marcela",
    velocidad: 0.95,
    sonidoBosque: leerLocal(CLAVE_SONIDO) !== "0",
    protegerPreferencias: leerLocal(CLAVE_PROTEGER) === "1",
    movimientoReducido: movimientoInicial(),
    tema: temaInicial(),
    escala: escalaInicial(),
  }));
  const sistemaReduce = useSistemaReduceMovimiento();
  const movimientoReducido = prefs.movimientoReducido ?? sistemaReduce;
  const ocupadoRef = useRef(false);
  const vistaRef = useRef<Vista | null>(null);
  const temporizadorPref = useRef<number | null>(null);
  // El ref sigue a la vista confirmada para los manejadores asíncronos (no se lee al renderizar).
  useEffect(() => {
    vistaRef.current = vista;
  }, [vista]);
  const preferencias = useRef<HTMLDialogElement>(null);
  const albumDialogo = useRef<HTMLDialogElement>(null);
  useCerrarFuera(preferencias);
  useCerrarFuera(albumDialogo);

  const idioma: Idioma = vista?.idioma ?? "es";
  const traductor = useMemo(
    () => crearTraductor(diccionarios, idioma),
    [diccionarios, idioma],
  );
  const { t } = traductor;

  const silenciarError = useCallback(() => undefined, []);
  const guia = useMemo(
    () => new GuiaVoz(silenciarError, setHablando, setProgresoVoz),
    [silenciarError],
  );
  const sonido = useMemo(() => new MotorSonido(), []);

  // Carga inicial: la cookie de sesión permite recuperar la partida al recargar.
  useEffect(() => {
    Promise.all([cargarVista(), cargarDiccionarios(), cargarConfigVoz()])
      .then(([v, d, c]) => {
        setVista(v);
        setDiccionarios(d);
        setGrabadas(c.grabadas ?? {});
        setVocesGrabadas(c.voces_grabadas ?? {});
      })
      .catch(() => setErrorCarga(true));
  }, []);

  useEffect(() => {
    const alSalir = () => {
      guia.parar();
      sonido.cerrar();
    };
    const alVisibilidad = () => sonido.fijarOculto(document.hidden);
    window.addEventListener("pagehide", alSalir);
    document.addEventListener("visibilitychange", alVisibilidad);
    return () => {
      window.removeEventListener("pagehide", alSalir);
      document.removeEventListener("visibilitychange", alVisibilidad);
    };
  }, [guia, sonido]);

  useEffect(() => {
    document.documentElement.lang = idioma;
    document.title = "Zoonauta · " + t("Animales y hábitats");
  }, [idioma, t]);
  useEffect(() => {
    document.documentElement.dataset.movimiento = movimientoReducido
      ? "reducido"
      : "normal";
  }, [movimientoReducido]);
  useEffect(() => {
    document.documentElement.dataset.tema = prefs.tema;
    guardarLocal(CLAVE_TEMA, prefs.tema);
    const meta = document.querySelector<HTMLMetaElement>(
      'meta[name="theme-color"]',
    );
    if (meta) meta.content = COLOR_TEMA[prefs.tema];
  }, [prefs.tema]);
  useEffect(() => {
    guardarLocal(CLAVE_PROTEGER, prefs.protegerPreferencias ? "1" : "0");
  }, [prefs.protegerPreferencias]);
  useEffect(() => {
    const alAntesInstalar = (e: Event) => {
      e.preventDefault();
      setEventoInstalar(e as EventoInstalacionPwa);
    };
    const alInstalada = () => setEventoInstalar(null);
    window.addEventListener("beforeinstallprompt", alAntesInstalar);
    window.addEventListener("appinstalled", alInstalada);
    return () => {
      window.removeEventListener("beforeinstallprompt", alAntesInstalar);
      window.removeEventListener("appinstalled", alInstalada);
    };
  }, []);
  useEffect(() => {
    document.documentElement.dataset.escala = prefs.escala;
    guardarLocal(CLAVE_ESCALA, prefs.escala);
  }, [prefs.escala]);
  useEffect(() => {
    guardarLocal(
      CLAVE_MOVIMIENTO,
      prefs.movimientoReducido === null
        ? null
        : prefs.movimientoReducido
          ? "1"
          : "0",
    );
  }, [prefs.movimientoReducido]);
  useEffect(() => {
    guardarLocal(CLAVE_SONIDO, prefs.sonidoBosque ? "1" : "0");
    sonido.fijarActivo(prefs.sonidoBosque);
    if (!prefs.sonidoBosque) return;
    const desbloquear = () => sonido.despertar();
    window.addEventListener("pointerdown", desbloquear, { passive: true });
    window.addEventListener("keydown", desbloquear, { passive: true });
    window.addEventListener("touchstart", desbloquear, { passive: true });
    window.addEventListener("click", desbloquear, { passive: true });
    return () => {
      window.removeEventListener("pointerdown", desbloquear);
      window.removeEventListener("keydown", desbloquear);
      window.removeEventListener("touchstart", desbloquear);
      window.removeEventListener("click", desbloquear);
    };
  }, [prefs.sonidoBosque, sonido]);
  useEffect(() => {
    guardarLocal(CLAVE_VOZ, prefs.vozGrabada);
  }, [prefs.vozGrabada]);
  useEffect(() => {
    sonido.fijarHablando(hablando);
  }, [hablando, sonido]);

  // Al cambiar de fase se lleva el foco al título de la pantalla nueva y se adapta la música.
  const fase = vista?.fase;
  const primeraFase = useRef(true);
  useEffect(() => {
    if (!fase) return;
    sonido.fijarOculto(document.hidden);
    sonido.fijarModo(
      fase === "COMPLETADA"
        ? "victoria"
        : fase === "PAUSADA"
          ? "pausa"
          : fase === "ABANDONADA"
            ? "silencio"
            : "juego",
    );
    if (primeraFase.current) {
      primeraFase.current = false;
      return;
    }
    window.scrollTo({ top: 0, behavior: "instant" });
    const destino =
      fase === "PAUSADA"
        ? document.querySelector<HTMLElement>(".cierre .control")
        : document.getElementById("titulo-pantalla");
    destino?.focus({ preventScroll: true });
  }, [fase, sonido]);

  const resolverVoz = useCallback(
    (idIdioma: Idioma) => {
      const lista = vocesGrabadas[idIdioma] ?? [];
      if (lista.some((v) => v.id === prefs.vozGrabada)) return prefs.vozGrabada;
      return (
        lista[0]?.id ??
        (idIdioma === "en"
          ? "jessica"
          : idIdioma === "pt-BR"
            ? "roberta"
            : "marcela")
      );
    },
    [vocesGrabadas, prefs.vozGrabada],
  );

  const hablar = useCallback(
    (v: Vista, contexto: ContextoLectura) => {
      const ajustes = {
        activa: prefs.vozActiva,
        velocidad: prefs.velocidad,
        grabadas: grabadas[v.idioma] ?? 0,
        voz: resolverVoz(v.idioma),
      };
      void guia.hablar(v, ajustes, contexto, {
        error: t(
          "No se pudo reproducir la voz. Puedes volver a pulsar Repetir.",
        ),
      });
    },
    [guia, prefs.vozActiva, prefs.velocidad, resolverVoz, grabadas, t],
  );

  const animalesDescubiertos = useMemo(
    () => new Set(album.map((r) => r.animalId)),
    [album],
  );
  const descubiertosRef = useRef<Set<string>>(animalesDescubiertos);
  useEffect(() => {
    descubiertosRef.current = animalesDescubiertos;
  }, [animalesDescubiertos]);

  const accion = useCallback(
    async (tipo: TipoAccion, payload: Record<string, unknown> = {}) => {
      const actual = vistaRef.current;
      if (ocupadoRef.current || !actual) return;
      if (tipo === "iniciar") {
        const n = Math.min(
          48,
          Math.max(1, Math.round(Number(prefs.retos) || 8)),
        );
        payload = {
          ...payload,
          retos: n,
          cantidad_opciones: prefs.opciones,
          animales_descubiertos: Array.from(descubiertosRef.current),
        };
      }
      ocupadoRef.current = true;
      setOcupado(true);
      guia.parar();
      sonido.despertar();
      try {
        const { ok, datos } = await enviarAccion(actual, tipo, payload);
        // El tablero no se reconstruye: React solo actualiza lo que cambió.
        // Al cambiar de pantalla con movimiento activo usamos View Transitions API.
        if (datos.vista) {
          const cambiaPantalla = datos.vista.fase !== actual.fase;
          const doc = document as Document & {
            startViewTransition?: (cb: () => void) => {
              finished: Promise<void>;
            };
          };
          if (
            cambiaPantalla &&
            !movimientoReducido &&
            typeof doc.startViewTransition === "function"
          ) {
            const trans = doc.startViewTransition(() => {
              flushSync(() => setVista(datos.vista!));
            });
            void trans.finished.finally(() => setAnimalVolando(null));
          } else {
            setVista(datos.vista);
            setAnimalVolando(null);
          }
        }
        if (!ok) {
          return;
        }
        if (datos.aceptada && datos.vista) {
          if (tipo === "iniciar" || tipo === "nueva_partida") {
            setHallazgos([]);
            sonido.tocar("transicion");
            vibrar("toque", movimientoReducido);
          } else if (tipo === "elegir_animal") {
            sonido.tocar("elegir");
            vibrar("toque", movimientoReducido);
          } else if (
            tipo === "continuar" &&
            datos.vista.fase !== "COMPLETADA"
          ) {
            sonido.tocar("transicion");
            vibrar("toque", movimientoReducido);
          } else if (
            tipo === "continuar" &&
            datos.vista.fase === "COMPLETADA"
          ) {
            sonido.tocar("cierre");
            vibrar("victoria", movimientoReducido);
          }
          if (
            tipo === "seleccionar_habitat" &&
            datos.vista.fase === "RETO_RESUELTO" &&
            actual.animal
          ) {
            const habId = String(payload.habitat_id ?? "");
            const hab = actual.opciones_habitat.find((h) => h.id === habId);
            if (hab) {
              setHallazgos((prev) =>
                prev.some(
                  (x) =>
                    x.animalId === actual.animal!.id && x.habitatId === hab.id,
                )
                  ? prev
                  : [
                      ...prev,
                      {
                        animalId: actual.animal!.id,
                        animalNombre: actual.animal!.nombre,
                        pictogramaId: actual.animal!.pictograma_id,
                        habitatId: hab.id,
                        habitatNombre: hab.nombre,
                      },
                    ],
              );
              const imagenAnimal =
                actual.pictogramas[actual.animal.pictograma_id]?.imagen ?? "";
              setAlbum(
                (prev) =>
                  registrarHallazgoEnAlbum(prev, {
                    animalId: actual.animal!.id,
                    animalNombre: actual.animal!.nombre,
                    pictogramaId: actual.animal!.pictograma_id,
                    imagenAnimal,
                    habitatId: hab.id,
                    habitatNombre: hab.nombre,
                  }).lista,
              );
            }
            sonido.tocar("acierto", habId);
            vibrar("acierto", movimientoReducido);
          } else if (
            tipo === "seleccionar_habitat" &&
            datos.vista.fase === "ESPERANDO_RESPUESTA"
          ) {
            sonido.tocar("neutral");
            vibrar("neutral", movimientoReducido);
          } else if (tipo === "ayuda") {
            sonido.tocar("pista");
            vibrar("pista", movimientoReducido);
          }
        }
        if (
          datos.aceptada &&
          datos.respuesta_emitida &&
          datos.vista &&
          tipo !== "pausar" &&
          tipo !== "nueva_partida"
        )
          hablar(datos.vista, "respuesta");
      } catch {
        /* sin notificaciones emergentes */
      } finally {
        ocupadoRef.current = false;
        setOcupado(false);
      }
    },
    [prefs.retos, prefs.opciones, movimientoReducido, guia, sonido, hablar],
  );

  const cambiarIdioma = useCallback(
    async (nuevo: Idioma) => {
      const actual = vistaRef.current;
      if (ocupadoRef.current || !actual || nuevo === actual.idioma) return;
      ocupadoRef.current = true;
      setOcupado(true);
      guia.parar();
      sonido.despertar();
      try {
        const { datos } = await enviarIdioma(actual, nuevo);
        if (datos.vista) setVista(datos.vista);
      } catch {
        /* sin notificaciones emergentes */
      } finally {
        ocupadoRef.current = false;
        setOcupado(false);
      }
    },
    [guia, sonido],
  );

  // El foco empieza en Idioma, el primer campo (Modern Web Guidance: dialog, foco inicial).
  const abrirPreferencias = () => {
    preferencias.current?.showModal();
    document.getElementById("pref-idioma")?.focus();
  };

  const abrirAlbum = () => {
    vibrar("toque", movimientoReducido);
    albumDialogo.current?.showModal();
  };

  const cancelarMantenerPref = () => {
    if (temporizadorPref.current !== null) {
      window.clearTimeout(temporizadorPref.current);
      temporizadorPref.current = null;
    }
    setManteniendoPref(false);
  };

  const iniciarMantenerPref = () => {
    if (!prefs.protegerPreferencias) return;
    cancelarMantenerPref();
    setManteniendoPref(true);
    temporizadorPref.current = window.setTimeout(() => {
      temporizadorPref.current = null;
      setManteniendoPref(false);
      vibrar("desbloqueo", movimientoReducido);
      abrirPreferencias();
    }, 1150);
  };

  const instalarApp = async () => {
    if (!eventoInstalar) return;
    try {
      await eventoInstalar.prompt();
      const res = await eventoInstalar.userChoice;
      if (res.outcome === "accepted") setEventoInstalar(null);
    } catch {
      /* el navegador canceló el aviso */
    }
  };

  const totalDescubiertos = useMemo(
    () => resumenAlbum(album).animalesUnicos,
    [album],
  );

  if (errorCarga)
    return (
      <main id="juego">
        <p className="introduccion">
          No se pudo cargar el juego. Inicia el servidor y vuelve a abrir esta
          página.
        </p>
      </main>
    );
  if (!vista)
    return (
      <main id="juego" aria-busy="true">
        <p className="cargando" role="status">
          Preparando tu expedición…
        </p>
      </main>
    );

  const enInicio = vista.fase === "INICIO";
  const clavePantalla = enInicio
    ? "INICIO"
    : vista.fase === "SELECCION_ANIMAL"
      ? "CATALOGO"
      : vista.fase === "PAUSADA" ||
          vista.fase === "COMPLETADA" ||
          vista.fase === "ABANDONADA"
        ? `CIERRE-${vista.fase}`
        : "RETO";
  let pantalla: React.ReactNode;
  if (enInicio) {
    pantalla = (
      <Portada
        vista={vista}
        tema={prefs.tema}
        reducido={movimientoReducido}
        onVideoActivo={setVideoPortadaActivo}
        onAbrirModalidad={() => hablar(vista, "modalidad")}
        onCerrarModalidad={() => {
          if (vistaRef.current?.fase === "INICIO") guia.parar();
        }}
        onComenzar={(modalidad: Modalidad) =>
          void accion("iniciar", { modalidad })
        }
      />
    );
  } else if (vista.fase === "SELECCION_ANIMAL") {
    pantalla = (
      <Catalogo
        vista={vista}
        animalVolando={animalVolando}
        descubiertos={animalesDescubiertos}
        reducido={movimientoReducido}
        onElegir={(id) => {
          setAnimalVolando(id);
          void accion("elegir_animal", { animal_id: id });
        }}
        onCambioPagina={() => sonido.tocar("pagina")}
        controles={
          <Controles vista={vista} onAccion={(tipo) => void accion(tipo)} />
        }
      />
    );
  } else if (
    vista.fase === "PAUSADA" ||
    vista.fase === "COMPLETADA" ||
    vista.fase === "ABANDONADA"
  ) {
    pantalla = (
      <Cierre
        vista={vista}
        hallazgos={hallazgos}
        reducido={movimientoReducido}
        onAccion={(tipo) => void accion(tipo)}
      />
    );
  } else {
    pantalla = (
      <Reto
        vista={vista}
        hablando={hablando}
        progresoVoz={progresoVoz}
        reducido={movimientoReducido}
        onAccion={(tipo, payload) => void accion(tipo, payload)}
      />
    );
  }

  return (
    <MotionConfig reducedMotion={movimientoReducido ? "always" : "user"}>
      <ContextoIdioma.Provider value={traductor}>
        <BosqueVivo
          fase={vista.fase}
          tema={prefs.tema}
          reducido={movimientoReducido || (enInicio && videoPortadaActivo)}
        />
        <a className="saltar" href="#juego">
          {t("Ir al juego")}
        </a>
        <header className="cabecera" data-fase={vista.fase}>
          <a className="marca" href="/">
            <LogoZoonauta size={44} />
            <span className="marca-texto">
              Zoonauta
              <span className="marca-subtitulo">
                {t("Animales y hábitats")}
              </span>
            </span>
          </a>
          <div className="cabecera-acciones">
            <button
              type="button"
              className="boton-texto"
              aria-haspopup="dialog"
              data-protegido={prefs.protegerPreferencias ? "true" : undefined}
              data-manteniendo={manteniendoPref ? "true" : undefined}
              title={
                prefs.protegerPreferencias
                  ? t("Mantén pulsado para abrir Preferencias")
                  : undefined
              }
              onClick={() => {
                if (!prefs.protegerPreferencias) abrirPreferencias();
              }}
              onPointerDown={iniciarMantenerPref}
              onPointerUp={cancelarMantenerPref}
              onPointerLeave={cancelarMantenerPref}
              onPointerCancel={cancelarMantenerPref}
              onKeyDown={(e) => {
                if (
                  prefs.protegerPreferencias &&
                  (e.key === "Enter" || e.key === " ") &&
                  !e.repeat
                ) {
                  e.preventDefault();
                  iniciarMantenerPref();
                }
              }}
              onKeyUp={(e) => {
                if (
                  prefs.protegerPreferencias &&
                  (e.key === "Enter" || e.key === " ")
                ) {
                  cancelarMantenerPref();
                }
              }}
            >
              <Icono
                nombre={prefs.protegerPreferencias ? "candado" : "ajustes"}
              />
              <span>{t("Preferencias")}</span>
            </button>
            <button
              type="button"
              className="boton-album"
              aria-haspopup="dialog"
              aria-label={t("Mi álbum")}
              onClick={abrirAlbum}
            >
              <Icono nombre="album" />
              <span className="boton-album-texto">{t("Mi álbum")}</span>
              {totalDescubiertos > 0 && (
                <span className="album-contador" aria-hidden="true">
                  {totalDescubiertos}
                </span>
              )}
            </button>
          </div>
        </header>
        <main
          id="juego"
          tabIndex={-1}
          aria-busy={ocupado}
          data-fase={vista.fase}
          data-hablando={hablando ? "true" : undefined}
        >
          <motion.div
            key={clavePantalla}
            className="escena-pantalla"
            initial={
              movimientoReducido || enInicio
                ? false
                : { opacity: 0, x: 18, scale: 0.992 }
            }
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            {pantalla}
          </motion.div>
        </main>
        <Preferencias
          ref={preferencias}
          idioma={idioma}
          enInicio={enInicio}
          grabadas={grabadas[idioma] ?? 0}
          vocesDisponibles={vocesGrabadas[idioma] ?? []}
          sistemaReduce={sistemaReduce}
          puedeInstalar={Boolean(eventoInstalar)}
          onInstalar={() => void instalarApp()}
          valores={prefs}
          onCambio={(cambios) => {
            if (
              "velocidad" in cambios ||
              "vozGrabada" in cambios ||
              cambios.vozActiva === false
            )
              guia.parar();
            setPrefs((p) => ({ ...p, ...cambios }));
          }}
          onIdioma={(nuevo) => void cambiarIdioma(nuevo)}
          onProbarVoz={() =>
            void guia.hablar(
              vista,
              {
                activa: true,
                velocidad: prefs.velocidad,
                grabadas: grabadas[vista.idioma] ?? 0,
                voz: resolverVoz(vista.idioma),
              },
              "prueba",
              {
                error: t(
                  "No se pudo reproducir la voz. Puedes volver a pulsar Repetir.",
                ),
              },
            )
          }
          onCerrar={() => undefined}
        />
        <Album
          ref={albumDialogo}
          registros={album}
          pictogramas={vista.pictogramas}
          reducido={movimientoReducido}
          onReiniciar={() => {
            limpiarAlbum();
            setAlbum([]);
            vibrar("toque", movimientoReducido);
          }}
          onCerrar={() => undefined}
        />
      </ContextoIdioma.Provider>
    </MotionConfig>
  );
}
