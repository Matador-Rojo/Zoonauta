/* Recorrido del prototipo 6.0 (React + TS + Vite servido por Python en /v6/).
   Portada de 8 paisajes → modalidad → catálogo → reto → Pista → Repetir → recarga.
   Sin descargar voces: la voz se desactiva para no depender de modelos. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = (process.env.INTERFAZ_URL || 'http://127.0.0.1:8000') + '/v6/';
const out = path.resolve(process.env.INTERFAZ_SALIDA || 'output/v6/navegador');
fs.mkdirSync(out, {recursive: true});
const ORDEN = ['H01', 'H09', 'H17', 'H22', 'H20', 'H37', 'H21', 'H25'];
const casos = [];
async function axe(page, nombre) {
  if (!process.env.AXE_SOURCE) return [];
  await page.addScriptTag({path: process.env.AXE_SOURCE});
  const r = await page.evaluate(() => window.axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']}));
  fs.writeFileSync(path.join(out, `axe_${nombre}.json`), JSON.stringify(r.violations, null, 2));
  return r.violations.map(v => `${nombre}: ${v.id} (${v.impact}) ${v.nodes.map(n => n.target.join(' ')).join(', ')}`);
}
const incidencias = [];
// /api/voz/grabada responde 404 cuando un mensaje no tiene grabación: es lo previsto
// (el cliente lee entonces con la voz alternativa).
const esperado404 = r => r.status() === 404 && new URL(r.url()).pathname === '/api/voz/grabada';
const caso = async (nombre, fn) => { await fn(); casos.push(nombre); };

(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 900}, reducedMotion: 'no-preference', bypassCSP: true});
    const page = await context.newPage();
    const errores = [];
    page.on('pageerror', e => errores.push(e.message));
    // Las respuestas con error se registran por URL; el aviso genérico de consola se omite.
    page.on('console', m => { if (m.type() === 'error' && !m.text().startsWith('Failed to load resource')) errores.push(m.text()); });
    page.on('response', r => { if (r.status() >= 400 && !esperado404(r)) errores.push(`${r.status()} ${new URL(r.url()).pathname}`); });
    await page.goto(base);
    await page.locator('#titulo-pantalla').waitFor();

    await caso('portada con exactamente ocho paisajes en orden', async () => {
      const vistos = [];
      for (let i = 0; i < 8; i++) {
        vistos.push(await page.locator('.portada-capa[data-estado="actual"]').getAttribute('data-habitat'));
        assert.equal(await page.locator('.carrusel-contador').textContent(), `${i + 1} / 8`);
        await page.getByRole('button', {name: 'Siguiente paisaje'}).click();
      }
      assert.deepEqual(vistos, ORDEN);
      assert.equal(await page.locator('.portada-capa[data-estado="actual"]').getAttribute('data-habitat'), 'H01');
      // Solo se montan actual, anterior y siguiente: nunca los ocho a la vez.
      assert.ok(await page.locator('.portada-capa').count() <= 3);
      await page.waitForTimeout(1600); // fin del fundido para la captura
      await page.screenshot({path: path.join(out, '01_portada.png')});
    });

    await caso('anuncio solo en cambios pedidos y pausa sin aria-pressed', async () => {
      assert.match(await page.locator('.carrusel [role="status"]').textContent(), /Paisaje \d de 8/);
      const pausa = page.getByRole('button', {name: 'Pausar paisajes'});
      assert.equal(await pausa.getAttribute('aria-pressed'), null);
      await pausa.click();
      await page.getByRole('button', {name: 'Reanudar paisajes'}).click();
    });

    await caso('reducir movimiento: fotos estáticas, sin pausa automática ni animaciones', async () => {
      await page.getByRole('button', {name: 'Preferencias'}).click();
      await page.getByRole('switch', {name: /Reducir movimiento/}).check();
      await page.getByRole('switch', {name: /Una guía con voz/}).uncheck();
      await page.keyboard.press('Escape');
      assert.equal(await page.evaluate(() => document.documentElement.dataset.movimiento), 'reducido');
      assert.equal(await page.getByRole('button', {name: /paisajes$/}).count(), 0);
      // Los cambios de color de los botones se mantienen (no son movimiento).
      const animaciones = () => page.evaluate(() => document.getAnimations()
        .filter(a => !/(color|box-shadow)$/.test(a.transitionProperty || ''))
        .map(a => `${a.constructor.name}:${a.animationName || a.transitionProperty}:${a.effect?.target?.className}`));
      // Los fundidos iniciados antes de activar la opción duran como máximo 1,4 s.
      await page.waitForTimeout(1500);
      assert.deepEqual(await animaciones(), []);
      await page.getByRole('button', {name: 'Siguiente paisaje'}).click();
      assert.deepEqual(await animaciones(), [], 'el cambio manual es instantáneo');
      assert.equal(await page.locator('.carrusel-contador').textContent(), '2 / 8');
    });

    await caso('selector de modalidad nativo con foco inicial y Esc', async () => {
      await page.getByRole('button', {name: 'Comenzar'}).click();
      const dialogo = page.locator('dialog.selector-modalidad');
      assert.ok(await dialogo.evaluate(d => d.open && d.matches(':modal')));
      assert.equal(await page.evaluate(() => document.activeElement.textContent.trim()), 'Yo elijo');
      await page.keyboard.press('Escape');
      assert.equal(await dialogo.evaluate(d => d.open), false);
      assert.equal(await page.evaluate(() => document.activeElement.textContent.trim()), 'Comenzar');
      await page.getByRole('button', {name: 'Comenzar'}).click();
      await page.getByRole('button', {name: 'Yo elijo'}).click();
      await page.locator('.catalogo-pantalla').waitFor();
    });

    await caso('catálogo: 288 animales, búsqueda y paginación', async () => {
      assert.equal(await page.locator('.catalogo-total').textContent(), '288 animales para explorar');
      assert.equal(await page.locator('.tarjeta-animal').count(), 6);
      await page.getByRole('button', {name: 'Siguientes'}).click();
      assert.equal(await page.locator('.paginacion-estado').textContent(), 'Página 2 de 48');
      await page.waitForFunction(() => document.activeElement.classList.contains('tarjeta-animal'), null, {timeout: 2000});
      await page.getByRole('searchbox', {name: 'Buscar animal'}).fill('jaguar');
      assert.equal(await page.locator('.tarjeta-animal').count(), 1);
      incidencias.push(...await axe(page, 'catalogo'));
      await page.screenshot({path: path.join(out, '02_catalogo.png')});
      await page.locator('.tarjeta-animal[data-animal="A01"]').click();
      await page.locator('.reto-pantalla').waitFor();
    });

    // Retrasa el servidor y las imágenes para comprobar que Pista y Repetir no parpadean.
    await page.route('**/api/accion', async r => { await new Promise(f => setTimeout(f, 400)); await r.continue(); });
    await page.route('**/media/**', async r => { await new Promise(f => setTimeout(f, 300)); await r.continue(); });

    await caso('Pista conserva tablero y foco, y cambia la guía completa', async () => {
      const marcar = () => page.evaluate(() => {
        window.__retrato = document.querySelector('.animal-actual img');
        window.__tarjetas = [...document.querySelectorAll('.tarjeta-habitat')];
      });
      await marcar();
      const antes = await page.locator('#mensaje').textContent();
      const pista = page.locator('button[data-control="ayuda"]');
      await pista.focus();
      await pista.press('Enter');
      // Durante la espera, el tablero sigue intacto y con la guía anterior.
      await page.waitForTimeout(200);
      assert.equal(await page.locator('#mensaje').textContent(), antes);
      assert.equal(await page.locator('.tira .tira-celda').count() > 0, true);
      await page.waitForFunction(t => document.querySelector('#mensaje').textContent !== t, antes);
      const intacto = await page.evaluate(() => window.__retrato === document.querySelector('.animal-actual img') &&
        window.__tarjetas.every(t => t.isConnected));
      assert.ok(intacto, 'el animal y las tarjetas no se reconstruyen');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.control), 'ayuda');
      // Texto y pictogramas llegan juntos: todas las imágenes de la guía ya están decodificadas.
      assert.ok(await page.evaluate(() => [...document.querySelectorAll('.tira img')].every(i => i.complete && i.naturalWidth > 0)));
      incidencias.push(...await axe(page, 'tablero'));
      await page.screenshot({path: path.join(out, '03_pista.png')});
    });

    await caso('Repetir conserva la guía exacta y el foco', async () => {
      const antes = await page.locator('.guia').innerHTML();
      const repetir = page.locator('button[data-control="repetir"]');
      await repetir.focus();
      const respuesta = page.waitForResponse('**/api/accion');
      await repetir.press('Enter');
      assert.equal((await (await respuesta).json()).aceptada, true);
      await page.waitForTimeout(100);
      assert.equal(await page.locator('.guia').innerHTML(), antes);
      assert.equal(await page.evaluate(() => document.activeElement.dataset.control), 'repetir');
    });

    await caso('recarga recupera la misma partida y reto', async () => {
      const v1 = await page.evaluate(async () => (await fetch('/api/vista')).json());
      await page.unroute('**/api/accion');
      await page.unroute('**/media/**');
      await page.reload();
      await page.locator('.reto-pantalla').waitFor();
      const v2 = await page.evaluate(async () => (await fetch('/api/vista')).json());
      assert.equal(v2.sesion_id, v1.sesion_id);
      assert.equal(v2.reto_id, v1.reto_id);
      assert.equal(await page.locator('.animal-actual strong').textContent(), 'Jaguar');
      assert.equal(await page.evaluate(() => document.documentElement.dataset.movimiento), 'reducido');
    });

    await caso('pausa con el robot existente y reanudación', async () => {
      await page.locator('button[data-control="pausar"]').click();
      await page.locator('.cierre[data-estado="PAUSADA"]').waitFor();
      assert.match(await page.locator('.cierre-visual img').getAttribute('src'), /robot_pausa\.webp$/);
      assert.equal(await page.evaluate(() => document.activeElement.dataset.control), 'reanudar');
      incidencias.push(...await axe(page, 'pausa'));
      await page.locator('button[data-control="reanudar"]').click();
      await page.locator('.reto-pantalla').waitFor();
    });

    await caso('móvil sin desplazamiento horizontal', async () => {
      await page.setViewportSize({width: 375, height: 812});
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path: path.join(out, '04_reto_movil.png'), fullPage: true});
    });

    assert.deepEqual(incidencias, [], 'axe-core sin incidencias');
    assert.deepEqual(errores, []);
    console.log(JSON.stringify({casos: casos.length, resultado: 'OK'}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
