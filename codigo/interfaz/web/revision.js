"use strict";
let datos=null;
async function actualizar(){try{const r=await fetch("/api/revision");if(!r.ok)throw Error();datos=await r.json();document.getElementById("datos").textContent=JSON.stringify(datos,null,2);}catch{document.getElementById("datos").textContent="No se pudo recuperar la sesión.";}}
document.getElementById("actualizar").addEventListener("click",actualizar);
document.getElementById("descargar").addEventListener("click",()=>{if(!datos)return;const u=URL.createObjectURL(new Blob([JSON.stringify(datos,null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=u;a.download="revision_"+datos.sesion_id+".json";a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});actualizar();
