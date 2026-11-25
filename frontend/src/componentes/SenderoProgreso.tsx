import { motion } from "motion/react";

const MAX_HITOS = 10;

/**
 * Mapa visual de sendero con huellas y estrellas de expedición.
 * Conserva el elemento <progress> nativo accesible para lectores de pantalla y WCAG,
 * mientras muestra el avance como un camino de estrellas (completados) y una huella
 * activa indicando el paso actual.
 */
export function SenderoProgreso({
  completados,
  total,
  etiquetaAria,
}: {
  completados: number;
  total: number;
  etiquetaAria: string;
}) {
  const seguroTotal = Math.max(1, total);
  const seguroComp = Math.min(seguroTotal, Math.max(0, completados));
  const fraccion = seguroComp / seguroTotal;
  const hitos = seguroTotal <= 12 ? seguroTotal : MAX_HITOS;
  const completadosVisual = seguroTotal <= 12 ? seguroComp : Math.floor(fraccion * hitos);
  const terminado = seguroComp >= seguroTotal;
  const indiceActual = terminado ? -1 : Math.min(hitos - 1, completadosVisual);
  const avanceLinea = terminado ? 1 : hitos > 1 ? Math.min(1, completadosVisual / (hitos - 1)) : fraccion;

  return (
    <div className="sendero-progreso" data-completo={terminado ? "true" : undefined}>
      <progress className="progreso-nativo" max={seguroTotal} value={seguroComp} aria-label={etiquetaAria} />
      <div className="sendero-pista" aria-hidden="true">
        <span className="sendero-linea" />
        <motion.span
          className="sendero-avance"
          initial={false}
          animate={{ scaleX: avanceLinea }}
          transition={{ type: "spring", stiffness: 280, damping: 28 }}
        />
        <ol className="sendero-hitos">
          {Array.from({ length: hitos }, (_, i) => {
            const hecho = i < completadosVisual;
            const actual = i === indiceActual;
            const estado = hecho ? "hecho" : actual ? "actual" : "pendiente";
            return (
              <motion.li
                key={i}
                className={`sendero-hito sendero-${estado}`}
                initial={false}
                animate={hecho ? { scale: [0.82, 1.22, 1] } : actual ? { scale: 1.08 } : { scale: 1 }}
                transition={{ type: "spring", stiffness: 420, damping: 20 }}
              >
                {hecho ? (
                  <svg viewBox="0 0 24 24" className="sendero-icono" focusable="false">
                    <path
                      fill="currentColor"
                      d="M12 2.4 14.9 8.3l6.5.9-4.7 4.6 1.1 6.5L12 17.2 6.2 20.3l1.1-6.5-4.7-4.6 6.5-.9L12 2.4Z"
                    />
                  </svg>
                ) : actual ? (
                  <svg viewBox="0 0 24 24" className="sendero-icono sendero-huella" focusable="false">
                    <circle cx="7.2" cy="9.2" r="2.2" fill="currentColor" />
                    <circle cx="12" cy="7.2" r="2.3" fill="currentColor" />
                    <circle cx="16.8" cy="9.2" r="2.2" fill="currentColor" />
                    <path
                      fill="currentColor"
                      d="M12 11.4c-3.1 0-5.4 2.1-5.4 4.6 0 1.8 1.4 3 3.2 3 1 0 1.6-.3 2.2-.3s1.2.3 2.2.3c1.8 0 3.2-1.2 3.2-3 0-2.5-2.3-4.6-5.4-4.6Z"
                    />
                  </svg>
                ) : (
                  <span className="sendero-punto" />
                )}
              </motion.li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
