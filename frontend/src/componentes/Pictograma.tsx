import { useEffect, useState } from "react";
import type { Pictograma as DatosPictograma } from "../api/tipos";

export function Pictograma({ id, datos, className, perezosa }: {
  id: string; datos: DatosPictograma | undefined; className?: string; perezosa?: boolean;
}) {
  if (!datos) return null;
  const clases = [className, /^P_A\d+$/.test(id) ? "animal-ilustracion" : ""].filter(Boolean).join(" ");
  return <img className={clases || undefined} src={datos.imagen} alt="" draggable={false} decoding="async"
    loading={perezosa ? "lazy" : undefined} />;
}

/**
 * Conserva el contenido visible hasta que los pictogramas nuevos estén decodificados,
 * y entonces cambia texto y pictogramas a la vez. Así Pista actualiza la guía sin
 * huecos ni parpadeos (corrección del parpadeo de 5.0).
 */
export function useContenidoListo<T extends { pictogramas: string[] }>(
  valor: T, pictogramas: Record<string, DatosPictograma>,
): T {
  const [visible, setVisible] = useState(valor);
  useEffect(() => {
    if (visible === valor) return;
    const mismos = visible.pictogramas.length === valor.pictogramas.length &&
      visible.pictogramas.every((id, i) => id === valor.pictogramas[i]);
    if (mismos) { setVisible(valor); return; }
    let vigente = true;
    const cargas = valor.pictogramas.map((id) => {
      const imagen = new Image();
      imagen.src = pictogramas[id]?.imagen ?? "";
      return imagen.decode();
    });
    void Promise.allSettled(cargas).then(() => { if (vigente) setVisible(valor); });
    return () => { vigente = false; };
  }, [valor, visible, pictogramas]);
  return visible;
}
