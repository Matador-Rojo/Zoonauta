/* Verificación en navegador real. Playwright solo es necesario para esta prueba.
   INTERFAZ_URL, PLAYWRIGHT_MODULE y CHROMIUM_EXECUTABLE son opciones de prueba. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL||'http://127.0.0.1:8000';
const out=path.resolve(__dirname,'../docs/interfaz');fs.mkdirSync(out,{recursive:true});
const resultados=[];
async function mockVoz(context){
  await context.addInitScript(()=>{
    window.__voz=[];window.__cancelaciones=0;
    const voz={voiceURI:'prueba-es',name:'Español de prueba',lang:'es-PE',localService:true};
    Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[voz],addEventListener:()=>{},cancel:()=>window.__cancelaciones++,speak:u=>window.__voz.push({texto:u.text,lang:u.lang,rate:u.rate})},configurable:true});
    window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
  });
}
async function vista(page){return page.evaluate(async()=>await (await fetch('/api/vista')).json());}
async function clicar(page,texto,fase){
  const antes=(await vista(page)).revision;
  await page.getByRole('button',{name:texto,exact:true}).click();
  await page.waitForFunction(async rev=>(await (await fetch('/api/vista')).json()).revision>rev,antes);
  if(fase)await page.waitForFunction(async f=>(await (await fetch('/api/vista')).json()).fase===f,fase);
  await page.waitForFunction(()=>document.getElementById('juego').getAttribute('aria-busy')==='false');
}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 try{
  const contexto=await browser.newContext({viewport:{width:1280,height:1080}});await mockVoz(contexto);
  const page=await contexto.newPage(),errores=[];page.on('pageerror',e=>errores.push(e.message));
  await page.goto(base);await page.getByRole('button',{name:'Yo elijo'}).waitFor();
  await page.screenshot({path:path.join(out,'01_inicio.png'),fullPage:true});
  await page.getByRole('button',{name:'Preferencias'}).click();
  await page.locator('#retos').fill('1');await page.getByRole('button',{name:'Probar voz',exact:true}).click();
  assert.equal((await page.evaluate(()=>window.__voz.at(-1))).lang,'es-PE');
  await page.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await clicar(page,'Yo elijo','SELECCION_ANIMAL');
  assert.equal(await page.locator('.catalogo button').count(),48);
  await page.screenshot({path:path.join(out,'02_catalogo.png'),fullPage:true});
  await clicar(page,'Capibara o ronsoco','ESPERANDO_RESPUESTA');
  assert.equal(await page.locator('.habitats button').count(),8);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  await clicar(page,'Ayuda');const ayuda=(await vista(page)).respuesta;
  const textoVoz=(await page.evaluate(()=>window.__voz.at(-1))).texto;assert.equal(textoVoz,ayuda.texto_voz);
  await clicar(page,'Repetir');assert.deepEqual((await vista(page)).respuesta,ayuda);assert.equal((await page.evaluate(()=>window.__voz.at(-1))).texto,textoVoz);
  const r=(await vista(page)).revision;await page.reload();await page.getByRole('button',{name:'Ayuda',exact:true}).waitFor();assert.equal((await vista(page)).revision,r);assert.equal(await page.evaluate(()=>window.__voz.length),0);
  await clicar(page,'Pausar','PAUSADA');assert.equal(await page.locator('.habitats').count(),0);assert.ok(await page.evaluate(()=>window.__cancelaciones)>0);
  await clicar(page,'Reanudar','ESPERANDO_RESPUESTA');assert.deepEqual((await vista(page)).respuesta,ayuda);
  await clicar(page,'Desierto cálido');assert.equal((await vista(page)).respuesta.tipo_respuesta,'NEUTRAL');assert.equal((await vista(page)).progreso.completados,0);
  await clicar(page,'Selva tropical','RETO_RESUELTO');assert.equal((await vista(page)).progreso.completados,1);assert.equal(await page.locator('.habitats button:enabled').count(),0);
  await clicar(page,'Continuar','COMPLETADA');await clicar(page,'Comenzar otra partida','INICIO');
  await clicar(page,'El agente elige','ESPERANDO_RESPUESTA');assert.equal(await page.locator('.habitats button').count(),8);
  await clicar(page,'Salir','ABANDONADA');
  resultados.push({caso:'Recorrido de jugador y agente, 48 animales, 8 opciones, ayuda, repetición, pausa, pendiente neutral, confirmación, cierre y nueva partida',resultado:'OK'});
  resultados.push({caso:'Actualización del navegador conserva sesión sin repetir eventos ni audio',resultado:'OK'});
  resultados.push({caso:'Voz española: texto exacto, repetición y cancelación',resultado:'OK',alcance:'Síntesis simulada en navegador; no certifica sonido audible ni comprensión.'});
  assert.deepEqual(errores,[]);
  // Captura de un reto con ayuda en escritorio.
  await clicar(page,'Comenzar otra partida','INICIO');await clicar(page,'Yo elijo','SELECCION_ANIMAL');await clicar(page,'Jirafa reticulada','ESPERANDO_RESPUESTA');await clicar(page,'Ayuda');
  await page.screenshot({path:path.join(out,'03_reto_escritorio.png'),fullPage:true});
  // Los 95 recursos se decodifican en el navegador (PNG y SVG).
  const assetTest=await page.evaluate(async()=>{
    const v=await (await fetch('/api/vista')).json();
    const fallos=[];await Promise.all(Object.values(v.pictogramas).map(p=>new Promise(resolve=>{const i=new Image();i.onload=()=>{if(!i.naturalWidth)fallos.push(p.imagen);resolve();};i.onerror=()=>{fallos.push(p.imagen);resolve();};i.src=p.imagen;})));return fallos;
  });assert.deepEqual(assetTest,[]);resultados.push({caso:'95 recursos visuales decodificados sin errores',resultado:'OK'});
  // Revisar las representaciones de animales en una plancha para inspección visual.
  await page.evaluate(async()=>{
    const v=await (await fetch('/api/vista')).json();const main=document.getElementById('juego');main.replaceChildren();
    const h=document.createElement('h1');h.textContent='Revisión visual: 48 animales';main.append(h);const grid=document.createElement('div');grid.className='catalogo';main.append(grid);
    for(const a of v.catalogo_animales){const d=document.createElement('div');d.className='tarjeta';const im=document.createElement('img');im.src=v.pictogramas[a.pictograma_id].imagen;const t=document.createElement('span');t.textContent=a.nombre;d.append(im,t);grid.append(d);}
  });await page.screenshot({path:path.join(out,'04_revision_animales.png'),fullPage:true});
  // Vista estrecha real: sin desbordamiento horizontal, controles alcanzables.
  const movil=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await mockVoz(movil);const pm=await movil.newPage();await pm.goto(base);await pm.getByRole('button',{name:'El agente elige'}).waitFor();await clicar(pm,'El agente elige','ESPERANDO_RESPUESTA');await clicar(pm,'Ayuda');
  assert.equal(await pm.locator('.habitats button').count(),8);
  assert.equal(await pm.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await pm.screenshot({path:path.join(out,'05_reto_movil.png'),fullPage:true});
  const minimo=await pm.locator('button').evaluateAll(bs=>Math.min(...bs.map(b=>b.getBoundingClientRect().height).filter(h=>h>0)));assert.ok(minimo>=44);
  resultados.push({caso:'Pantalla móvil 390 × 844: ocho opciones, sin desbordamiento horizontal, botones de al menos 44 px',resultado:'OK'});
  // Ausencia de voces: la interfaz debe explicar la limitación y seguir funcionando.
  const sinvoz=await browser.newContext();await sinvoz.addInitScript(()=>Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[],addEventListener:()=>{},cancel:()=>{}},configurable:true}));
  const pv=await sinvoz.newPage();await pv.goto(base);await pv.getByRole('button',{name:'El agente elige'}).waitFor();await clicar(pv,'El agente elige','ESPERANDO_RESPUESTA');assert.match(await pv.locator('#aviso').textContent(),/No hay voz en español/);assert.equal(await pv.locator('.habitats button:enabled').count(),8);
  resultados.push({caso:'Dispositivo sin voz española: aviso visible, texto y pictogramas operativos',resultado:'OK'});
  // Página técnica de la misma cookie: solo lectura, modelo congelado.
  await page.goto(base+'/revision');await page.locator('#datos').filter({hasText:'parametros_congelados'}).waitFor();
  const tecnicos=JSON.parse(await page.locator('#datos').textContent());assert.equal(tecnicos.parametros_congelados,true);
  resultados.push({caso:'Consulta técnica separada y modelo congelado',resultado:'OK'});
  fs.writeFileSync(path.join(out,'revision_navegador.json'),JSON.stringify({fecha:'2026-10-09',navegador:browser.version(),resultados,errores_js:errores},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultados:'OK',navegador:browser.version()}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
