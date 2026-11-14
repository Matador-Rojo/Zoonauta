// Lectura en voz alta. Porta la lógica de 5.0 (app.js): una sola lectura a la vez,
// cancelación al cambiar de mensaje o pausar, voces locales (Piper/Kokoro vía
// /api/voz) y voces compatibles del navegador (Microsoft/Google, es-419 y pt-BR).
import { cancelarVoz, pedirVoz } from "./api/cliente";
import type { Idioma, Vista, VozCatalogo } from "./api/tipos";

export interface OpcionVoz extends Omit<VozCatalogo, "motor"> {
  motor: VozCatalogo["motor"];
  nativa?: SpeechSynthesisVoice;
  idioma_voz?: string;
  local?: boolean;
}

const REGIONES_LATAM = new Set([
  "419",
  "AR",
  "BO",
  "CL",
  "CO",
  "CR",
  "CU",
  "DO",
  "EC",
  "GT",
  "HN",
  "MX",
  "NI",
  "PA",
  "PE",
  "PR",
  "PY",
  "SV",
  "UY",
  "VE",
  "US",
]);

export function vocesNavegador(): OpcionVoz[] {
  if (!window.speechSynthesis || typeof window.SpeechSynthesisUtterance !== "function") return [];
  const resultado: OpcionVoz[] = [];
  const vistos = new Set<string>();
  for (const voz of window.speechSynthesis.getVoices()) {
    const idioma = voz.lang.replaceAll("_", "-");
    const partes = idioma.split("-");
    const lengua = partes[0].toLowerCase();
    const region = partes.find((p) => /^(?:[A-Z]{2}|419)$/.test(p.toUpperCase()) && p !== partes[0])?.toUpperCase();
    // No se presenta es-ES como latinoamericana ni pt-PT como brasileña.
    if (!((lengua === "es" && region && REGIONES_LATAM.has(region)) || (lengua === "pt" && region === "BR"))) continue;
    const nombre = `${voz.name} ${voz.voiceURI}`;
    const motor = /\bmicrosoft\b/i.test(nombre) ? "microsoft" : /\bgoogle\b/i.test(nombre) ? "google" : null;
    if (!motor) continue;
    const id = "navegador:" + encodeURIComponent([voz.voiceURI, voz.name, idioma].join("|"));
    if (vistos.has(id)) continue;
    vistos.add(id);
    resultado.push({
      id,
      nombre: voz.name,
      motor,
      idioma: lengua === "es" ? "es" : "pt-BR",
      region: region!,
      disponible: true,
      nativa: voz,
      idioma_voz: idioma,
      local: voz.localService,
    });
  }
  return resultado.sort((a, b) => a.nombre.localeCompare(b.nombre));
}

export interface AjustesVoz {
  activa: boolean;
  vozId: string;
  velocidad: number;
}

export type ContextoLectura = "respuesta" | "modalidad" | "prueba";

export class GuiaVoz {
  private readonly canal = crypto.randomUUID();
  private turno = 0;
  private pedido: AbortController | null = null;
  private audio: HTMLAudioElement | null = null;
  private audioURL: string | null = null;
  private lecturaNativa: SpeechSynthesisUtterance | null = null;

  constructor(private readonly alError: (mensaje: string) => void) {}

  parar() {
    const pendiente = this.pedido;
    this.turno++;
    pendiente?.abort();
    this.pedido = null;
    if (pendiente) void cancelarVoz(this.canal, this.turno);
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute("src");
      this.audio = null;
    }
    if (this.lecturaNativa) {
      this.lecturaNativa = null;
      window.speechSynthesis?.cancel();
    }
    if (this.audioURL) {
      URL.revokeObjectURL(this.audioURL);
      this.audioURL = null;
    }
  }

  async hablar(
    vista: Vista,
    voces: OpcionVoz[],
    ajustes: AjustesVoz,
    contexto: ContextoLectura,
    textos: { prueba: string; modalidad: string; error: string },
  ) {
    if (!ajustes.activa && contexto !== "prueba") return;
    this.parar();
    const voz = voces.find((v) => v.id === ajustes.vozId && v.disponible);
    if (!voz) return;
    const turno = this.turno;
    if (voz.nativa) {
      const texto =
        contexto === "prueba" ? textos.prueba : contexto === "modalidad" ? textos.modalidad : vista.respuesta.texto_voz;
      const lectura = new SpeechSynthesisUtterance(texto);
      lectura.voice = voz.nativa;
      lectura.lang = voz.idioma_voz ?? vista.idioma;
      lectura.rate = ajustes.velocidad;
      this.lecturaNativa = lectura;
      lectura.onend = () => {
        if (turno === this.turno) this.lecturaNativa = null;
      };
      lectura.onerror = () => {
        if (turno === this.turno) {
          this.parar();
          this.alError(textos.error);
        }
      };
      try {
        window.speechSynthesis.speak(lectura);
      } catch {
        this.parar();
        this.alError(textos.error);
      }
      return;
    }
    const control = new AbortController();
    this.pedido = control;
    const entrada = {
      voz: voz.id,
      idioma: vista.idioma,
      prueba: contexto === "prueba",
      revision: vista.revision,
      sesion_id: vista.sesion_id,
      reto_id: vista.reto_id,
      canal_voz: this.canal,
      turno_voz: turno,
      contexto: contexto === "modalidad" ? "modalidad" : "respuesta",
    };
    try {
      const r = await pedirVoz(entrada, control.signal);
      if (!r.ok) {
        const d = (await r.json()) as { error?: string; cancelada?: boolean };
        if (d.cancelada) return;
        throw new Error(d.error || textos.error);
      }
      const blob = await r.blob();
      if (turno !== this.turno) return;
      this.pedido = null;
      this.audioURL = URL.createObjectURL(blob);
      const audio = new Audio(this.audioURL);
      this.audio = audio;
      audio.playbackRate = ajustes.velocidad;
      audio.preservesPitch = true;
      audio.onended = () => {
        if (turno === this.turno) this.parar();
      };
      audio.onerror = () => {
        if (turno === this.turno) {
          this.parar();
          this.alError(textos.error);
        }
      };
      await audio.play();
    } catch (e) {
      if ((e as Error).name !== "AbortError" && turno === this.turno) {
        this.parar();
        this.alError((e as Error).message);
      }
    }
  }
}

export function vocesDisponibles(catalogo: VozCatalogo[], idioma: Idioma): OpcionVoz[] {
  return [...catalogo, ...vocesNavegador()].filter((v) => v.idioma === idioma);
}
