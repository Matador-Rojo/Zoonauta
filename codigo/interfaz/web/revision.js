"use strict";
let datos=null, diccionarios={es:{},"pt-BR":{}};
const originales=[];const walker=document.createTreeWalker(document.querySelector("main"),NodeFilter.SHOW_TEXT);
while(walker.nextNode())if(walker.currentNode.textContent.trim()&&!walker.currentNode.parentElement.closest("#datos"))originales.push([walker.currentNode,walker.currentNode.textContent]);
function traducir(){
  const diccionario=diccionarios[datos?.idioma||"es"]||{};
  document.documentElement.lang=datos?.idioma||"es";
  document.title=diccionario["Zoonauta · Revisión técnica"]||"Zoonauta · Revisión técnica";
  for(const [n,original] of originales)n.textContent=original.replace(original.trim(),diccionario[original.trim()]||original.trim());
}
async function actualizar(){try{const r=await fetch("/api/revision");if(!r.ok)throw Error();datos=await r.json();traducir();document.getElementById("datos").textContent=JSON.stringify(datos,null,2);}catch{document.getElementById("datos").textContent=diccionarios[datos?.idioma||"es"]?.["No se pudo recuperar la sesión."]||"No se pudo recuperar la sesión.";}}
document.getElementById("actualizar").addEventListener("click",actualizar);
document.getElementById("descargar").addEventListener("click",()=>{if(!datos)return;const u=URL.createObjectURL(new Blob([JSON.stringify(datos,null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=u;a.download="revision_"+datos.sesion_id+".json";a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
fetch("/api/idiomas").then(r=>r.json()).then(d=>{diccionarios=d;return actualizar();}).catch(actualizar);
