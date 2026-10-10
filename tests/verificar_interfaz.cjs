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
async function captura(page,archivo,fullPage=true){
  await page.mouse.move(0,0);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  await page.evaluate(async()=>await Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
  await page.screenshot({path:path.join(out,archivo),fullPage});
}
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
  const page=await contexto.newPage(),errores=[];await page.clock.install();page.on('pageerror',e=>errores.push(e.message));
  await page.goto(base);await page.getByRole('button',{name:'Yo elijo'}).waitFor();
  assert.equal(await page.locator('.lugares,.paisaje-tarjeta').count(),0);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight),true);
  const revisionInicial=(await vista(page)).revision,paisajes=(await vista(page)).opciones_habitat;
  for(let i=1;i<=8;i++){
    await page.clock.runFor(10001);const h=paisajes[i%8];
    assert.equal(await page.locator('.hero-paisaje').getAttribute('data-habitat'),h.id);
    assert.equal(await page.locator('.hero-ficha strong').textContent(),h.nombre);
    assert.equal(await page.locator('.ficha-numero').textContent(),`${String(i%8+1).padStart(2,'0')} / 08`);
  }
  assert.equal((await vista(page)).revision,revisionInicial);
  await page.getByRole('button',{name:'Siguiente paisaje',exact:true}).click();
  await page.clock.runFor(20000);assert.equal(await page.locator('.ficha-numero').textContent(),'02 / 08');
  await page.getByRole('button',{name:'Paisaje anterior',exact:true}).click();
  await page.getByRole('button',{name:'Reanudar paisajes',exact:true}).click();
  await page.getByRole('button',{name:'Preferencias',exact:true}).click();
  await page.clock.runFor(20000);assert.equal(await page.locator('.ficha-numero').textContent(),'01 / 08');
  const dialogoCerrado=page.evaluate(()=>new Promise(resolve=>document.getElementById('preferencias').addEventListener('close',()=>resolve(),{once:true})));
  await page.getByRole('button',{name:'Volver al juego',exact:true}).click();await dialogoCerrado;
  await page.clock.runFor(10001);assert.equal(await page.locator('.ficha-numero').textContent(),'02 / 08');
  await page.getByRole('button',{name:'Paisaje anterior',exact:true}).click();
  resultados.push({caso:'Ocho fondos rotan cada 10 segundos con nombre y contador sincronizados; pausa, navegación manual y Preferencias sin alterar la partida',resultado:'OK'});
  assert.equal(await page.locator('video,canvas').count(),0);
  await captura(page,'01_inicio.png');
  await page.setViewportSize({width:1920,height:1080});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);
  await captura(page,'08_inicio_panoramico.png');await page.setViewportSize({width:1280,height:1080});
  await page.getByRole('button',{name:'Preferencias'}).click();
  await page.locator('#retos').fill('1');await page.getByRole('button',{name:'Probar voz',exact:true}).click();
  assert.equal((await page.evaluate(()=>window.__voz.at(-1))).lang,'es-PE');
  await page.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await clicar(page,'Yo elijo','SELECCION_ANIMAL');
  assert.equal(await page.locator('.catalogo button').count(),48);
  await captura(page,'02_catalogo.png');
  const revisionCatalogo=(await vista(page)).revision,busqueda=page.getByRole('searchbox',{name:'Buscar animal'});
  await busqueda.fill('  PINGUINO  ');assert.equal(await page.locator('.catalogo button:visible').count(),1);
  assert.equal(await page.getByRole('button',{name:'Pingüino emperador',exact:true}).isVisible(),true);
  await busqueda.fill('animal inexistente');assert.equal(await page.locator('.catalogo button:visible').count(),0);assert.equal(await page.locator('.busqueda-vacia').isVisible(),true);
  await busqueda.fill('');assert.equal(await page.locator('.catalogo button:visible').count(),48);assert.equal(await page.locator('.busqueda-vacia').isVisible(),false);
  assert.equal((await vista(page)).revision,revisionCatalogo);
  resultados.push({caso:'Búsqueda de 48 animales: mayúsculas y tildes, sin resultados, restauración y sin cambiar la partida',resultado:'OK'});
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
  await captura(page,'03_reto_escritorio.png');
  // Los 95 recursos se decodifican en el navegador (PNG y SVG).
  const assetTest=await page.evaluate(async()=>{
    const v=await (await fetch('/api/vista')).json();
    const fallos=[],rutas=[...Object.values(v.pictogramas).map(p=>p.imagen),'/portada-selva.webp','/paisajes.webp',...Array.from({length:7},(_,i)=>`/fondos/H0${i+2}.webp`)];
    await Promise.all(rutas.map(ruta=>new Promise(resolve=>{const i=new Image();i.onload=()=>{if(!i.naturalWidth)fallos.push(ruta);resolve();};i.onerror=()=>{fallos.push(ruta);resolve();};i.src=ruta;})));return fallos;
  });assert.deepEqual(assetTest,[]);resultados.push({caso:'95 pictogramas y nueve imágenes decorativas decodificados sin errores; ocho fondos sin vídeo ni canvas',resultado:'OK'});
  // Revisar las representaciones de animales en una plancha para inspección visual.
  await page.evaluate(async()=>{
    const v=await (await fetch('/api/vista')).json();const main=document.getElementById('juego');main.replaceChildren();
    const h=document.createElement('h1');h.textContent='Revisión visual: 48 animales';main.append(h);const grid=document.createElement('div');grid.className='catalogo';main.append(grid);
    for(const a of v.catalogo_animales){const d=document.createElement('div');d.className='tarjeta';const im=document.createElement('img');im.src=v.pictogramas[a.pictograma_id].imagen;const t=document.createElement('span');t.textContent=a.nombre;d.append(im,t);grid.append(d);}
  });await captura(page,'04_revision_animales.png');
  // Vista estrecha real: sin desbordamiento horizontal, controles alcanzables.
  const movil=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await mockVoz(movil);const pm=await movil.newPage();pm.on('pageerror',e=>errores.push(e.message));await pm.goto(base);await pm.getByRole('button',{name:'El agente elige'}).waitFor();
  assert.equal(await pm.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);await captura(pm,'06_inicio_movil.png');
  await pm.getByRole('button',{name:'Preferencias'}).click();
  const dialogo=await pm.locator('dialog').boundingBox();assert.ok(dialogo.x>=0&&dialogo.x+dialogo.width<=390);
  await captura(pm,'07_preferencias_movil.png',false);await pm.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await clicar(pm,'El agente elige','ESPERANDO_RESPUESTA');await clicar(pm,'Ayuda');
  assert.equal(await pm.locator('.habitats button').count(),8);
  assert.equal(await pm.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await captura(pm,'05_reto_movil.png');
  const minimo=await pm.locator('button').evaluateAll(bs=>Math.min(...bs.map(b=>b.getBoundingClientRect().height).filter(h=>h>0)));assert.ok(minimo>=44);
  resultados.push({caso:'Pantalla móvil 390 × 844: inicio, preferencias y partida, ocho opciones, sin desbordamiento horizontal, botones de al menos 44 px',resultado:'OK'});
  // Teclado y movimiento reducido: inicio, búsqueda y selección sin ratón.
  const teclado=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'});await mockVoz(teclado);
  const pt=await teclado.newPage();await pt.clock.install();pt.on('pageerror',e=>errores.push(e.message));await pt.goto(base);await pt.getByRole('button',{name:'Yo elijo'}).waitFor();
  assert.equal(await pt.locator('.bienvenida').evaluate(el=>getComputedStyle(el).animationName),'none');
  await pt.clock.runFor(20000);assert.equal(await pt.locator('.ficha-numero').textContent(),'01 / 08');
  for(const [width,height] of [[320,568],[390,844],[650,390],[844,390],[768,900],[1024,600],[1024,768],[1280,720],[1920,1080]]){await pt.setViewportSize({width,height});assert.equal(await pt.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);for(const nombre of ['Yo elijo','El agente elige','Paisaje anterior','Siguiente paisaje']){const b=await pt.getByRole('button',{name:nombre,exact:true}).boundingBox();assert.ok(b.y>=0&&b.y+b.height<=height,`${nombre} fuera de pantalla ${width}x${height}`);}}
  await pt.setViewportSize({width:1280,height:900});
  for(let i=0;i<6;i++){await pt.keyboard.press('Tab');if(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')==='Yo elijo'))break;}
  assert.equal(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Yo elijo');await pt.keyboard.press('Enter');
  await pt.getByRole('searchbox',{name:'Buscar animal'}).waitFor();await pt.getByRole('searchbox',{name:'Buscar animal'}).focus();await pt.keyboard.type('jaguar');await pt.keyboard.press('Tab');
  assert.equal(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Jaguar');await pt.keyboard.press('Enter');await pt.getByRole('button',{name:'Ayuda',exact:true}).waitFor();
  assert.equal(await pt.locator('.habitats button').count(),8);assert.equal(await pt.getByRole('progressbar',{name:'Progreso de la partida'}).evaluate(el=>el.value),0);
  for(const ancho of [320,768,1024,1280]){await pt.setViewportSize({width:ancho,height:900});assert.equal(await pt.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
  resultados.push({caso:'Teclado: iniciar, buscar y elegir un animal; progreso accesible y preferencia de movimiento reducido',resultado:'OK'});
  resultados.push({caso:'Inicio en una pantalla entre 320 × 568 y 1920 × 1080, con botones visibles; partida sin desbordamiento horizontal',resultado:'OK'});
  // Ausencia de voces: la interfaz debe explicar la limitación y seguir funcionando.
  const sinvoz=await browser.newContext();await sinvoz.addInitScript(()=>Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[],addEventListener:()=>{},cancel:()=>{}},configurable:true}));
  const pv=await sinvoz.newPage();pv.on('pageerror',e=>errores.push(e.message));await pv.goto(base);await pv.getByRole('button',{name:'El agente elige'}).waitFor();await clicar(pv,'El agente elige','ESPERANDO_RESPUESTA');assert.match(await pv.locator('#aviso').textContent(),/No hay voz en español/);assert.equal(await pv.locator('.habitats button:enabled').count(),8);
  resultados.push({caso:'Dispositivo sin voz española: aviso visible, texto y pictogramas operativos',resultado:'OK'});
  // Selección automática de Google español cuando existe junto a voces locales.
  const google=await browser.newContext();await mockVoz(google);
  await google.addInitScript(()=>{window.speechSynthesis.getVoices=()=>[{voiceURI:'local',name:'Microsoft español',lang:'es-ES',localService:true},{voiceURI:'google',name:'Google español',lang:'es-ES',localService:false}];});
  const pg=await google.newPage();await pg.goto(base);await pg.getByRole('button',{name:'Yo elijo',exact:true}).waitFor();
  assert.equal(await pg.locator('#voces').inputValue(),'google');
  resultados.push({caso:'Google español tiene prioridad sobre otras voces españolas disponibles',resultado:'OK'});
  // La elección manual y el ritmo deben mantenerse sin un servicio de voz del servidor.
  await pg.getByRole('button',{name:'Preferencias',exact:true}).click();
  await pg.locator('#voces').selectOption('local');await pg.locator('#velocidad').selectOption('0.8');
  await pg.getByRole('button',{name:'Probar voz',exact:true}).click();
  assert.equal((await pg.evaluate(()=>window.__voz.at(-1))).rate,0.8);
  await pg.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await pg.getByRole('button',{name:'Preferencias',exact:true}).click();
  assert.equal(await pg.locator('#voces').inputValue(),'local');
  await pg.evaluate(()=>cargarVoces());assert.equal(await pg.locator('#voces').inputValue(),'local');
  assert.equal(await pg.locator('#voces option:disabled').count(),0);
  assert.equal(await pg.locator('#voces option').count(),2);
  await pg.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await clicar(pg,'El agente elige','ESPERANDO_RESPUESTA');
  const textoAntes=(await vista(pg)).respuesta.texto_voz;
  assert.equal((await pg.evaluate(()=>window.__voz.at(-1))).texto,textoAntes);
  const cancelaciones=await pg.evaluate(()=>window.__cancelaciones);
  await clicar(pg,'Pausar','PAUSADA');
  assert.ok(await pg.evaluate(n=>window.__cancelaciones>n,cancelaciones));
  await pg.getByRole('button',{name:'Preferencias',exact:true}).click();
  await pg.locator('#voz').uncheck();
  await pg.getByRole('button',{name:'Volver al juego',exact:true}).click();
  const lecturas=await pg.evaluate(()=>window.__voz.length);
  await clicar(pg,'Reanudar','ESPERANDO_RESPUESTA');
  assert.equal(await pg.evaluate(()=>window.__voz.length),lecturas);
  resultados.push({caso:'Preferencias de voz: selección manual conservada, ritmo, lectura exacta, cancelación al pausar y guía silenciada',resultado:'OK',alcance:'Síntesis simulada en navegador; no certifica sonido audible.'});
  // Página técnica de la misma cookie: solo lectura, modelo congelado.
  await page.goto(base+'/revision');await page.locator('#datos').filter({hasText:'parametros_congelados'}).waitFor();
  const tecnicos=JSON.parse(await page.locator('#datos').textContent());assert.equal(tecnicos.parametros_congelados,true);
  resultados.push({caso:'Consulta técnica separada y modelo congelado',resultado:'OK'});
  assert.deepEqual(errores,[]);
  fs.writeFileSync(path.join(out,'revision_navegador.json'),JSON.stringify({fecha:'2026-10-10',version:'3.3.1',navegador:browser.version(),resultados,errores_js:errores},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultados:'OK',navegador:browser.version()}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
