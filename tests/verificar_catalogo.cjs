/* El catálogo adapta la paginación y conserva el tamaño del animal. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL||'http://127.0.0.1:8000';
const out=path.resolve(process.env.INTERFAZ_SALIDA||'output/catalogo_pantalla/navegador');
fs.mkdirSync(out,{recursive:true});
async function vista(p){return p.evaluate(async()=>await(await fetch('/api/vista')).json());}
async function clicar(p,nombre,fase){
 await p.getByRole('button',{name:nombre,exact:true}).click();
 await p.waitForFunction(f=>document.body.dataset.fase===f,fase);
}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 const resultados=[];
 try{
  for(const idioma of ['es','pt-BR']){
   const context=await browser.newContext({viewport:{width:1920,height:988}});
   const p=await context.newPage(),errores=[];
   p.on('pageerror',e=>errores.push(e.message));
   await p.goto(base);await p.locator('#ajustes').click();await p.locator('#voz').uncheck();
   if(idioma==='pt-BR'){await p.locator('#idioma').selectOption(idioma);await p.waitForFunction(()=>document.documentElement.lang==='pt-BR');}
   await p.locator('#cerrar-preferencias').click();
   await p.getByRole('button',{name:idioma==='es'?'Comenzar':'Começar',exact:true}).click();
   await clicar(p,idioma==='es'?'Yo elijo':'Eu escolho','SELECCION_ANIMAL');
   const antes=await vista(p),anterior=idioma==='es'?'Anteriores':'Anteriores',siguiente=idioma==='es'?'Siguientes':'Próximos';
   const buscador=p.getByRole('searchbox',{name:idioma==='es'?'Buscar animal':'Buscar animal'});
   for(const [width,height] of [[1920,988],[1536,864],[1366,768],[1280,720],[1024,768],[1000,660],[1280,1080]]){
    await p.setViewportSize({width,height});
    await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    await buscador.fill('');
    const medidas=await p.evaluate(()=>{
     const tarjetas=[...document.querySelectorAll('.catalogo button')];
     const dentro=e=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight+1&&r.left>=0&&r.right<=innerWidth+1;};
     return {sinScroll:document.documentElement.scrollHeight<=innerHeight&&document.documentElement.scrollWidth<=innerWidth,
      tarjetas:tarjetas.length,grandes:tarjetas.every(e=>e.getBoundingClientRect().width>=434&&e.getBoundingClientRect().height>=264),
      animales:tarjetas.every(e=>{const i=e.querySelector('img').getBoundingClientRect();return i.width>=406&&i.height>=154;}),
      todoVisible:[...tarjetas,...document.querySelectorAll('.acciones button,.catalogo-paginacion button,.busqueda')].every(dentro)};
    });
    assert.ok(medidas.sinScroll&&medidas.grandes&&medidas.animales&&medidas.todoVisible,JSON.stringify({width,height,idioma,medidas}));
    const revisionAntesDePaginas=(await vista(p)).revision;
    const todos=[],paso=medidas.tarjetas,paginas=Math.ceil(48/paso);
    for(let n=0;n<paginas;n++){
     todos.push(...await p.locator('.catalogo .animal-numero').allTextContents());
     if(n+1<paginas)await p.getByRole('button',{name:siguiente,exact:true}).click();
    }
    assert.equal(todos.length,48);assert.equal(new Set(todos).size,48);
    assert.deepEqual(todos,Array.from({length:48},(_,n)=>String(n+1).padStart(2,'0')));
    assert.equal((await vista(p)).revision,revisionAntesDePaginas);
    const pagina=await p.locator('.catalogo-pagina').textContent();
    await clicar(p,'Pausar','PAUSADA');
    await clicar(p,idioma==='es'?'Reanudar':'Retomar','SELECCION_ANIMAL');
    assert.equal(await p.locator('.catalogo-pagina').textContent(),pagina);
    if(width===1920||width===1280&&height===720){
     // Buscar vuelve a la primera página antes de capturar.
     await buscador.fill('jag');await buscador.fill('');
     await p.waitForFunction(()=>[...document.querySelectorAll('.catalogo img')].every(i=>i.complete&&i.naturalWidth));
     await p.screenshot({path:path.join(out,`catalogo_${idioma}_${width}_${height}.png`)});
    }
    await buscador.fill('zzzz');assert.equal(await p.locator('.catalogo button').count(),0);
    assert.equal(await p.locator('.busqueda-vacia').isVisible(),true);
    await buscador.fill('');
    resultados.push({idioma,width,height,resultado:'OK',...medidas,paginas});
   }
   assert.equal((await vista(p)).sesion_id,antes.sesion_id);
   assert.equal((await vista(p)).progreso.completados,0);
   await p.locator('.catalogo button[data-animal="A06"]').focus();
   for(const [width,height] of [[1024,768],[1920,988]]){
    await p.setViewportSize({width,height});
    await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    assert.equal(await p.evaluate(()=>document.activeElement.dataset.animal),'A06');
   }
   resultados.push({idioma,caso:'foco_conservado_al_redistribuir',resultado:'OK'});
   await p.setViewportSize({width:390,height:844});
   await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const jaguar=(await vista(p)).catalogo_animales.find(a=>a.id==='A01').nombre;
   await buscador.fill(jaguar);await clicar(p,jaguar,'ESPERANDO_RESPUESTA');
   assert.deepEqual(errores,[]);await context.close();
  }
  fs.writeFileSync(path.join(out,'revision_catalogo.json'),JSON.stringify({fecha:process.env.VERIFICACION_FECHA||new Date().toISOString().slice(0,10),navegador:browser.version(),resultados},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultado:'OK'}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
