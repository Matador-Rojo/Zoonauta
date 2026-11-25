import type { PointerEvent } from "react";

/**
 * Reflejo interactivo que sigue el puntero sobre tarjetas y paneles.
 * Usa CSSOM (setProperty) para cumplir con CSP estricta (`style-src 'self'`) y
 * se desactiva automáticamente en pantallas táctiles o con movimiento reducido.
 */
export function moverLuzPuntero(e: PointerEvent<HTMLElement>) {
  if (e.pointerType !== "mouse") return;
  if (document.documentElement.dataset.movimiento === "reducido") return;
  const el = e.currentTarget;
  const rect = el.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return;
  const x = ((e.clientX - rect.left) / rect.width) * 100;
  const y = ((e.clientY - rect.top) / rect.height) * 100;
  el.style.setProperty("--luz-x", `${x.toFixed(1)}%`);
  el.style.setProperty("--luz-y", `${y.toFixed(1)}%`);
}

/**
 * Efecto 3D Tilt + micro-paralaje + brillo de cristal para tarjetas de hábitat
 * (desactivado en pantallas táctiles, movimiento reducido y Alto contraste).
 */
export function moverTiltTarjeta(e: PointerEvent<HTMLElement>) {
  if (e.pointerType !== "mouse") return;
  if (document.documentElement.dataset.movimiento === "reducido") return;
  if (document.documentElement.dataset.tema === "contraste") return;
  const el = e.currentTarget;
  const rect = el.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return;
  const rx = (e.clientX - rect.left) / rect.width;
  const ry = (e.clientY - rect.top) / rect.height;
  const tiltY = (rx - 0.5) * 9; // -4.5deg .. +4.5deg
  const tiltX = (0.5 - ry) * 8; // -4deg .. +4deg
  const px = (rx - 0.5) * -8; // micro-paralaje inverso en px
  const py = (ry - 0.5) * -6;
  el.style.setProperty("--luz-x", `${(rx * 100).toFixed(1)}%`);
  el.style.setProperty("--luz-y", `${(ry * 100).toFixed(1)}%`);
  el.style.setProperty("--tilt-x", `${tiltX.toFixed(2)}deg`);
  el.style.setProperty("--tilt-y", `${tiltY.toFixed(2)}deg`);
  el.style.setProperty("--px", `${px.toFixed(1)}px`);
  el.style.setProperty("--py", `${py.toFixed(1)}px`);
}

export function resetTiltTarjeta(e: PointerEvent<HTMLElement>) {
  const el = e.currentTarget;
  el.style.setProperty("--tilt-x", "0deg");
  el.style.setProperty("--tilt-y", "0deg");
  el.style.setProperty("--px", "0px");
  el.style.setProperty("--py", "0px");
}
