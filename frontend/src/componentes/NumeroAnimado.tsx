import { AnimatePresence, motion } from "motion/react";

/**
 * Odómetro numérico mecánico inspirado en barvian/number-flow, 100 % compatible
 * con la política CSP estricta (style-src 'self', sin <style> inyectados).
 * Con movimiento normal cada dígito rueda suavemente con física de resorte;
 * con movimiento reducido muestra el texto plano inmediato.
 */
export function NumeroAnimado({
  valor,
  reducido = false,
  className,
}: {
  valor: number;
  reducido?: boolean;
  className?: string;
}) {
  if (reducido) {
    return <span className={className}>{valor}</span>;
  }
  const digitos = String(valor).split("");
  return (
    <span className={`numero-animado ${className ?? ""}`.trim()}>
      {digitos.map((digito, i) => (
        <span key={digitos.length - i} className="digito-ranura">
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.span
              key={digito}
              className="digito-valor"
              initial={{ y: "85%", opacity: 0 }}
              animate={{ y: "0%", opacity: 1 }}
              exit={{ y: "-85%", opacity: 0 }}
              transition={{ type: "spring", stiffness: 380, damping: 28 }}
            >
              {digito}
            </motion.span>
          </AnimatePresence>
        </span>
      ))}
    </span>
  );
}
