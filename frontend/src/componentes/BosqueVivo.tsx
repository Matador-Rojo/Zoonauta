import { useEffect, useRef } from "react";
import type { Fase } from "../api/tipos";
import type { TemaVisual } from "./Preferencias";

interface Punto {
  x: number;
  y: number;
}

interface Particula {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radio: number;
  fase: number;
  velocidadPulso: number;
  deriva: number;
  tono: "cian" | "luna" | "ambar";
  forma: "luz" | "hoja";
  angulo: number;
  velocidadGiro: number;
  estela: Punto[];
  vida?: number;
  vidaMax?: number;
}

interface Onda {
  x: number;
  y: number;
  radio: number;
  radioMax: number;
  alfa: number;
  tono: "cian" | "ambar";
}

interface DestelloRio {
  x: number;
  y: number;
  ancho: number;
  fase: number;
  velocidad: number;
}

const COLORES_NOCHE = {
  cian: "94, 234, 212",
  luna: "207, 250, 254",
  ambar: "253, 224, 71",
} as const;

// En Bosque de día usamos 100 % hojas verdes naturales de alta nitidez sobre el fondo claro
// (esmeralda bosque, verde hoja fresca y verde oliva soleado).
const COLORES_DIA = {
  cian: "5, 122, 85",
  luna: "22, 163, 74",
  ambar: "101, 163, 13",
} as const;

function crearAmbiente(
  ancho: number,
  alto: number,
  enPortada: boolean,
  esDia: boolean,
): Particula {
  const r = Math.random();
  const tono: Particula["tono"] =
    r < 0.45 ? "cian" : r < 0.8 ? "luna" : "ambar";
  const esHoja = esDia;
  const x = enPortada
    ? ancho * (0.24 + Math.random() * 0.76)
    : Math.random() * ancho;
  const y = enPortada
    ? alto * (0.1 + Math.random() * 0.86)
    : Math.random() * alto;
  return {
    x,
    y,
    vx: esHoja ? 0.22 + Math.random() * 0.3 : (Math.random() - 0.5) * 0.28,
    vy: esHoja ? 0.24 + Math.random() * 0.3 : -0.08 - Math.random() * 0.22,
    radio: esHoja
      ? 6.8 + Math.random() * 4.8
      : (enPortada ? 1.6 : 1.3) + Math.random() * (enPortada ? 2.2 : 1.6),
    fase: Math.random() * Math.PI * 2,
    velocidadPulso: 0.016 + Math.random() * 0.022,
    deriva: esHoja ? 0.38 + Math.random() * 0.28 : 0.14 + Math.random() * 0.22,
    tono,
    forma: esHoja ? "hoja" : "luz",
    angulo: Math.random() * Math.PI * 2,
    velocidadGiro: (Math.random() - 0.5) * 0.026,
    estela: [],
  };
}

function crearDestello(ancho: number, alto: number, esDia: boolean): Particula {
  const tono: Particula["tono"] = Math.random() < 0.6 ? "cian" : "ambar";
  return {
    x: ancho * (0.2 + Math.random() * 0.7),
    y: alto * (0.48 + Math.random() * 0.44),
    vx: (Math.random() - 0.5) * 0.85,
    vy: -0.6 - Math.random() * 0.9,
    radio: esDia ? 7.5 + Math.random() * 4.5 : 2 + Math.random() * 2.5,
    fase: Math.random() * Math.PI * 2,
    velocidadPulso: 0.045 + Math.random() * 0.035,
    deriva: 0.34,
    tono,
    forma: esDia ? "hoja" : "luz",
    angulo: Math.random() * Math.PI * 2,
    velocidadGiro: (Math.random() - 0.5) * 0.06,
    estela: [],
    vida: 0,
    vidaMax: 120 + Math.random() * 85,
  };
}

function crearDestellosRio(ancho: number, alto: number): DestelloRio[] {
  const cantidad = ancho < 700 ? 10 : 18;
  return Array.from({ length: cantidad }, () => ({
    x: ancho * (0.34 + Math.random() * 0.46),
    y: alto * (0.68 + Math.random() * 0.28),
    ancho: 18 + Math.random() * 44,
    fase: Math.random() * Math.PI * 2,
    velocidad: 0.015 + Math.random() * 0.02,
  }));
}

/**
 * Motor atmosférico bioluminiscente «Bosque vivo»:
 * - En Bosque de noche: haces suaves de luz lunar, reflejos sobre el río y luciérnagas con estela.
 * - En Bosque de día: luciérnagas y polen dorado/esmeralda de alto contraste sobre el fondo claro.
 * - En Alto contraste, pausa o movimiento reducido: se detiene y limpia por completo.
 */
export function BosqueVivo({
  fase,
  tema = "noche",
  reducido,
}: {
  fase: Fase;
  tema?: TemaVisual;
  reducido: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const faseRef = useRef<Fase>(fase);
  const brotePendiente = useRef(false);

  useEffect(() => {
    const previa = faseRef.current;
    faseRef.current = fase;
    if (
      (fase === "RETO_RESUELTO" || fase === "COMPLETADA") &&
      previa !== fase
    ) {
      brotePendiente.current = true;
    }
  }, [fase]);

  const activo = !reducido && fase !== "PAUSADA" && tema !== "contraste";
  const esDia = tema === "dia";

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (!activo) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    let ancho = window.innerWidth;
    let alto = window.innerHeight;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let destellosRio: DestelloRio[] = [];

    const ajustar = () => {
      ancho = window.innerWidth;
      alto = window.innerHeight;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(ancho * dpr));
      canvas.height = Math.max(1, Math.floor(alto * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      destellosRio = crearDestellosRio(ancho, alto);
    };
    ajustar();

    const enPortada = fase === "INICIO";
    const cantidad = enPortada
      ? ancho < 700
        ? 22
        : 38
      : ancho < 700
        ? 16
        : esDia
          ? 34
          : 22;
    const particulas: Particula[] = Array.from({ length: cantidad }, () =>
      crearAmbiente(ancho, alto, enPortada, esDia),
    );
    const destellos: Particula[] = [];
    const ondas: Onda[] = [];

    const puntero = { x: -9999, y: -9999, activo: false };
    const esFino = matchMedia("(pointer: fine)").matches;
    const alMover = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      puntero.x = e.clientX;
      puntero.y = e.clientY;
      puntero.activo = true;
    };
    const alSalir = () => {
      puntero.activo = false;
    };
    const alPulsar = (e: PointerEvent) => {
      if (ondas.length > 5) ondas.shift();
      ondas.push({
        x: e.clientX,
        y: e.clientY,
        radio: 6,
        radioMax: ancho < 700 ? 85 : 135,
        alfa: 0.42,
        tono: faseRef.current === "RETO_RESUELTO" ? "ambar" : "cian",
      });
    };

    if (esFino) {
      window.addEventListener("pointermove", alMover, { passive: true });
      window.addEventListener("pointerleave", alSalir);
    }
    window.addEventListener("pointerdown", alPulsar, { passive: true });
    window.addEventListener("resize", ajustar, { passive: true });

    let tiempo = 0;
    let marco = 0;

    const paleta = esDia ? COLORES_DIA : COLORES_NOCHE;

    const dibujarParticula = (p: Particula, alfa: number) => {
      const rgb = paleta[p.tono];

      // En Bosque de día, todas las partículas son hojas verdes botánicas girando con la brisa.
      if (p.forma === "hoja" && esDia) {
        const s = p.radio;
        const op = Math.min(0.88, alfa * 0.82);
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.angulo);
        // Sombra muy suave para dar relieve sobre el fondo claro
        ctx.fillStyle = `rgba(6, 78, 59, ${(op * 0.18).toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(1.2, -s + 1.4);
        ctx.quadraticCurveTo(s * 0.92 + 1.2, -s * 0.1 + 1.4, 1.2, s + 1.4);
        ctx.quadraticCurveTo(-s * 0.92 + 1.2, -s * 0.1 + 1.4, 1.2, -s + 1.4);
        ctx.closePath();
        ctx.fill();
        // Cuerpo de la hoja
        ctx.fillStyle = `rgba(${rgb}, ${op.toFixed(3)})`;
        ctx.beginPath();
        ctx.moveTo(0, -s);
        ctx.quadraticCurveTo(s * 0.9, -s * 0.12, 0, s);
        ctx.quadraticCurveTo(-s * 0.9, -s * 0.12, 0, -s);
        ctx.closePath();
        ctx.fill();
        // Nervadura central clara
        ctx.strokeStyle = `rgba(240, 253, 244, ${(op * 0.72).toFixed(3)})`;
        ctx.lineWidth = 1.05;
        ctx.beginPath();
        ctx.moveTo(0, -s * 0.78);
        ctx.lineTo(0, s * 0.85);
        ctx.stroke();
        ctx.restore();
        return;
      }

      const escala = esDia ? 1.45 : 1;
      const radio = p.radio * escala;

      // Estela suave detrás de cada luciérnaga en movimiento.
      if (p.estela.length > 1) {
        for (let i = 0; i < p.estela.length; i++) {
          const pt = p.estela[i]!;
          const factor = (i + 1) / p.estela.length;
          ctx.fillStyle = `rgba(${rgb}, ${(alfa * factor * (esDia ? 0.34 : 0.24)).toFixed(3)})`;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, radio * (0.45 + factor * 0.55), 0, Math.PI * 2);
          ctx.fill();
        }
      }

      const halo = ctx.createRadialGradient(
        p.x,
        p.y,
        0,
        p.x,
        p.y,
        radio * (esDia ? 3.8 : 4.6),
      );
      halo.addColorStop(
        0,
        `rgba(${rgb}, ${(alfa * (esDia ? 0.92 : 0.94)).toFixed(3)})`,
      );
      halo.addColorStop(
        0.4,
        `rgba(${rgb}, ${(alfa * (esDia ? 0.42 : 0.36)).toFixed(3)})`,
      );
      halo.addColorStop(1, `rgba(${rgb}, 0)`);
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radio * (esDia ? 3.8 : 4.6), 0, Math.PI * 2);
      ctx.fill();

      // En modo día el núcleo es cálido/saturado para destacar con nitidez sobre fondo claro.
      ctx.fillStyle = esDia
        ? `rgba(${rgb}, ${(alfa * 0.96).toFixed(3)})`
        : `rgba(245, 254, 255, ${(alfa * 0.96).toFixed(3)})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radio * (esDia ? 0.72 : 0.55), 0, Math.PI * 2);
      ctx.fill();
      if (esDia) {
        ctx.fillStyle = `rgba(255, 251, 235, ${(alfa * 0.85).toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(
          p.x - radio * 0.16,
          p.y - radio * 0.16,
          radio * 0.28,
          0,
          Math.PI * 2,
        );
        ctx.fill();
      }
    };

    const dibujar = () => {
      if (document.hidden) {
        marco = requestAnimationFrame(dibujar);
        return;
      }

      tiempo += 0.012;

      if (brotePendiente.current) {
        brotePendiente.current = false;
        const extra = ancho < 700 ? 14 : 26;
        for (let i = 0; i < extra; i++)
          destellos.push(crearDestello(ancho, alto, esDia));
        ondas.push({
          x: ancho * 0.62,
          y: alto * 0.42,
          radio: 24,
          radioMax: Math.min(ancho, alto) * 0.62,
          alfa: 0.36,
          tono: "cian",
        });
      }

      ctx.clearRect(0, 0, ancho, alto);

      // Capa 1 (solo portada): haces suaves de luz y reflejos vivos sobre el río.
      if (faseRef.current === "INICIO") {
        ctx.save();
        for (let i = 0; i < 3; i++) {
          const osc = Math.sin(tiempo * (0.55 + i * 0.17) + i * 1.9);
          const origenX = ancho * (0.64 + i * 0.08) + osc * 22;
          const origenY = -alto * 0.06;
          const finX = ancho * (0.36 + i * 0.14) + osc * 34;
          const finY = alto * 0.88;
          const grosor = ancho * (0.045 + i * 0.018);
          const haz = ctx.createLinearGradient(origenX, origenY, finX, finY);
          if (esDia) {
            const brillo = 0.055 + 0.028 * (0.5 + 0.5 * osc);
            haz.addColorStop(
              0,
              `rgba(253, 224, 71, ${(brillo * 1.35).toFixed(3)})`,
            );
            haz.addColorStop(0.52, `rgba(254, 243, 199, ${brillo.toFixed(3)})`);
            haz.addColorStop(1, "rgba(254, 243, 199, 0)");
          } else {
            const brillo = 0.036 + 0.022 * (0.5 + 0.5 * osc);
            haz.addColorStop(
              0,
              `rgba(165, 243, 252, ${(brillo * 1.4).toFixed(3)})`,
            );
            haz.addColorStop(0.52, `rgba(94, 234, 212, ${brillo.toFixed(3)})`);
            haz.addColorStop(1, "rgba(94, 234, 212, 0)");
          }
          ctx.fillStyle = haz;
          ctx.beginPath();
          ctx.moveTo(origenX - grosor * 0.35, origenY);
          ctx.lineTo(origenX + grosor * 0.35, origenY);
          ctx.lineTo(finX + grosor * 1.45, finY);
          ctx.lineTo(finX - grosor * 0.9, finY);
          ctx.closePath();
          ctx.fill();
        }

        // Reflejos suaves sobre el agua del río (dorados en día, bioluminiscentes en noche).
        for (const r of destellosRio) {
          r.fase += r.velocidad;
          const pulso = 0.5 + 0.5 * Math.sin(r.fase);
          const dx = Math.sin(r.fase * 0.7) * 6;
          const grad = ctx.createRadialGradient(
            r.x + dx,
            r.y,
            0,
            r.x + dx,
            r.y,
            r.ancho,
          );
          if (esDia) {
            grad.addColorStop(
              0,
              `rgba(254, 249, 195, ${(pulso * 0.22).toFixed(3)})`,
            );
            grad.addColorStop(1, "rgba(253, 224, 71, 0)");
          } else {
            grad.addColorStop(
              0,
              `rgba(147, 250, 236, ${(pulso * 0.16).toFixed(3)})`,
            );
            grad.addColorStop(1, "rgba(34, 211, 238, 0)");
          }
          ctx.fillStyle = grad;
          ctx.save();
          ctx.translate(r.x + dx, r.y);
          ctx.scale(1, 0.18);
          ctx.beginPath();
          ctx.arc(0, 0, r.ancho, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }
        ctx.restore();
      }

      // Capa 1b (Bosque de día en el juego): rayos de sol cálidos y suaves cruzando desde arriba.
      if (esDia && faseRef.current !== "INICIO") {
        ctx.save();
        for (let i = 0; i < 2; i++) {
          const osc = Math.sin(tiempo * (0.42 + i * 0.15) + i * 2.1);
          const origenX = ancho * (0.74 + i * 0.14) + osc * 18;
          const origenY = -alto * 0.08;
          const finX = ancho * (0.4 + i * 0.22) + osc * 28;
          const finY = alto * 0.92;
          const grosor = ancho * (0.075 + i * 0.03);
          const haz = ctx.createLinearGradient(origenX, origenY, finX, finY);
          const brillo = 0.085 + 0.025 * (0.5 + 0.5 * osc);
          haz.addColorStop(
            0,
            `rgba(253, 224, 71, ${(brillo * 1.25).toFixed(3)})`,
          );
          haz.addColorStop(0.5, `rgba(254, 243, 199, ${brillo.toFixed(3)})`);
          haz.addColorStop(1, "rgba(254, 243, 199, 0)");
          ctx.fillStyle = haz;
          ctx.beginPath();
          ctx.moveTo(origenX - grosor * 0.4, origenY);
          ctx.lineTo(origenX + grosor * 0.4, origenY);
          ctx.lineTo(finX + grosor * 1.5, finY);
          ctx.lineTo(finX - grosor * 0.9, finY);
          ctx.closePath();
          ctx.fill();
        }
        ctx.restore();
      }

      // Capa 2: ondas concéntricas suaves al tocar/hacer clic o al acertar.
      for (let i = ondas.length - 1; i >= 0; i--) {
        const o = ondas[i]!;
        o.radio += (o.radioMax - o.radio) * 0.065 + 1.2;
        const progreso = o.radio / o.radioMax;
        if (progreso >= 0.98) {
          ondas.splice(i, 1);
          continue;
        }
        const alfa = o.alfa * (1 - progreso) * (1 - progreso);
        const rgb = paleta[o.tono];
        ctx.strokeStyle = `rgba(${rgb}, ${alfa.toFixed(3)})`;
        ctx.lineWidth = esDia ? 2.1 : 1.6;
        ctx.beginPath();
        ctx.arc(o.x, o.y, o.radio, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Capa 3: luciérnagas ambientales con vuelo orgánico y estela suave.
      const intensidad =
        faseRef.current === "INICIO" ? 0.88 : esDia ? 0.84 : 0.54;
      for (const p of particulas) {
        p.estela.push({ x: p.x, y: p.y });
        if (p.estela.length > 6) p.estela.shift();

        p.fase += p.velocidadPulso;
        p.angulo += p.velocidadGiro;
        p.x += p.vx + Math.sin(p.fase * 0.75) * p.deriva;
        p.y += p.vy + Math.cos(p.fase * 0.55) * 0.08;

        let extraBrillo = 0;
        if (puntero.activo) {
          const dx = puntero.x - p.x;
          const dy = puntero.y - p.y;
          const dist2 = dx * dx + dy * dy;
          if (dist2 < 32000 && dist2 > 9) {
            const factor = 1 - Math.sqrt(dist2) / 180;
            p.x += dx * factor * 0.008;
            p.y += dy * factor * 0.008;
            extraBrillo = factor * 0.35;
          }
        }

        if (p.forma === "hoja" && p.y > alto + 20) {
          p.y = -18;
          p.x = Math.random() * ancho;
          p.estela.length = 0;
        } else if (p.y < -20) {
          p.y = alto + 16;
          p.x =
            faseRef.current === "INICIO"
              ? ancho * (0.22 + Math.random() * 0.78)
              : Math.random() * ancho;
          p.estela.length = 0;
        }
        if (p.x < -20) {
          p.x = ancho + 16;
          p.estela.length = 0;
        }
        if (p.x > ancho + 20) {
          p.x = -16;
          p.estela.length = 0;
        }

        const pulso = 0.34 + 0.66 * (0.5 + 0.5 * Math.sin(p.fase));
        const alfa = Math.min(1, pulso * intensidad + extraBrillo);
        dibujarParticula(p, alfa);
      }

      // Capa 4: floración ascendente de celebración.
      for (let i = destellos.length - 1; i >= 0; i--) {
        const d = destellos[i]!;
        d.vida = (d.vida ?? 0) + 1;
        const max = d.vidaMax ?? 140;
        if (d.vida >= max) {
          destellos.splice(i, 1);
          continue;
        }
        d.estela.push({ x: d.x, y: d.y });
        if (d.estela.length > 7) d.estela.shift();

        d.fase += d.velocidadPulso;
        d.angulo += d.velocidadGiro;
        d.x += d.vx + Math.sin(d.fase) * d.deriva;
        d.y += d.vy;
        const progreso = d.vida / max;
        const envolvente = Math.sin(progreso * Math.PI);
        dibujarParticula(d, envolvente * 0.95);
      }

      marco = requestAnimationFrame(dibujar);
    };

    marco = requestAnimationFrame(dibujar);
    return () => {
      cancelAnimationFrame(marco);
      window.removeEventListener("resize", ajustar);
      window.removeEventListener("pointerdown", alPulsar);
      if (esFino) {
        window.removeEventListener("pointermove", alMover);
        window.removeEventListener("pointerleave", alSalir);
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [activo, fase, esDia]);

  return (
    <canvas
      ref={canvasRef}
      className="bosque-vivo"
      data-fase={fase}
      aria-hidden="true"
    />
  );
}
