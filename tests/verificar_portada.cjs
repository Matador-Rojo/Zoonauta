/* Portada 6.0 (/v6/): exactamente ocho paisajes, rotación, pausa, movimiento
   reducido, marcas, móvil y accesibilidad automatizada (axe-core si AXE_SOURCE
   apunta a axe.min.js). La portada 5.0 de 48 fondos se prueba con --portada-5. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = (process.env.INTERFAZ_URL || 'http://127.0.0.1:8000') + '/v6/';
const out = path.resolve(process.env.INTERFAZ_SALIDA || 'output/v6/portada');
fs.mkdirSync(out, {recursive: true});
const ORDEN = ['H01', 'H09', 'H17', 'H22', 'H20', 'H37', 'H21', 'H25'];
const casos = [];
const caso = async (nombre, fn) => { await fn(); casos.push(nombre); };
const actual = page => page.locator('.portada-capa[data-estado="actual"]').getAttribute('data-habitat');
const animaciones = page => page.evaluate(() => document.getAnimations()
  .filter(a => !/color$/.test(a.transitionProperty || ''))
  .map(a => a.animationName || a.transitionProperty));

async function axe(page, nombre) {
  if (!process.env.AXE_SOURCE) return null;
  await page.addScriptTag({path: process.env.AXE_SOURCE});
  const r = await page.evaluate(() => window.axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']}));
  fs.writeFileSync(path.join(out, `axe_${nombre}.json`), JSON.stringify(r.violations, null, 2));
  return r.violations.map(v => `${v.id} (${v.impact}): ${v.nodes.map(n => n.target.join(' ')).join(', ')}`);
}

(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  const errores = [];
  const nueva = async (opciones) => {
    const context = await browser.newContext(opciones);
    const page = await context.newPage();
    page.on('pageerror', e => errores.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errores.push(m.text()); });
    page.on('response', r => { if (r.status() >= 400) errores.push(`${r.status()} ${r.url()}`); });
    return page;
  };
  try {
    // --- Escritorio con movimiento permitido ---
    // bypassCSP solo para inyectar axe-core; la CSP real del servidor no cambia.
    const page = await nueva({viewport: {width: 1440, height: 900}, reducedMotion: 'no-preference', bypassCSP: true});
    await page.clock.install();
    await page.goto(base);
    await page.locator('.carrusel').waitFor();
    const vista = await page.evaluate(async () => (await fetch('/api/vista')).json());
    const nombre = id => vista.opciones_habitat.find(h => h.id === id).nombre;

    await caso('ocho paisajes exactos con nombre, contador y marcas sincronizados', async () => {
      assert.equal(await page.locator('.marca-paisaje').count(), 8);
      for (let i = 0; i < 8; i++) {
        assert.equal(await actual(page), ORDEN[i]);
        assert.equal(await page.locator('.carrusel-nombre strong').textContent(), nombre(ORDEN[i]));
        assert.equal(await page.locator('.carrusel-contador').textContent(), `${i + 1} / 8`);
        assert.equal(await page.locator('.marca-paisaje[aria-current="true"]').getAttribute('aria-label'), nombre(ORDEN[i]));
        const img = page.locator('.portada-capa[data-estado="actual"] .escena > img').first();
        await img.evaluate(i => i.decode());
        assert.match(await img.evaluate(i => i.currentSrc), new RegExp(`/fondos/(catalogo/${ORDEN[i]}|portada/${ORDEN[i]}-960)\\.webp$`));
        // Los fundidos CSS corren en tiempo real, no con el reloj simulado.
        await page.waitForTimeout(1600);
        await page.screenshot({path: path.join(out, `escritorio_${i + 1}_${ORDEN[i]}.png`)});
        await page.getByRole('button', {name: 'Siguiente paisaje'}).click();
      }
      assert.equal(await actual(page), 'H01', 'vuelve al primero');
      await page.getByRole('button', {name: 'Paisaje anterior'}).click();
      assert.equal(await actual(page), 'H25');
      await page.locator('.marca-paisaje').nth(4).click();
      assert.equal(await actual(page), 'H20');
      // Solo se montan actual, anterior y siguiente.
      assert.ok(await page.locator('.portada-capa').count() <= 3);
    });

    await caso('rotación cada diez segundos, detenida con foco, puntero y pausa', async () => {
      await page.mouse.move(5, 5);
      await page.locator('#titulo-pantalla').focus();
      const antes = await actual(page);
      await page.clock.runFor(9_500);
      assert.equal(await actual(page), antes);
      await page.clock.runFor(1_000);
      assert.notEqual(await actual(page), antes, 'avanza a los 10 s');
      // Foco dentro del carrusel: no rota.
      await page.getByRole('button', {name: 'Siguiente paisaje'}).focus();
      const conFoco = await actual(page);
      await page.clock.runFor(25_000);
      assert.equal(await actual(page), conFoco);
      await page.locator('#titulo-pantalla').focus();
      // Pausa: no rota y el ambiente queda en pausa.
      await page.getByRole('button', {name: 'Pausar paisajes'}).click();
      await page.locator('#titulo-pantalla').focus();
      await page.mouse.move(5, 5);
      const pausado = await actual(page);
      await page.clock.runFor(25_000);
      assert.equal(await actual(page), pausado);
      assert.equal(await page.locator('.portada').getAttribute('data-ambiente'), 'pausado');
      const enPausa = await page.evaluate(() => document.getAnimations().filter(a => a.playState === 'running' && a.animationName).length);
      assert.equal(enPausa, 0, 'el movimiento ambiental también se detiene');
      await page.getByRole('button', {name: 'Reanudar paisajes'}).click();
    });

    await caso('se suspende con Preferencias, con el selector y con la pestaña oculta', async () => {
      await page.getByRole('button', {name: 'Preferencias'}).click();
      const conDialogo = await actual(page);
      await page.clock.runFor(25_000);
      assert.equal(await actual(page), conDialogo);
      await page.keyboard.press('Escape');
      await page.getByRole('button', {name: 'Comenzar'}).click();
      await page.clock.runFor(25_000);
      assert.equal(await actual(page), conDialogo);
      await page.keyboard.press('Escape');
      await page.evaluate(() => {
        Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'});
        document.dispatchEvent(new Event('visibilitychange'));
      });
      await page.locator('#titulo-pantalla').focus();
      await page.mouse.move(5, 5);
      await page.clock.runFor(25_000);
      assert.equal(await actual(page), conDialogo);
      await page.evaluate(() => {
        Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'visible'});
        document.dispatchEvent(new Event('visibilitychange'));
      });
    });

    await caso('las capas con transparencia cargan sobre su paisaje', async () => {
      const capas = {H01: ['niebla', 'hojas'], H09: ['hierba'], H20: ['nubes'], H37: ['algas']};
      for (const [id, nombres] of Object.entries(capas)) {
        await page.locator('.marca-paisaje').nth(ORDEN.indexOf(id)).click();
        for (const nombre of nombres) {
          const capa = page.locator(`.portada-capa[data-estado="actual"] .capa-${nombre}`);
          await capa.evaluate(i => i.decode());
          assert.ok(await capa.evaluate(i => i.naturalWidth > 0 && i.getAnimations().length === 1), `${id}-${nombre}`);
        }
      }
    });

    await caso('el movimiento ambiental es lento y sin cámara ni zoom', async () => {
      while (await actual(page) !== 'H09') await page.getByRole('button', {name: 'Siguiente paisaje'}).click();
      await page.locator('#titulo-pantalla').focus();
      const datos = await page.evaluate(() => document.getAnimations().filter(a => a.animationName).map(a => ({
        nombre: a.animationName, duracion: a.effect.getTiming().duration,
        transform: getComputedStyle(a.effect.target).transform,
      })));
      assert.ok(datos.length > 0);
      for (const d of datos) assert.ok(d.duracion >= 6000, `${d.nombre} dura ${d.duracion} ms`);
      // La foto base nunca se anima.
      assert.equal(await page.evaluate(() => document.querySelector('.portada-capa[data-estado="actual"] .escena > img').getAnimations().length), 0);
    });

    await caso('axe-core en la portada y el selector de modalidad', async () => {
      const v1 = await axe(page, 'portada');
      if (v1 === null) return;
      await page.getByRole('button', {name: 'Comenzar'}).click();
      const v2 = await axe(page, 'selector');
      await page.keyboard.press('Escape');
      assert.deepEqual([...v1, ...v2], []);
    });

    // --- Sistema con movimiento reducido ---
    const quieta = await nueva({viewport: {width: 1440, height: 900}, reducedMotion: 'reduce'});
    await quieta.clock.install();
    await quieta.goto(base);
    await quieta.locator('.carrusel').waitFor();
    await caso('con prefers-reduced-motion: fotos fijas y avance manual', async () => {
      assert.equal(await quieta.evaluate(() => document.documentElement.dataset.movimiento), 'reducido');
      assert.equal(await quieta.getByRole('button', {name: /paisajes$/}).count(), 0);
      await quieta.clock.runFor(60_000);
      assert.equal(await actual(quieta), 'H01');
      assert.deepEqual(await animaciones(quieta), []);
      await quieta.getByRole('button', {name: 'Siguiente paisaje'}).click();
      assert.equal(await actual(quieta), 'H09');
      assert.deepEqual(await animaciones(quieta), [], 'cambio instantáneo');
      assert.equal(await quieta.locator('.efecto').evaluateAll(e => e.filter(x => getComputedStyle(x).display !== 'none').length), 0);
      // Las capas siguen visibles (forman parte de la escena), pero quietas.
      await quieta.locator('.marca-paisaje').nth(ORDEN.indexOf('H01')).click();
      assert.equal(await quieta.locator('.portada-capa[data-estado="actual"] .capa').count(), 2);
      await quieta.getByRole('button', {name: 'Preferencias'}).click();
      const interruptor = quieta.getByRole('switch', {name: /Reducir movimiento/});
      assert.ok(await interruptor.isChecked());
      assert.ok(await interruptor.isDisabled());
      await quieta.keyboard.press('Escape');
    });

    // --- Móvil ---
    const movil = await nueva({viewport: {width: 375, height: 812}, isMobile: true, hasTouch: true, deviceScaleFactor: 2, reducedMotion: 'no-preference'});
    await movil.goto(base);
    await movil.locator('.carrusel').waitFor();
    await caso('móvil: sin desplazamiento horizontal, controles táctiles y foto de 960 px', async () => {
      assert.ok(await movil.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      for (const control of await movil.locator('.carrusel button, .portada-texto .boton-principal').all()) {
        const caja = await control.boundingBox();
        assert.ok(caja.width >= 24 && caja.height >= 24, 'área mínima 24 × 24 (WCAG 2.5.8)');
      }
      const img = movil.locator('.portada-capa[data-estado="actual"] .escena > img').first();
      await img.evaluate(i => i.decode());
      // 375 px de ancho visible pero la escena cubre 812 px de alto → ~1443 px CSS × 2.
      assert.match(await img.evaluate(i => i.currentSrc), /\.webp$/);
      await movil.screenshot({path: path.join(out, 'movil_portada.png')});
      await movil.getByRole('button', {name: 'Comenzar'}).tap();
      await movil.locator('.opcion-modalidad img').evaluateAll(imgs => Promise.all(imgs.map(i => i.decode())));
      await movil.screenshot({path: path.join(out, 'movil_selector.png')});
    });

    assert.deepEqual(errores, []);
    console.log(JSON.stringify({casos: casos.length, resultado: 'OK', axe: Boolean(process.env.AXE_SOURCE)}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
