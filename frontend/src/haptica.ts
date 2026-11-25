/**
 * Retroalimentación háptica suave (Vibration API) para dispositivos táctiles compatibles.
 * Siempre silenciosa y segura cuando el navegador no soporta vibración o el usuario pide reducir movimiento.
 */
export type PatronHaptico = "toque" | "pista" | "acierto" | "neutral" | "victoria" | "desbloqueo";

const PATRONES: Record<PatronHaptico, number | number[]> = {
  toque: 8,
  pista: [10, 26, 14],
  acierto: [14, 28, 20, 28, 34],
  neutral: 12,
  victoria: [18, 36, 22, 36, 46],
  desbloqueo: [12, 20, 18],
};

export function vibrar(patron: PatronHaptico, desactivado = false) {
  if (desactivado || typeof navigator === "undefined" || typeof navigator.vibrate !== "function") return;
  try {
    navigator.vibrate(PATRONES[patron]);
  } catch {
    /* ignorar navegadores que restringen vibrate */
  }
}
