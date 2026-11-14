/* Cadena de voz del frontend 6.0 (/v6/). Las respuestas de audio se simulan para que
   la prueba sea determinista; las acciones de la partida usan el servidor real.
   La 6.0 usa solo la voz grabada de Zoonauta (Marcela, ElevenLabs): sin grabación no se lee
   con otra voz. Comprueba: grabación, una sola voz a la vez, velocidad, cancelación al
   pausar, interruptor de voz, fallo de red, que sin grabaciones no se piden y que en pt-BR
   la voz está bloqueada. */
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = (process.env.INTERFAZ_URL || 'http://127.0.0.1:8000') + '/';

// WAV PCM de 0,6 s en silencio (8 kHz, 16 bits, mono).
function wav(segundos = 0.6) {
  const muestras = Math.round(8000 * segundos), datos = muestras * 2, b = Buffer.alloc(44 + datos);
  b.write('RIFF', 0); b.writeUInt32LE(36 + datos, 4); b.write('WAVE', 8); b.write('fmt ', 12);
  b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22); b.writeUInt32LE(8000, 24);
  b.writeUInt32LE(16000, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(datos, 40);
  return b;
}
const AUDIO = wav(3);
const casos = [];
const caso = async (nombre, fn) => { await fn(); casos.push(nombre); };

(async () => {
  const browser = await chromium.launch({
    headless: true, args: ['--autoplay-policy=no-user-gesture-required'],
    ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {}),
  });
  const estado = {grabadas: 6, grabada: true, retraso: 0, fallo: false};
  const pedidos = {grabada: 0, voz: [], cancelar: 0};
  try {
    const context = await browser.newContext({viewport: {width: 1280, height: 860}, reducedMotion: 'reduce'});
    // Registra cada elemento de audio que se reproduce.
    await context.addInitScript(() => {
      window.__audios = [];
      const reproducir = HTMLMediaElement.prototype.play;
      HTMLMediaElement.prototype.play = function () {
        window.__audios.push(this);
        return reproducir.call(this);
      };
    });
    // El catálogo simulado incluye una voz Piper a propósito: la prueba comprueba que la 6.0
    // NO la usa (solo voz grabada; pedidos.voz debe quedar vacío).
    await context.route('**/api/voz/config', r => r.fulfill({json: {
      voces: [{id: 'piper:prueba', nombre: 'Prueba', motor: 'piper', idioma: 'es', region: 'MX', disponible: true}],
      grabadas: {es: estado.grabadas, 'pt-BR': 0},
    }}));
    await context.route('**/api/voz/grabada', async r => {
      pedidos.grabada++;
      if (estado.retraso) await new Promise(f => setTimeout(f, estado.retraso));
      if (estado.fallo) return r.abort('internetdisconnected');
      if (estado.grabada) { try { await r.fulfill({body: AUDIO, contentType: 'audio/wav'}); } catch { /* cancelada */ } }
      else await r.fulfill({status: 404, json: {grabada: false}});
    });
    await context.route('**/api/voz', async r => {
      pedidos.voz.push(JSON.parse(r.request().postData()));
      if (estado.retraso) await new Promise(f => setTimeout(f, estado.retraso));
      if (estado.fallo) return r.abort('internetdisconnected');
      try { await r.fulfill({body: AUDIO, contentType: 'audio/wav'}); } catch { /* cancelada */ }
    });
    await context.route('**/api/voz/cancelar', async r => { pedidos.cancelar++; await r.continue(); });

    const page = await context.newPage();
    const errores = [];
    page.on('pageerror', e => errores.push(e.message));
    const activos = () => page.evaluate(() => window.__audios.filter(a => !a.paused && a.getAttribute('src')).length);
    const ultimaVelocidad = () => page.evaluate(() => window.__audios.at(-1)?.playbackRate);
    const esperarActivo = () => page.waitForFunction(() => window.__audios.some(a => !a.paused && a.getAttribute('src')), null, {timeout: 5000});
    const repetir = () => page.locator('button[data-control="repetir"]').click();

    await page.goto(base);
    await page.getByRole('button', {name: 'Comenzar'}).click();
    await page.getByRole('button', {name: 'Yo elijo'}).click();
    await page.locator('.tarjeta-animal').first().click();
    await page.locator('.reto-pantalla').waitFor();

    await caso('con grabación disponible se usa el audio grabado', async () => {
      await esperarActivo();
      assert.ok(pedidos.grabada >= 1);
      assert.equal(pedidos.voz.length, 0, 'no se sintetiza si hay grabación');
      assert.equal(await activos(), 1);
      assert.equal(await ultimaVelocidad(), 0.95);
    });

    await caso('Repetir relee y nunca suenan dos voces a la vez', async () => {
      const antes = await page.evaluate(() => window.__audios.length);
      await repetir();
      await page.waitForFunction(n => window.__audios.length > n, antes);
      await esperarActivo();
      assert.equal(await activos(), 1);
      assert.ok(await page.evaluate(() => window.__audios.slice(0, -1).every(a => a.paused)), 'la lectura anterior se detuvo');
    });

    await caso('sin grabación la guía no lee con otra voz', async () => {
      estado.grabada = false;
      const antes = await page.evaluate(() => window.__audios.length);
      await repetir();
      await page.waitForTimeout(800);
      assert.equal(pedidos.voz.length, 0, 'no se pide voz sintetizada');
      assert.equal(await page.evaluate(() => window.__audios.length), antes);
      assert.equal(await activos(), 0);
      estado.grabada = true;
    });

    await caso('la velocidad elegida se aplica a la lectura', async () => {
      await page.getByRole('button', {name: 'Preferencias'}).click();
      await page.getByLabel('Ritmo de lectura').selectOption('0.8');
      await page.keyboard.press('Escape');
      const antes = await page.evaluate(() => window.__audios.length);
      await repetir();
      await page.waitForFunction(n => window.__audios.length > n, antes);
      assert.equal(await ultimaVelocidad(), 0.8);
    });

    await caso('Pausar cancela una lectura pendiente', async () => {
      estado.retraso = 1500;
      const cancelaciones = pedidos.cancelar;
      const audios = await page.evaluate(() => window.__audios.length);
      await repetir();
      await page.locator('button[data-control="pausar"]').click();
      await page.locator('.cierre[data-estado="PAUSADA"]').waitFor();
      await page.waitForTimeout(2000);
      assert.ok(pedidos.cancelar > cancelaciones, 'se avisa al servidor de la cancelación');
      assert.equal(await activos(), 0, 'nada suena en pausa');
      assert.equal(await page.evaluate(() => window.__audios.length), audios, 'la lectura cancelada no llega a sonar');
      estado.retraso = 0;
      await page.locator('button[data-control="reanudar"]').click();
      await page.locator('.reto-pantalla').waitFor();
    });

    await caso('con la voz desactivada no se pide ningún audio', async () => {
      await page.getByRole('button', {name: 'Preferencias'}).click();
      await page.getByRole('switch', {name: /Una guía con voz/}).uncheck();
      await page.keyboard.press('Escape');
      assert.equal(await activos(), 0, 'desactivar la voz detiene la lectura');
      const antes = {g: pedidos.grabada, v: pedidos.voz.length};
      await repetir();
      await page.waitForTimeout(800);
      assert.deepEqual({g: pedidos.grabada, v: pedidos.voz.length}, antes);
      await page.getByRole('button', {name: 'Preferencias'}).click();
      await page.getByRole('switch', {name: /Una guía con voz/}).check();
      await page.keyboard.press('Escape');
    });

    await caso('sin conexión con la voz: aviso persistente y la partida sigue', async () => {
      estado.fallo = true;
      await repetir();
      const aviso = page.getByRole('alert');
      await aviso.waitFor();
      assert.match(await aviso.textContent(), /No se pudo reproducir la voz/);
      await page.waitForTimeout(500);
      assert.equal(await aviso.count(), 1, 'el aviso no desaparece solo');
      estado.fallo = false;
      const mensaje = await page.locator('#mensaje').textContent();
      await page.locator('button[data-control="ayuda"]').click();
      await page.waitForFunction(t => document.querySelector('#mensaje').textContent !== t, mensaje);
      await aviso.getByRole('button', {name: 'Cerrar notificación'}).click();
      assert.equal(await page.getByRole('alert').count(), 0);
    });

    await caso('Preferencias: una sola voz (Marcela) y bloqueada en pt-BR', async () => {
      await page.getByRole('button', {name: 'Preferencias'}).click();
      const selector = page.locator('#pref-voces');
      assert.deepEqual(await selector.locator('option').allTextContents(), ['Marcela · ElevenLabs']);
      assert.equal(await selector.isDisabled(), false);
      await page.locator('#pref-idioma').selectOption('pt-BR');
      await page.waitForFunction(() => document.documentElement.lang === 'pt-BR');
      assert.ok(await selector.isDisabled(), 'selector bloqueado en pt-BR');
      assert.ok(await page.getByRole('switch', {name: /voz/i}).first().isDisabled());
      assert.ok(await page.locator('.pref-probar').isDisabled());
      const antes = pedidos.grabada + pedidos.voz.length;
      await page.keyboard.press('Escape');
      await repetir();
      await page.waitForTimeout(800);
      assert.equal(pedidos.grabada + pedidos.voz.length, antes, 'en pt-BR no se pide audio');
      await page.getByRole('button', {name: /Preferências|Preferencias/}).click();
      await page.locator('#pref-idioma').selectOption('es');
      await page.waitForFunction(() => document.documentElement.lang === 'es');
      await page.keyboard.press('Escape');
    });

    await caso('sin grabaciones en el idioma no se piden ni suena nada', async () => {
      estado.grabadas = 0;
      await page.reload();
      await page.locator('.reto-pantalla').waitFor();
      const antes = pedidos.grabada;
      await repetir();
      await page.waitForTimeout(800);
      assert.equal(pedidos.grabada, antes);
      assert.equal(pedidos.voz.length, 0);
    });

    assert.deepEqual(errores, []);
    console.log(JSON.stringify({casos: casos.length, resultado: 'OK'}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
