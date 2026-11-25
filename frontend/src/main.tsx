import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "@fontsource-variable/atkinson-hyperlegible-next/wght.css";
import "@fontsource-variable/fraunces/opsz.css";
import "./estilos/base.css";
import "./estilos/portada.css";
import "./estilos/pantallas.css";
import "./estilos/tema.css";
import "./estilos/preferencias.css";

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

if ("serviceWorker" in navigator && /^https?:$/.test(window.location.protocol)) {
  window.addEventListener("load", () => {
    void navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  });
}
