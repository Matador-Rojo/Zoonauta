/* Verificación en navegador real. Playwright solo es necesario para esta prueba.
   INTERFAZ_URL, PLAYWRIGHT_MODULE y CHROMIUM_EXECUTABLE son opciones de prueba. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL||'http://127.0.0.1:8000';
const out=process.env.INTERFAZ_SALIDA?path.resolve(process.env.INTERFAZ_SALIDA):path.resolve(__dirname,'../docs/interfaz');fs.mkdirSync(out,{recursive:true});
const resultados=[];
async function mockVoz(context,disponibles=true,vocesNativas=[]){
  await context.route('**/api/voz/config',async route=>{
    const r=await route.fetch(),d=await r.json();d.voces.forEach(v=>v.disponible=disponibles);await route.fulfill({json:d});
  });
  await context.route('**/api/voz',async route=>{
    const b=Buffer.alloc(244);b.write('RIFF');b.writeUInt32LE(236,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(22050,24);b.writeUInt32LE(44100,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(200,40);
    await route.fulfill({contentType:'audio/wav',body:b});
  });
  await context.addInitScript(vocesNativas=>{
    const sintesis=new EventTarget();
    let lista=vocesNativas;
    window.__vozNativa=[];window.__cancelacionesNativas=0;
    sintesis.getVoices=()=>lista;
    sintesis.speak=u=>{window.__nativaActual=u;window.__vozNativa.push({texto:u.text,voz:u.voice.name,lang:u.lang,rate:u.rate});};
    sintesis.cancel=()=>{window.__cancelacionesNativas++;const antigua=window.__nativaActual;window.__nativaActual=null;queueMicrotask(()=>antigua?.onerror?.({error:'canceled'}));};
    window.__actualizarVocesNativas=v=>{lista=v;sintesis.dispatchEvent(new Event('voiceschanged'));};
    Object.defineProperty(window,'speechSynthesis',{value:sintesis,configurable:true});
    window.SpeechSynthesisUtterance=class{constructor(texto){this.text=texto;}};
    window.__voz=[];window.__cancelaciones=0;window.__pedido=null;
    const original=window.fetch.bind(window);
    window.fetch=async(url,opciones)=>{
      const r=await original(url,opciones);
      if(url==='/api/voz'&&r.ok){
        const e=JSON.parse(opciones.body),v=await (await original('/api/vista')).json();
        window.__pedido={...e,lang:e.idioma,texto:e.prueba?(e.idioma==='es'?'Hola. Vamos a descubrir dónde viven los animales.':'Olá. Vamos descobrir onde os animais vivem.'):e.contexto==='modalidad'?(e.idioma==='es'?'¿Quién elige el animal?':'Quem escolhe o animal?'):v.respuesta.texto_voz};
      }return r;
    };
    window.Audio=class{
      constructor(url){this.src=url;}
      async play(){window.__voz.push({...window.__pedido,rate:this.playbackRate});}
      pause(){window.__cancelaciones++;}
      removeAttribute(){this.src='';}
    };
  },vocesNativas);
}
async function vista(page){return page.evaluate(async()=>await (await fetch('/api/vista')).json());}
async function comprobarTransparencia(locator){
  const estilos=await locator.evaluateAll(imgs=>imgs.map(i=>{const s=getComputedStyle(i);return {fondo:s.backgroundColor,borde:s.borderTopWidth,relleno:s.paddingTop};}));
  assert.ok(estilos.length>0);
  assert.ok(estilos.every(s=>s.fondo==='rgba(0, 0, 0, 0)'&&s.borde==='0px'&&s.relleno==='0px'));
}
async function comprobarPictogramas(page){
  const v=await vista(page);
  assert.deepEqual(await page.locator('.secuencia img').evaluateAll(imgs=>imgs.map(i=>i.getAttribute('src'))),v.respuesta.pictogramas.map(id=>v.pictogramas[id].imagen));
  assert.equal(await page.locator('.secuencia .animal-foto').count(),0);
  await comprobarTransparencia(page.locator('.secuencia img'));
  assert.ok((await page.locator('.secuencia img').evaluateAll(imgs=>imgs.map(i=>i.getBoundingClientRect().width))).every(w=>w>=84));
}
async function comprobarControles(page){
  const v=await vista(page),ids={Pista:'P_AYUDA',Repetir:'P_REPETIR',Pausar:'P_PAUSAR',Reanudar:'P_REANUDAR',Continuar:'P_CONTINUAR',Salir:'P_SALIR'};
  for(const b of await page.locator('.acciones button').all()){
    const nombre=await b.getAttribute('aria-label');
    assert.equal(await b.locator('img').getAttribute('src'),v.pictogramas[ids[nombre]].imagen);
    assert.ok(await b.locator('img').evaluate(i=>i.getBoundingClientRect().width>=56));
    await comprobarTransparencia(b.locator('img'));
  }
}
async function comprobarCierre(page){
  const v=await vista(page),anterior=page.viewportSize();
  assert.equal(await page.locator('.cierre-ilustracion').count(),1);
  assert.equal(await page.locator('.cierre-visual .etiqueta').textContent(),v.idioma==='es'?'Tu guía':'Seu guia');
  assert.equal(await page.locator('.cierre-leyenda').textContent(),v.fase==='PAUSADA'?(v.idioma==='es'?'A tu ritmo':'No seu ritmo'):(v.idioma==='es'?'Gracias por jugar':'Obrigado por jogar'));
  assert.equal(await page.locator('.cierre-ilustracion').getAttribute('src'),`/ilustraciones/${v.fase==='PAUSADA'?'robot_pausa':'robot_despedida'}.webp`);
  assert.equal(await page.locator('.cierre-resumen progress').getAttribute('value'),String(v.progreso.completados));
  assert.equal(await page.locator('.cierre-resumen progress').getAttribute('max'),String(v.progreso.total));
  for(const [width,height] of [[1920,988],[1366,768],[1280,720],[1024,768],[390,844]]){
    await page.setViewportSize({width,height});
    const m=await page.evaluate(()=>{
      const rect=s=>document.querySelector(s).getBoundingClientRect(),c=rect('.cierre'),i=rect('.cierre-ilustracion'),n=rect('.cierre-leyenda'),v=rect('.cierre-visual'),t=rect('.cierre-contenido'),b=rect('.cierre-contenido>.accion,.cierre-contenido .acciones button');
      return {sinDesborde:document.documentElement.scrollWidth<=innerWidth,
       completa:i.left>=v.left&&i.right<=v.right&&i.bottom<=n.top&&n.bottom<=v.bottom,
       proporciones:getComputedStyle(document.querySelector('.cierre-ilustracion')).objectFit==='contain',
       separados:innerWidth>850?v.right<=t.left:v.bottom<=t.top,
       control:b.height>=44&&b.left>=c.left&&b.right<=c.right,
       escritorio:innerWidth<=850||document.documentElement.scrollHeight<=innerHeight,
       centrado:innerWidth<=850||Math.abs(c.top+c.height/2-innerHeight/2)<2};
    });assert.ok(Object.values(m).every(Boolean),JSON.stringify({width,height,...m}));
    if(width===390)await captura(page,'cierre_'+v.fase.toLowerCase()+'_'+v.idioma+'_movil.png');
  }
  await page.setViewportSize(anterior);
}
async function comprobarTablero(page){
  const anterior=page.viewportSize();
  for(const [width,height] of [[1024,768],[1280,720],[1366,768],[1440,900],[1920,988],[1920,1080]]){
    await page.setViewportSize({width,height});
    const m=await page.evaluate(()=>{
      const guia=document.querySelector('.mesa').getBoundingClientRect();
      const habitats=document.querySelector('.habitats').getBoundingClientRect();
      const animal=document.querySelector('.companero').getBoundingClientRect();
      const controles=document.querySelector('.panel-animal .acciones').getBoundingClientRect();
      const retrato=document.querySelector('.animal-retrato').getBoundingClientRect();
      const nombre=document.querySelector('.animal-actual strong').getBoundingClientRect();
      const tablero=document.querySelector('.tablero').getBoundingClientRect();
      const fondo=getComputedStyle(document.body);
      return {sinScroll:document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight,
        alineados:Math.abs(guia.left-habitats.left)<1&&Math.abs(guia.right-habitats.right)<1,
        lateral:controles.top>=animal.bottom&&controles.right<=habitats.left,
        espacio:document.querySelector('#juego').getBoundingClientRect().width>=innerWidth-1&&Math.abs(tablero.bottom-(innerHeight-24))<1,
        animalGrande:retrato.width>=200&&retrato.height>=180&&nombre.top>=retrato.bottom&&nombre.bottom<=animal.bottom&&getComputedStyle(document.querySelector('.animal-retrato img')).objectFit==='contain',
        fondoContinuo:document.body.getBoundingClientRect().height>=innerHeight&&fondo.backgroundRepeat.split(',').every(v=>v.trim()==='no-repeat')&&fondo.backgroundAttachment.split(',').every(v=>v.trim()==='fixed'),
        visibles:[...document.querySelectorAll('.habitats button,.panel-animal button')].every(b=>{const r=b.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.height>=44;})};
    });
    assert.ok(Object.values(m).every(Boolean),`Tablero fuera de pantalla ${width}x${height}: ${JSON.stringify(m)}`);
  }
  for(const [width,height] of [[1024,600],[900,500]]){
    await page.setViewportSize({width,height});
    assert.equal(await page.evaluate(()=>{const a=document.querySelector('.companero').getBoundingClientRect(),i=document.querySelector('.animal-retrato').getBoundingClientRect(),n=document.querySelector('.animal-actual strong').getBoundingClientRect();return document.documentElement.scrollWidth<=innerWidth&&i.height>=180&&n.top>=i.bottom&&n.bottom<=a.bottom;}),true,'Una ventana baja debe permitir scroll sin recortar el animal o su nombre');
  }
  await page.setViewportSize(anterior);
}
async function captura(page,archivo,fullPage=true){
  await page.mouse.move(0,0);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  await page.evaluate(async()=>await Promise.all([...document.images].map(i=>i.decode())));
  await page.evaluate(async()=>await Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
  await page.screenshot({path:path.join(out,archivo),fullPage});
}
async function clicar(page,texto,fase){
  if(['Yo elijo','El agente elige','Eu escolho','O agente escolhe'].includes(texto)&&!await page.getByRole('button',{name:texto,exact:true}).isVisible())await page.getByRole('button',{name:/^(Comenzar|Começar)$/}).click();
  const antes=(await vista(page)).revision;
  await page.getByRole('button',{name:texto,exact:true}).click();
  await page.waitForFunction(async rev=>(await (await fetch('/api/vista')).json()).revision>rev,antes);
  if(fase)await page.waitForFunction(async f=>(await (await fetch('/api/vista')).json()).fase===f,fase);
  await page.waitForFunction(()=>document.getElementById('juego').getAttribute('aria-busy')==='false');
  const inicio=await page.evaluate(()=>document.body.dataset.fase==='INICIO');
  assert.equal(await page.locator('.cabecera').isVisible(),inicio);
  assert.equal(await page.locator('.creditos').evaluate(e=>e.hidden),!inicio);
  if(!inicio)assert.equal(await page.locator('.creditos').isVisible(),false);
  if(!['Pausar','Comenzar otra partida','Começar outra partida'].includes(texto))await page.waitForFunction(async()=>{
    if(!document.getElementById('voz').checked||document.getElementById('probar-voz').disabled)return true;
    const v=await (await fetch('/api/vista')).json();return window.__voz.at(-1)?.revision===v.revision;
  });
}

(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 try{
  let contexto=await browser.newContext({viewport:{width:1280,height:1080}});await mockVoz(contexto);
  let page=await contexto.newPage();const errores=[];await page.clock.install();page.on('pageerror',e=>errores.push(e.message));
  await page.goto(base);await page.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  assert.equal(await page.locator('.entrada button:visible').count(),1);
  assert.equal(await page.getByRole('button',{name:'Yo elijo',exact:true}).isVisible(),false);
  const antesSelector=await vista(page);
  await page.getByRole('button',{name:'Comenzar',exact:true}).click();
  assert.equal(await page.getByRole('dialog',{name:'¿Quién elige el animal?',exact:true}).isVisible(),true);
  await page.waitForFunction(()=>window.__voz.at(-1)?.contexto==='modalidad');
  assert.equal(await page.evaluate(()=>window.__voz.at(-1).texto),'¿Quién elige el animal?');
  await captura(page,'15_selector_modalidad.png',false);
  assert.deepEqual(await vista(page),antesSelector);
  const paisajeSelector=await page.locator('.ficha-numero').textContent();
  await page.clock.runFor(20000);assert.equal(await page.locator('.ficha-numero').textContent(),paisajeSelector);
  await page.getByRole('button',{name:'Volver al inicio',exact:true}).click();
  assert.equal(await page.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Comenzar');
  await page.getByRole('button',{name:'Comenzar',exact:true}).click();await page.keyboard.press('Escape');
  assert.equal(await page.locator('#elegir-modalidad').isVisible(),false);
  assert.deepEqual(await vista(page),antesSelector);
  resultados.push({caso:'Un solo botón Comenzar en la portada; después se elige jugador o agente en diálogo con pictogramas. Abrir, volver y Escape no crean una partida; el selector suspende el carrusel y devuelve el foco',resultado:'OK'});
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
  await page.getByRole('button',{name:'Pausar paisajes',exact:true}).click();
  await page.clock.runFor(20000);assert.equal(await page.locator('.ficha-numero').textContent(),'01 / 08');
  await page.getByRole('button',{name:'Reanudar paisajes',exact:true}).click();
  await page.clock.runFor(10001);assert.equal(await page.locator('.ficha-numero').textContent(),'02 / 08');
  await page.getByRole('button',{name:'Pausar paisajes',exact:true}).click();
  await page.getByRole('button',{name:'Siguiente paisaje',exact:true}).click();
  assert.equal(await page.locator('.ficha-numero').textContent(),'03 / 08');
  await page.getByRole('button',{name:'Pausar paisajes',exact:true}).waitFor();
  await page.clock.runFor(9000);assert.equal(await page.locator('.ficha-numero').textContent(),'03 / 08');
  await page.clock.runFor(1001);assert.equal(await page.locator('.ficha-numero').textContent(),'04 / 08');
  await page.getByRole('button',{name:'Pausar paisajes',exact:true}).click();
  await page.getByRole('button',{name:'Paisaje anterior',exact:true}).click();
  await page.clock.runFor(10001);assert.equal(await page.locator('.ficha-numero').textContent(),'04 / 08');
  await page.getByRole('button',{name:'Preferencias',exact:true}).click();
  await page.clock.runFor(20000);assert.equal(await page.locator('.ficha-numero').textContent(),'04 / 08');
  const dialogoCerrado=page.evaluate(()=>new Promise(resolve=>document.getElementById('preferencias').addEventListener('close',()=>resolve(),{once:true})));
  await page.getByRole('button',{name:'Volver al juego',exact:true}).click();await dialogoCerrado;
  await page.clock.runFor(10001);assert.equal(await page.locator('.ficha-numero').textContent(),'05 / 08');
  await page.getByRole('button',{name:'Paisaje anterior',exact:true}).click();
  assert.equal((await vista(page)).revision,revisionInicial);
  resultados.push({caso:'Ocho fondos rotan cada 10 segundos; pausa solo por botón, play y ambas flechas reanudan y reinician el intervalo; Preferencias suspende sin alterar la partida',resultado:'OK'});
  assert.equal(await page.locator('video,canvas').count(),0);
  await captura(page,'01_inicio.png');
  await page.setViewportSize({width:1920,height:1080});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);
  await captura(page,'08_inicio_panoramico.png');await page.setViewportSize({width:1280,height:1080});
  await page.getByRole('button',{name:'Preferencias'}).click();
  await page.locator('#retos').fill('1');await page.getByRole('button',{name:'Probar voz',exact:true}).click();
  await page.waitForFunction(()=>window.__voz.length>0);assert.equal((await page.evaluate(()=>window.__voz.at(-1))).lang,'es');
  await page.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await clicar(page,'Yo elijo','SELECCION_ANIMAL');
  assert.equal(await page.locator('.catalogo button').count(),6);
  assert.equal(await page.getByRole('button',{name:'Anteriores',exact:true}).isDisabled(),true);
  await captura(page,'02_catalogo.png');
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await captura(page,'02_catalogo_movil.png');await page.setViewportSize({width:1280,height:1080});
  const revisionCatalogo=(await vista(page)).revision,busqueda=page.getByRole('searchbox',{name:'Buscar animal'});
  const encontrados=[];
  for(let pagina=1;pagina<=8;pagina++){
    assert.equal(await page.locator('.catalogo-pagina').textContent(),`Página ${pagina} de 8`);
    const nombres=await page.locator('.catalogo button').evaluateAll(btns=>btns.map(b=>b.getAttribute('aria-label')));
    assert.equal(nombres.length,6);encontrados.push(...nombres);
    const v=await vista(page);
    for(const b of await page.locator('.catalogo button').all()){
      const nombre=await b.getAttribute('aria-label'),animal=v.catalogo_animales.find(a=>a.nombre===nombre);
      assert.equal(await b.locator('img').count(),1);
      assert.equal(await b.locator('.animal-ilustracion').getAttribute('src'),v.pictogramas[animal.pictograma_id].imagen);
    }
    if(pagina<8)await page.getByRole('button',{name:'Siguientes',exact:true}).click();
  }
  assert.equal(new Set(encontrados).size,48);
  assert.deepEqual(encontrados,(await vista(page)).catalogo_animales.map(a=>a.nombre));
  assert.equal((await vista(page)).revision,revisionCatalogo);
  assert.equal(await page.getByRole('button',{name:'Siguientes',exact:true}).isDisabled(),true);
  await page.getByRole('button',{name:'Anteriores',exact:true}).click();
  assert.equal(await page.locator('.catalogo-pagina').textContent(),'Página 7 de 8');
  await clicar(page,'Pausar','PAUSADA');await clicar(page,'Reanudar','SELECCION_ANIMAL');
  assert.equal(await page.locator('.catalogo-pagina').textContent(),'Página 7 de 8');
  const revisionBusqueda=(await vista(page)).revision;
  await busqueda.fill('  PINGUINO  ');assert.equal(await page.locator('.catalogo button:visible').count(),1);
  assert.equal(await page.locator('.catalogo-pagina').textContent(),'Página 1 de 1');
  assert.equal(await page.getByRole('button',{name:'Pingüino emperador',exact:true}).isVisible(),true);
  await busqueda.fill('animal inexistente');assert.equal(await page.locator('.catalogo button:visible').count(),0);assert.equal(await page.locator('.busqueda-vacia').isVisible(),true);assert.equal(await page.locator('.catalogo-paginacion').isVisible(),false);
  await busqueda.fill('');assert.equal(await page.locator('.catalogo button:visible').count(),6);assert.equal(await page.locator('.busqueda-vacia').isVisible(),false);
  assert.equal(await page.locator('.catalogo-pagina').textContent(),'Página 1 de 8');
  assert.equal((await vista(page)).revision,revisionBusqueda);
  resultados.push({caso:'Catálogo de seis por página: acceso a los 48 animales sin duplicados, límites, retroceso, pausa conserva página, búsqueda global con tildes y sin resultados; navegar y buscar no cambia la partida',resultado:'OK'});
  await busqueda.fill('capibara');
  for(const ancho of [320,390,768,1024,1280]){
    await page.setViewportSize({width:ancho,height:1080});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const posiciones=await page.locator('.catalogo .animal-imagenes img').evaluateAll(imgs=>imgs.map(i=>{
      const r=i.getBoundingClientRect(),p=i.closest('button').getBoundingClientRect(),nombre=i.closest('button').querySelector('span:not(.animal-numero)').getBoundingClientRect();
      return {ancho:r.width,dentro:r.left>=p.left&&r.right<=p.right&&r.top>=p.top&&r.bottom<nombre.top};
    }));
    assert.ok(posiciones.every(m=>m.ancho>=96&&m.dentro));
  }
  await page.setViewportSize({width:1280,height:1080});
  await clicar(page,'Capibara o ronsoco','ESPERANDO_RESPUESTA');
  await comprobarPictogramas(page);
  await comprobarControles(page);
  assert.equal(await page.locator('.animal-retrato img').getAttribute('src'),(await vista(page)).pictogramas.P_A31.imagen);
  assert.equal(await page.locator('.habitats button').count(),8);
  for(const ancho of [320,390,768,1024,1280]){
    await page.setViewportSize({width:ancho,height:1080});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.equal(await page.locator('.habitats .tarjeta img').count(),0);
    assert.deepEqual(await page.locator('.habitats .habitat-numero').allTextContents(),['01','02','03','04','05','06','07','08']);
    const numeros=await page.locator('.habitats .habitat-numero').evaluateAll(es=>es.map(e=>{const r=e.getBoundingClientRect(),p=e.closest('button').getBoundingClientRect();return r.left>=p.left&&r.right<=p.right&&r.top>=p.top&&r.bottom<=p.bottom&&r.left>(p.left+p.right)/2&&r.bottom<(p.top+p.bottom)/2;}));
    assert.ok(numeros.every(Boolean));
    const medidas=await page.locator('.habitats .tarjeta .paisaje').evaluateAll(imgs=>imgs.map(i=>{const r=i.getBoundingClientRect(),p=i.parentElement.getBoundingClientRect();return {ancho:r.width,alto:r.height,dentro:r.left>=p.left&&r.right<=p.right,fondo:getComputedStyle(i).backgroundImage};}));
    assert.equal(medidas.length,8);assert.ok(medidas.every(m=>m.ancho>=48&&m.alto>=125&&m.dentro&&m.fondo.includes('/habitats/')));
    const ubicacion=await page.locator('.habitats').evaluate(e=>{const r=e.getBoundingClientRect(),t=e.closest('.tablero'),g=t.querySelector('.mesa').getBoundingClientRect(),c=t.querySelector('.acciones').getBoundingClientRect();return innerWidth>850?Math.abs(r.left-g.left)<1&&Math.abs(r.right-g.right)<1&&c.right<=r.left:r.top>=c.bottom;});
    assert.ok(ubicacion);
  }
  await comprobarTablero(page);
  await page.setViewportSize({width:1280,height:1080});
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  await clicar(page,'Pista');const ayuda=(await vista(page)).respuesta;
  await comprobarTablero(page);
  await comprobarPictogramas(page);
  const textoVoz=(await page.evaluate(()=>window.__voz.at(-1))).texto;assert.equal(textoVoz,ayuda.texto_voz);
  await clicar(page,'Repetir');assert.deepEqual((await vista(page)).respuesta,ayuda);assert.equal((await page.evaluate(()=>window.__voz.at(-1))).texto,textoVoz);
  const r=(await vista(page)).revision;await page.reload();await page.getByRole('button',{name:'Pista',exact:true}).waitFor();assert.equal((await vista(page)).revision,r);assert.equal(await page.evaluate(()=>window.__voz.length),0);
  await clicar(page,'Repetir');await clicar(page,'Pausar','PAUSADA');assert.equal(await page.locator('.habitats').count(),0);assert.ok(await page.evaluate(()=>window.__cancelaciones)>0);
  await comprobarPictogramas(page);await comprobarControles(page);await comprobarCierre(page);await captura(page,'16_pausa_pictogramas.png');
  await clicar(page,'Reanudar','ESPERANDO_RESPUESTA');assert.deepEqual((await vista(page)).respuesta,ayuda);
  await clicar(page,'Desierto cálido');assert.equal((await vista(page)).respuesta.tipo_respuesta,'NEUTRAL');assert.equal((await vista(page)).progreso.completados,0);
  const automatica=(await vista(page)).respuesta;
  assert.equal(automatica.nivel,2);assert.ok(automatica.texto_voz.startsWith('Vamos a buscar otro lugar.'));
  await comprobarTablero(page);
  await comprobarPictogramas(page);await captura(page,'17_pista_automatica.png');
  await clicar(page,'Repetir');assert.deepEqual((await vista(page)).respuesta,automatica);
  await clicar(page,'Selva tropical','RETO_RESUELTO');assert.equal((await vista(page)).progreso.completados,1);assert.equal(await page.locator('.habitats button:enabled').count(),0);
  await comprobarTablero(page);
  await clicar(page,'Continuar','COMPLETADA');
  await comprobarPictogramas(page);
  assert.equal(await page.getByRole('button',{name:'Comenzar otra partida',exact:true}).locator('img').getAttribute('src'),(await vista(page)).pictogramas.P_INICIAR.imagen);
  await comprobarTransparencia(page.getByRole('button',{name:'Comenzar otra partida',exact:true}).locator('img'));
  assert.equal(await page.locator('.cierre-resumen strong').textContent(),'1 / 1');
  await comprobarCierre(page);await captura(page,'13_cierre_completado.png');
  const antesReinicio=await page.evaluate(()=>window.__voz.length);
  await clicar(page,'Comenzar otra partida','INICIO');
  await page.clock.runFor(1000);assert.equal(await page.evaluate(()=>window.__voz.length),antesReinicio);
  await page.getByRole('button',{name:'Comenzar',exact:true}).click();
  await page.waitForFunction(n=>window.__voz.length===n+1,antesReinicio);
  assert.equal(await page.evaluate(()=>window.__voz.at(-1).texto),'¿Quién elige el animal?');
  const cancelacionesModal=await page.evaluate(()=>window.__cancelaciones);
  await page.keyboard.press('Escape');await page.waitForFunction(n=>window.__cancelaciones>n,cancelacionesModal);
  await clicar(page,'El agente elige','ESPERANDO_RESPUESTA');assert.equal(await page.locator('.habitats button').count(),8);
  await clicar(page,'Salir','ABANDONADA');
  await comprobarPictogramas(page);
  assert.equal(await page.locator('.cierre-resumen strong').textContent(),'0 / 8');
  await comprobarCierre(page);await captura(page,'14_cierre_salida.png');
  resultados.push({caso:'Robot de despedida en cierre completado/abandonado y robot sentado en pausa; etiquetas en español y portugués, progreso real accesible, imágenes completas, centrado sin scroll en cuatro escritorios y contenido completo sin desborde en móvil',resultado:'OK'});
  resultados.push({caso:'Recorrido de jugador y agente, 48 animales, ocho opciones, pista, repetición, pausa, pendiente neutral, confirmación, cierre y nueva partida; tablero de ancho completo que ocupa la altura disponible, animal de al menos 200 × 180 px con nombre debajo y sin recorte, fondo continuo, hábitats alineados con la guía, controles bajo el animal en dos filas y números 01–08. Pregunta, pista, apoyo neutral y confirmación sin scroll en seis resoluciones de 1024 × 768 a 1920 × 1080; cabecera y Preferencias solo en inicio',resultado:'OK'});
  resultados.push({caso:'Apoyo pictográfico: controles de 56 px, preguntas/pistas de al menos 84 px, secuencias de pausa/cierre e Iniciar sin fondos ni bordes; una selección pendiente ofrece pista automática y Repetir conserva el contenido',resultado:'OK'});
  resultados.push({caso:'Actualización del navegador conserva sesión sin repetir eventos ni audio',resultado:'OK'});
  resultados.push({caso:'Nueva partida vuelve a la portada sin voz; abrir el selector lee su pregunta exacta y cerrarlo cancela la lectura, sin cambiar el estado del juego',resultado:'OK'});
  resultados.push({caso:'Audio local español: texto exacto, repetición y cancelación',resultado:'OK',alcance:'API WAV y reproductor controlados; no certifica sonido audible ni comprensión.'});
  // Notificaciones independientes sin desplazar la portada ni alterar la partida.
  // Liberar imágenes, audio simulado y reloj del escenario anterior. La cookie
  // conserva la partida para continuar comprobándola en un contexto nuevo.
  const sesionInicial=await contexto.storageState();await contexto.close();
  console.log('Recorridos iniciales completos; comprobando avisos.');
  const avisos=await browser.newContext({viewport:{width:1366,height:768}});await mockVoz(avisos);
  const pa=await avisos.newPage();pa.on('pageerror',e=>errores.push(e.message));
  await pa.clock.install({time:new Date('2026-10-11T00:00:00Z')});await pa.clock.pauseAt(new Date('2026-10-11T00:00:01Z'));
  await pa.goto(base);await pa.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  const tarjetas=pa.locator('.notificacion'),cerrar=pa.locator('.notificacion-cerrar');
  const vaciar=async()=>{while(await tarjetas.count())await cerrar.last().click();};
  const comprobarAvisos=async()=>{
    assert.equal(await pa.locator('#aviso').isVisible(),true);
    const m=await pa.locator('#aviso').evaluate(e=>{
      const r=e.getBoundingClientRect(),cs=[...e.children].map(c=>{const t=c.getBoundingClientRect(),b=c.querySelector('button').getBoundingClientRect();return {w:t.width,arriba:t.top,abajo:t.bottom,completa:t.top>=22&&t.bottom<=innerHeight-22&&b.top>=0&&b.right<=innerWidth,boton:b.width>=44&&b.height>=44,circular:Math.abs(b.x+b.width/2-t.right)<2&&Math.abs(b.y+b.height/2-t.top)<2};});
      return {right:innerWidth-r.right,bottom:innerHeight-r.bottom,sinDesborde:document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight,popover:e.matches(':popover-open'),sinScroll:e.scrollHeight===e.clientHeight&&e.scrollWidth===e.clientWidth&&getComputedStyle(e).overflow==='visible',cs};
    });
    assert.ok(m.right>=11&&m.right<=13&&m.bottom>=11&&m.bottom<=13&&m.sinDesborde&&m.popover&&m.sinScroll&&m.cs.length<=3,JSON.stringify(m));
    assert.ok(m.cs.every(c=>c.w<=260&&c.completa&&c.boton&&c.circular),JSON.stringify(m));
    for(let i=1;i<m.cs.length;i++)assert.ok(m.cs[i-1].abajo<m.cs[i].arriba,'No se superponen');
  };
  for(const idioma of ['es','pt-BR']){
    await pa.locator('#ajustes').click();await pa.locator('#idioma').selectOption(idioma);
    await pa.waitForFunction(i=>document.documentElement.lang===i,idioma);
    await pa.locator('.creditos-ajustes summary').click();
    assert.equal(await pa.locator('.creditos-version').textContent(),'Zoonauta 4.4');
    await captura(pa,'creditos_'+idioma+'.png',false);
    await pa.locator('.creditos-ajustes summary').click();
    const antesAvisos=await vista(pa),vozAntes=await pa.evaluate(()=>window.__voz.length);
    await pa.locator('#retos').fill('50');await pa.locator('#retos').press('Tab');await comprobarAvisos();
    assert.equal(await tarjetas.last().locator('.notificacion-texto').textContent(),idioma==='es'?'Escribe un número entero del 1 al 48.':'Digite um número inteiro de 1 a 48.');
    assert.equal(await cerrar.last().getAttribute('aria-label'),idioma==='es'?'Cerrar notificación':'Fechar notificação');
    await captura(pa,'notificacion_preferencias_'+idioma+'.png',false);
    await pa.clock.runFor(7999);assert.equal(await tarjetas.count(),1);
    await pa.clock.runFor(1);assert.equal(await tarjetas.count(),0);
    await pa.locator('#cerrar-preferencias').click();
    const comenzar=pa.getByRole('button',{name:idioma==='es'?'Comenzar':'Começar',exact:true});
    for(const valor of ['50','0','-1','','1.5']){
      await pa.locator('#ajustes').click();await pa.locator('#retos').fill(valor);await pa.locator('#cerrar-preferencias').click();
      await comenzar.click();await comprobarAvisos();
      assert.equal(await pa.locator('#elegir-modalidad').isVisible(),false);
      assert.equal(await tarjetas.last().locator('.notificacion-texto').textContent(),idioma==='es'?'Para comenzar, abre Preferencias y escribe un número entero del 1 al 48.':'Para começar, abra Preferências e digite um número inteiro de 1 a 48.');
      assert.deepEqual(await vista(pa),antesAvisos);assert.equal(await pa.evaluate(()=>window.__voz.length),vozAntes);
      await vaciar();assert.equal(await pa.locator('#aviso').isVisible(),false);
    }
    await comenzar.click();const yPrimero=(await tarjetas.first().boundingBox()).y;
    await pa.clock.runFor(4000);await comenzar.click();assert.equal(await tarjetas.count(),2);
    assert.ok((await tarjetas.first().boundingBox()).y<yPrimero,'El anterior sube al llegar otro');
    await comprobarAvisos();await captura(pa,'avisos_apilados_'+idioma+'.png',false);
    await pa.clock.runFor(4000);assert.equal(await tarjetas.count(),1);
    await pa.clock.runFor(3999);assert.equal(await tarjetas.count(),1);
    await pa.clock.runFor(1);assert.equal(await tarjetas.count(),0);
    await comenzar.click();await pa.locator('#ajustes').click();await comprobarAvisos();
    assert.equal(await pa.locator('#aviso').evaluate(e=>e.parentElement.id),'preferencias');
    // Un error real del reproductor se acumula con la advertencia existente.
    await pa.evaluate(idioma=>{window.Audio.prototype.play=async()=>{throw new Error(idioma==='es'?'No se pudo reproducir la voz.':'Não foi possível reproduzir a voz.');};},idioma);
    await pa.locator('#probar-voz').click();await pa.locator('.notificacion[data-tipo="error"]').waitFor();
    assert.equal(await tarjetas.count(),2);await comprobarAvisos();
    const colores=await tarjetas.evaluateAll(cs=>cs.map(c=>{const s=getComputedStyle(c);return {borde:s.borderTopColor,fondo:s.backgroundColor};}));
    assert.notEqual(colores[0].borde,colores[1].borde);assert.equal(colores[0].fondo,colores[1].fondo);
    assert.equal(colores[0].fondo,'rgb(20, 32, 30)');
    await captura(pa,'avisos_tipos_'+idioma+'.png',false);
    await cerrar.first().focus();await pa.keyboard.press('Enter');assert.equal(await tarjetas.count(),1);
    await cerrar.last().focus();await pa.keyboard.press(' ');assert.equal(await tarjetas.count(),0);
    await pa.locator('#cerrar-preferencias').click();await comenzar.click();await comenzar.click();
    for(const [width,height] of [[320,568],[390,844],[1366,768]]){
      await pa.setViewportSize({width,height});await comprobarAvisos();
      await captura(pa,'notificacion_inicio_'+idioma+'_'+width+'.png',false);
    }
    await vaciar();
    await pa.setViewportSize({width:1366,height:768});
    const descartados=[];
    for(let i=0;i<8;i++){
      if(i)await pa.clock.runFor(500);
      if(await tarjetas.count()===3)descartados.push(await tarjetas.first().elementHandle());
      await comenzar.click();assert.equal(await tarjetas.count(),Math.min(i+1,3));await comprobarAvisos();
      for(const viejo of descartados)assert.equal(await viejo.evaluate(e=>e.isConnected),false,'El más antiguo sale de la pila');
    }
    await captura(pa,'limite_avisos_'+idioma+'_escritorio.png',false);
    // Los tres conservados llegan a ocho segundos desde su propia creación.
    await pa.clock.runFor(6999);assert.equal(await tarjetas.count(),3);
    await pa.clock.runFor(1);assert.equal(await tarjetas.count(),2);
    await pa.clock.runFor(500);assert.equal(await tarjetas.count(),1);
    await pa.clock.runFor(500);assert.equal(await tarjetas.count(),0);
    for(let i=0;i<3;i++)await comenzar.click();
    const retenidos=await tarjetas.elementHandles(),ultimo=retenidos.at(-1);
    await pa.setViewportSize({width:320,height:390});await comprobarAvisos();
    assert.ok(await tarjetas.count()<3,'Una ventana baja reduce la pila');
    assert.equal(await ultimo.evaluate(e=>e.isConnected),true,'Conserva el más reciente');
    assert.equal(await retenidos[0].evaluate(e=>e.isConnected),false);
    await captura(pa,'limite_avisos_'+idioma+'_ventana_baja.png',false);
    await pa.setViewportSize({width:320,height:568});
    for(let i=0;i<8;i++){await comenzar.click();await comprobarAvisos();}
    await captura(pa,'limite_avisos_'+idioma+'_movil.png',false);
    await pa.setViewportSize({width:1366,height:768});await comprobarAvisos();
    await pa.clock.runFor(8000);assert.equal(await tarjetas.count(),0);
    await comenzar.click();
    assert.equal(await pa.locator('.hero-ficha button').first().isEnabled(),true);
    await pa.locator('.hero-ficha button').first().click();assert.equal(await tarjetas.count(),1);
    await pa.locator('#ajustes').click();await pa.locator('#retos').fill('1');await pa.locator('#retos').press('Tab');assert.equal(await tarjetas.count(),0);
    // Restablecer el reproductor controlado para el diálogo de modalidad.
    await pa.evaluate(()=>{window.Audio.prototype.play=async function(){window.__voz.push({...window.__pedido,rate:this.playbackRate});};});
    await pa.locator('#cerrar-preferencias').click();await comenzar.click();await pa.locator('#elegir-modalidad').waitFor();await pa.keyboard.press('Escape');
    await pa.locator('#ajustes').click();await pa.locator('#retos').fill('48');await pa.locator('#cerrar-preferencias').click();
    await comenzar.click();await pa.locator('#elegir-modalidad').waitFor();await pa.keyboard.press('Escape');
    assert.equal(await tarjetas.count(),0);
  }
  resultados.push({caso:'Notificaciones de hasta 260 px: fondo oscuro y bordes por tipo, nuevas debajo de anteriores sin superposición, máximo tres avisos y menos si falta altura, antiguos descartados sin scroll ni recortes, ocho segundos independientes, cierre circular sobre la esquina por X y teclado; accesibles sobre Preferencias, sin bloquear controles del fondo; validación entera 1–48 antes de modalidad, español/portugués, escritorio/móvil y versión visible en créditos',resultado:'OK'});
  await avisos.close();
  assert.deepEqual(errores,[]);
  contexto=await browser.newContext({viewport:{width:1280,height:1080},storageState:sesionInicial});await mockVoz(contexto);
  page=await contexto.newPage();page.on('pageerror',e=>errores.push(e.message));
  await page.goto(base);await page.getByRole('button',{name:'Comenzar otra partida',exact:true}).waitFor();
  console.log('Avisos completos; comprobando recursos y vistas móviles.');
  // Captura de un reto con ayuda en escritorio.
  await clicar(page,'Comenzar otra partida','INICIO');await clicar(page,'Yo elijo','SELECCION_ANIMAL');await page.getByRole('searchbox',{name:'Buscar animal'}).fill('jirafa');await clicar(page,'Jirafa reticulada','ESPERANDO_RESPUESTA');await clicar(page,'Pista');
  await captura(page,'03_reto_escritorio.png');
  // Los 95 recursos activos se decodifican en el navegador (WebP transparentes).
  const assetTest=await page.evaluate(async()=>{
    const v=await (await fetch('/api/vista')).json();
    const fallos=[],rutas=[...Object.values(v.pictogramas).map(p=>p.imagen),'/ilustraciones/robot_despedida.webp','/ilustraciones/robot_pausa.webp','/zoonauta-logo.svg','/portada-selva.webp','/paisajes.webp',...Array.from({length:7},(_,i)=>`/fondos/H0${i+2}.webp`),...Array.from({length:8},(_,i)=>`/habitats/H0${i+1}.webp`),...Array.from({length:48},(_,i)=>`/animales/A${String(i+1).padStart(2,'0')}.webp`)];
    for(let inicio=0;inicio<rutas.length;inicio+=8){
      await Promise.all(rutas.slice(inicio,inicio+8).map(async ruta=>{
        const i=new Image();i.src=ruta;
        try{await i.decode();if(!i.naturalWidth)fallos.push(ruta);}catch{fallos.push(ruta);}
      }));
    }return fallos;
  });assert.deepEqual(assetTest,[]);
  assert.equal(await page.evaluate(async()=>(await fetch('/habitats/H09.webp')).status),404);
  assert.equal(await page.evaluate(async()=>(await fetch('/ilustraciones/inexistente.webp')).status),404);
  resultados.push({caso:'48 caricaturas, logo, 95 recursos educativos, dos ilustraciones de robot, nueve paisajes de portada y ocho paisajes exclusivos de tarjetas decodificados sin errores',resultado:'OK'});
  // Revisar las representaciones de animales en una plancha para inspección visual.
  await page.evaluate(async()=>{
    const v=await (await fetch('/api/vista')).json();const main=document.getElementById('juego');main.replaceChildren();
    const h=document.createElement('h1');h.textContent='Revisión visual: 48 animales';main.append(h);const grid=document.createElement('div');grid.className='catalogo';main.append(grid);
    for(const a of v.catalogo_animales){const d=document.createElement('div');d.className='tarjeta';const im=document.createElement('img');im.src=`/animales/${a.id}.webp`;const t=document.createElement('span');t.textContent=a.nombre;d.append(im,t);grid.append(d);}
  });await captura(page,'04_revision_animales.png');
  const sesionRevision=await contexto.storageState();await contexto.close();
  // Vista estrecha real: sin desbordamiento horizontal, controles alcanzables.
  const movil=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await mockVoz(movil);const pm=await movil.newPage();pm.on('pageerror',e=>errores.push(e.message));await pm.goto(base);await pm.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  assert.equal(await pm.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);await captura(pm,'06_inicio_movil.png');
  await pm.getByRole('button',{name:'Preferencias'}).click();
  const dialogo=await pm.locator('#preferencias').boundingBox();assert.ok(dialogo.x>=0&&dialogo.x+dialogo.width<=390);
  await captura(pm,'07_preferencias_movil.png',false);await pm.getByRole('button',{name:'Volver al juego',exact:true}).click();
  await pm.getByRole('button',{name:'Comenzar',exact:true}).click();
  await captura(pm,'16_selector_modalidad_movil.png',false);
  await clicar(pm,'El agente elige','ESPERANDO_RESPUESTA');await clicar(pm,'Pista');
  assert.equal(await pm.locator('.habitats button').count(),8);
  assert.equal(await pm.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await captura(pm,'05_reto_movil.png');
  const minimo=await pm.locator('button').evaluateAll(bs=>Math.min(...bs.map(b=>b.getBoundingClientRect().height).filter(h=>h>0)));assert.ok(minimo>=44);
  resultados.push({caso:'Pantalla móvil 390 × 844: inicio, preferencias y partida, ocho opciones, sin desbordamiento horizontal, botones de al menos 44 px',resultado:'OK'});
  await movil.close();
  // Teclado y movimiento reducido: inicio, búsqueda y selección sin ratón.
  const teclado=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'});await mockVoz(teclado);
  const pt=await teclado.newPage();await pt.clock.install();pt.on('pageerror',e=>errores.push(e.message));await pt.goto(base);await pt.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  assert.equal(await pt.locator('.bienvenida').evaluate(el=>getComputedStyle(el).animationName),'none');
  await pt.clock.runFor(20001);assert.equal(await pt.locator('.ficha-numero').textContent(),'03 / 08');
  await pt.emulateMedia({reducedMotion:'no-preference'});await pt.emulateMedia({reducedMotion:'reduce'});
  await pt.clock.runFor(10001);assert.equal(await pt.locator('.ficha-numero').textContent(),'04 / 08');
  await pt.getByRole('button',{name:'Pausar paisajes',exact:true}).click();
  await pt.clock.runFor(20000);assert.equal(await pt.locator('.ficha-numero').textContent(),'04 / 08');
  for(const [width,height] of [[320,568],[390,844],[650,390],[844,390],[768,900],[1024,600],[1024,768],[1280,720],[1920,1080]]){await pt.setViewportSize({width,height});assert.equal(await pt.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);for(const nombre of ['Comenzar','Paisaje anterior','Siguiente paisaje']){const b=await pt.getByRole('button',{name:nombre,exact:true}).boundingBox();assert.ok(b.y>=0&&b.y+b.height<=height,`${nombre} fuera de pantalla ${width}x${height}`);}}
  await pt.setViewportSize({width:1280,height:900});
  await pt.getByRole('button',{name:'Preferencias',exact:true}).focus();
  for(let i=0;i<6;i++){await pt.keyboard.press('Tab');if(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')==='Comenzar'))break;}
  assert.equal(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Comenzar');await pt.keyboard.press('Enter');
  assert.equal(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Yo elijo');await pt.keyboard.press('Enter');
  await pt.getByRole('searchbox',{name:'Buscar animal'}).waitFor();await pt.getByRole('searchbox',{name:'Buscar animal'}).focus();await pt.keyboard.type('jaguar');await pt.keyboard.press('Tab');
  assert.equal(await pt.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Jaguar');await pt.keyboard.press('Enter');await pt.getByRole('button',{name:'Pista',exact:true}).waitFor();
  assert.equal(await pt.locator('.habitats button').count(),8);assert.equal(await pt.getByRole('progressbar',{name:'Progreso de la partida'}).evaluate(el=>el.value),0);
  for(const ancho of [320,768,1024,1280]){await pt.setViewportSize({width:ancho,height:900});assert.equal(await pt.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);}
  resultados.push({caso:'Teclado: iniciar, buscar y elegir un animal; progreso accesible y preferencia de movimiento reducido',resultado:'OK'});
  resultados.push({caso:'Inicio en una pantalla entre 320 × 568 y 1920 × 1080, con botones visibles; partida sin desbordamiento horizontal',resultado:'OK'});
  await teclado.close();
  // Modelos ausentes: se informa de la preparación, sin recurrir a voces del navegador.
  const sinvoz=await browser.newContext();await mockVoz(sinvoz,false);
  const pv=await sinvoz.newPage();pv.on('pageerror',e=>errores.push(e.message));await pv.goto(base);await pv.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  await pv.getByRole('button',{name:'Preferencias'}).click();assert.match(await pv.locator('#estado-voz').textContent(),/No hay voces preparadas/);assert.equal(await pv.locator('#probar-voz').isDisabled(),true);
  await pv.getByRole('button',{name:'Volver al juego',exact:true}).click();await clicar(pv,'El agente elige','ESPERANDO_RESPUESTA');assert.equal(await pv.locator('.habitats button:enabled').count(),8);
  resultados.push({caso:'Modelos ausentes: preparación explícita, sin voces del navegador; texto y pictogramas operativos',resultado:'OK'});
  await sinvoz.close();
  console.log('Recursos, móvil y teclado completos; comprobando idioma y voz.');
  const bilingue=await browser.newContext();await mockVoz(bilingue);
  const pg=await bilingue.newPage();pg.on('pageerror',e=>errores.push(e.message));await pg.goto(base);await pg.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  await pg.getByRole('button',{name:'Preferencias',exact:true}).click();
  const revisionIdioma=(await vista(pg)).revision;
  for(const idioma of ['es','pt-BR']){
    await pg.locator('#idioma').selectOption(idioma);await pg.waitForFunction(i=>document.documentElement.lang===i,idioma);
    assert.equal(await pg.locator('#voces option').count(),7);
    for(const id of await pg.locator('#voces option').evaluateAll(os=>os.map(o=>o.value))){
      await pg.locator('#voces').selectOption(id);const antes=await pg.evaluate(()=>window.__voz.length);
      await pg.locator('#probar-voz').click();await pg.waitForFunction(n=>window.__voz.length>n,antes);
      const voz=await pg.evaluate(()=>window.__voz.at(-1));assert.equal(voz.voz,id);assert.equal(voz.idioma,idioma);
      assert.equal(voz.texto,idioma==='es'?'Hola. Vamos a descubrir dónde viven los animales.':'Olá. Vamos descobrir onde os animais vivem.');
    }
  }
  assert.equal((await vista(pg)).revision,revisionIdioma);
  assert.equal(await pg.getByRole('button',{name:'Preferências',exact:true}).isVisible(),true);
  assert.equal(await pg.locator('#etiqueta-voces').textContent(),'Voz em português brasileiro');
  assert.equal(await pg.evaluate(()=>document.documentElement.scrollHeight<=innerHeight),true);
  await captura(pg,'09_preferencias_portugues.png',false);
  await pg.getByRole('button',{name:'Voltar ao jogo',exact:true}).click();
  for(const [width,height] of [[320,568],[390,844],[650,390],[844,390],[768,900],[1024,600],[1024,768],[1280,720],[1920,1080]]){
    await pg.setViewportSize({width,height});assert.equal(await pg.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),true);
    const b=await pg.getByRole('button',{name:'Começar',exact:true}).boundingBox();assert.ok(b.y>=0&&b.y+b.height<=height);
  }
  await pg.setViewportSize({width:390,height:844});await captura(pg,'11_inicio_portugues_movil.png');
  await pg.getByRole('button',{name:'Preferências',exact:true}).click();await captura(pg,'12_preferencias_portugues_movil.png',false);
  await pg.setViewportSize({width:1280,height:900});
  await pg.getByRole('button',{name:'Voltar ao jogo',exact:true}).click();
  await clicar(pg,'Eu escolho','SELECCION_ANIMAL');
  assert.equal(await pg.locator('.catalogo button').count(),6);
  assert.equal(await pg.locator('.catalogo-pagina').textContent(),'Página 1 de 8');
  await pg.getByRole('button',{name:'Próximos',exact:true}).click();
  assert.equal(await pg.locator('.catalogo-pagina').textContent(),'Página 2 de 8');
  const buscarPT=pg.getByRole('searchbox',{name:'Buscar animal'});await buscarPT.fill('PINGUIM');
  assert.equal(await pg.locator('.catalogo button:visible').count(),1);
  await clicar(pg,'Pinguim-imperador','ESPERANDO_RESPUESTA');
  await clicar(pg,'Dica');const ajuda=(await vista(pg)).respuesta;
  await clicar(pg,'Repetir');assert.deepEqual((await vista(pg)).respuesta,ajuda);
  assert.equal((await pg.evaluate(()=>window.__voz.at(-1))).lang,'pt-BR');
  const tecnicaAntes=await pg.evaluate(async()=>await (await fetch('/api/revision')).json());
  // Preferencias solo tiene acceso visible en inicio. Invocación de prueba para
  // conservar el contrato del adaptador de idioma/voz sobre una sesión activa.
  assert.equal(await pg.locator('#ajustes').isVisible(),false);
  await pg.locator('#ajustes').evaluate(b=>b.click());
  await pg.locator('#idioma').selectOption('es');await pg.waitForFunction(()=>document.documentElement.lang==='es');
  assert.equal(await pg.locator('#voces').inputValue(),'kokoro:em_santa');
  await pg.locator('#voces').selectOption('piper:es_AR-daniela-high');await pg.locator('#velocidad').selectOption('0.8');
  await pg.locator('#probar-voz').click();await pg.waitForFunction(()=>window.__voz.at(-1)?.rate===0.8);
  await pg.getByRole('button',{name:'Volver al juego',exact:true}).click();
  const tecnicaDespues=await pg.evaluate(async()=>await (await fetch('/api/revision')).json());tecnicaDespues.idioma=tecnicaAntes.idioma;assert.deepEqual(tecnicaDespues,tecnicaAntes);
  await pg.locator('#ajustes').evaluate(b=>b.click());assert.equal(await pg.locator('#voces').inputValue(),'piper:es_AR-daniela-high');
  await pg.locator('#idioma').selectOption('pt-BR');await pg.waitForFunction(()=>document.documentElement.lang==='pt-BR');
  assert.equal(await pg.locator('#voces').inputValue(),'kokoro:pm_santa');
  await pg.getByRole('button',{name:'Voltar ao jogo',exact:true}).click();
  await captura(pg,'10_reto_portugues.png');
  await clicar(pg,'Repetir');const cancelaciones=await pg.evaluate(()=>window.__cancelaciones);
  await clicar(pg,'Pausar','PAUSADA');assert.ok(await pg.evaluate(n=>window.__cancelaciones>n,cancelaciones));
  await comprobarCierre(pg);await comprobarPictogramas(pg);await captura(pg,'pausa_portugues.png');
  await pg.locator('#ajustes').evaluate(b=>b.click());await pg.locator('#voz').uncheck();
  await pg.getByRole('button',{name:'Voltar ao jogo',exact:true}).click();const lecturas=await pg.evaluate(()=>window.__voz.length);
  await clicar(pg,'Retomar','ESPERANDO_RESPUESTA');assert.equal(await pg.evaluate(()=>window.__voz.length),lecturas);
  const revisionRecarga=(await vista(pg)).revision;
  await pg.reload();await pg.getByRole('button',{name:'Dica',exact:true}).waitFor();assert.equal((await vista(pg)).revision,revisionRecarga);assert.equal(await pg.evaluate(()=>window.__voz.length),0);
  resultados.push({caso:'14 voces locales: 7 por idioma, muestras, ritmo, elección por idioma, cancelación y silencio',resultado:'OK',alcance:'API WAV y reproductor controlados.'});
  resultados.push({caso:'Portugués brasileño: interfaz, catálogo, búsqueda, pictogramas, ayudas y recarga; adaptador de idioma sobre una sesión activa sin alterar estado, registros o modelo. Preferencias visible solo en inicio',resultado:'OK'});
  await clicar(pg,'Sair','ABANDONADA');await comprobarCierre(pg);await comprobarPictogramas(pg);await captura(pg,'cierre_portugues.png');
  await pg.goto(base+'/revision');await pg.locator('#datos').filter({hasText:'parametros_congelados'}).waitFor();
  assert.equal(await pg.getByRole('button',{name:'Atualizar registro',exact:true}).isVisible(),true);
  resultados.push({caso:'Revisión técnica con encabezados en portugués y registros originales conservados',resultado:'OK'});
  await bilingue.close();
  // Página técnica de la misma cookie: solo lectura, modelo congelado.
  contexto=await browser.newContext({storageState:sesionRevision});page=await contexto.newPage();
  await page.goto(base+'/revision');await page.locator('#datos').filter({hasText:'parametros_congelados'}).waitFor();
  const tecnicos=JSON.parse(await page.locator('#datos').textContent());assert.equal(tecnicos.parametros_congelados,true);
  resultados.push({caso:'Consulta técnica separada y modelo congelado',resultado:'OK'});
  await contexto.close();
  // Una muestra que todavía se descarga no debe bloquear el cambio de voz.
  const cambios=await browser.newContext();await mockVoz(cambios);
  let listo,liberar,primera,peticiones=0;
  const pendiente=new Promise(r=>listo=r),continuar=new Promise(r=>liberar=r);
  await cambios.route('**/api/voz',async route=>{
    if(++peticiones===1){primera=route.request().postDataJSON();listo();await continuar;}
    const b=Buffer.alloc(244);b.write('RIFF');b.writeUInt32LE(236,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(22050,24);b.writeUInt32LE(44100,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(200,40);
    await route.fulfill({contentType:'audio/wav',body:b}).catch(e=>{if(!route.request().failure())throw e;});
  });
  const pc=await cambios.newPage();pc.on('pageerror',e=>errores.push(e.message));
  await pc.goto(base);await pc.getByRole('button',{name:'Comenzar',exact:true}).waitFor();
  const antesCambio=await vista(pc);
  await pc.getByRole('button',{name:'Preferencias',exact:true}).click();
  await pc.locator('#probar-voz').click();await pendiente;
  const cancelada=pc.waitForResponse(r=>r.url().endsWith('/api/voz/cancelar'));
  await pc.locator('#voces').selectOption('piper:es_MX-ald-medium');
  const cancelacion=await cancelada;
  assert.equal(cancelacion.status(),200);
  const corte=cancelacion.request().postDataJSON();
  assert.equal(corte.canal_voz,primera.canal_voz);assert.ok(corte.turno_voz>primera.turno_voz);
  liberar();await pc.locator('#probar-voz').click();
  await pc.waitForFunction(()=>window.__voz.length===1);
  assert.equal(await pc.evaluate(()=>window.__voz[0].voz),'piper:es_MX-ald-medium');
  assert.deepEqual(await vista(pc),antesCambio);
  resultados.push({caso:'Cambiar de voz durante una descarga cancela la lectura en el servidor y reproduce solo la última muestra, sin modificar la partida',resultado:'OK',alcance:'Descarga de WAV y reproductor controlados.'});
  await cambios.close();
  assert.deepEqual(errores,[]);
  fs.writeFileSync(path.join(out,'revision_navegador.json'),JSON.stringify({fecha:process.env.VERIFICACION_FECHA||new Date().toISOString().slice(0,10),version:'4.4.0',navegador:browser.version(),resultados,errores_js:errores},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultados:'OK',navegador:browser.version()}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
