/* Audio real: servidor con Piper/Kokoro, WAV y reproductor nativo de Chromium. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL;
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 try{
  const page=await browser.newPage(),errores=[],audios=[],peticiones=[];
  page.on('pageerror',e=>errores.push(e.message));
  page.on('request',r=>{if(r.url()===base+'/api/voz')peticiones.push(r.postDataJSON());});
  page.on('response',r=>{if(r.url()===base+'/api/voz')audios.push(r);});
  await page.addInitScript(()=>{
   window.__wavReales=[];const original=window.fetch.bind(window);
   window.fetch=async(url,opciones)=>{
    const r=await original(url,opciones);
    if(url==='/api/voz'&&r.ok){const b=new Uint8Array(await r.clone().arrayBuffer());window.__wavReales.push({bytes:b.length,riff:String.fromCharCode(...b.slice(0,4)),wave:String.fromCharCode(...b.slice(8,12))});}
    return r;
   };
  });
  await page.goto(base);await page.locator('.modalidad').first().waitFor();
  const antes=await page.evaluate(async()=>await (await fetch('/api/revision')).json());
  await page.locator('#ajustes').click();
  const resultados=[];
  for(const [idioma,voz] of [['es','piper:es_AR-daniela-high'],['pt-BR','kokoro:pf_dora']]){
   await page.locator('#idioma').selectOption(idioma);await page.waitForFunction(i=>document.documentElement.lang===i,idioma);
   await page.locator('#voces').selectOption(voz);await page.locator('#velocidad').selectOption('0.8');
   const n=audios.length;await page.locator('#probar-voz').click();
   await page.waitForFunction(()=>locucion&&locucion.readyState>=2&&locucion.currentTime>0,{},{timeout:30000});
   const reproductor=await page.evaluate(()=>({duracion:locucion.duration,tiempo:locucion.currentTime,ritmo:locucion.playbackRate,conserva_tono:locucion.preservesPitch}));
   assert.equal(reproductor.ritmo,0.8);assert.equal(reproductor.conserva_tono,true);assert.ok(reproductor.duracion>0.5);
   assert.equal(audios[n].status(),200);const wav=await page.evaluate(n=>window.__wavReales[n],n);
   assert.equal(wav.riff,'RIFF');assert.equal(wav.wave,'WAVE');assert.ok(wav.bytes>1000);
   assert.equal(wav.bytes,Number(audios[n].headers()['content-length']));
   assert.equal(peticiones[n].voz,voz);assert.equal(peticiones[n].idioma,idioma);assert.equal('texto' in peticiones[n],false);
   assert.equal(await page.locator('#aviso').textContent(),'');
   resultados.push({idioma,voz,bytes_wav:wav.bytes,reproductor,resultado:'OK'});
   await page.waitForFunction(()=>locucion===null,{},{timeout:15000});
  }
  const despues=await page.evaluate(async()=>await (await fetch('/api/revision')).json());despues.idioma=antes.idioma;assert.deepEqual(despues,antes);
  assert.deepEqual(errores,[]);
  fs.writeFileSync(path.resolve(__dirname,'../docs/interfaz/revision_audio_navegador.json'),JSON.stringify({version:'4.0.0',fecha:'2026-10-11',navegador:browser.version(),alcance:'Síntesis local, descarga WAV, decodificación y avance de reproducción nativa en Chromium. No acredita escucha humana en otro dispositivo.',resultados,errores_js:errores},null,2)+'\n');
  console.log(JSON.stringify({audio_real:resultados.length,resultado:'OK',navegador:browser.version()}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
