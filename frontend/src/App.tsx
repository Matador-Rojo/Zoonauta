import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { cargarConfigVoz, cargarDiccionarios, cargarVista, enviarAccion, enviarIdioma } from "./api/cliente";
import type { Diccionarios, Idioma, Modalidad, TipoAccion, Vista, VozCatalogo } from "./api/tipos";
import { Catalogo } from "./componentes/Catalogo";
import { Cierre } from "./componentes/Cierre";
import { Icono } from "./componentes/Icono";
import { Portada } from "./componentes/Portada";
import { Preferencias, type ValoresPreferencias } from "./componentes/Preferencias";
import { Controles, Reto } from "./componentes/Reto";
import { ContextoIdioma, crearTraductor } from "./i18n";
import { GuiaVoz, vocesDisponibles, type ContextoLectura } from "./voz";

interface Aviso { id: number; texto: string }
const CLAVE_MOVIMIENTO = "zoonauta.movimientoReducido";

function movimientoInicial(): boolean {
  try {
    const guardado = localStorage.getItem(CLAVE_MOVIMIENTO);
    if (guardado !== null) return guardado === "1";
  } catch { /* almacenamiento no disponible */ }
  return false;
}

// Preferencia del sistema, escuchada en vivo. Si pide reducir, manda sobre la elección local.
function useSistemaReduceMovimiento(): boolean {
  const [reduce, setReduce] = useState(() => matchMedia("(prefers-reduced-motion: reduce)").matches);
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
  const [diccionarios, setDiccionarios] = useState<Diccionarios>({ es: {}, "pt-BR": {} });
  const [catalogoVoces, setCatalogoVoces] = useState<VozCatalogo[]>([]);
  const [errorCarga, setErrorCarga] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);
  const [versionVoces, setVersionVoces] = useState(0);
  const [prefs, setPrefs] = useState<ValoresPreferencias>(() => ({
    retos: "8", opciones: 8, vozActiva: true, vozId: "", velocidad: 0.95, movimientoReducido: movimientoInicial(),
  }));
  const sistemaReduce = useSistemaReduceMovimiento();
  const movimientoReducido = prefs.movimientoReducido || sistemaReduce;
  const ocupadoRef = useRef(false);
  const vistaRef = useRef<Vista | null>(null);
  vistaRef.current = vista;
  const preferencias = useRef<HTMLDialogElement>(null);
  const eleccionesVoz = useRef<Partial<Record<Idioma, string>>>({});

  const idioma: Idioma = vista?.idioma ?? "es";
  const traductor = useMemo(() => crearTraductor(diccionarios, idioma), [diccionarios, idioma]);
  const { t } = traductor;

  const notificar = useCallback((texto: string) => {
    const id = Date.now() + Math.random();
    setAvisos((a) => [...a.slice(-2), { id, texto }]);
    window.setTimeout(() => setAvisos((a) => a.filter((x) => x.id !== id)), 8000);
  }, []);
  const guia = useMemo(() => new GuiaVoz(notificar), [notificar]);

  // Carga inicial: la cookie de sesión permite recuperar la partida al recargar.
  useEffect(() => {
    Promise.all([cargarVista(), cargarDiccionarios(), cargarConfigVoz()])
      .then(([v, d, c]) => { setVista(v); setDiccionarios(d); setCatalogoVoces(c.voces); })
      .catch(() => setErrorCarga(true));
  }, []);

  useEffect(() => {
    const alCambiar = () => setVersionVoces((n) => n + 1);
    window.speechSynthesis?.addEventListener("voiceschanged", alCambiar);
    const alSalir = () => guia.parar();
    window.addEventListener("pagehide", alSalir);
    return () => {
      window.speechSynthesis?.removeEventListener("voiceschanged", alCambiar);
      window.removeEventListener("pagehide", alSalir);
    };
  }, [guia]);

  const voces = useMemo(() => vocesDisponibles(catalogoVoces, idioma),
    // versionVoces fuerza la relectura cuando el navegador publica sus voces.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [catalogoVoces, idioma, versionVoces]);
  const vozId = useMemo(() => {
    const recordada = eleccionesVoz.current[idioma];
    return (voces.find((v) => v.id === recordada && v.disponible) ?? voces.find((v) => v.id === prefs.vozId && v.disponible)
      ?? voces.find((v) => v.disponible))?.id ?? "";
  }, [voces, idioma, prefs.vozId]);

  useEffect(() => {
    document.documentElement.lang = idioma;
    document.title = "Zoonauta · " + t("Animales y hábitats");
  }, [idioma, t]);
  useEffect(() => {
    document.documentElement.dataset.movimiento = movimientoReducido ? "reducido" : "normal";
  }, [movimientoReducido]);
  useEffect(() => {
    try { localStorage.setItem(CLAVE_MOVIMIENTO, prefs.movimientoReducido ? "1" : "0"); } catch { /* sin almacenamiento */ }
  }, [prefs.movimientoReducido]);

  // Al cambiar de fase se lleva el foco al título de la pantalla nueva.
  const fase = vista?.fase;
  const primeraFase = useRef(true);
  useEffect(() => {
    if (!fase) return;
    if (primeraFase.current) { primeraFase.current = false; return; }
    window.scrollTo({ top: 0, behavior: "instant" });
    const destino = fase === "PAUSADA" ? document.querySelector<HTMLElement>(".cierre .control")
      : document.getElementById("titulo-pantalla");
    destino?.focus({ preventScroll: true });
  }, [fase]);

  const hablar = useCallback((v: Vista, contexto: ContextoLectura) => {
    void guia.hablar(v, voces, { activa: prefs.vozActiva, vozId, velocidad: prefs.velocidad }, contexto, {
      prueba: t("Hola. Vamos a descubrir dónde viven los animales."),
      modalidad: t("¿Quién elige el animal?"),
      error: t("No se pudo reproducir la voz. Puedes volver a pulsar Repetir."),
    });
  }, [guia, voces, prefs.vozActiva, prefs.velocidad, vozId, t]);

  const accion = useCallback(async (tipo: TipoAccion, payload: Record<string, unknown> = {}) => {
    const actual = vistaRef.current;
    if (ocupadoRef.current || !actual) return;
    if (tipo === "iniciar") {
      const n = Number(prefs.retos);
      if (!Number.isInteger(n) || n < 1 || n > 48) {
        notificar(t("Para comenzar, abre Preferencias y escribe un número entero del 1 al 48."));
        return;
      }
      payload = { ...payload, retos: n, cantidad_opciones: prefs.opciones };
    }
    ocupadoRef.current = true;
    setOcupado(true);
    guia.parar();
    try {
      const { ok, datos } = await enviarAccion(actual, tipo, payload);
      // El tablero no se reconstruye: React solo actualiza lo que cambió.
      if (datos.vista) setVista(datos.vista);
      if (!ok) { notificar(datos.error || t("No se pudo aplicar la acción.")); return; }
      if (datos.aceptada && datos.respuesta_emitida && datos.vista && tipo !== "pausar" && tipo !== "nueva_partida")
        hablar(datos.vista, "respuesta");
    } catch {
      notificar(t("No se pudo conectar con el juego. Comprueba que el servidor siga abierto y recarga la página para recuperar la partida."));
    } finally {
      ocupadoRef.current = false;
      setOcupado(false);
    }
  }, [prefs.retos, prefs.opciones, guia, hablar, notificar, t]);

  const cambiarIdioma = useCallback(async (nuevo: Idioma) => {
    const actual = vistaRef.current;
    if (ocupadoRef.current || !actual || nuevo === actual.idioma) return;
    ocupadoRef.current = true;
    setOcupado(true);
    guia.parar();
    try {
      const { ok, datos } = await enviarIdioma(actual, nuevo);
      if (datos.vista) setVista(datos.vista);
      if (!ok) notificar(datos.error || t("No se pudo cambiar el idioma."));
    } catch {
      notificar(t("No se pudo cambiar el idioma."));
    } finally {
      ocupadoRef.current = false;
      setOcupado(false);
    }
  }, [guia, notificar, t]);

  const abrirPreferencias = () => {
    preferencias.current?.showModal();
    setDialogoAbierto(true);
  };

  if (errorCarga) return <main id="juego"><p className="introduccion">No se pudo cargar el juego. Inicia el servidor y vuelve a abrir esta página.</p></main>;
  if (!vista) return <main id="juego" aria-busy="true"><p className="cargando" role="status">Preparando tu expedición…</p></main>;

  const enInicio = vista.fase === "INICIO";
  let pantalla: React.ReactNode;
  if (enInicio) {
    pantalla = (
      <Portada vista={vista} movimientoReducido={movimientoReducido} dialogoAbierto={dialogoAbierto}
        onAbrirModalidad={() => { setDialogoAbierto(true); hablar(vista, "modalidad"); }}
        onCerrarModalidad={() => { setDialogoAbierto(false); if (vistaRef.current?.fase === "INICIO") guia.parar(); }}
        onComenzar={(modalidad: Modalidad) => void accion("iniciar", { modalidad })} />
    );
  } else if (vista.fase === "SELECCION_ANIMAL") {
    pantalla = <Catalogo vista={vista} onElegir={(id) => void accion("elegir_animal", { animal_id: id })}
      controles={<Controles vista={vista} onAccion={(tipo) => void accion(tipo)} />} />;
  } else if (vista.fase === "PAUSADA" || vista.fase === "COMPLETADA" || vista.fase === "ABANDONADA") {
    pantalla = <Cierre vista={vista} onAccion={(tipo) => void accion(tipo)} />;
  } else {
    pantalla = <Reto vista={vista} onAccion={(tipo, payload) => void accion(tipo, payload)} />;
  }

  return (
    <ContextoIdioma.Provider value={traductor}>
      <a className="saltar" href="#juego">{t("Ir al juego")}</a>
      <header className="cabecera" data-fase={vista.fase}>
        <a className="marca" href="/v6/" aria-label={t("Zoonauta, recuperar pantalla")}>
          <img src="/zoonauta-logo.svg" alt="" width={44} height={44} />
          <span className="marca-texto">Zoonauta<span className="marca-subtitulo">{t("Animales y hábitats")}</span></span>
        </a>
        <button type="button" className="boton-texto" aria-haspopup="dialog" onClick={abrirPreferencias}>
          <Icono nombre="ajustes" /><span>{t("Preferencias")}</span>
        </button>
      </header>
      <main id="juego" tabIndex={-1} aria-busy={ocupado} data-fase={vista.fase}>{pantalla}</main>
      {enInicio && (
        <footer className="creditos">
          <span>Zoonauta <span className="version">6.0 · prototipo</span></span>
          <p>{t("Ilustraciones de animales, pictogramas y paisajes originales generados con IA.")}</p>
        </footer>
      )}
      <div className="avisos" role="region" aria-label={t("Notificaciones")}>
        {avisos.map((a) => (
          <article key={a.id} className="aviso" role="status" aria-atomic="true">
            <p>{a.texto}</p>
            <button type="button" className="control-redondo" aria-label={t("Cerrar notificación")}
              onClick={() => setAvisos((x) => x.filter((y) => y.id !== a.id))}><Icono nombre="cerrar" /></button>
          </article>
        ))}
      </div>
      <Preferencias ref={preferencias} idioma={idioma} enInicio={enInicio} voces={voces} sistemaReduce={sistemaReduce}
        valores={{ ...prefs, vozId }}
        onCambio={(cambios) => {
          if ("vozId" in cambios || "velocidad" in cambios || cambios.vozActiva === false) guia.parar();
          if (cambios.vozId) eleccionesVoz.current[idioma] = cambios.vozId;
          setPrefs((p) => ({ ...p, ...cambios }));
        }}
        onIdioma={(nuevo) => void cambiarIdioma(nuevo)}
        onProbarVoz={() => void guia.hablar(vista, voces, { activa: true, vozId, velocidad: prefs.velocidad }, "prueba", {
          prueba: t("Hola. Vamos a descubrir dónde viven los animales."), modalidad: "", error: t("No se pudo reproducir la voz. Puedes volver a pulsar Repetir."),
        })}
        onCerrar={() => setDialogoAbierto(Boolean(document.querySelector("dialog[open]")))} />
    </ContextoIdioma.Provider>
  );
}
