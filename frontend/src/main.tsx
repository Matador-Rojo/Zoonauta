import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "@fontsource-variable/atkinson-hyperlegible-next/wght.css";
import "./estilos/base.css";
import "./estilos/portada.css";
import "./estilos/pantallas.css";

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
