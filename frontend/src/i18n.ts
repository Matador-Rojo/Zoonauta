import { createContext, useContext } from "react";
import type { Diccionarios, Idioma } from "./api/tipos";

// Los textos se identifican por su versión en español, como en 5.0, y las
// traducciones pt-BR vienen de /api/idiomas (datos/traducciones_pt_BR.json).
//
// Textos nuevos de la 6.0 que todavía no están en el diccionario del servidor.
// BORRADOR pt-BR: pendiente de revisión humana antes de trasladarlos a
// datos/traducciones_pt_BR.json.
// Vacío: los textos de la portada «Bosque de luz» y de Preferencias 6.0 se aprobaron el
// 2026-11-14 y están en datos/traducciones_pt_BR.json (sección «interfaz»).
export const TEXTOS_NUEVOS_PENDIENTES: Record<string, string> = {
  Todas: "Todas",
  "Filtrar por letra inicial": "Filtrar pela letra inicial",
  "Hallazgos de esta partida": "Descobertas desta partida",
  "Sonidos del bosque": "Sons da floresta",
  "Ambiente suave y tonos de aviso.": "Ambiente suave e tons de aviso.",
  "Aspecto visual": "Aparência visual",
  "Bosque de noche": "Floresta à noite",
  "Bosque de día": "Floresta de dia",
  "Alto contraste": "Alto contraste",
  "Tamaño de texto": "Tamanho do texto",
  "Voz en portugués brasileño": "Voz em português brasileiro",
  "Voz en inglés": "Voz em inglês",
  "La voz en inglés todavía no está disponible.": "A voz em inglês ainda não está disponível.",
  Pequeño: "Pequeno",
  Normal: "Normal",
  Grande: "Grande",
  "Proteger Preferencias": "Proteger Preferências",
  "Mantener pulsado para abrir.": "Segure para abrir.",
  "Mantén pulsado para abrir Preferencias": "Segure para abrir Preferências",
  "Instalar app": "Instalar app",
  "Mi álbum": "Meu álbum",
  "Tu pasaporte": "Seu passaporte",
  "Mi álbum de expedición": "Meu álbum de expedição",
  "Cada animal que descubres guarda su sello en tu cuaderno.":
    "Cada animal que você descobre guarda seu selo no caderno.",
  "Cerrar álbum": "Fechar álbum",
  "Animales descubiertos": "Animais descobertos",
  "Hábitats explorados": "Habitats explorados",
  "Estrellas de animales": "Estrelas de animais",
  "Estrellas de hábitats": "Estrelas de habitats",
  "Hallazgos sellados": "Descobertas seladas",
  "Primer hallazgo": "Primeira descoberta",
  "1 animal": "1 animal",
  "Rastreador curioso": "Rastreador curioso",
  "20 animales": "20 animais",
  "Explorador experto": "Explorador experiente",
  "80 animales": "80 animais",
  "Guardián de fauna": "Guardião da fauna",
  "160 animales": "160 animais",
  "Atlas completo": "Atlas completo",
  "288 animales": "288 animais",
  "Primer paisaje": "Primeira paisagem",
  "1 hábitat": "1 habitat",
  "Viajero natural": "Viajante natural",
  "5 hábitats": "5 habitats",
  "Guía de biomas": "Guia de biomas",
  "15 hábitats": "15 habitats",
  "Maestro de ecosistemas": "Mestre dos ecossistemas",
  "30 hábitats": "30 habitats",
  "Mundo completo": "Mundo completo",
  "48 hábitats": "48 habitats",
  "Por descubrir": "Por descobrir",
  "Ya descubierto": "Já descoberto",
  "¡Felicidades! Ya descubriste todos los animales del álbum.":
    "Parabéns! Você já descobriu todos os animais do álbum.",
  "Tu álbum todavía espera el primer sello.": "Seu álbum ainda espera o primeiro selo.",
  "Empieza una partida y encuentra el hogar de un animal para verlo aquí.":
    "Comece uma partida e encontre o lar de um animal para vê-lo aqui.",
  "Guardado automáticamente en este equipo.": "Salvo automaticamente neste dispositivo.",
  "Reiniciar álbum": "Reiniciar álbum",
  "Confirmar reinicio del álbum": "Confirmar reinício do álbum",
  "¿Borrar todos los sellos?": "Apagar todos os selos?",
  "Sí, reiniciar": "Sim, reiniciar",
  Cancelar: "Cancelar",
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

export const ContextoIdioma = createContext<Traductor>(crearTraductor({ es: {}, "pt-BR": {}, en: {} }, "es"));
export const useT = () => useContext(ContextoIdioma);
