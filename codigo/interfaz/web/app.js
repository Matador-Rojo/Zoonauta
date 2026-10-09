"use strict";
let vista = null, ocupado = false, voces = [], vozElegida = "", locucion = null;
const $ = id => document.getElementById(id);
const juego = $("juego"), aviso = $("aviso");
function nodo(tag, clase, texto) { const n=document.createElement(tag); if(clase)n.className=clase; if(texto)n.textContent=texto; return n; }
function imagen(id, clase="") { const im=nodo("img",clase); im.src=vista.pictogramas[id].imagen; im.alt=""; im.draggable=false; return im; }
function boton(texto,tipo,payload={},clase="accion",picto=null) {
  const b=nodo("button",clase); b.type="button"; b.dataset.clave=tipo+JSON.stringify(payload);
  if(picto)b.append(imagen(picto)); b.append(nodo("span","",texto));
  b.addEventListener("click",()=>accion(tipo,payload)); return b;
}
function respuesta(r) {
  const bloque=nodo("section","respuesta "+(r.tipo_respuesta==="CONFIRMACION"?"confirmacion":r.tipo_respuesta==="NEUTRAL"?"neutral":""));
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
function titulo(texto,sub) {
  const fila=nodo("div","titulo-fila"), izq=nodo("div"); const h=nodo("h1","",texto); h.id="titulo-pantalla";h.tabIndex=-1;izq.append(h);
  if(sub)izq.append(nodo("p","subtitulo",sub));
  fila.append(izq,nodo("p","progreso",`${vista.progreso.completados} de ${vista.progreso.total} completados`)); return fila;
}
function render(enfocar=false) {
  const foco=document.activeElement?.dataset?.clave; juego.replaceChildren(); juego.setAttribute("aria-busy","false");
  const f=vista.fase;
  if(f==="INICIO") {
    const b=nodo("section","bienvenida"); b.append(nodo("p","etiqueta","Explora y aprende"),nodo("h1","","¿Dónde viven los animales?"),nodo("p","introduccion","Elige quién escoge el animal para comenzar."));
    const modos=nodo("div","modalidades");
    for(const [m,p,t,s] of [["JUGADOR","P_JUGADOR","Yo elijo","Escoge entre 48 animales"],["AGENTE","P_AGENTE","El agente elige","Descubre el animal que te propone"]]) {
      const btn=boton("", "iniciar",{modalidad:m},"modalidad"); btn.setAttribute("aria-label",t); btn.replaceChildren(imagen(p),nodo("strong","",t),nodo("span","",s)); modos.append(btn);
    } b.append(modos,nodo("p","subtitulo","Puedes pedir ayuda, repetir o pausar cuando lo necesites.")); juego.append(b);
  } else if(f==="SELECCION_ANIMAL") {
    juego.append(titulo("Elige un animal","Toca el animal con el que quieres jugar."));
    const catalogo=nodo("div","catalogo"); catalogo.setAttribute("aria-label","48 animales disponibles");
    for(const a of vista.catalogo_animales) catalogo.append(boton(a.nombre,"elegir_animal",{animal_id:a.id},"tarjeta",a.pictograma_id));
    juego.append(catalogo,controles());
  } else if(f==="PAUSADA"||f==="COMPLETADA"||f==="ABANDONADA") {
    const b=nodo("section","centro"); const pid=f==="PAUSADA"?"P_PAUSAR":f==="COMPLETADA"?"P_FIN":"P_SALIR";
    b.append(imagen(pid,"grande"),nodo("h1","",f==="PAUSADA"?"Tomamos una pausa":f==="COMPLETADA"?"¡Terminamos!":"Partida terminada"),nodo("p","introduccion",vista.respuesta.texto_apoyo));
    if(f==="PAUSADA")b.append(controles()); else b.append(boton("Comenzar otra partida","nueva_partida",{},"accion continuar","P_INICIAR"));
    juego.append(b);
  } else {
    juego.append(titulo(f==="RETO_RESUELTO"?"¡Encontraste un lugar!":"Elige un hábitat"));
    const escena=nodo("div","escena"),animal=nodo("div","animal-actual");
    animal.append(imagen(vista.animal.pictograma_id),nodo("strong","",vista.animal.nombre)); escena.append(animal,respuesta(vista.respuesta)); juego.append(escena);
    if(f==="ESPERANDO_RESPUESTA")juego.append(nodo("p","instruccion","Toca un lugar donde pueda vivir."));
    const hab=nodo("div","habitats"); hab.setAttribute("aria-label","Ocho hábitats");
    for(const h of vista.opciones_habitat){const b=boton(h.nombre,"seleccionar_habitat",{habitat_id:h.id},"tarjeta",h.pictograma_id); b.disabled=!vista.seleccion_habilitada; hab.append(b);}
    juego.append(hab,controles());
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
