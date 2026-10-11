/* Contrato de las voces Microsoft/Google, con síntesis controlada. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL||'http://127.0.0.1:8000';
const out=path.resolve(process.env.INTERFAZ_SALIDA||'resultados_nuevos/voces_navegador');
const inventario=[
 {name:'Google español latinoamericano',voiceURI:'google-es-419',lang:'es-419',localService:false},
 {name:'Microsoft Sabina - Spanish (Mexico)',voiceURI:'ms-es-MX',lang:'es-MX',localService:true},
 {name:'Google español',voiceURI:'google-es-ES',lang:'es-ES',localService:false},
 {name:'Google português do Brasil',voiceURI:'google-pt-BR',lang:'pt-BR',localService:false},
 {name:'Microsoft Antonio - Portuguese (Brazil)',voiceURI:'ms-pt-BR',lang:'pt_BR',localService:true},
 {name:'Microsoft Portuguese (Portugal)',voiceURI:'ms-pt-PT',lang:'pt-PT',localService:true},
 {name:'Otro proveedor',voiceURI:'otro-es-MX',lang:'es-MX',localService:true}
];
async function contexto(browser,voces=inventario,locales=true){
 const c=await browser.newContext();
 await c.route('**/api/voz/config',async route=>{
  const r=await route.fetch(),d=await r.json();d.voces.forEach(v=>v.disponible=locales);await route.fulfill({json:d});
 });
 await c.addInitScript(voces=>{
  const s=new EventTarget();let lista=voces;
  window.__lecturas=[];window.__cancelaciones=0;window.__wav=0;
  s.getVoices=()=>lista;
  s.speak=u=>{window.__actual=u;window.__lecturas.push({texto:u.text,voz:u.voice.name,lang:u.lang,rate:u.rate});};
  s.cancel=()=>{window.__cancelaciones++;const vieja=window.__actual;window.__actual=null;queueMicrotask(()=>vieja?.onerror?.({error:'canceled'}));};
  window.__actualizar=v=>{lista=v;s.dispatchEvent(new Event('voiceschanged'));};
  Object.defineProperty(window,'speechSynthesis',{value:s,configurable:true});
  window.SpeechSynthesisUtterance=class{constructor(texto){this.text=texto;}};
  const original=fetch.bind(window);
  window.fetch=(url,op)=>{if(url==='/api/voz')window.__wav++;return original(url,op);};
 },voces);
 return c;
}
async function abrir(c){const p=await c.newPage();await p.goto(base);await p.getByRole('button',{name:'Comenzar',exact:true}).waitFor();return p;}
async function revision(p){return p.evaluate(async()=>await(await fetch('/api/revision')).json());}
async function elegir(p,nombre){const o=await p.locator('#voces option').filter({hasText:nombre}).getAttribute('value');await p.locator('#voces').selectOption(o);return o;}
async function probar(p){const n=await p.evaluate(()=>window.__lecturas.length);await p.locator('#probar-voz').click();await p.waitForFunction(n=>window.__lecturas.length>n,n);return p.evaluate(()=>window.__lecturas.at(-1));}
async function actuar(p,nombre,fase){
  if(['Yo elijo','El agente elige','Eu escolho','O agente escolhe'].includes(nombre)&&!await p.getByRole('button',{name:nombre,exact:true}).isVisible())await p.getByRole('button',{name:/^(Comenzar|Começar)$/}).click();
 const rev=(await revision(p)).registro.filter(x=>x.tipo_registro==='EVENTO').length;
 await p.getByRole('button',{name:nombre,exact:true}).click();
 await p.waitForFunction(()=>document.getElementById('juego').getAttribute('aria-busy')==='false');
 if(fase)await p.waitForFunction(async f=>(await(await fetch('/api/vista')).json()).fase===f,fase);
 assert.ok((await revision(p)).registro.filter(x=>x.tipo_registro==='EVENTO').length>rev);
}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 const resultados=[],errores=[];
 try{
  const c=await contexto(browser),p=await abrir(c);p.on('pageerror',e=>errores.push(e.message));
  const antes=await revision(p);
  await p.getByRole('button',{name:'Preferencias',exact:true}).click();
  assert.equal(await p.locator('#voces option').count(),9);
  assert.deepEqual(await p.locator('#voces optgroup').evaluateAll(gs=>gs.map(g=>g.label)),['Google','Microsoft','Piper','Kokoro']);
  assert.equal(await p.locator('#voces option').filter({hasText:'España'}).count(),3); // Solo las tres voces Kokoro originales.
  assert.equal(await p.locator('#voces option').filter({hasText:'Otro proveedor'}).count(),0);
  await p.locator('#velocidad').selectOption('0.8');
  const googleES=await elegir(p,'Google español latinoamericano');
  let lectura=await probar(p);assert.equal(lectura.lang,'es-419');assert.equal(lectura.rate,0.8);assert.equal(lectura.texto,'Hola. Vamos a descubrir dónde viven los animales.');
  assert.match(await p.locator('#estado-voz').textContent(),/Puede necesitar Internet/);
  await elegir(p,'Microsoft Sabina');lectura=await probar(p);assert.equal(lectura.lang,'es-MX');assert.match(await p.locator('#estado-voz').textContent(),/instalada/);
  await p.locator('#idioma').selectOption('pt-BR');await p.waitForFunction(()=>document.documentElement.lang==='pt-BR');
  assert.equal(await p.locator('#voces option').count(),9);assert.equal(await p.locator('#voces option').filter({hasText:'Portugal'}).count(),0);
  await elegir(p,'Google português');lectura=await probar(p);assert.equal(lectura.lang,'pt-BR');assert.equal(lectura.texto,'Olá. Vamos descobrir onde os animais vivem.');
  assert.match(await p.locator('#estado-voz').textContent(),/Pode precisar de Internet/);
  const microsoftPT=await elegir(p,'Microsoft Antonio');lectura=await probar(p);assert.equal(lectura.lang,'pt-BR');
  await p.locator('#idioma').selectOption('es');await p.waitForFunction(()=>document.documentElement.lang==='es');
  assert.match(await p.locator('#voces option:checked').textContent(),/Microsoft Sabina/);
  await p.locator('#voces').selectOption(googleES);
  await p.evaluate(v=>window.__actualizar([...v,v[0]]),inventario);
  assert.equal(await p.locator('#voces').inputValue(),googleES);assert.equal(await p.locator('#voces option').count(),9);
  const despues=await revision(p);despues.idioma=antes.idioma;assert.deepEqual(despues,antes);assert.equal(await p.evaluate(()=>window.__wav),0);
  resultados.push({caso:'Microsoft y Google en español latinoamericano y portugués brasileño: región real, saludo, ritmo, selección por idioma y modelo inmutable',resultado:'OK'});

  await p.locator('#idioma').selectOption('pt-BR');await p.waitForFunction(()=>document.documentElement.lang==='pt-BR');assert.equal(await p.locator('#voces').inputValue(),microsoftPT);
  await probar(p);const cancelaciones=await p.evaluate(()=>window.__cancelaciones);
  await p.locator('#voz').uncheck();assert.ok(await p.evaluate(()=>window.__cancelaciones)>cancelaciones);
  await p.locator('#voz').check();await probar(p);
  await p.evaluate(()=>window.__actual.onerror({error:'network'}));assert.match(await p.locator('#aviso').textContent(),/Não foi possível reproduzir/);
  await p.reload();await p.getByRole('button',{name:'Começar',exact:true}).waitFor();assert.equal(await p.evaluate(()=>window.__lecturas.length),0);
  resultados.push({caso:'Silencio, errores de voz localizados, eventos cancelados antiguos y recarga sin lectura automática',resultado:'OK'});

  const tardio=await contexto(browser,[],false),pt=await abrir(tardio);pt.on('pageerror',e=>errores.push(e.message));
  await pt.getByRole('button',{name:'Preferencias',exact:true}).click();assert.equal(await pt.locator('#probar-voz').isDisabled(),true);
  await pt.evaluate(v=>window.__actualizar(v),inventario);assert.equal(await pt.locator('#probar-voz').isDisabled(),false);assert.equal(await pt.evaluate(()=>window.__lecturas.length),0);
  const elegida=await elegir(pt,'Microsoft Sabina');await probar(pt);
  await pt.evaluate(()=>window.__actualizar([]));assert.equal(await pt.locator('#probar-voz').isDisabled(),true);
  await pt.evaluate(v=>window.__actualizar(v),inventario);assert.equal(await pt.locator('#voces').inputValue(),elegida);
  await pt.getByRole('button',{name:'Volver al juego',exact:true}).click();await actuar(pt,'Yo elijo','SELECCION_ANIMAL');await pt.getByRole('searchbox',{name:'Buscar animal'}).fill('capibara');await actuar(pt,'Capibara o ronsoco','ESPERANDO_RESPUESTA');
  await actuar(pt,'Pista');const ayuda=await pt.evaluate(()=>window.__lecturas.at(-1));await actuar(pt,'Repetir');assert.equal((await pt.evaluate(()=>window.__lecturas.at(-1))).texto,ayuda.texto);
  await actuar(pt,'Pausar','PAUSADA');await actuar(pt,'Reanudar','ESPERANDO_RESPUESTA');assert.equal((await pt.evaluate(()=>window.__lecturas.at(-1))).texto,ayuda.texto);
  await actuar(pt,'Desierto cálido');assert.equal((await revision(pt)).estado.resultado,'PENDIENTE');await actuar(pt,'Selva tropical','RETO_RESUELTO');assert.equal((await revision(pt)).estado.completados,1);
  assert.equal(await pt.evaluate(()=>window.__wav),0);assert.equal((await revision(pt)).parametros_congelados,true);
  resultados.push({caso:'Voces que aparecen tarde o desaparecen, restauración de selección y partida con voz del navegador sin modelos locales',resultado:'OK'});

  // Pasar de WAV pendiente a voz del navegador conserva la cancelación del servidor.
  let recibida,liberar;const pendiente=new Promise(r=>recibida=r),fin=new Promise(r=>liberar=r);
  await c.route('**/api/voz',async route=>{recibida();await fin;await route.abort().catch(()=>{});});
  await p.getByRole('button',{name:'Preferências',exact:true}).click();await elegir(p,'Cadu');
  await p.locator('#probar-voz').click();await pendiente;
  const cancelada=p.waitForResponse(r=>r.url().endsWith('/api/voz/cancelar'));
  await elegir(p,'Google português');assert.equal((await cancelada).status(),200);
  lectura=await probar(p);assert.equal(lectura.lang,'pt-BR');liberar();
  await p.waitForFunction(()=>document.getElementById('aviso').textContent==='');
  resultados.push({caso:'Cambio de una lectura WAV pendiente a Google: cancela la cola local y lee con el navegador',resultado:'OK'});
  assert.deepEqual(errores,[]);
  fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'revision_voces_navegador.json'),JSON.stringify({fecha:'2026-10-11',version:'3.8.0',navegador:browser.version(),alcance:'Síntesis y disponibilidad controladas. No certifica disponibilidad de proveedores ni escucha humana en otro equipo.',resultados,errores_js:errores},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultados:'OK',navegador:browser.version()}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
