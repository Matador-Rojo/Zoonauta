"use strict";

let datos = null;
let filtroActual = "TODOS";
let diccionarios = { es: {}, "pt-BR": {} };

const originales = [];
const walker = document.createTreeWalker(document.querySelector("main"), NodeFilter.SHOW_TEXT);
while (walker.nextNode()) {
  const txt = walker.currentNode.textContent;
  if (txt && txt.trim() && !walker.currentNode.parentElement.closest("#datos, #rev-metricas, #rev-linea")) {
    originales.push([walker.currentNode, txt]);
  }
}

function traducir() {
  const diccionario = diccionarios[datos?.idioma || "es"] || {};
  document.documentElement.lang = datos?.idioma || "es";
  document.title = diccionario["Zoonauta · Revisión técnica"] || "Zoonauta · Revisión técnica";
  for (const [nodo, original] of originales) {
    const limpio = original.trim();
    nodo.textContent = original.replace(limpio, diccionario[limpio] || limpio);
  }
}

function crearElemento(tag, clase, texto) {
  const el = document.createElement(tag);
  if (clase) el.className = clase;
  if (texto !== undefined) el.textContent = String(texto);
  return el;
}

function descargarArchivo(nombre, contenido, mime) {
  const url = URL.createObjectURL(new Blob([contenido], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function resumirFila(f) {
  const reg = f.tipo_registro || "EVENTO";
  if (reg === "AYUDA_PRESENTADA") {
    return {
      categoria: "AYUDA",
      badge: "AYUDA",
      titulo: `Pista del agente · ${f.animal_id || "—"} (${f.variante_id || f.respuesta?.contenido_id || "—"})`,
      meta: [f.respuesta?.texto_apoyo, f.reto_id ? `Reto ${f.reto_id.slice(-3)}` : null, f.nivel != null ? `Nivel ${f.nivel}` : null]
        .filter(Boolean)
        .join(" · "),
      eventoTipo: "ayuda_presentada",
      animalId: f.animal_id || "",
      habitatId: f.habitat_guia_id || "",
      tipoRespuesta: f.respuesta?.tipo_respuesta || "AYUDA",
      contenidoId: f.respuesta?.contenido_id || "",
      nivel: f.nivel ?? "",
      varianteId: f.variante_id || "",
      motivo: f.decision?.regla || f.decision?.razon || "",
    };
  }
  if (reg === "OBSERVACION_CERRADA") {
    const ok = f.resultado === 1;
    return {
      categoria: ok ? "CONFIRMACION" : "AYUDA",
      badge: ok ? "CONFIRMACION" : "OBSERVACION",
      titulo: `Observación cerrada · ${f.animal_id || "—"} (${ok ? "acierto tras ayuda" : "pendiente"})`,
      meta: [f.variante_id ? `Variante ${f.variante_id}` : null, f.evento_cierre || null].filter(Boolean).join(" · "),
      eventoTipo: "observacion_cerrada",
      animalId: f.animal_id || "",
      habitatId: f.habitat_guia_id || "",
      tipoRespuesta: ok ? "CONFIRMACION" : "NEUTRAL",
      contenidoId: f.nodo_id || "",
      nivel: f.nivel ?? "",
      varianteId: f.variante_id || "",
      motivo: f.evento_cierre || "",
    };
  }
  const ev = f.evento || {};
  const resp = f.respuesta_emitida || {};
  const est = f.estado_despues || {};
  const tipoResp = resp.tipo_respuesta || "EVENTO";
  const hab = ev.payload?.habitat_id || est.habitat_seleccionado_id || "";
  const ani = ev.payload?.animal_id || est.animal_id || "";
  return {
    categoria:
      tipoResp === "CONFIRMACION"
        ? "CONFIRMACION"
        : tipoResp === "AYUDA" || ev.tipo === "ayuda"
          ? "AYUDA"
          : ev.tipo === "seleccionar_habitat"
            ? "SELECCION"
            : "EVENTO",
    badge: tipoResp,
    titulo: [ev.tipo || "evento", ani ? `· ${ani}` : "", hab ? `→ ${hab}` : ""].filter(Boolean).join(" "),
    meta: [resp.texto_apoyo, resp.variante_id ? `Variante ${resp.variante_id}` : null, f.motivo || null]
      .filter(Boolean)
      .join(" · "),
    eventoTipo: ev.tipo || "evento",
    animalId: ani,
    habitatId: hab,
    tipoRespuesta: tipoResp,
    contenidoId: resp.contenido_id || "",
    nivel: resp.nivel ?? est.nivel ?? "",
    varianteId: resp.variante_id || "",
    motivo: f.motivo || "",
  };
}

function pintarMetricas() {
  const contenedor = document.getElementById("rev-metricas");
  contenedor.replaceChildren();
  if (!datos) return;
  const filas = Array.isArray(datos.registro) ? datos.registro : [];
  const ayudas = filas.filter((f) => f.tipo_registro === "AYUDA_PRESENTADA").length;
  const confirmaciones = filas.filter(
    (f) => f.tipo_registro === "EVENTO" && f.respuesta_emitida?.tipo_respuesta === "CONFIRMACION",
  ).length;
  const completados = datos.estado?.completados ?? 0;
  const ver = String(datos.modelo_version || "—");
  const verCorta = ver.length > 16 ? `${ver.slice(0, 12)}…` : ver;
  const tarjetas = [
    ["Política activa", datos.politica || "—", ""],
    ["Versión del modelo", verCorta, ver],
    ["Fase actual", datos.estado?.fase || "—", ""],
    ["Retos completados", String(completados), ""],
    ["Ayudas del agente", String(ayudas), ""],
    ["Confirmaciones", String(confirmaciones), ""],
    ["Observaciones cerradas", String(Array.isArray(datos.observaciones_cerradas) ? datos.observaciones_cerradas.length : 0), ""],
    ["Parámetros", datos.parametros_congelados ? "Congelados" : "Activos", ""],
  ];
  for (const [etiqueta, valor, titulo] of tarjetas) {
    const kpi = crearElemento("article", "rev-kpi");
    const valEl = crearElemento("strong", "rev-kpi-valor", valor);
    if (titulo) valEl.title = titulo;
    kpi.append(crearElemento("span", "rev-kpi-etiqueta", etiqueta), valEl);
    contenedor.append(kpi);
  }
}

function coincideFiltro(item) {
  if (filtroActual === "TODOS") return true;
  return item.categoria === filtroActual;
}

function pintarLinea() {
  const lista = document.getElementById("rev-linea");
  lista.replaceChildren();
  const filas = (Array.isArray(datos?.registro) ? datos.registro : []).map((f, idx) => ({
    idx: idx + 1,
    res: resumirFila(f),
  }));
  const filtradas = filas.filter((x) => coincideFiltro(x.res));
  if (filtradas.length === 0) {
    lista.append(
      crearElemento("li", "rev-vacio", "Todavía no hay eventos para este filtro. Juega un reto y pulsa «Actualizar registro»."),
    );
    return;
  }
  for (const { idx, res } of filtradas) {
    const li = crearElemento("li", "rev-evento");
    li.dataset.tipo = res.categoria;

    const badge = crearElemento("span", "rev-badge", res.badge);
    const cuerpo = crearElemento("div", "rev-evento-cuerpo");
    cuerpo.append(crearElemento("strong", "", res.titulo), crearElemento("span", "rev-evento-meta", res.meta || "—"));

    const paso = crearElemento("span", "rev-hora", `#${String(idx).padStart(2, "0")}`);
    li.append(badge, cuerpo, paso);
    lista.append(li);
  }
}

function convertirCSV(filas) {
  const columnas = [
    "paso",
    "evento_tipo",
    "animal_id",
    "habitat_id",
    "tipo_respuesta",
    "contenido_id",
    "nivel",
    "variante_id",
    "motivo",
  ];
  const escapar = (v) => {
    const s = v === null || v === undefined ? "" : String(v);
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lineas = [columnas.join(",")];
  filas.forEach((f, i) => {
    const r = resumirFila(f);
    const valores = [i + 1, r.eventoTipo, r.animalId, r.habitatId, r.tipoRespuesta, r.contenidoId, r.nivel, r.varianteId, r.motivo];
    lineas.push(valores.map(escapar).join(","));
  });
  return lineas.join("\n") + "\n";
}

function anonimizar(entrada) {
  const copia = JSON.parse(JSON.stringify(entrada));
  copia.sesion_id = "anon_sesion";
  if (copia.estado && "sesion_id" in copia.estado) copia.estado.sesion_id = "anon_sesion";
  if (Array.isArray(copia.registro)) {
    for (const fila of copia.registro) {
      if ("sesion_id" in fila) fila.sesion_id = "anon_sesion";
      if (fila.evento && "sesion_id" in fila.evento) fila.evento.sesion_id = "anon_sesion";
      if (fila.evento && "evento_id" in fila.evento) fila.evento.evento_id = "anon_evento";
    }
  }
  return copia;
}

async function actualizar() {
  try {
    const r = await fetch("/api/revision");
    if (!r.ok) throw Error();
    datos = await r.json();
    traducir();
    pintarMetricas();
    pintarLinea();
    document.getElementById("datos").textContent = JSON.stringify(datos, null, 2);
  } catch {
    document.getElementById("datos").textContent =
      diccionarios[datos?.idioma || "es"]?.["No se pudo recuperar la sesión."] || "No se pudo recuperar la sesión.";
  }
}

document.getElementById("actualizar").addEventListener("click", actualizar);
document.getElementById("descargar").addEventListener("click", () => {
  if (!datos) return;
  descargarArchivo(`revision_${datos.sesion_id}.json`, JSON.stringify(datos, null, 2), "application/json");
});
document.getElementById("descargar-csv").addEventListener("click", () => {
  if (!datos) return;
  const filas = Array.isArray(datos.registro) ? datos.registro : [];
  descargarArchivo(`revision_${datos.sesion_id}.csv`, convertirCSV(filas), "text/csv; charset=utf-8");
});
document.getElementById("descargar-anonimo").addEventListener("click", () => {
  if (!datos) return;
  descargarArchivo("zoonauta_sesion_anonima.json", JSON.stringify(anonimizar(datos), null, 2), "application/json");
});

for (const btn of document.querySelectorAll(".rev-chip")) {
  btn.addEventListener("click", () => {
    filtroActual = btn.dataset.filtro || "TODOS";
    for (const b of document.querySelectorAll(".rev-chip")) {
      b.setAttribute("aria-pressed", String(b === btn));
    }
    pintarLinea();
  });
}

fetch("/api/idiomas")
  .then((r) => r.json())
  .then((d) => {
    diccionarios = d;
    return actualizar();
  })
  .catch(actualizar);
