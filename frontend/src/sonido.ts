/**
 * Motor sonoro y musical procedural del «Bosque de luz» (Web Audio API).
 * 100 % offline, sin archivos de audio externos y bajo control del usuario:
 * - Durante el juego: paisaje suave de brisa y arroyo + micro-sonidos armónicos táctiles.
 * - En PAUSA: música serena inspirada en la naturaleza (kalimba/arpa lenta + brisa cálida + gotas de rocío).
 * - Al COMPLETAR (Victoria): fanfarria luminosa con canto de ave + melodía alegre del amanecer en el bosque.
 * - Atenuación automática (ducking) mientras habla la voz grabada de Zoonauta.
 * - Silencio inmediato al ocultar la pestaña o desactivar «Sonidos del bosque».
 */

export type EfectoSonido = "pista" | "acierto" | "neutral" | "pagina" | "cierre" | "transicion" | "elegir";
export type ModoMusica = "juego" | "pausa" | "victoria" | "silencio";
export type BiomaAcustico = "mar" | "agua" | "bosque" | "montana" | "sabana";

export function clasificarBiomaAcustico(habitatId?: string | null): BiomaAcustico | null {
  if (!habitatId) return null;
  const h = habitatId.toUpperCase();
  if (
    h.includes("MAR") ||
    h.includes("OCEANO") ||
    h.includes("ARRECIFE") ||
    h.includes("COSTA") ||
    h.includes("PLAYA") ||
    h.includes("ALGAS") ||
    h.includes("MANGLAR") ||
    h.includes("DUNA") ||
    h.includes("ACANTILADO") ||
    h.includes("ISLA")
  ) {
    return "mar";
  }
  if (
    h.includes("RIO") ||
    h.includes("LAGO") ||
    h.includes("HUMEDAL") ||
    h.includes("PANTANO") ||
    h.includes("ESTUARIO") ||
    h.includes("OASIS") ||
    h.includes("LAGUNA") ||
    h.includes("CHARCA") ||
    h.includes("ARROYO")
  ) {
    return "agua";
  }
  if (h.includes("BOSQUE") || h.includes("SELVA") || h.includes("TAIGA") || h.includes("JUNGLA")) {
    return "bosque";
  }
  if (
    h.includes("MONTANA") ||
    h.includes("HIELO") ||
    h.includes("POLAR") ||
    h.includes("TUNDRA") ||
    h.includes("CUEVA") ||
    h.includes("PARAMO") ||
    h.includes("GLACIAR") ||
    h.includes("ALTA")
  ) {
    return "montana";
  }
  return "sabana";
}

export class MotorSonido {
  private ctx: AudioContext | null = null;
  private maestro: GainNode | null = null;
  private musicaGain: GainNode | null = null;
  private ambienteGain: GainNode | null = null;
  private ambienteFiltro: BiquadFilterNode | null = null;
  private fuenteRuido: AudioBufferSourceNode | null = null;
  private temporizador: number | null = null;
  private compas = 0;
  private activo = false;
  private oculto = false;
  private hablando = false;
  private modo: ModoMusica = "juego";

  private asegurarContexto(): AudioContext | null {
    if (typeof window === "undefined") return null;
    const Ctor =
      window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return null;
    if (!this.ctx) {
      try {
        this.ctx = new Ctor();
        this.maestro = this.ctx.createGain();
        this.maestro.gain.value = 0.85;
        this.maestro.connect(this.ctx.destination);

        this.musicaGain = this.ctx.createGain();
        this.musicaGain.gain.value = 0.0001;
        this.musicaGain.connect(this.maestro);

        this.ctx.onstatechange = () => {
          if (this.ctx?.state === "running" && this.puedeSonar()) {
            this.iniciarAmbiente(this.ctx);
            this.actualizarNiveles();
            if ((this.modo === "pausa" || this.modo === "victoria") && this.temporizador === null) {
              this.sincronizarMusica(this.modo === "victoria");
            }
          }
        };
      } catch {
        return null;
      }
    }
    if (this.ctx.state === "suspended") {
      void this.ctx
        .resume()
        .then(() => {
          if (this.ctx && this.puedeSonar()) {
            this.iniciarAmbiente(this.ctx);
            this.actualizarNiveles();
          }
        })
        .catch(() => undefined);
    }
    return this.ctx;
  }

  private iniciarAmbiente(ctx: AudioContext) {
    if (this.fuenteRuido || !this.maestro) return;
    // Ruido rosa suave de 4 segundos en bucle, filtrado para evocar brisa y arroyo lejano.
    const largo = ctx.sampleRate * 4;
    const buffer = ctx.createBuffer(1, largo, ctx.sampleRate);
    const datos = buffer.getChannelData(0);
    let b0 = 0;
    let b1 = 0;
    let b2 = 0;
    for (let i = 0; i < largo; i++) {
      const blanco = Math.random() * 2 - 1;
      b0 = 0.997 * b0 + blanco * 0.029;
      b1 = 0.985 * b1 + blanco * 0.032;
      b2 = 0.95 * b2 + blanco * 0.048;
      datos[i] = (b0 + b1 + b2 + blanco * 0.008) * 0.35;
    }

    const fuente = ctx.createBufferSource();
    fuente.buffer = buffer;
    fuente.loop = true;

    const filtro = ctx.createBiquadFilter();
    filtro.type = "bandpass";
    filtro.frequency.value = 420;
    filtro.Q.value = 0.85;

    const ganancia = ctx.createGain();
    ganancia.gain.value = 0.0001;

    fuente.connect(filtro);
    filtro.connect(ganancia);
    ganancia.connect(this.maestro);
    fuente.start();

    this.fuenteRuido = fuente;
    this.ambienteFiltro = filtro;
    this.ambienteGain = ganancia;
  }

  private puedeSonar(): boolean {
    return this.activo && !this.oculto && this.modo !== "silencio";
  }

  private actualizarNiveles() {
    if (!this.ctx) return;
    const ahora = this.ctx.currentTime;
    const audible = this.puedeSonar();

    if (this.ambienteGain && this.ambienteFiltro) {
      let objAmb = 0.0001;
      let freq = 420;
      if (audible) {
        if (this.modo === "pausa") {
          objAmb = this.hablando ? 0.015 : 0.055;
          freq = 280; // Brisa más cálida y calma en pausa
        } else if (this.modo === "victoria") {
          objAmb = this.hablando ? 0.012 : 0.04;
          freq = 520; // Aire claro y luminoso al celebrar
        } else {
          objAmb = this.hablando ? 0.02 : 0.085;
          freq = 420;
        }
      }
      this.ambienteGain.gain.cancelScheduledValues(ahora);
      this.ambienteGain.gain.setTargetAtTime(objAmb, ahora, 0.32);
      this.ambienteFiltro.frequency.cancelScheduledValues(ahora);
      this.ambienteFiltro.frequency.setTargetAtTime(freq, ahora, 0.45);
    }

    if (this.musicaGain) {
      const conMusica = audible && (this.modo === "pausa" || this.modo === "victoria");
      const objMus = !conMusica ? 0.0001 : this.hablando ? 0.26 : 0.92;
      this.musicaGain.gain.cancelScheduledValues(ahora);
      this.musicaGain.gain.setTargetAtTime(objMus, ahora, 0.28);
    }
  }

  private detenerBucleMusica() {
    if (this.temporizador !== null) {
      window.clearTimeout(this.temporizador);
      this.temporizador = null;
    }
  }

  private programarVoz(
    destino: AudioNode,
    freq: number,
    inicio: number,
    duracion: number,
    vol: number,
    tipo: OscillatorType = "sine",
    corteHz = 2400,
  ) {
    if (!this.ctx) return;
    const t0 = this.ctx.currentTime + inicio;
    const osc = this.ctx.createOscillator();
    const filtro = this.ctx.createBiquadFilter();
    const env = this.ctx.createGain();
    osc.type = tipo;
    osc.frequency.setValueAtTime(freq, t0);
    filtro.type = "lowpass";
    filtro.frequency.setValueAtTime(corteHz, t0);
    env.gain.setValueAtTime(0.0001, t0);
    env.gain.linearRampToValueAtTime(vol, t0 + Math.min(0.06, duracion * 0.25));
    env.gain.exponentialRampToValueAtTime(0.0001, t0 + duracion);
    osc.connect(filtro);
    filtro.connect(env);
    env.connect(destino);
    osc.start(t0);
    osc.stop(t0 + duracion + 0.05);
  }

  /** Canto sutil y orgánico de pájaro del bosque para la música de victoria. */
  private cantarAve(destino: AudioNode, inicio: number, pitchBase = 1950, vol = 0.022) {
    if (!this.ctx) return;
    const t0 = this.ctx.currentTime + inicio;
    const osc = this.ctx.createOscillator();
    const env = this.ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(pitchBase, t0);
    osc.frequency.exponentialRampToValueAtTime(pitchBase * 1.28, t0 + 0.07);
    osc.frequency.exponentialRampToValueAtTime(pitchBase * 1.05, t0 + 0.14);
    osc.frequency.exponentialRampToValueAtTime(pitchBase * 1.34, t0 + 0.21);
    env.gain.setValueAtTime(0.0001, t0);
    env.gain.linearRampToValueAtTime(vol, t0 + 0.03);
    env.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.24);
    osc.connect(env);
    env.connect(destino);
    osc.start(t0);
    osc.stop(t0 + 0.26);
  }

  /** Gota de rocío suave sobre estanque para la música serena de pausa. */
  private gotaAgua(destino: AudioNode, inicio: number, freq = 920) {
    if (!this.ctx) return;
    const t0 = this.ctx.currentTime + inicio;
    const osc = this.ctx.createOscillator();
    const env = this.ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq * 0.72, t0);
    osc.frequency.exponentialRampToValueAtTime(freq, t0 + 0.065);
    env.gain.setValueAtTime(0.0001, t0);
    env.gain.linearRampToValueAtTime(0.026, t0 + 0.012);
    env.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.16);
    osc.connect(env);
    env.connect(destino);
    osc.start(t0);
    osc.stop(t0 + 0.18);
  }

  /** Compás sereno de pausa: kalimba/arpa de agua en Fa mayor / Re menor 9 + gotas de rocío. */
  private tocarFrasePausa() {
    if (!this.puedeSonar() || this.modo !== "pausa") return;
    const ctx = this.asegurarContexto();
    if (!ctx || !this.musicaGain) return;
    const dest = this.musicaGain;

    // 4 acordes contemplativos (Fmaj7 -> Dm9 -> Bbmaj7 -> C6), 1 por paso del ciclo
    const progresion: Array<{ pad: number[]; arpa: number[]; gota: number }> = [
      { pad: [174.61, 220.0, 261.63, 329.63], arpa: [349.23, 440.0, 523.25, 659.25, 523.25], gota: 880 },
      { pad: [146.83, 220.0, 261.63, 329.63], arpa: [293.66, 349.23, 440.0, 523.25, 440.0], gota: 784 },
      { pad: [233.08, 293.66, 349.23, 440.0], arpa: [349.23, 440.0, 587.33, 523.25, 440.0], gota: 932 },
      { pad: [196.0, 261.63, 329.63, 440.0], arpa: [329.63, 392.0, 440.0, 523.25, 392.0], gota: 830 },
    ];
    const frase = progresion[this.compas % progresion.length];
    this.compas++;

    // Colchón tibio respiratorio
    for (const f of frase.pad) {
      this.programarVoz(dest, f, 0.05, 3.3, 0.018, "sine", 780);
    }
    // Arpegio lento tipo kalimba/arpa suave
    frase.arpa.forEach((f, idx) => {
      this.programarVoz(dest, f, 0.15 + idx * 0.56, 1.45, 0.036, "triangle", 1350);
    });
    // Gota suave de rocío
    this.gotaAgua(dest, 2.2, frase.gota);

    this.temporizador = window.setTimeout(() => this.tocarFrasePausa(), 3400);
  }

  /** Fanfarria y melodía festiva de victoria: «Amanecer en el bosque» (Do mayor luminoso + aves). */
  private tocarFraseVictoria(esApertura: boolean) {
    if (!this.puedeSonar() || this.modo !== "victoria") return;
    const ctx = this.asegurarContexto();
    if (!ctx || !this.musicaGain) return;
    const dest = this.musicaGain;

    if (esApertura) {
      // Fanfarria cálida y alegre de marimba + flauta + canto de ave
      const fanfarria: Array<[number, number, number, OscillatorType]> = [
        [523.25, 0.0, 0.36, "triangle"], // C5
        [659.25, 0.12, 0.36, "triangle"], // E5
        [783.99, 0.24, 0.42, "triangle"], // G5
        [880.0, 0.38, 0.42, "sine"], // A5
        [1046.5, 0.54, 1.25, "triangle"], // C6
        [523.25, 0.54, 1.35, "sine"], // C5 soporte
        [783.99, 0.54, 1.35, "sine"], // G5 soporte
      ];
      for (const [f, t, d, tipo] of fanfarria) {
        this.programarVoz(dest, f, t, d, 0.062, tipo, 2800);
      }
      this.cantarAve(dest, 0.72, 2050, 0.025);
      this.cantarAve(dest, 1.18, 2320, 0.02);
      this.compas = 0;
      this.temporizador = window.setTimeout(() => this.tocarFraseVictoria(false), 1850);
      return;
    }

    // Melodía alegre de celebración natural en 4 compases (C -> F -> G -> C)
    const progresion: Array<{ bajo: number; acorde: number[]; melodia: Array<[number, number]>; ave?: number }> = [
      {
        bajo: 261.63,
        acorde: [329.63, 392.0, 493.88],
        melodia: [
          [523.25, 0.0],
          [659.25, 0.32],
          [783.99, 0.64],
          [880.0, 1.05],
          [783.99, 1.45],
        ],
        ave: 1.55,
      },
      {
        bajo: 174.61,
        acorde: [261.63, 349.23, 440.0],
        melodia: [
          [698.46, 0.0],
          [880.0, 0.36],
          [783.99, 0.78],
          [659.25, 1.25],
        ],
      },
      {
        bajo: 196.0,
        acorde: [293.66, 392.0, 493.88],
        melodia: [
          [587.33, 0.0],
          [783.99, 0.36],
          [880.0, 0.76],
          [987.77, 1.18],
        ],
        ave: 1.35,
      },
      {
        bajo: 261.63,
        acorde: [329.63, 392.0, 523.25],
        melodia: [
          [1046.5, 0.0],
          [880.0, 0.42],
          [783.99, 0.84],
          [1046.5, 1.26],
        ],
      },
    ];
    const frase = progresion[this.compas % progresion.length];
    this.compas++;

    this.programarVoz(dest, frase.bajo, 0, 2.05, 0.032, "sine", 700);
    for (const f of frase.acorde) {
      this.programarVoz(dest, f, 0.04, 1.95, 0.02, "sine", 1100);
    }
    for (const [f, t] of frase.melodia) {
      this.programarVoz(dest, f, t, 0.75, 0.044, "triangle", 2400);
      this.programarVoz(dest, f * 2, t + 0.01, 0.35, 0.012, "sine", 3200);
    }
    if (frase.ave !== undefined) {
      this.cantarAve(dest, frase.ave, 1980 + (this.compas % 2) * 240, 0.018);
    }

    this.temporizador = window.setTimeout(() => this.tocarFraseVictoria(false), 2150);
  }

  private sincronizarMusica(reiniciarApertura = false) {
    this.detenerBucleMusica();
    if (!this.puedeSonar()) {
      this.actualizarNiveles();
      return;
    }
    const ctx = this.asegurarContexto();
    if (!ctx) return;
    this.iniciarAmbiente(ctx);
    this.actualizarNiveles();

    if (this.modo === "pausa") {
      this.compas = 0;
      this.tocarFrasePausa();
    } else if (this.modo === "victoria") {
      this.tocarFraseVictoria(reiniciarApertura);
    }
  }

  fijarActivo(activo: boolean) {
    const cambio = this.activo !== activo;
    this.activo = activo;
    if (!activo) {
      this.detenerBucleMusica();
      this.actualizarNiveles();
      return;
    }
    if (cambio) this.sincronizarMusica(this.modo === "victoria");
    else this.actualizarNiveles();
  }

  fijarOculto(oculto: boolean) {
    if (this.oculto === oculto) return;
    this.oculto = oculto;
    if (oculto) {
      this.detenerBucleMusica();
      this.actualizarNiveles();
    } else {
      this.sincronizarMusica(false);
    }
  }

  fijarModo(modo: ModoMusica) {
    if (this.modo === modo) return;
    this.modo = modo;
    this.sincronizarMusica(modo === "victoria");
  }

  fijarHablando(hablando: boolean) {
    this.hablando = hablando;
    this.actualizarNiveles();
  }

  /** Reanuda el contexto de audio tras el primer gesto del usuario (política autoplay). */
  despertar() {
    if (!this.puedeSonar()) return;
    const ctx = this.asegurarContexto();
    if (!ctx) return;
    const arrancar = () => {
      if (!this.ctx || !this.puedeSonar()) return;
      this.iniciarAmbiente(this.ctx);
      this.actualizarNiveles();
      if ((this.modo === "pausa" || this.modo === "victoria") && this.temporizador === null) {
        this.sincronizarMusica(this.modo === "victoria");
      }
    };
    if (ctx.state === "running") {
      arrancar();
    } else {
      void ctx
        .resume()
        .then(arrancar)
        .catch(() => undefined);
    }
  }

  /** Susurro breve de ola marina usando ruido filtrado para celebrar hábitats marinos/costeros. */
  private olaSuave(destino: AudioNode, inicio: number) {
    if (!this.ctx) return;
    const largo = Math.floor(this.ctx.sampleRate * 0.72);
    const buffer = this.ctx.createBuffer(1, largo, this.ctx.sampleRate);
    const datos = buffer.getChannelData(0);
    let last = 0;
    for (let i = 0; i < largo; i++) {
      const blanco = Math.random() * 2 - 1;
      last = 0.94 * last + blanco * 0.06;
      datos[i] = last * 1.4;
    }
    const t0 = this.ctx.currentTime + inicio;
    const src = this.ctx.createBufferSource();
    src.buffer = buffer;
    const filtro = this.ctx.createBiquadFilter();
    filtro.type = "bandpass";
    filtro.frequency.setValueAtTime(340, t0);
    filtro.frequency.exponentialRampToValueAtTime(760, t0 + 0.28);
    filtro.frequency.exponentialRampToValueAtTime(280, t0 + 0.7);
    filtro.Q.value = 1.1;
    const env = this.ctx.createGain();
    env.gain.setValueAtTime(0.0001, t0);
    env.gain.linearRampToValueAtTime(0.085, t0 + 0.24);
    env.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.7);
    src.connect(filtro);
    filtro.connect(env);
    env.connect(destino);
    src.start(t0);
    src.stop(t0 + 0.74);
  }

  tocar(efecto: EfectoSonido, habitatId?: string | null) {
    if (!this.puedeSonar()) return;
    const ctx = this.asegurarContexto();
    if (!ctx || !this.maestro) return;
    this.iniciarAmbiente(ctx);
    this.actualizarNiveles();

    const ahora = ctx.currentTime;
    const nota = (freq: number, inicio: number, duracion: number, vol: number, tipo: OscillatorType = "sine") => {
      if (!this.maestro) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = tipo;
      osc.frequency.setValueAtTime(freq, ahora + inicio);
      gain.gain.setValueAtTime(0.0001, ahora + inicio);
      gain.gain.linearRampToValueAtTime(vol, ahora + inicio + 0.025);
      gain.gain.exponentialRampToValueAtTime(0.0001, ahora + inicio + duracion);
      osc.connect(gain);
      gain.connect(this.maestro);
      osc.start(ahora + inicio);
      osc.stop(ahora + inicio + duracion + 0.03);
    };

    if (efecto === "pagina") {
      nota(520, 0, 0.09, 0.045, "triangle");
      nota(660, 0.035, 0.08, 0.035, "sine");
    } else if (efecto === "transicion") {
      // Paso suave de página de atlas: susurro aéreo breve + nota cálida
      nota(392.0, 0, 0.11, 0.028, "sine");
      nota(523.25, 0.045, 0.14, 0.032, "triangle");
    } else if (efecto === "elegir") {
      // Toque alegre al elegir un animal del catálogo
      nota(440.0, 0, 0.12, 0.042, "triangle");
      nota(659.25, 0.055, 0.18, 0.045, "sine");
    } else if (efecto === "pista") {
      // Campanilla cálida ascendente
      nota(440, 0, 0.22, 0.06, "triangle");
      nota(587.33, 0.09, 0.3, 0.055, "sine");
    } else if (efecto === "neutral") {
      // Gota suave de madera, amable y no punitiva
      nota(349.23, 0, 0.16, 0.05, "sine");
      nota(329.63, 0.08, 0.22, 0.04, "sine");
    } else if (efecto === "acierto") {
      // Acorde pentatónico luminoso de descubrimiento + firma acústica del bioma
      nota(523.25, 0, 0.34, 0.065, "sine");
      nota(659.25, 0.09, 0.38, 0.06, "triangle");
      nota(783.99, 0.18, 0.52, 0.065, "sine");

      const bioma = clasificarBiomaAcustico(habitatId);
      if (bioma === "bosque") {
        this.cantarAve(this.maestro, 0.28, 2080, 0.024);
      } else if (bioma === "agua") {
        this.gotaAgua(this.maestro, 0.24, 960);
        this.gotaAgua(this.maestro, 0.4, 1180);
      } else if (bioma === "mar") {
        this.olaSuave(this.maestro, 0.12);
      } else if (bioma === "montana") {
        // Destello cristalino de alta montaña / hielo
        nota(1567.98, 0.26, 0.48, 0.022, "sine");
        nota(2093.0, 0.34, 0.56, 0.018, "sine");
      } else if (bioma === "sabana") {
        // Toque cálido de marimba de madera
        nota(392.0, 0.24, 0.24, 0.042, "triangle");
        nota(587.33, 0.35, 0.32, 0.036, "triangle");
      }
    } else if (efecto === "cierre") {
      // Acompaña la transición hacia la música de victoria
      nota(523.25, 0, 0.32, 0.05, "sine");
      nota(659.25, 0.09, 0.34, 0.05, "sine");
      nota(783.99, 0.18, 0.42, 0.055, "triangle");
    }
  }

  cerrar() {
    this.activo = false;
    this.detenerBucleMusica();
    try {
      this.fuenteRuido?.stop();
    } catch {
      /* ya detenida */
    }
    this.fuenteRuido = null;
    this.ambienteFiltro = null;
    this.ambienteGain = null;
    this.musicaGain = null;
    if (this.ctx) {
      void this.ctx.close().catch(() => undefined);
      this.ctx = null;
      this.maestro = null;
    }
  }
}
