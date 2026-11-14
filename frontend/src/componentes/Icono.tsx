// Iconos generales de interfaz (los mismos trazos de 5.0). Los pictogramas
// educativos se muestran siempre con <Pictograma>, nunca con estos iconos.
const CAMINOS = {
  flecha: "M5 12h14m-6-6 6 6-6 6",
  anterior: "M19 12H5m6-6-6 6 6 6",
  pausa: "M9 5v14M15 5v14",
  reproducir: "m8 5 11 7-11 7V5",
  buscar: "M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  reloj: "M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  ajustes: "M4 7h16M4 17h16M9 4v6M15 14v6",
  cerrar: "M6 6l12 12M18 6 6 18",
} as const;

export type NombreIcono = keyof typeof CAMINOS;

export function Icono({ nombre, className }: { nombre: NombreIcono; className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={CAMINOS[nombre]} />
    </svg>
  );
}
