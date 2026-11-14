// Lectura en voz alta de la guía. Una sola lectura a la vez y cancelación al cambiar de
// mensaje o pausar (lógica de la 5.0). La única voz es la grabada de Zoonauta (Marcela,
// ElevenLabs, /api/voz/grabada), y solo en español (decisión del propietario, 2026-11-14:
// sin Piper, Kokoro ni voces del navegador). Nunca se unen audios: si un mensaje no tiene
// grabación, no se lee con otra voz.
import { pedirGrabacion } from "./api/cliente";
import type { Idioma, Vista } from "./api/tipos";

/** Idiomas con voz. En pt-BR la voz queda bloqueada hasta que existan grabaciones. */
export const IDIOMAS_CON_VOZ: readonly Idioma[] = ["es"];

export interface AjustesVoz {
  activa: boolean;
  velocidad: number;
  /** Mensajes con grabación disponible en este idioma (0 = no se piden). */
  grabadas: number;
}

export type ContextoLectura = "respuesta" | "modalidad" | "prueba";

export class GuiaVoz {
  private turno = 0;
  private pedido: AbortController | null = null;
  private audio: HTMLAudioElement | null = null;
  private audioURL: string | null = null;

  constructor(private readonly alError: (mensaje: string) => void) {}

  parar() {
    this.turno++;
    this.pedido?.abort();
    this.pedido = null;
    if (this.audio) {
      this.audio.pause();
      this.audio.removeAttribute("src");
      this.audio = null;
    }
    if (this.audioURL) {
      URL.revokeObjectURL(this.audioURL);
      this.audioURL = null;
    }
  }

  /** «Probar voz» (contexto "prueba") reproduce la grabación del mensaje que está en pantalla. */
  async hablar(vista: Vista, ajustes: AjustesVoz, contexto: ContextoLectura, textos: { error: string }) {
    if (!ajustes.activa && contexto !== "prueba") return;
    this.parar();
    if (!IDIOMAS_CON_VOZ.includes(vista.idioma) || ajustes.grabadas === 0) {
      // Si la persona pulsó Probar voz, se le avisa de por qué no suena nada.
      if (contexto === "prueba") this.alError(textos.error);
      return;
    }
    const turno = this.turno;
    const control = new AbortController();
    this.pedido = control;
    try {
      const r = await pedirGrabacion(
        {
          idioma: vista.idioma,
          revision: vista.revision,
          sesion_id: vista.sesion_id,
          reto_id: vista.reto_id,
          contexto: contexto === "modalidad" ? "modalidad" : "respuesta",
        },
        control.signal,
      );
      if (turno !== this.turno) return;
      if (!r.ok) {
        this.pedido = null;
        if (contexto === "prueba") this.alError(textos.error);
        return;
      }
      // El pedido sigue cancelable mientras llega el audio; después se vuelve a comprobar el
      // turno para que una lectura ya sustituida nunca llegue a sonar (una sola voz a la vez).
      const blob = await r.blob();
      if (turno !== this.turno) return;
      this.pedido = null;
      await this.reproducir(blob, turno, ajustes.velocidad, textos.error);
    } catch (e) {
      if ((e as Error).name === "AbortError" || turno !== this.turno) return;
      // Un fallo de red se avisa con el mensaje traducido, no con el del navegador.
      this.parar();
      this.alError(textos.error);
    }
  }

  private async reproducir(blob: Blob, turno: number, velocidad: number, error: string) {
    this.audioURL = URL.createObjectURL(blob);
    const audio = new Audio(this.audioURL);
    this.audio = audio;
    audio.playbackRate = velocidad;
    audio.preservesPitch = true;
    audio.onended = () => {
      if (turno === this.turno) this.parar();
    };
    audio.onerror = () => {
      if (turno === this.turno) {
        this.parar();
        this.alError(error);
      }
    };
    await audio.play();
  }
}
