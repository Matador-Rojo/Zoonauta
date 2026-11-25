/**
 * Álbum / Pasaporte persistente de expedición (localStorage).
 * Registra los animales y hábitats descubiertos a lo largo de todas las partidas
 * y calcula dos series de 5 estrellas: 5 para animales y 5 para hábitats.
 */

export interface RegistroAlbum {
  animalId: string;
  animalNombre: string;
  pictogramaId: string;
  imagenAnimal: string;
  habitatId: string;
  habitatNombre: string;
  descubiertoEn: string;
}

export interface MedallaAlbum {
  id: string;
  titulo: string;
  meta: string;
  obtenida: boolean;
}

const CLAVE_ALBUM = "zoonauta.album.v1";

export function cargarAlbum(): RegistroAlbum[] {
  try {
    const crudo = localStorage.getItem(CLAVE_ALBUM);
    if (!crudo) return [];
    const parsed = JSON.parse(crudo) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (x): x is RegistroAlbum =>
        Boolean(x) &&
        typeof x === "object" &&
        typeof (x as RegistroAlbum).animalId === "string" &&
        typeof (x as RegistroAlbum).habitatId === "string",
    );
  } catch {
    return [];
  }
}

export function guardarAlbum(registros: RegistroAlbum[]) {
  try {
    localStorage.setItem(CLAVE_ALBUM, JSON.stringify(registros));
  } catch {
    /* almacenamiento no disponible */
  }
}

export function limpiarAlbum() {
  try {
    localStorage.removeItem(CLAVE_ALBUM);
  } catch {
    /* almacenamiento no disponible */
  }
}

export function registrarHallazgoEnAlbum(
  actual: RegistroAlbum[],
  nuevo: Omit<RegistroAlbum, "descubiertoEn">,
): { lista: RegistroAlbum[]; esNuevo: boolean } {
  const yaExiste = actual.some((r) => r.animalId === nuevo.animalId && r.habitatId === nuevo.habitatId);
  if (yaExiste) return { lista: actual, esNuevo: false };
  const entrada: RegistroAlbum = { ...nuevo, descubiertoEn: new Date().toISOString() };
  const lista = [entrada, ...actual].slice(0, 600);
  guardarAlbum(lista);
  return { lista, esNuevo: true };
}

export function resumenAlbum(registros: RegistroAlbum[]) {
  const animalesUnicos = new Set(registros.map((r) => r.animalId)).size;
  const habitatsUnicos = new Set(registros.map((r) => r.habitatId)).size;

  const medallasAnimales: MedallaAlbum[] = [
    { id: "a-1", titulo: "Primer hallazgo", meta: "1 animal", obtenida: animalesUnicos >= 1 },
    { id: "a-20", titulo: "Rastreador curioso", meta: "20 animales", obtenida: animalesUnicos >= 20 },
    { id: "a-80", titulo: "Explorador experto", meta: "80 animales", obtenida: animalesUnicos >= 80 },
    { id: "a-160", titulo: "Guardián de fauna", meta: "160 animales", obtenida: animalesUnicos >= 160 },
    { id: "a-288", titulo: "Atlas completo", meta: "288 animales", obtenida: animalesUnicos >= 288 },
  ];

  const medallasHabitats: MedallaAlbum[] = [
    { id: "h-1", titulo: "Primer paisaje", meta: "1 hábitat", obtenida: habitatsUnicos >= 1 },
    { id: "h-5", titulo: "Viajero natural", meta: "5 hábitats", obtenida: habitatsUnicos >= 5 },
    { id: "h-15", titulo: "Guía de biomas", meta: "15 hábitats", obtenida: habitatsUnicos >= 15 },
    { id: "h-30", titulo: "Maestro de ecosistemas", meta: "30 hábitats", obtenida: habitatsUnicos >= 30 },
    { id: "h-48", titulo: "Mundo completo", meta: "48 hábitats", obtenida: habitatsUnicos >= 48 },
  ];

  return { animalesUnicos, habitatsUnicos, medallasAnimales, medallasHabitats };
}
