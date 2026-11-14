import { createContext, useContext } from "react";
import type { Diccionarios, Idioma } from "./api/tipos";

// Los textos se identifican por su versión en español, como en 5.0, y las
// traducciones pt-BR vienen de /api/idiomas (datos/traducciones_pt_BR.json).
//
// Textos nuevos de la 6.0 que todavía no están en el diccionario del servidor.
// BORRADOR pt-BR: pendiente de revisión humana antes de trasladarlos a
// datos/traducciones_pt_BR.json.
export const TEXTOS_NUEVOS_PENDIENTES: Record<string, string> = {
  "Reducir movimiento": "Reduzir movimento",
  "Muestra fotografías fijas y cambia de paisaje solo con los botones.":
    "Mostra fotografias fixas e muda de paisagem só com os botões.",
  "Paisaje {n} de {total}": "Paisagem {n} de {total}",
  "Paisajes de la portada": "Paisagens da página inicial",
  "Cerrar notificación": "Fechar notificação",
};

export interface Traductor {
  idioma: Idioma;
  t: (texto: string, valores?: Record<string, string | number>) => string;
}

export function crearTraductor(diccionarios: Diccionarios, idioma: Idioma): Traductor {
  const tabla = diccionarios[idioma] ?? {};
  return {
    idioma,
    t(texto, valores = {}) {
      let salida = tabla[texto] ?? (idioma === "pt-BR" ? TEXTOS_NUEVOS_PENDIENTES[texto] : undefined) ?? texto;
      for (const [clave, valor] of Object.entries(valores)) salida = salida.replaceAll(`{${clave}}`, String(valor));
      return salida;
    },
  };
}

export const ContextoIdioma = createContext<Traductor>(crearTraductor({ es: {}, "pt-BR": {} }, "es"));
export const useT = () => useContext(ContextoIdioma);
