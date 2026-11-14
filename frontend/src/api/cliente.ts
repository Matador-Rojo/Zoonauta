import type { Diccionarios, Idioma, ResultadoAccion, TipoAccion, Vista, VozCatalogo } from "./tipos";

async function json<T>(respuesta: Response): Promise<T> {
  return (await respuesta.json()) as T;
}

async function obtener<T>(ruta: string): Promise<T> {
  const r = await fetch(ruta, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`GET ${ruta}: ${r.status}`);
  return json<T>(r);
}

function enviar(ruta: string, cuerpo: unknown, signal?: AbortSignal, keepalive = false) {
  return fetch(ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
    signal,
    keepalive,
  });
}

export const cargarVista = () => obtener<Vista>("/api/vista");
export const cargarDiccionarios = () => obtener<Diccionarios>("/api/idiomas");
export const cargarConfigVoz = () => obtener<{ voces: VozCatalogo[] }>("/api/voz/config");

/** Envía una acción con la semántica de 5.0: evento_id único, revisión, sesión y reto. */
export async function enviarAccion(
  vista: Vista,
  tipo: TipoAccion,
  payload: Record<string, unknown>,
): Promise<{ ok: boolean; datos: ResultadoAccion }> {
  const entrada = {
    tipo,
    payload,
    evento_id: crypto.randomUUID(),
    revision: vista.revision,
    sesion_id: vista.sesion_id,
    reto_id: vista.reto_id,
  };
  const r = await enviar("/api/accion", entrada);
  return { ok: r.ok, datos: await json<ResultadoAccion>(r) };
}

export async function enviarIdioma(vista: Vista, idioma: Idioma) {
  const r = await enviar("/api/idioma", {
    idioma,
    revision: vista.revision,
    sesion_id: vista.sesion_id,
    reto_id: vista.reto_id,
  });
  return { ok: r.ok, datos: await json<ResultadoAccion>(r) };
}

export function pedirVoz(entrada: Record<string, unknown>, signal: AbortSignal) {
  return enviar("/api/voz", entrada, signal);
}

export function cancelarVoz(canal: string, turno: number) {
  return enviar("/api/voz/cancelar", { canal_voz: canal, turno_voz: turno }, undefined, true).catch(() => undefined);
}
