/* Comprobaciones técnicas de accesibilidad; no sustituyen pruebas con usuarios. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.INTERFAZ_URL||'http://127.0.0.1:8000';
const out=path.resolve(process.env.INTERFAZ_SALIDA||'output/hito3_cierre/navegador');
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
 const resultados=[];
 try{
  for(const idioma of ['es','pt-BR']){
   const context=await browser.newContext({viewport:{width:1280,height:720},reducedMotion:'reduce'});
   const page=await context.newPage(),errores=[];
   page.on('pageerror',e=>errores.push(e.message));
   await page.goto(base);await page.locator('#ajustes').click();
   if(idioma==='pt-BR'){
    await page.locator('#idioma').selectOption(idioma);
    await page.waitForFunction(()=>document.documentElement.lang==='pt-BR');
   }
   await page.waitForFunction(()=>document.querySelector('#voces option')?.textContent!=='Buscando voces…');
   for(const [width,height] of [[1920,1080],[1366,768],[1280,720],[1024,768],[390,844],[320,568],[640,360]]){
    await page.setViewportSize({width,height});
    const medidas=await page.locator('#preferencias').evaluate(d=>{
     const columns=d.querySelector('.ajustes-columnas'),a=d.querySelector('.ajustes-columna').getBoundingClientRect(),b=d.querySelector('.ajustes-audio').getBoundingClientRect();
     const rect=d.getBoundingClientRect();
     return {sinScrollHorizontal:d.scrollWidth<=d.clientWidth+1&&document.documentElement.scrollWidth<=innerWidth,
      sinScrollVertical:d.scrollHeight<=d.clientHeight+1,
      dentroDePantalla:rect.top>=0&&rect.bottom<=innerHeight+1,
      columnas:getComputedStyle(columns).gridTemplateColumns.split(' ').length,
      lados:b.left>a.right,mismaFila:Math.abs(a.top-b.top)<2,
      controles:[...d.querySelectorAll('select,button,input[type=number]')].every(e=>e.getBoundingClientRect().height>=44)};
    });
    assert.ok(medidas.sinScrollHorizontal&&medidas.dentroDePantalla&&medidas.controles,JSON.stringify({idioma,width,height,medidas}));
    if(width>=1024&&height>=720)assert.ok(medidas.sinScrollVertical&&medidas.lados&&medidas.mismaFila,JSON.stringify({idioma,width,height,medidas}));
    if(width<760)assert.equal(medidas.columnas,1);
    if(width===1280||width===390)await page.screenshot({path:path.join(out,`preferencias_${idioma}_${width}.png`)});
    // El último botón permanece alcanzable en ventanas bajas y a zoom equivalente.
    await page.locator('#cerrar-preferencias').scrollIntoViewIfNeeded();
    await page.locator('#cerrar-preferencias').click();
    await page.locator('#ajustes').click();
    resultados.push({caso:'distribucion_preferencias',idioma,width,height,resultado:'OK',...medidas});
   }
   await page.setViewportSize({width:1280,height:720});
   await page.locator('#retos').fill('3');
   await page.locator('#cantidad-opciones').selectOption('4');
   await page.locator('#voz').uncheck();
   await page.locator('#cerrar-ajustes').focus();
   for(let n=0;n<24;n++){
    await page.keyboard.press('Tab');
    assert.ok(await page.evaluate(()=>document.activeElement.closest('#preferencias')!==null),'El foco salió del diálogo');
   }
   await page.locator('#cerrar-ajustes').focus();
   await page.keyboard.press('Shift+Tab');
   assert.equal(await page.evaluate(()=>document.activeElement.id),'cerrar-preferencias');
   await page.keyboard.press('Escape');
   assert.equal(await page.locator('#preferencias').evaluate(d=>d.open),false);
   await page.locator('#ajustes').focus();await page.keyboard.press('Enter');
   assert.equal(await page.locator('#retos').inputValue(),'3');
   assert.equal(await page.locator('#cantidad-opciones').inputValue(),'4');
   assert.equal(await page.locator('#voz').isChecked(),false);
   // Créditos abiertos deben ampliar el contenido, nunca recortar sus enlaces/controles.
   await page.locator('.creditos-ajustes summary').click();
   await page.locator('#cerrar-preferencias').scrollIntoViewIfNeeded();
   await page.locator('#cerrar-preferencias').click();
   assert.deepEqual(errores,[]);
   resultados.push({caso:'teclado_y_conservacion',idioma,resultado:'OK'});
   await context.close();
  }
  fs.writeFileSync(path.join(out,'revision_hito3.json'),JSON.stringify({fecha:process.env.VERIFICACION_FECHA||new Date().toISOString().slice(0,10),
   navegador:browser.version(),alcance:'VERIFICACION_TECNICA_SIN_USUARIOS',resultados},null,2));
  console.log(JSON.stringify({casos:resultados.length,resultado:'OK'}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
