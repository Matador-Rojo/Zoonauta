/* Voz de la 5.0 («/v5/») con el catálogo ampliado: la voz grabada de Zoonauta (Marcela) suena
   desde /api/voz/grabada, nunca se pide síntesis (/api/voz), una sola voz a la vez, Pausar corta
   una lectura pendiente y Preferencias informa de la voz grabada (2026-11-14). Las respuestas de
   audio usan el servidor real; el reproductor se observa sin sonido. */
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = (process.env.INTERFAZ_URL || 'http://127.0.0.1:8000') + '/v5/';
const casos = [];
const caso = async (nombre, fn) => { await fn(); casos.push(nombre); };

(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  const pedidos = {grabada: 0, sintesis: 0};
  const estado = {retraso: 0};
  try {
    const context = await browser.newContext({viewport: {width: 1366, height: 860}});
    // Reproductor observado: registra cada audio que empieza a sonar, sin emitir sonido.
    await context.addInitScript(() => {
      window.__audios = [];
      window.Audio = class {
        constructor(url) { this.src = url; this.paused = true; window.__audios.push(this); }
        async play() { this.paused = false; }
        pause() { this.paused = true; }
        removeAttribute() { this.src = ''; }
      };
    });
    await context.route('**/api/voz/grabada', async r => {
      pedidos.grabada++;
      if (estado.retraso) await new Promise(f => setTimeout(f, estado.retraso));
      try { await r.continue(); } catch { /* cancelada */ }
    });
    await context.route('**/api/voz', async r => { pedidos.sintesis++; await r.continue(); });
    const page = await context.newPage();
    const errores = [];
    page.on('pageerror', e => errores.push(e.message));
    const sonando = () => page.evaluate(() => window.__audios.filter(a => !a.paused && a.src).length);

    await page.goto(base);
    await page.getByRole('button', {name: 'Comenzar', exact: true}).waitFor();

    await caso('Preferencias: voz grabada disponible y Probar voz activo', async () => {
      await page.getByRole('button', {name: 'Preferencias', exact: true}).click();
      assert.match(await page.locator('#estado-voz').textContent(), /Voz grabada de Zoonauta/);
      assert.equal(await page.locator('#probar-voz').isDisabled(), false);
      assert.equal(await page.locator('#voces optgroup[label="Piper"], #voces optgroup[label="Kokoro"]').count(), 0);
      const antes = pedidos.grabada;
      await page.locator('#probar-voz').click();
      await page.waitForFunction(() => window.__audios.some(a => !a.paused && a.src));
      assert.ok(pedidos.grabada > antes, 'Probar voz usa la grabación');
      await page.getByRole('button', {name: 'Volver al juego', exact: true}).click();
    });

    await caso('la pregunta de modalidad y el reto se leen con la grabación', async () => {
      const antes = pedidos.grabada;
      await page.getByRole('button', {name: 'Comenzar', exact: true}).click();
      await page.waitForFunction(n => window.__audios.length > n, await page.evaluate(() => window.__audios.length));
      await page.getByRole('button', {name: 'El agente elige', exact: true}).click();
      await page.getByRole('button', {name: 'Pista', exact: true}).waitFor();
      await page.waitForTimeout(800);
      assert.ok(pedidos.grabada >= antes + 2);
      assert.equal(await sonando(), 1, 'una sola voz a la vez');
    });

    await caso('Pausar corta una lectura pendiente: no llega a sonar', async () => {
      estado.retraso = 1500;
      const audios = await page.evaluate(() => window.__audios.length);
      await page.getByRole('button', {name: 'Repetir', exact: true}).click();
      await page.getByRole('button', {name: 'Pausar', exact: true}).click();
      await page.waitForTimeout(2200);
      assert.equal(await sonando(), 0, 'nada suena en pausa');
      assert.equal(await page.evaluate(() => window.__audios.length), audios, 'la lectura cortada no se reproduce');
      estado.retraso = 0;
    });

    await caso('nunca se pide voz sintetizada', async () => {
      assert.equal(pedidos.sintesis, 0);
    });

    assert.deepEqual(errores, []);
    console.log(JSON.stringify({casos: casos.length, resultado: 'OK'}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
