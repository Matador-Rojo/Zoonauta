/* Recorridos reales del panel de opciones accesibles. Sin descargar voces. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL||'http://127.0.0.1:8000';
const out=path.resolve(process.env.INTERFAZ_SALIDA||'output/hito2_cambios/navegador');
fs.mkdirSync(out,{recursive:true});
const resultados=[];
async function vista(page){return page.evaluate(async()=>await(await fetch('/api/vista')).json());}
async function clicar(page,nombre){
  const antes=(await vista(page)).revision;
  await page.getByRole('button',{name:nombre,exact:true}).click();
  await page.waitForFunction(async r=>(await(await fetch('/api/vista')).json()).revision>r,antes);
  await page.waitForFunction(()=>document.querySelector('#juego').getAttribute('aria-busy')==='false');
}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 try{
  for(const idioma of ['es','pt-BR'])for(const n of [2,4,8]){
   const context=await browser.newContext({viewport:{width:1280,height:720}});
   const page=await context.newPage(),errores=[];
   page.on('pageerror',e=>errores.push(e.message));
   await page.goto(base);await page.locator('#ajustes').click();
   await page.locator('#voz').uncheck();await page.locator('#retos').fill('1');
   await page.locator('#cantidad-opciones').selectOption(String(n));
   if(idioma==='pt-BR'){
    await page.locator('#idioma').selectOption(idioma);
    await page.waitForFunction(()=>document.documentElement.lang==='pt-BR');
   }
   assert.equal(await page.locator('#cantidad-opciones option:checked').textContent(),`${n} ${idioma==='es'?'hábitats':'habitats'}`);
   await page.locator('#cerrar-preferencias').click();
   await page.getByRole('button',{name:idioma==='es'?'Comenzar':'Começar',exact:true}).click();
   await clicar(page,idioma==='es'?'Yo elijo':'Eu escolho');
   const nombre=(await vista(page)).catalogo_animales.find(a=>a.id==='A02').nombre;
   await clicar(page,nombre);
   assert.equal(await page.locator('.habitats button').count(),n);
   const opciones=(await vista(page)).opciones_habitat;
   await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
   assert.equal(new Set(opciones.map(h=>h.id)).size,n);
   assert.deepEqual(await page.locator('.habitat-numero').allTextContents(),opciones.map(h=>h.id.slice(1)));
   for(const [width,height] of [[1024,768],[1280,720],[1920,1080],[390,844]]){
    await page.setViewportSize({width,height});
    const medidas=await page.evaluate(()=>({ancho:document.documentElement.scrollWidth<=innerWidth,
      alto:innerWidth<=850||document.documentElement.scrollHeight<=innerHeight,
      botones:[...document.querySelectorAll('.habitats button')].every(b=>b.getBoundingClientRect().height>=44)}));
    assert.ok(Object.values(medidas).every(Boolean),JSON.stringify({n,width,height,...medidas}));
    if(width===1280||width===390)await page.screenshot({path:path.join(out,`opciones_${n}_${idioma}_${width}.png`),fullPage:true});
   }
   await page.setViewportSize({width:1280,height:720});
   await clicar(page,idioma==='es'?'Pista':'Dica');
   const ayuda=(await vista(page)).respuesta;
   await clicar(page,'Repetir');assert.deepEqual((await vista(page)).respuesta,ayuda);
   await clicar(page,idioma==='es'?'Pausar':'Pausar');
   await clicar(page,idioma==='es'?'Reanudar':'Retomar');
   assert.deepEqual((await vista(page)).opciones_habitat,opciones);
   await page.reload();await page.locator('.habitats').waitFor();
   assert.deepEqual((await vista(page)).opciones_habitat,opciones);
   assert.equal(await page.locator('#cantidad-opciones').inputValue(),String(n));
   const pendiente=opciones.find(h=>h.id!=='H01');
   await clicar(page,pendiente.nombre);await clicar(page,pendiente.nombre);
   const v=await vista(page);assert.equal(v.respuesta.nivel,3);assert.equal(v.progreso.completados,0);
   const tecnica=await page.evaluate(async()=>await(await fetch('/api/revision')).json());
   assert.equal(tecnica.parametros_congelados,true);
   assert.equal(tecnica.estado.elecciones_reto.length,2);
   assert.ok(tecnica.observaciones_cerradas.slice(-2).every(o=>o.resultado===null));
   await clicar(page,opciones.find(h=>h.id==='H01').nombre);
   await clicar(page,idioma==='es'?'Continuar':'Continuar');
   assert.equal((await vista(page)).fase,'COMPLETADA');assert.deepEqual(errores,[]);
   resultados.push({idioma,opciones:n,resultado:'OK',recarga:true,pausa:true,apoyo_explicito:true});
   await context.close();
  }
  fs.writeFileSync(path.join(out,'revision_hito2.json'),JSON.stringify({fecha:'2026-10-18',navegador:browser.version(),resultados},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultado:'OK'}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
