/* Portada 6.0 «Bosque de luz» (/v6/): ocupa la vista sin desplazamiento en varios tamaños,
   fondo aprobado fijo (sin capas, filtros ni animación), sin pictogramas, Comenzar abre
   «¿Quién elige el animal?», Preferencias se abre encima sin empujar nada, movimiento
   reducido y accesibilidad automatizada (axe-core si AXE_SOURCE apunta a axe.min.js).
   La portada 5.0 de 48 fondos se prueba con --portada-5. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = (process.env.INTERFAZ_URL || 'http://127.0.0.1:8000') + '/';
const out = path.resolve(process.env.INTERFAZ_SALIDA || 'output/v6/portada');
fs.mkdirSync(out, {recursive: true});
const casos = [];
const caso = async (nombre, fn) => { await fn(); casos.push(nombre); };
const VISTAS = [['escritorio', 1440, 900, false], ['portatil', 1280, 720, false], ['movil', 390, 844, true],
  ['movil-pequeno', 320, 568, true], ['apaisado', 844, 390, true]];

// Sin desplazamiento de página y con los elementos clave dentro de la vista.
const encaje = page => page.evaluate(() => {
  const fuera = [];
  for (const sel of ['.cabecera .marca', '.cabecera [aria-haspopup="dialog"]', '#titulo-pantalla', '.portada-descripcion', '.portada-comenzar', 'dialog[open]']) {
    const e = document.querySelector(sel);
    if (!e || getComputedStyle(e).display === 'none') continue;
    const r = e.getBoundingClientRect();
    if (r.left < -0.5 || r.top < -0.5 || r.right > innerWidth + 0.5 || r.bottom > innerHeight + 0.5) fuera.push(sel);
  }
  return {vertical: document.documentElement.scrollHeight - innerHeight, horizontal: document.documentElement.scrollWidth - innerWidth, fuera};
});

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
    // bypassCSP solo para inyectar axe-core; la CSP real del servidor no cambia.
    const page = await nueva({viewport: {width: 1440, height: 900}, reducedMotion: 'no-preference', bypassCSP: true});
    await page.goto(base);
    await page.locator('.portada-paisaje').waitFor();

    await caso('fondo aprobado fijo, textos y sin pictogramas', async () => {
      const img = page.locator('.portada-paisaje');
      await img.evaluate(i => i.decode());
      assert.match(await img.evaluate(i => i.currentSrc), /bosque-de-luz-(960|1672)-[\w-]+\.webp$/);
      assert.equal(await img.evaluate(i => i.getAnimations().length + (getComputedStyle(i).filter === 'none' ? 0 : 1)), 0);
      assert.equal(await page.locator('#titulo-pantalla').innerText(), 'Descubre el\nbosque de luz.');
      assert.equal(await page.locator('.portada-descripcion').textContent(), 'Elige un animal. Sigue las pistas y descubre dónde vive.');
      assert.equal(await page.locator('.portada img:not(dialog img)').count(), 1, 'la única imagen de la portada es el fondo');
      assert.equal(await page.locator('.cabecera-nota, .carrusel, .resumen-inicio').count(), 0);
    });

    await caso('ocupa la vista sin desplazamiento, también con los diálogos abiertos', async () => {
      for (const [nombre, w, h, movil] of VISTAS) {
        const p = await nueva({viewport: {width: w, height: h}, isMobile: movil, hasTouch: movil, reducedMotion: 'reduce'});
        await p.goto(base);
        await p.locator('.portada-comenzar').waitFor();
        assert.deepEqual(await encaje(p), {vertical: 0, horizontal: 0, fuera: []}, `${nombre} portada`);
        await p.screenshot({path: path.join(out, `${nombre}_portada.png`)});
        await p.locator('.portada-comenzar').click();
        assert.deepEqual(await encaje(p), {vertical: 0, horizontal: 0, fuera: []}, `${nombre} selector`);
        // «Volver al inicio» a la vista: el selector no se desplaza por dentro.
        assert.ok(await p.locator('dialog.selector-modalidad').evaluate(d => d.scrollHeight <= d.clientHeight + 1), `${nombre}: selector sin desplazamiento interno`);
        await p.keyboard.press('Escape');
        await p.getByRole('button', {name: 'Preferencias'}).click();
        assert.deepEqual(await encaje(p), {vertical: 0, horizontal: 0, fuera: []}, `${nombre} preferencias`);
        await p.screenshot({path: path.join(out, `${nombre}_preferencias.png`)});
        await p.context().close();
      }
    });

    await caso('Comenzar abre «¿Quién elige el animal?» y Escape vuelve con el foco', async () => {
      const comenzar = page.getByRole('button', {name: 'Comenzar'});
      const caja = await comenzar.boundingBox();
      assert.ok(caja.height >= 48 && caja.width >= 120, 'Comenzar es la acción más visible');
      await comenzar.click();
      await page.getByRole('heading', {name: '¿Quién elige el animal?'}).waitFor();
      assert.equal(await page.getByRole('button', {name: 'Yo elijo'}).count(), 1);
      assert.equal(await page.getByRole('button', {name: 'El agente elige'}).count(), 1);
      await page.keyboard.press('Escape');
      assert.equal(await page.evaluate(() => document.activeElement.textContent.trim()), 'Comenzar');
    });

    await caso('axe-core en la portada, el selector y Preferencias', async () => {
      const v1 = await axe(page, 'portada');
      if (v1 === null) return;
      await page.getByRole('button', {name: 'Comenzar'}).click();
      const v2 = await axe(page, 'selector');
      await page.keyboard.press('Escape');
      await page.getByRole('button', {name: 'Preferencias'}).click();
      const v3 = await axe(page, 'preferencias');
      await page.keyboard.press('Escape');
      assert.deepEqual([...v1, ...v2, ...v3], []);
    });

    // --- Sistema con movimiento reducido ---
    const quieta = await nueva({viewport: {width: 1440, height: 900}, reducedMotion: 'reduce'});
    await quieta.goto(base);
    await quieta.locator('.portada-comenzar').waitFor();
    await caso('con prefers-reduced-motion: sin animaciones y el interruptor lo refleja', async () => {
      assert.equal(await quieta.evaluate(() => document.documentElement.dataset.movimiento), 'reducido');
      // Ni animaciones ni transiciones de movimiento (los cambios de color no son movimiento).
      assert.deepEqual(await quieta.evaluate(() => document.getAnimations()
        .filter(a => a.animationName || /transform|translate|scale/.test(a.transitionProperty || ''))
        .map(a => a.animationName || a.transitionProperty)), []);
      await quieta.getByRole('button', {name: 'Preferencias'}).click();
      const interruptor = quieta.getByRole('switch', {name: /Reducir movimiento/});
      assert.ok(await interruptor.isChecked());
      assert.ok(await interruptor.isDisabled());
      await quieta.keyboard.press('Escape');
    });

    // --- Móvil táctil ---
    const movil = await nueva({viewport: {width: 375, height: 812}, isMobile: true, hasTouch: true, deviceScaleFactor: 2, reducedMotion: 'no-preference'});
    await movil.goto(base);
    await movil.locator('.portada-comenzar').waitFor();
    await caso('móvil: controles táctiles y selector', async () => {
      for (const control of await movil.locator('.cabecera button, .portada-comenzar').all()) {
        const caja = await control.boundingBox();
        assert.ok(caja.width >= 44 && caja.height >= 44, 'área táctil mínima 44 × 44');
      }
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
