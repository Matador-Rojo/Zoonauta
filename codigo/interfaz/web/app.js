"use strict";
let vista = null, ocupado = false, voces = [], vozElegida = "", locucion = null;
let diccionarios={es:{},"pt-BR":{}}, catalogoVoces=[], pedidoVoz=null, turnoVoz=0, audioURL=null;
let locucionNativa=null;
const eleccionesVoz={};
const canalVoz=crypto.randomUUID();
let carrusel = null, temporizadorPaisaje = null;
let estadoCatalogo = {consulta:"", pagina:0, idioma:null};

const $ = id => document.getElementById(id);
const juego = $("juego"), aviso = $("aviso");
function t(texto, valores={}) {
  let salida=diccionarios[vista?.idioma||"es"]?.[texto]||texto;
  for(const [k,v] of Object.entries(valores))salida=salida.replaceAll(`{${k}}`,String(v));
  return salida;
}
const textosFijos=[], atributosFijos=[];
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
while(walker.nextNode()) {
  const n=walker.currentNode;
  if(!n.parentElement.closest("script,#juego,#voces,#idioma,#estado-voz" )&&n.textContent.trim())textosFijos.push([n,n.textContent]);
}
for(const n of document.querySelectorAll("[aria-label],[placeholder],[title]"))for(const a of ["aria-label","placeholder","title"])if(n.hasAttribute(a))atributosFijos.push([n,a,n.getAttribute(a)]);
function idiomaPantalla() {
  document.documentElement.lang=vista.idioma;
  document.title="Zoonauta · "+t("Animales y hábitats");
  for(const [n,original] of textosFijos)n.textContent=original.replace(original.trim(),t(original.trim()));
  for(const [n,a,original] of atributosFijos)n.setAttribute(a,t(original));
  $("idioma").value=vista.idioma;
  $("etiqueta-voces").textContent=t(vista.idioma==="pt-BR"?"Voz en portugués brasileño":"Voz en español");
}
function nodo(tag, clase, texto) { const n=document.createElement(tag); if(clase)n.className=clase; if(texto)n.textContent=t(texto); return n; }
function imagen(id, clase="") {
  const im=nodo("img",clase);
  im.src=vista.pictogramas[id].imagen;
  if(/^P_A\d{2}$/.test(id))im.classList.add("animal-ilustracion");
  im.alt=""; im.draggable=false; im.decoding="async"; return im;
}
function icono(nombre,clase="") {
  const caminos={
    flecha:"M5 12h14m-6-6 6 6-6 6",
    anterior:"M19 12H5m6-6-6 6 6 6",
    pausa:"M9 5v14M15 5v14",
    reproducir:"m8 5 11 7-11 7V5",
    ayuda:"M9 8a3 3 0 0 1 6 0c0 2-3 2-3 5m0 4v.1M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
    repetir:"M4 10a8 8 0 1 1 1 9M4 3v7h7",
    salir:"M9 4H4v16h5m5-13 5 5-5 5m-6-5h11",
    persona:"M8 6a4 4 0 1 0 8 0 4 4 0 0 0-8 0M4 22v-3a8 8 0 0 1 16 0v3",
    brujula:"M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20m5-15-3 7-7 3 3-7 7-3",
    buscar:"M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
    mapa:"M3 5l6-3 6 3 6-3v17l-6 3-6-3-6 3V5m6-3v17m6-14v17",
    reloj:"M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
    hoja:"M20 3c0 9-1 17-9 17a7 7 0 0 1-7-7C4 5 12 4 20 3M4 20l11-11",
    animales:"M12 11c-3 0-3 3-5 4-3 2-1 6 2 5 2-1 4-1 6 0 3 1 5-3 2-5-2-1-2-4-5-4M7 5v2m5-4v3m5-1v2M3 9v2m18-2v2"
  };
  const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.setAttribute("viewBox","0 0 24 24"); svg.setAttribute("fill","none");
  svg.setAttribute("stroke","currentColor"); svg.setAttribute("stroke-width","1.8");
  svg.setAttribute("stroke-linecap","round"); svg.setAttribute("stroke-linejoin","round");
  svg.setAttribute("aria-hidden","true"); svg.setAttribute("focusable","false");
  if(clase)svg.setAttribute("class",clase);
  const path=document.createElementNS(svg.namespaceURI,"path"); path.setAttribute("d",caminos[nombre]); svg.append(path); return svg;
}
function boton(texto,tipo,payload={},clase="accion",picto=null) {
  const b=nodo("button",clase); b.type="button"; b.dataset.clave=tipo+JSON.stringify(payload);
  if(texto)b.setAttribute("aria-label",t(texto));
  if(picto)b.append(imagen(picto)); if(texto)b.append(nodo("span","",texto));
  b.addEventListener("click",()=>accion(tipo,payload)); return b;
}
function respuesta(r) {
  const bloque=nodo("section","respuesta "+(r.tipo_respuesta==="CONFIRMACION"?"confirmacion":r.tipo_respuesta==="NEUTRAL"?"neutral":""));
  const guia=nodo("div","guia-cabecera"),marca=nodo("img");
  marca.src="/zoonauta-logo.svg";marca.alt="";guia.append(marca,nodo("span","","Tu guía")); bloque.append(guia);
  const titulo=nodo("h2","",r.texto_apoyo); titulo.id="mensaje"; titulo.tabIndex=-1; bloque.append(titulo);
  bloque.append(secuencia(r)); return bloque;
}
function secuencia(r) {
  const sec=nodo("div","secuencia"); sec.setAttribute("aria-label",t("Secuencia de pictogramas"));
  for(const id of r.pictogramas) {const f=nodo("figure","simbolo"); f.append(imagen(id),nodo("figcaption","",vista.pictogramas[id].etiqueta)); sec.append(f);}
  return sec;
}
function controles() {
  const a=nodo("nav","acciones"); a.setAttribute("aria-label",t("Controles de la partida"));
  const etiquetas={ayuda:["Ayuda","P_AYUDA"],repetir:["Repetir","P_REPETIR"],pausar:["Pausar","P_PAUSAR"],reanudar:["Reanudar","P_REANUDAR"],continuar:["Continuar","P_CONTINUAR"],salir:["Salir","P_SALIR"]};
  for(const t of vista.controles_disponibles) if(etiquetas[t]) {
    const [texto,picto]=etiquetas[t],b=boton(texto,t,{},"accion "+(t==="ayuda"?"destacada":t==="continuar"?"continuar":t==="salir"?"salir":""),picto);
    a.append(b);
  } return a;
}
function titulo(texto,sub,etiqueta="Tu expedición") {
  const fila=nodo("div","titulo-fila"), izq=nodo("div");
  izq.append(nodo("p","etiqueta",etiqueta));
  const h=nodo("h1","",texto); h.id="titulo-pantalla"; h.tabIndex=-1; izq.append(h);
  if(sub)izq.append(nodo("p","subtitulo",sub));
  const progreso=nodo("div","progreso");
  progreso.append(nodo("span","",t("{n} de {total} completados",{n:vista.progreso.completados,total:vista.progreso.total})));
  const barra=nodo("progress"); barra.max=vista.progreso.total; barra.value=vista.progreso.completados;
  barra.setAttribute("aria-label",t("Progreso de la partida")); progreso.append(barra);
  fila.append(izq,progreso); return fila;
}
function paisaje(habitat,clase="") {
  const p=nodo("div","paisaje "+clase); p.dataset.habitat=habitat;
  p.setAttribute("aria-hidden","true"); return p;
}
function detenerCarrusel() { clearInterval(temporizadorPaisaje); temporizadorPaisaje=null; }
function ritmoCarrusel() {
  detenerCarrusel();
  if(carrusel&&!carrusel.pausado&&!document.hidden&&!$("preferencias").open&&!$("elegir-modalidad")?.open&&vista?.fase==="INICIO")
    temporizadorPaisaje=setInterval(()=>cambiarPaisaje(1),10000);
}
function cambiarPaisaje(paso) {
  if(!carrusel)return;
  const c=carrusel; c.indice=(c.indice+paso+c.paisajes.length)%c.paisajes.length;
  const h=c.paisajes[c.indice],src=h.id==="H01"?"/portada-selva.webp":`/fondos/${h.id}.webp`;
  c.foto.src=src; c.foto.dataset.habitat=h.id;
  c.numero.textContent=`${String(c.indice+1).padStart(2,"0")} / ${String(c.paisajes.length).padStart(2,"0")}`;
  c.nombre.textContent=h.nombre;
  c.navegacion.setAttribute("aria-label",t("Paisajes: {nombre}, {n} de {total}",{nombre:h.nombre,n:c.indice+1,total:c.paisajes.length}));
  c.pausa.setAttribute("aria-label",t(c.pausado?"Reanudar paisajes":"Pausar paisajes"));
  c.pausa.replaceChildren(icono(c.pausado?"reproducir":"pausa"));
  // Cargar solo la siguiente fotografía. Las ocho imágenes son locales.
  const siguiente=c.paisajes[(c.indice+1)%c.paisajes.length];
  const precarga=new Image(); precarga.src=siguiente.id==="H01"?"/portada-selva.webp":`/fondos/${siguiente.id}.webp`;
}
function inicio() {
  const b=nodo("section","bienvenida"),foto=nodo("img","hero-paisaje");
  foto.alt=""; foto.setAttribute("aria-hidden","true"); foto.draggable=false;
  const layout=nodo("div","hero-layout"),texto=nodo("div","hero-texto");
  texto.append(nodo("p","etiqueta","El mundo está esperando"));
  const h=nodo("h1"); h.id="titulo-pantalla"; h.tabIndex=-1;
  h.append(nodo("span","","Cada animal."),nodo("em","","Su mundo."));
  texto.append(h,nodo("p","introduccion","48 animales. 8 hábitats. Descubre dónde viven con pictogramas y una guía que te acompaña."));
  const entrada=nodo("div","entrada"),comenzar=nodo("button","modalidad comenzar");
  comenzar.type="button";comenzar.setAttribute("aria-label",t("Comenzar"));comenzar.setAttribute("aria-haspopup","dialog");
  comenzar.append(icono("reproducir","modo-icono"),nodo("span","","Comenzar"),icono("flecha","flecha"));
  const selector=nodo("dialog","selector-modalidad");selector.id="elegir-modalidad";selector.setAttribute("aria-labelledby","titulo-modalidad");
  const encabezado=nodo("h2","","¿Quién elige el animal?");encabezado.id="titulo-modalidad";
  const modos=nodo("div","opciones-modalidad");
  for(const [m,etiqueta] of [["JUGADOR","Yo elijo"],["AGENTE","El agente elige"]]) {
    const btn=nodo("button","opcion-modalidad");btn.type="button";btn.setAttribute("aria-label",t(etiqueta));
    btn.append(imagen(m==="JUGADOR"?"P_JUGADOR":"P_AGENTE"),nodo("span","",etiqueta));
    btn.addEventListener("click",()=>{selector.close();accion("iniciar",{modalidad:m});});modos.append(btn);
  }
  const volver=nodo("button","accion volver-inicio","Volver al inicio");volver.type="button";volver.addEventListener("click",()=>selector.close());
  selector.append(encabezado,modos,volver);
  comenzar.addEventListener("click",()=>{selector.showModal();ritmoCarrusel();});
  selector.addEventListener("close",()=>{comenzar.focus({preventScroll:true});ritmoCarrusel();});
  const nota=nodo("p","inicio-nota"); nota.append(icono("reloj"),nodo("span","","Sin reloj. Con ayuda. A tu ritmo."));
  entrada.append(comenzar,nota); texto.append(entrada); layout.append(texto);
  const ficha=nodo("div","hero-ficha"),numero=nodo("span","ficha-numero"),nombre=nodo("strong");
  ficha.append(numero,nombre);
  const navegacion=nodo("nav","paisaje-controles");
  const control=(etiqueta,icon,fn)=>{const btn=nodo("button","paisaje-control");btn.type="button";btn.setAttribute("aria-label",t(etiqueta));btn.append(icono(icon));btn.addEventListener("click",fn);return btn;};
  const manual=paso=>{carrusel.pausado=false;cambiarPaisaje(paso);ritmoCarrusel();};
  const anterior=control("Paisaje anterior","anterior",()=>manual(-1));
  const pausa=control("Pausar paisajes","pausa",()=>{carrusel.pausado=!carrusel.pausado;cambiarPaisaje(0);ritmoCarrusel();});
  const siguiente=control("Siguiente paisaje","flecha",()=>manual(1));
  navegacion.append(anterior,pausa,siguiente);ficha.append(navegacion);layout.append(ficha);
  const resumen=nodo("div","resumen-inicio");
  for(const [t,sub] of [["48","Animales por descubrir"],["08","Hábitats para explorar"],["A tu ritmo","Ayuda, repetición y pausa"]]) {
    const item=nodo("div","resumen-item");item.append(nodo("strong","",t),nodo("span","",sub));resumen.append(item);
  }
  b.append(foto,nodo("div","hero-sombra"),layout,resumen,selector);
  carrusel={foto,numero,nombre,navegacion,pausa,paisajes:vista.opciones_habitat,indice:0,pausado:false};
  cambiarPaisaje(0);ritmoCarrusel();return [b];
}
function catalogoAnimales() {
  if(estadoCatalogo.idioma!==vista.idioma)estadoCatalogo={consulta:"",pagina:0,idioma:vista.idioma};
  const barra=nodo("div","catalogo-barra"),total=nodo("p","catalogo-total",t("{n} animales para explorar",{n:vista.catalogo_animales.length}));
  total.setAttribute("aria-live","polite"); total.setAttribute("aria-atomic","true");
  const buscar=nodo("label","busqueda"),input=nodo("input");
  input.type="search"; input.placeholder=t("Busca un animal…"); input.setAttribute("aria-label",t("Buscar animal")); input.autocomplete="off";
  input.value=estadoCatalogo.consulta;
  buscar.append(icono("buscar"),input); barra.append(total,buscar);
  const catalogo=nodo("div","catalogo"); catalogo.id="catalogo-animales"; catalogo.setAttribute("aria-label",t("Animales de esta página"));
  const normalizar=t=>t.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase(vista.idioma).trim();
  const vacia=nodo("p","busqueda-vacia","No encontramos ese animal. Prueba con otro nombre."); vacia.hidden=true;
  const paginas=nodo("nav","catalogo-paginacion"),estado=nodo("span","catalogo-pagina");
  paginas.setAttribute("aria-label",t("Páginas de animales"));
  estado.setAttribute("aria-live","polite"); estado.setAttribute("aria-atomic","true");
  const control=(etiqueta,simbolo,paso)=>{
    const b=nodo("button","accion");b.type="button";b.setAttribute("aria-label",t(etiqueta));b.setAttribute("aria-controls",catalogo.id);
    b.append(icono(simbolo),nodo("span","",etiqueta));
    b.addEventListener("click",()=>{estadoCatalogo.pagina+=paso;dibujar();catalogo.querySelector("button")?.focus({preventScroll:true});catalogo.scrollIntoView({block:"nearest"});});
    return b;
  };
  const anterior=control("Anteriores","anterior",-1),siguiente=control("Siguientes","flecha",1);
  paginas.append(anterior,estado,siguiente);
  function dibujar() {
    const consulta=normalizar(estadoCatalogo.consulta);
    const animales=vista.catalogo_animales.filter(a=>normalizar(a.nombre).includes(consulta));
    const cantidadPaginas=Math.ceil(animales.length/6);
    estadoCatalogo.pagina=Math.max(0,Math.min(estadoCatalogo.pagina,cantidadPaginas-1));
    catalogo.replaceChildren();
    for(const a of animales.slice(estadoCatalogo.pagina*6,(estadoCatalogo.pagina+1)*6)) {
      const tarjeta=boton(a.nombre,"elegir_animal",{animal_id:a.id},"tarjeta");
      const visual=nodo("div","animal-imagenes");
      visual.append(imagen(a.pictograma_id));
      tarjeta.prepend(visual);
      tarjeta.prepend(nodo("span","animal-numero",a.id.slice(1)));
      tarjeta.append(icono("flecha","animal-flecha")); catalogo.append(tarjeta);
    }
    total.textContent=consulta?t("{n} de {total} animales",{n:animales.length,total:vista.catalogo_animales.length}):t("{n} animales para explorar",{n:vista.catalogo_animales.length});
    estado.textContent=t("Página {pagina} de {total}",{pagina:estadoCatalogo.pagina+1,total:cantidadPaginas});
    anterior.disabled=estadoCatalogo.pagina===0;
    siguiente.disabled=estadoCatalogo.pagina>=cantidadPaginas-1;
    paginas.hidden=animales.length===0; vacia.hidden=animales.length!==0;
  }
  input.addEventListener("input",()=>{estadoCatalogo.consulta=input.value;estadoCatalogo.pagina=0;dibujar();});
  dibujar();return [barra,catalogo,paginas,vacia];
}
function cierre(fase) {
  const b=nodo("section","centro cierre"),visual=nodo("div","cierre-visual"),contenido=nodo("div","cierre-contenido");
  visual.setAttribute("aria-hidden","true");
  const ids=fase==="PAUSADA"&&vista.animal?[vista.animal.pictograma_id]:["P_A05","P_A31","P_A01"];
  ids.forEach((id,i)=>visual.append(imagen(id,`cierre-animal cierre-animal-${i}`)));
  const h=nodo("h1","",fase==="PAUSADA"?"Tomamos una pausa":fase==="COMPLETADA"?"¡Terminamos!":"Partida terminada");h.id="titulo-pantalla";h.tabIndex=-1;
  contenido.append(nodo("p","etiqueta","Tu expedición"),h,nodo("p","introduccion",vista.respuesta.texto_apoyo),secuencia(vista.respuesta));
  const resumen=nodo("div","cierre-resumen");
  resumen.append(nodo("strong","",`${vista.progreso.completados} / ${vista.progreso.total}`),nodo("span","","Retos completados"));
  contenido.append(resumen);
  if(fase==="PAUSADA")contenido.append(controles());
  else {const btn=boton("Comenzar otra partida","nueva_partida",{},"accion continuar","P_INICIAR");contenido.append(btn);}
  contenido.append(nodo("p","cierre-nota","48 animales. Ocho mundos por descubrir."));
  b.append(visual,contenido);return b;
}
function render(enfocar=false,conservarPaisaje=false) {
  const previo=conservarPaisaje&&carrusel?{indice:carrusel.indice,pausado:carrusel.pausado}:null;
  detenerCarrusel(); carrusel=null;idiomaPantalla();
  const foco=document.activeElement?.dataset?.clave; juego.replaceChildren(); juego.setAttribute("aria-busy","false");
  const f=vista.fase; document.body.dataset.fase=f;
  if(f==="INICIO") {estadoCatalogo={consulta:"",pagina:0,idioma:vista.idioma};juego.append(...inicio());if(previo){Object.assign(carrusel,previo);cambiarPaisaje(0);ritmoCarrusel();}}
  else if(f==="SELECCION_ANIMAL") {
    juego.append(titulo("Elige un animal","Toca el animal con el que quieres jugar.","Explora los animales"),...catalogoAnimales(),controles());
  } else if(f==="PAUSADA"||f==="COMPLETADA"||f==="ABANDONADA") {
    juego.append(cierre(f));
  } else {
    juego.append(titulo(f==="RETO_RESUELTO"?"¡Encontraste un lugar!":"Elige un hábitat",null,"Encuentra su hábitat"));
    const tablero=nodo("div","tablero"),companero=nodo("aside","companero"),animal=nodo("div","animal-actual"),retrato=nodo("div","animal-retrato");
    retrato.append(imagen(vista.animal.pictograma_id));
    animal.append(nodo("p","etiqueta","Tu animal"),retrato,nodo("strong","",vista.animal.nombre));
    companero.append(animal,nodo("p","companero-nota","Puedes pedir una pista, repetirla o tomar una pausa."));
    const mesa=nodo("div","mesa"); mesa.append(respuesta(vista.respuesta));
    if(f==="ESPERANDO_RESPUESTA")mesa.append(nodo("p","instruccion","Toca un lugar donde pueda vivir."));
    const hab=nodo("div","habitats"); hab.setAttribute("aria-label",t("Ocho hábitats"));
    for(const h of vista.opciones_habitat) {
      const b=boton(h.nombre,"seleccionar_habitat",{habitat_id:h.id},"tarjeta",h.pictograma_id);
      b.prepend(paisaje(h.id));b.append(nodo("span","habitat-numero",h.id.slice(1)));
      b.dataset.habitat=h.id; b.disabled=!vista.seleccion_habilitada; hab.append(b);
    }
    mesa.append(hab); tablero.append(companero,mesa); juego.append(tablero,controles());
  }
  if(enfocar) {
    const igual=[...juego.querySelectorAll("button")].find(b=>b.dataset.clave===foco&&!b.disabled);
    (igual||$("titulo-pantalla")||juego.querySelector("h1")||juego.querySelector("button"))?.focus({preventScroll:true});
    if(f==="PAUSADA")juego.querySelector("button")?.focus();
  }
}
function pararVoz() {
  const pendiente=pedidoVoz;
  turnoVoz++;pendiente?.abort();pedidoVoz=null;
  if(pendiente)fetch("/api/voz/cancelar",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({canal_voz:canalVoz,turno_voz:turnoVoz}),keepalive:true}).catch(()=>{});
  if(locucion){locucion.pause();locucion.removeAttribute("src");locucion=null;}
  if(locucionNativa){locucionNativa=null;window.speechSynthesis?.cancel();}
  if(audioURL){URL.revokeObjectURL(audioURL);audioURL=null;}
}
function vocesNavegador() {
  if(!window.speechSynthesis||typeof window.SpeechSynthesisUtterance!=="function")return [];
  const regiones=new Set(["419","AR","BO","CL","CO","CR","CU","DO","EC","GT","HN","MX","NI","PA","PE","PR","PY","SV","UY","VE","US"]);
  const resultado=[],vistos=new Set();
  for(const voz of window.speechSynthesis.getVoices()) {
    const idioma=voz.lang.replaceAll("_","-");
    const partes=idioma.split("-"),lengua=partes[0].toLowerCase();
    const region=partes.find(p=>/^(?:[A-Z]{2}|419)$/.test(p.toUpperCase())&&p!==partes[0])?.toUpperCase();
    if(!(lengua==="es"&&regiones.has(region)||lengua==="pt"&&region==="BR"))continue;
    const nombre=voz.name+" "+voz.voiceURI;
    const motor=/\bmicrosoft\b/i.test(nombre)?"microsoft":/\bgoogle\b/i.test(nombre)?"google":null;
    if(!motor)continue;
    const id="navegador:"+encodeURIComponent([voz.voiceURI,voz.name,idioma].join("|"));
    if(vistos.has(id))continue;vistos.add(id);
    resultado.push({id,nombre:voz.name,motor,idioma:lengua==="es"?"es":"pt-BR",region,
      disponible:true,nativa:voz,idioma_voz:idioma,local:voz.localService});
  }
  return resultado.sort((a,b)=>a.nombre.localeCompare(b.nombre));
}
function nombreRegion(region) {
  if(region==="419")return t("Latinoamérica");
  try{return new Intl.DisplayNames([vista?.idioma||"es"],{type:"region"}).of(region);}
  catch{return t({MX:"México",AR:"Argentina",ES:"España",BR:"Brasil",US:"Estados Unidos"}[region]||region);}
}
function notaVoz() {
  const disponible=voces.some(v=>v.disponible);
  const seleccionada=voces.find(v=>v.id===vozElegida);
  const mensaje=seleccionada?.nativa?(seleccionada.local?
    "Voz del navegador instalada en este equipo. No requiere descargar modelos.":
    "Voz del navegador. Puede necesitar Internet; no requiere descargar modelos."):
    disponible?"Las voces se reproducen en este equipo, sin conexión después de preparar los modelos.":
    "No hay voces preparadas para este idioma. Abre iniciar_juego.bat para descargar los modelos.";
  $("estado-voz").textContent=t(mensaje);
  $("disponibilidad-voces-navegador").textContent=t(voces.some(v=>v.nativa)?
    "Microsoft y Google: se muestran las voces compatibles que ofrece tu navegador.":
    "Este navegador no ofrece voces de Microsoft o Google para esta región. Puedes usar Piper o Kokoro.");
  $("probar-voz").disabled=!disponible;
}
function cargarVoces() {
  const idioma=vista?.idioma||"es";
  const anterior=vozElegida;
  voces=[...catalogoVoces,...vocesNavegador()].filter(v=>v.idioma===idioma);
  const sel=$("voces");sel.replaceChildren();
  for(const motor of ["google","microsoft","piper","kokoro"]){
    const grupo=nodo("optgroup");grupo.label={google:"Google",microsoft:"Microsoft",piper:"Piper",kokoro:"Kokoro"}[motor];
    for(const v of voces.filter(v=>v.motor===motor)){
      const calidad=v.calidad?" · "+t({high:"Calidad alta",medium:"Calidad media",low:"Calidad baja",x_low:"Ligera"}[v.calidad]):"";
      const region=nombreRegion(v.region);
      const o=nodo("option","",`${v.nombre} · ${region}${calidad}`);o.value=v.id;o.disabled=!v.disponible;grupo.append(o);
    }
    if(grupo.children.length)sel.append(grupo);
  }
  const recordada=eleccionesVoz[idioma];
  const candidata=voces.find(v=>v.id===recordada&&v.disponible)||voces.find(v=>v.id===anterior&&v.disponible)||voces.find(v=>v.disponible);
  vozElegida=candidata?.id||"";sel.value=vozElegida||voces[0]?.id||"";sel.disabled=!vozElegida;notaVoz();
  if(anterior&&anterior!==vozElegida)pararVoz();
}
function hablarNavegador(voz,prueba) {
  const turno=turnoVoz;
  const texto=prueba?t("Hola. Vamos a descubrir dónde viven los animales."):vista.respuesta.texto_voz;
  const lectura=new SpeechSynthesisUtterance(texto);
  lectura.voice=voz.nativa;lectura.lang=voz.idioma_voz;
  lectura.rate=Number($("velocidad").value);lectura.pitch=1;lectura.volume=1;
  locucionNativa=lectura;
  lectura.onend=()=>{if(turno===turnoVoz&&locucionNativa===lectura){locucionNativa=null;notaVoz();}};
  lectura.onerror=()=>{if(turno===turnoVoz&&locucionNativa===lectura){pararVoz();aviso.textContent=t("No se pudo reproducir la voz. Puedes volver a pulsar Repetir.");notaVoz();}};
  try{window.speechSynthesis.speak(lectura);notaVoz();}
  catch{pararVoz();aviso.textContent=t("No se pudo reproducir la voz. Puedes volver a pulsar Repetir.");notaVoz();}
}
async function hablar(prueba=false) {
  if(!vista||!$("voz").checked)return;
  pararVoz();
  if(!vozElegida){notaVoz();return;}
  const seleccionada=voces.find(v=>v.id===vozElegida);
  if(seleccionada?.nativa){hablarNavegador(seleccionada,prueba);return;}
  const turno=turnoVoz,control=new AbortController();pedidoVoz=control;
  const entrada={voz:vozElegida,idioma:vista.idioma,prueba,revision:vista.revision,sesion_id:vista.sesion_id,reto_id:vista.reto_id,
    canal_voz:canalVoz,turno_voz:turno};
  $("estado-voz").textContent=t("Preparando la lectura…");
  try {
    const r=await fetch("/api/voz",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(entrada),signal:control.signal});
    if(!r.ok){const d=await r.json();throw Error(d.error||t("No se pudo reproducir la voz. Puedes volver a pulsar Repetir."));}
    const blob=await r.blob();if(turno!==turnoVoz)return;
    pedidoVoz=null;
    audioURL=URL.createObjectURL(blob);const audio=new Audio(audioURL);locucion=audio;
    audio.playbackRate=Number($("velocidad").value);audio.preservesPitch=true;
    audio.onended=()=>{if(turno===turnoVoz){pararVoz();notaVoz();}};
    audio.onerror=()=>{if(turno===turnoVoz){pararVoz();aviso.textContent=t("No se pudo reproducir la voz. Puedes volver a pulsar Repetir.");notaVoz();}};
    await audio.play();if(turno===turnoVoz)notaVoz();
  }catch(e){if(e.name!=="AbortError"&&turno===turnoVoz){pararVoz();aviso.textContent=e.message;notaVoz();}}
}
async function cambiarIdioma() {
  if(ocupado||!vista){$("idioma").value=vista?.idioma||"es";return;}
  ocupado=true;pararVoz();aviso.textContent="";$("idioma").disabled=true;
  for(const b of juego.querySelectorAll("button"))b.disabled=true;
  const entrada={idioma:$("idioma").value,revision:vista.revision,sesion_id:vista.sesion_id,reto_id:vista.reto_id};
  try{
    const r=await fetch("/api/idioma",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(entrada)}),d=await r.json();
    if(d.vista){vista=d.vista;render(false,true);cargarVoces();}
    if(!r.ok)aviso.textContent=d.error||t("No se pudo cambiar el idioma.");
  }catch{aviso.textContent=t("No se pudo cambiar el idioma.");render(false,true);}
  finally{ocupado=false;$("idioma").disabled=false;$("idioma").value=vista.idioma;}
}
async function accion(tipo,payload) {
  if(ocupado||!vista)return; ocupado=true; aviso.textContent=""; const antes=vista.fase;
  if(tipo==="iniciar") {const n=Number($("retos").value);if(!Number.isInteger(n)||n<1||n>48){aviso.textContent=t("Selecciona entre 1 y 48 retos en Preferencias.");ocupado=false;return;} payload={...payload,retos:n};}
  pararVoz();
  for(const b of juego.querySelectorAll("button"))b.disabled=true;
  juego.setAttribute("aria-busy","true");
  const entrada={tipo,payload,evento_id:crypto.randomUUID(),revision:vista.revision,sesion_id:vista.sesion_id,reto_id:vista.reto_id};
  try {
    const r=await fetch("/api/accion",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(entrada)}),d=await r.json();
    if(d.vista){vista=d.vista;render(true);} if(!r.ok){aviso.textContent=d.error||t("No se pudo aplicar la acción.");return;}
    if(d.aceptada&&d.respuesta_emitida&&tipo!=="pausar")hablar();
    if(antes!==vista.fase)window.scrollTo({top:0,behavior:"instant"});
  } catch(e) {aviso.textContent=t("No se pudo conectar con el juego. Comprueba que el servidor siga abierto y recarga la página para recuperar la partida.");juego.setAttribute("aria-busy","false");}
  finally {ocupado=false;}
}
$("ajustes").addEventListener("click",()=>{$("retos").disabled=vista&&vista.fase!=="INICIO";cargarVoces();$("preferencias").showModal();ritmoCarrusel();});
$("cerrar-preferencias").addEventListener("click",()=>$("preferencias").close());
$("cerrar-ajustes").addEventListener("click",()=>$("preferencias").close());
$("preferencias").addEventListener("close",ritmoCarrusel);
document.addEventListener("visibilitychange",ritmoCarrusel);
$("voz").addEventListener("change",()=>{if(!$("voz").checked)pararVoz();});
$("voces").addEventListener("change",()=>{pararVoz();vozElegida=$("voces").value;eleccionesVoz[vista.idioma]=vozElegida;notaVoz();});
$("velocidad").addEventListener("change",pararVoz);
$("probar-voz").addEventListener("click",()=>hablar(true));
$("idioma").addEventListener("change",cambiarIdioma);
window.speechSynthesis?.addEventListener("voiceschanged",()=>{if(vista)cargarVoces();});
window.addEventListener("pagehide",()=>{pararVoz();detenerCarrusel();});
Promise.all([fetch("/api/vista"),fetch("/api/idiomas"),fetch("/api/voz/config")].map(async p=>{const r=await p;if(!r.ok)throw Error();return r.json();}))
.then(([v,d,c])=>{vista=v;diccionarios=d;catalogoVoces=c.voces;render();cargarVoces();})
.catch(()=>{juego.replaceChildren(nodo("p","introduccion","No se pudo cargar el juego. Inicia el servidor y vuelve a abrir esta página."));juego.setAttribute("aria-busy","false");});
