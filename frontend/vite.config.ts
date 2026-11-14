import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El servidor Python sirve el compilado en /v6/ y la API en el mismo origen.
// En desarrollo, Vite reenvía la API y los recursos al servidor Python.
const backend = process.env.ZOONAUTA_BACKEND ?? "http://127.0.0.1:8766";
const rutasBackend = ["/api", "/media", "/fondos", "/habitats", "/animales", "/ilustraciones", "/zoonauta-logo.svg"];

export default defineConfig({
  base: "/v6/",
  plugins: [react()],
  build: {
    outDir: "../codigo/interfaz/web6",
    emptyOutDir: true,
    target: "es2022",
    assetsInlineLimit: 0,
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: Object.fromEntries(rutasBackend.map((ruta) => [ruta, { target: backend, changeOrigin: false }])),
  },
});
