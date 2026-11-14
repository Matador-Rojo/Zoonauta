/* Partidas completas en /v6/ usando solo el teclado (Tab, Mayús+Tab, Intro, Espacio).
   Ambas modalidades, 2/4/8 hábitats, una partida en pt-BR y una a 320 px de ancho.
   El servidor decide si un hábitat es válido: se prueban hábitats hasta resolver cada reto. */
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = (process.env.INTERFAZ_URL || 'http://127.0.0.1:8000') + '/v6/';
const casos = [];

async function vista(page) {
  return page.evaluate(async () => (await fetch('/api/vista')).json());
}
// Lleva el foco con Tab (hacia delante) hasta el elemento indicado y lo activa con Intro.
async function tabularYActivar(page, selector, tecla = 'Enter') {
  const objetivo = page.locator(selector).first();
  await objetivo.waitFor();
  for (let i = 0; i < 80; i++) {
    if (await objetivo.evaluate(e => e === document.activeElement)) {
      await page.keyboard.press(tecla);
      return;
    }
    await page.keyboard.press('Tab');
  }
  throw new Error(`No se llegó con Tab a ${selector}`);
}
async function esperarRevision(page, anterior) {
  await page.waitForFunction(async r => (await (await fetch('/api/vista')).json()).revision > r, anterior);
}

async function partida(browser, {modalidad, opciones, retos, idioma = 'es', ancho = 1280}) {
  const context = await browser.newContext({viewport: {width: ancho, height: 800}, reducedMotion: 'reduce'});
  const page = await context.newPage();
  const errores = [];
  page.on('pageerror', e => errores.push(e.message));
  await page.goto(base);
  await page.locator('.portada-comenzar').waitFor();
  // Voz desactivada y ajustes de la partida, todo con teclado.
  await tabularYActivar(page, '.cabecera .boton-texto');
  const dialogo = page.locator('dialog.preferencias');
  assert.ok(await dialogo.evaluate(d => d.open));
  if (idioma !== 'es') {
    await page.locator('#pref-idioma').focus();
    await page.keyboard.press(idioma === 'pt-BR' ? 'ArrowDown' : 'ArrowUp');
    // Con el select de estilo propio (appearance: base-select) la flecha abre la lista:
    // se baja a la opción y se confirma con Intro, como en cualquier lista desplegable.
    if (await page.locator('#pref-idioma').evaluate(s => s.matches(':open'))) {
      await page.keyboard.press(idioma === 'pt-BR' ? 'ArrowDown' : 'ArrowUp');
      await page.keyboard.press('Enter');
    }
    await page.waitForFunction(i => document.documentElement.lang === i, idioma);
  }
  await page.locator('#pref-retos').focus();
  await page.keyboard.press('Control+A');
  await page.keyboard.type(String(retos));
  await page.keyboard.press('Tab'); // al salir del campo se ajusta de 1 a 48
  await page.locator('dialog.preferencias select').nth(1).selectOption(String(opciones));
  const voz = page.locator('.pref-voz input[role="switch"]');
  // En pt-BR la voz está bloqueada (apagada y desactivada); en español se apaga con teclado.
  if (idioma === 'es') {
    await voz.focus();
    await page.keyboard.press('Space');
  } else assert.ok(await voz.isDisabled());
  assert.equal(await voz.isChecked(), false);
  await page.keyboard.press('Escape');
  assert.equal(await dialogo.evaluate(d => d.open), false);

  await tabularYActivar(page, '.portada-comenzar');
  await page.locator('dialog.selector-modalidad').waitFor();
  // El foco inicial está en «Yo elijo»; Tab lleva a «El agente elige».
  if (modalidad === 'AGENTE') await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');

  let v = await vista(page);
  for (let reto = 0; reto < retos; reto++) {
    if (v.fase === 'SELECCION_ANIMAL') {
      await tabularYActivar(page, '.tarjeta-animal');
      await esperarRevision(page, v.revision);
      v = await vista(page);
    }
    assert.equal(v.fase, 'ESPERANDO_RESPUESTA');
    assert.equal(await page.locator('.tarjeta-habitat').count(), opciones);
    // Prueba hábitats en orden hasta que el servidor confirme uno.
    for (const h of v.opciones_habitat) {
      if (v.fase !== 'ESPERANDO_RESPUESTA') break;
      await page.locator(`.tarjeta-habitat[data-habitat="${h.id}"]`).focus();
      await page.keyboard.press('Enter');
      await esperarRevision(page, v.revision);
      v = await vista(page);
    }
    assert.equal(v.fase, 'RETO_RESUELTO', `reto ${reto + 1} resuelto`);
    assert.ok(await page.locator('.guia.confirmacion').count() === 1);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'sin desplazamiento horizontal');
    const sobra = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    if (sobra > 0) await page.screenshot({path: require('node:path').resolve(process.env.INTERFAZ_SALIDA || 'output', `desplaza_${modalidad}_${opciones}_${idioma}_${ancho}.png`)});
    // Nada aplastado: las tarjetas de hábitat se ven y se pueden pulsar.
    const bajas = await page.locator('.tarjeta-habitat').evaluateAll(t => t.map(e => e.getBoundingClientRect().height).filter(h => h < 56));
    assert.deepEqual(bajas, [], 'tarjetas de hábitat de al menos 56 px');
    assert.equal(sobra, 0, `sin desplazamiento vertical (${modalidad}, ${opciones} hábitats, ${idioma}, ${ancho}px, reto ${reto + 1})`);
    await tabularYActivar(page, 'button[data-control="continuar"]', reto % 2 ? 'Space' : 'Enter');
    await esperarRevision(page, v.revision);
    v = await vista(page);
  }
  assert.equal(v.fase, 'COMPLETADA');
  await page.locator('.cierre[data-estado="COMPLETADA"]').waitFor();
  assert.equal(await page.evaluate(() => document.activeElement.id), 'titulo-pantalla', 'el foco va al título del cierre');
  assert.match(await page.locator('.cierre-resumen strong').textContent(), new RegExp(`${retos}\\s*/\\s*${retos}`));
  await tabularYActivar(page, '.cierre .boton-principal');
  await page.locator('.portada-comenzar').waitFor();
  assert.equal((await vista(page)).fase, 'INICIO');
  assert.deepEqual(errores, []);
  await context.close();
  casos.push(`${modalidad} · ${opciones} hábitats · ${retos} retos · ${idioma} · ${ancho}px`);
}

(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  try {
    await partida(browser, {modalidad: 'JUGADOR', opciones: 2, retos: 2});
    await partida(browser, {modalidad: 'AGENTE', opciones: 4, retos: 2});
    await partida(browser, {modalidad: 'JUGADOR', opciones: 8, retos: 2, idioma: 'pt-BR'});
    await partida(browser, {modalidad: 'AGENTE', opciones: 8, retos: 1, ancho: 320});
    console.log(JSON.stringify({casos: casos.length, partidas: casos, resultado: 'OK'}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
