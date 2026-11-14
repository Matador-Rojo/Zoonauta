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
  "Tu equipo ya pide reducir el movimiento.": "Seu dispositivo já pede para reduzir o movimento.",
  // Portada «Bosque de luz» (2026-11-14)
  "Un bosque que cobra vida": "Uma floresta que ganha vida",
  "Descubre el": "Descubra a",
  "bosque de luz.": "floresta de luz.",
  "Elige un animal. Sigue las pistas y descubre dónde vive.":
    "Escolha um animal. Siga as pistas e descubra onde ele vive.",
  // Preferencias 6.0
  Voz: "Voz",
  Pantalla: "Tela",
  "Uno menos": "Um a menos",
  "Uno más": "Um a mais",
  "La voz en portugués todavía no está disponible.": "A voz em português ainda não está disponível.",
  "Sin voces disponibles": "Sem vozes disponíveis",
  "Voz grabada de Zoonauta. Funciona en este equipo, sin Internet.":
    "Voz gravada do Zoonauta. Funciona neste dispositivo, sem Internet.",
  "Faltan las grabaciones de la voz de Zoonauta en assets/voz/grabada.":
    "Faltam as gravações da voz do Zoonauta em assets/voz/grabada.",
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
