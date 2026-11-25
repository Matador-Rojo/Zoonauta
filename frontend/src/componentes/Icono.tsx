// Iconos generales de interfaz inspirados en pqoqubbw/icons (lucide-animated):
// trazos vectoriales limpios con micro-animaciones discretas al interactuar.
// Los pictogramas educativos se muestran siempre con <Pictograma>, nunca aquí.
export type NombreIcono =
  | "flecha"
  | "anterior"
  | "pausa"
  | "reproducir"
  | "buscar"
  | "reloj"
  | "ajustes"
  | "cerrar"
  | "album"
  | "descargar"
  | "candado";

export function Icono({ nombre, className }: { nombre: NombreIcono; className?: string }) {
  return (
    <svg
      className={`icono-ui icono-${nombre} ${className ?? ""}`.trim()}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.85}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {nombre === "ajustes" && (
        <>
          <path d="M4 7h16" />
          <path d="M4 17h16" />
          <path className="ic-knob-a" d="M9 4v6" />
          <path className="ic-knob-b" d="M15 14v6" />
        </>
      )}
      {nombre === "album" && (
        <>
          <path d="M2 6.5A2.5 2.5 0 0 1 4.5 4H12v16H4.5A2.5 2.5 0 0 1 2 17.5Z" />
          <path className="ic-pagina" d="M22 6.5A2.5 2.5 0 0 0 19.5 4H12v16h7.5a2.5 2.5 0 0 0 2.5-2.5Z" />
          <path className="ic-estrella" d="M16 9.2 16.7 10.6l1.5.2-1.1 1.1.3 1.5-1.4-.7-1.4.7.3-1.5-1.1-1.1 1.5-.2Z" />
        </>
      )}
      {nombre === "descargar" && (
        <>
          <path className="ic-bajar" d="M12 3v12m0 0-4.5-4.5M12 15l4.5-4.5" />
          <path d="M4 17.5v1.5A2 2 0 0 0 6 21h12a2 2 0 0 0 2-2v-1.5" />
        </>
      )}
      {nombre === "candado" && (
        <>
          <rect x="5" y="11" width="14" height="10" rx="2.2" />
          <path className="ic-arco" d="M8 11V7.5a4 4 0 0 1 8 0V11" />
        </>
      )}
      {nombre === "flecha" && <path className="ic-flecha-der" d="M5 12h14m-6-6 6 6-6 6" />}
      {nombre === "anterior" && <path className="ic-flecha-izq" d="M19 12H5m6-6-6 6 6 6" />}
      {nombre === "pausa" && <path d="M9 5v14M15 5v14" />}
      {nombre === "reproducir" && <path className="ic-play" d="m8 5 11 7-11 7V5" />}
      {nombre === "buscar" && <path d="M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0" />}
      {nombre === "reloj" && <path d="M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0" />}
      {nombre === "cerrar" && <path className="ic-cerrar" d="M6 6l12 12M18 6 6 18" />}
    </svg>
  );
}
