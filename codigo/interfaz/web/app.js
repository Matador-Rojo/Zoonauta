"use strict";
let vista = null, ocupado = false, voces = [], vozElegida = "", locucion = null;
const $ = id => document.getElementById(id);
const juego = $("juego"), aviso = $("aviso");
function nodo(tag, clase, texto) { const n=document.createElement(tag); if(clase)n.className=clase; if(texto)n.textContent=texto; return n; }
function imagen(id, clase="") { const im=nodo("img",clase); im.src=vista.pictogramas[id].imagen; im.alt=""; im.draggable=false; return im; }
function icono(nombre,clase="") {
  const caminos={
    flecha:"M5 12h14m-6-6 6 6-6 6",
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
  if(texto)b.setAttribute("aria-label",texto);
  if(picto)b.append(imagen(picto)); if(texto)b.append(nodo("span","",texto));
  b.addEventListener("click",()=>accion(tipo,payload)); return b;
}
function respuesta(r) {
  const bloque=nodo("section","respuesta "+(r.tipo_respuesta==="CONFIRMACION"?"confirmacion":r.tipo_respuesta==="NEUTRAL"?"neutral":""));
  const guia=nodo("div","guia-cabecera"); guia.append(imagen("P_AGENTE"),nodo("span","","Tu guía")); bloque.append(guia);
  const titulo=nodo("h2","",r.texto_apoyo); titulo.id="mensaje"; titulo.tabIndex=-1; bloque.append(titulo);
  const sec=nodo("div","secuencia"); sec.setAttribute("aria-label","Secuencia de pictogramas");
  for(const id of r.pictogramas) {const f=nodo("figure","simbolo"); f.append(imagen(id),nodo("figcaption","",vista.pictogramas[id].etiqueta)); sec.append(f);}
  bloque.append(sec); return bloque;
}
function controles() {
  const a=nodo("nav","acciones"); a.setAttribute("aria-label","Controles de la partida");
  const etiquetas={ayuda:["Ayuda","P_AYUDA"],repetir:["Repetir","P_REPETIR"],pausar:["Pausar","P_PAUSAR"],reanudar:["Reanudar","P_REANUDAR"],continuar:["Continuar","P_CONTINUAR"],salir:["Salir","P_SALIR"]};
  for(const t of vista.controles_disponibles) if(etiquetas[t]) {
    const [texto,p]=etiquetas[t]; a.append(boton(texto,t,{},"accion "+(t==="ayuda"?"destacada":t==="continuar"?"continuar":t==="salir"?"salir":""),p));
  } return a;
}
function titulo(texto,sub,etiqueta="Tu expedición") {
  const fila=nodo("div","titulo-fila"), izq=nodo("div");
  izq.append(nodo("p","etiqueta",etiqueta));
  const h=nodo("h1","",texto); h.id="titulo-pantalla"; h.tabIndex=-1; izq.append(h);
  if(sub)izq.append(nodo("p","subtitulo",sub));
  const progreso=nodo("div","progreso");
  progreso.append(nodo("span","",`${vista.progreso.completados} de ${vista.progreso.total} completados`));
  const barra=nodo("progress"); barra.max=vista.progreso.total; barra.value=vista.progreso.completados;
  barra.setAttribute("aria-label","Progreso de la partida"); progreso.append(barra);
  fila.append(izq,progreso); return fila;
}
function inicio() {
  const b=nodo("section","bienvenida"), grid=nodo("div","inicio-grid"), texto=nodo("div","inicio-texto");
  texto.append(nodo("p","etiqueta","Una aventura entre animales"));
  const h=nodo("h1","","Descubre dónde "); h.id="titulo-pantalla"; h.tabIndex=-1;
  h.append(nodo("em","","vive cada animal.")); texto.append(h,nodo("p","introduccion","Explora 8 hábitats con 48 animales. Elige, descubre y aprende con pictogramas y una guía que te acompaña."));
  texto.append(nodo("h2","pregunta-inicio","¿Quién elige el animal?"));
  const modos=nodo("div","modalidades");
  for(const [m,p,t,s] of [["JUGADOR","P_JUGADOR","Yo elijo","Escoge el animal que quieres descubrir."],["AGENTE","P_AGENTE","El agente elige","Déjate sorprender con un nuevo animal."]]) {
    const btn=boton("", "iniciar",{modalidad:m},"modalidad"); btn.setAttribute("aria-label",t);
    const copia=nodo("div","modalidad-copia"); copia.append(nodo("strong","",t),nodo("span","modalidad-detalle",s));
    btn.append(imagen(p),copia,icono("flecha","flecha")); modos.append(btn);
  }
  const nota=nodo("p","inicio-nota"); nota.append(icono("hoja"),nodo("span","","Pide ayuda, repite o pausa cuando lo necesites."));
  texto.append(modos,nota);
  const mundo=nodo("div","mundo"); mundo.setAttribute("aria-hidden","true");
  const arte=nodo("img","mundo-arte"); arte.src="/mundo.svg"; arte.alt=""; arte.draggable=false;
  mundo.append(arte,nodo("p","mundo-titulo","Tu mapa de exploración"),nodo("span","mundo-sello","8 hábitats"));
  for(const [clase,id,nombre] of [["jaguar","P_A01","Jaguar"],["jirafa","P_A08","Jirafa"]]) {
    const animal=nodo("div","animal-flotante "+clase); animal.append(imagen(id),nodo("span","",nombre)); mundo.append(animal);
  }
  const pie=nodo("div","mundo-pie"),puntos=nodo("div","mundo-puntos");
  for(let i=0;i<8;i++)puntos.append(nodo("span"));
  pie.append(nodo("strong","","Mucho por descubrir"),puntos); mundo.append(pie); grid.append(texto,mundo);
  const resumen=nodo("div","resumen-inicio");
  for(const [ic,t,s] of [["animales","48 animales","Un mundo para descubrir"],["mapa","8 hábitats","Diferentes lugares para vivir"],["reloj","A tu ritmo","Sin tiempo límite"]]) {
    const item=nodo("div","resumen-item"),copia=nodo("div"); copia.append(nodo("strong","",t),nodo("span","",s)); item.append(icono(ic,"resumen-icono"),copia); resumen.append(item);
  }
  b.append(grid,resumen); return b;
}
function catalogoAnimales() {
  const barra=nodo("div","catalogo-barra"),total=nodo("p","catalogo-total",`${vista.catalogo_animales.length} animales para explorar`);
  total.setAttribute("aria-live","polite"); total.setAttribute("aria-atomic","true");
  const buscar=nodo("label","busqueda"),input=nodo("input");
  input.type="search"; input.placeholder="Busca un animal…"; input.setAttribute("aria-label","Buscar animal"); input.autocomplete="off";
  buscar.append(icono("buscar"),input); barra.append(total,buscar);
  const catalogo=nodo("div","catalogo"); catalogo.setAttribute("aria-label","48 animales disponibles");
  const normalizar=t=>t.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase("es").trim();
  for(const a of vista.catalogo_animales) {
    const tarjeta=boton(a.nombre,"elegir_animal",{animal_id:a.id},"tarjeta",a.pictograma_id);
    tarjeta.dataset.busqueda=normalizar(a.nombre); catalogo.append(tarjeta);
  }
  const vacia=nodo("p","busqueda-vacia","No encontramos ese animal. Prueba con otro nombre."); vacia.hidden=true;
  input.addEventListener("input",()=>{
    const consulta=normalizar(input.value); let cantidad=0;
    for(const b of catalogo.children) {b.hidden=!b.dataset.busqueda.includes(consulta); if(!b.hidden)cantidad++;}
    total.textContent=consulta?`${cantidad} de ${vista.catalogo_animales.length} animales`:`${vista.catalogo_animales.length} animales para explorar`;
    vacia.hidden=cantidad!==0;
  });
  return [barra,catalogo,vacia];
}
function render(enfocar=false) {
  const foco=document.activeElement?.dataset?.clave; juego.replaceChildren(); juego.setAttribute("aria-busy","false");
  const f=vista.fase;
  if(f==="INICIO") juego.append(inicio());
  else if(f==="SELECCION_ANIMAL") {
    juego.append(titulo("Elige un animal","Toca el animal con el que quieres jugar.","Explora los animales"),...catalogoAnimales(),controles());
  } else if(f==="PAUSADA"||f==="COMPLETADA"||f==="ABANDONADA") {
    const b=nodo("section","centro"); const pid=f==="PAUSADA"?"P_PAUSAR":f==="COMPLETADA"?"P_FIN":"P_SALIR";
    const h=nodo("h1","",f==="PAUSADA"?"Tomamos una pausa":f==="COMPLETADA"?"¡Terminamos!":"Partida terminada"); h.id="titulo-pantalla"; h.tabIndex=-1;
    b.append(imagen(pid,"grande"),h,nodo("p","introduccion",vista.respuesta.texto_apoyo));
    if(f==="PAUSADA")b.append(controles()); else b.append(boton("Comenzar otra partida","nueva_partida",{},"accion continuar","P_INICIAR"));
    juego.append(b);
  } else {
    juego.append(titulo(f==="RETO_RESUELTO"?"¡Encontraste un lugar!":"Elige un hábitat",null,"Encuentra su hábitat"));
    const tablero=nodo("div","tablero"),companero=nodo("aside","companero"),animal=nodo("div","animal-actual"),retrato=nodo("div","animal-retrato");
    retrato.append(imagen(vista.animal.pictograma_id));
    animal.append(nodo("p","etiqueta","Tu animal"),retrato,nodo("strong","",vista.animal.nombre));
    companero.append(animal,nodo("p","companero-nota","Puedes pedir una pista, repetirla o tomar una pausa."));
    const mesa=nodo("div","mesa"); mesa.append(respuesta(vista.respuesta));
    if(f==="ESPERANDO_RESPUESTA")mesa.append(nodo("p","instruccion","Toca un lugar donde pueda vivir."));
    const hab=nodo("div","habitats"); hab.setAttribute("aria-label","Ocho hábitats");
    for(const h of vista.opciones_habitat) {
      const b=boton(h.nombre,"seleccionar_habitat",{habitat_id:h.id},"tarjeta",h.pictograma_id);
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
function pararVoz(){ if("speechSynthesis" in window) window.speechSynthesis.cancel(); locucion=null; }
function cargarVoces() {
  voces=("speechSynthesis" in window?window.speechSynthesis.getVoices():[]).filter(v=>/^es(?:-|$)/i.test(v.lang));
  const sel=$("voces"), anterior=sel.value||vozElegida; sel.replaceChildren();
  if(!voces.length){const o=nodo("option","","Sin voz española disponible");o.value="";sel.append(o);$("estado-voz").textContent="La voz requiere una voz en español instalada en este dispositivo. El juego conserva texto y pictogramas.";}
  else {for(const v of voces){const o=nodo("option","",`${v.name} (${v.lang})`);o.value=v.voiceURI;sel.append(o);}sel.value=voces.some(v=>v.voiceURI===anterior)?anterior:(voces.find(v=>v.localService)||voces[0]).voiceURI;$("estado-voz").textContent="La disponibilidad y el sonido de la voz dependen del dispositivo.";}
  vozElegida=sel.value;
}
function hablar(texto) {
  if(!$("voz").checked)return;
  if(!("speechSynthesis" in window)||!voces.length){aviso.textContent="No hay voz en español disponible. Puedes seguir con los pictogramas y el texto.";return;}
  pararVoz(); const u=new SpeechSynthesisUtterance(texto); locucion=u;
  u.voice=voces.find(v=>v.voiceURI===$("voces").value)||voces[0];u.lang=u.voice.lang;u.rate=Number($("velocidad").value);u.pitch=1;
  u.onerror=e=>{if(!["canceled","interrupted"].includes(e.error))aviso.textContent="No se pudo reproducir la voz. Puedes volver a pulsar Repetir.";};
  window.speechSynthesis.speak(u);
}
async function accion(tipo,payload) {
  if(ocupado||!vista)return; ocupado=true; aviso.textContent=""; const antes=vista.fase;
  if(tipo==="iniciar") {const n=Number($("retos").value);if(!Number.isInteger(n)||n<1||n>48){aviso.textContent="Selecciona entre 1 y 48 retos en Preferencias.";ocupado=false;return;} payload={...payload,retos:n};}
  if(["pausar","salir","nueva_partida"].includes(tipo))pararVoz();
  for(const b of juego.querySelectorAll("button"))b.disabled=true;
  juego.setAttribute("aria-busy","true");
  const entrada={tipo,payload,evento_id:crypto.randomUUID(),revision:vista.revision,sesion_id:vista.sesion_id,reto_id:vista.reto_id};
  try {
    const r=await fetch("/api/accion",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(entrada)}),d=await r.json();
    if(d.vista){vista=d.vista;render(true);} if(!r.ok){aviso.textContent=d.error||"No se pudo aplicar la acción.";return;}
    if(d.aceptada&&d.respuesta_emitida&&tipo!=="pausar")hablar(d.respuesta_emitida.texto_voz);
    if(antes!==vista.fase)window.scrollTo({top:0,behavior:"instant"});
  } catch(e) {aviso.textContent="No se pudo conectar con el juego. Comprueba que el servidor siga abierto y recarga la página para recuperar la partida.";juego.setAttribute("aria-busy","false");}
  finally {ocupado=false;}
}
$("ajustes").addEventListener("click",()=>{$("retos").disabled=vista&&vista.fase!=="INICIO";cargarVoces();$("preferencias").showModal();});
$("cerrar-preferencias").addEventListener("click",()=>$("preferencias").close());
$("voz").addEventListener("change",()=>{if(!$("voz").checked)pararVoz();});
$("voces").addEventListener("change",()=>vozElegida=$("voces").value);
$("probar-voz").addEventListener("click",()=>hablar("Hola. Vamos a descubrir dónde viven los animales."));
window.addEventListener("pagehide",pararVoz);cargarVoces();
if("speechSynthesis" in window)window.speechSynthesis.addEventListener("voiceschanged",cargarVoces);
fetch("/api/vista").then(r=>{if(!r.ok)throw Error();return r.json();}).then(v=>{vista=v;render();}).catch(()=>{juego.replaceChildren(nodo("p","introduccion","No se pudo cargar el juego. Inicia el servidor y vuelve a abrir esta página."));juego.setAttribute("aria-busy","false");});
