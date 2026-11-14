import { useEffect, type RefObject } from "react";

/**
 * Cierre al tocar fuera de un diálogo modal (Modern Web Guidance: light-dismiss-a-dialog).
 * `closedby="any"` lo hace de forma nativa; React aún no tipa el atributo, por eso se pasa
 * con un objeto. Donde el navegador no lo admite (Safari), el gancho añade la alternativa:
 * cierra solo si la pulsación empieza y termina fuera de la caja del diálogo.
 */
export const CERRAR_FUERA = { closedby: "any" } as Record<string, string>;

export function useCerrarFuera(ref: RefObject<HTMLDialogElement | null>) {
  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo || "closedBy" in HTMLDialogElement.prototype) return;
    const fuera = (e: PointerEvent) => {
      const r = dialogo.getBoundingClientRect();
      return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    };
    let pulsadoFuera = false;
    const abajo = (e: PointerEvent) => (pulsadoFuera = fuera(e));
    const arriba = (e: PointerEvent) => {
      if (pulsadoFuera && fuera(e)) dialogo.close();
    };
    dialogo.addEventListener("pointerdown", abajo);
    dialogo.addEventListener("pointerup", arriba);
    return () => {
      dialogo.removeEventListener("pointerdown", abajo);
      dialogo.removeEventListener("pointerup", arriba);
    };
  }, [ref]);
}
