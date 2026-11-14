// Contrato de /api/vista. El servidor Python es la autoridad de reglas y progreso;
// el frontend solo presenta la vista y envía acciones con su revisión.

export type Idioma = "es" | "pt-BR";

export type Fase =
  | "INICIO"
  | "SELECCION_ANIMAL"
  | "ESPERANDO_RESPUESTA"
  | "RETO_RESUELTO"
  | "PAUSADA"
  | "COMPLETADA"
  | "ABANDONADA";

export type Modalidad = "JUGADOR" | "AGENTE";

export type TipoAccion =
  | "iniciar"
  | "elegir_animal"
  | "seleccionar_habitat"
  | "ayuda"
  | "repetir"
  | "pausar"
  | "reanudar"
  | "continuar"
  | "salir"
  | "nueva_partida";

export interface Elemento {
  id: string;
  nombre: string;
  pictograma_id: string;
}

export interface Respuesta {
  contenido_id: string;
  tipo_respuesta: "NAVEGACION" | "PREGUNTA" | "AYUDA" | "CONFIRMACION" | "NEUTRAL" | string;
  pictogramas: string[];
  texto_apoyo: string;
  texto_voz: string;
  nivel: number | null;
  variante_id: string | null;
}

export interface Pictograma {
  etiqueta: string;
  imagen: string;
}

export interface Vista {
  fase: Fase;
  modalidad: Modalidad | null;
  animal: Elemento | null;
  catalogo_animales: Elemento[];
  opciones_habitat: Elemento[];
  cantidad_opciones: number;
  seleccion_habilitada: boolean;
  progreso: { completados: number; total: number };
  controles_disponibles: string[];
  respuesta: Respuesta;
  sesion_id: string;
  reto_id: string | null;
  revision: number;
  catalogo_ampliado: boolean;
  pictogramas: Record<string, Pictograma>;
  idioma: Idioma;
}

export interface ResultadoAccion {
  vista?: Vista;
  aceptada?: boolean;
  motivo?: string;
  respuesta_emitida?: Respuesta | null;
  error?: string;
}

export interface VozCatalogo {
  id: string;
  nombre: string;
  motor: "piper" | "kokoro" | "google" | "microsoft";
  idioma: Idioma;
  region: string;
  calidad?: string;
  disponible: boolean;
}

export type Diccionarios = Record<Idioma, Record<string, string>>;
