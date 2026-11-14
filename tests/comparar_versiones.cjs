/* Captura cada pantalla en la 5.0 («/») y en la 6.0 («/v6/») con la MISMA sesión, en escritorio y
   móvil. Lo usa tests/comparar_versiones.py, que las junta lado a lado.
   Uso: node comparar_versiones.cjs <url base> <carpeta de salida> <json de cookies por pantalla> */
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [, , base, salida, cookiesJson] = process.argv;
const cookies = JSON.parse(cookiesJson);
const VIEWPORTS = {escritorio: {width: 1440, height: 900}, movil: {width: 390, height: 844}};
const VERSIONES = {'5.0': '/', '6.0': '/v6/'};
// Pantallas que se abren desde la interfaz (no desde la API): botón a pulsar en cada versión.
const PULSAR = {modalidad: {'5.0': 'button.comenzar', '6.0': 'main [aria-haspopup="dialog"]'}};

(async () => {
  fs.mkdirSync(salida, {recursive: true});
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  try {
    for (const [pantalla, valor] of Object.entries(cookies)) {
      for (const [nombreVp, viewport] of Object.entries(VIEWPORTS)) {
        for (const [version, ruta] of Object.entries(VERSIONES)) {
          // Movimiento reducido: capturas estables, sin fundidos a medias.
          const context = await browser.newContext({viewport, reducedMotion: 'reduce', isMobile: nombreVp === 'movil', deviceScaleFactor: 1});
          await context.addCookies([{name: 'habitats', value: valor, url: base}]);
          const page = await context.newPage();
          await page.goto(base + ruta);
          await page.waitForLoadState('load');
          await page.waitForTimeout(2200);
          if (PULSAR[pantalla]) { await page.click(PULSAR[pantalla][version]); await page.waitForTimeout(800); }
          await page.screenshot({path: path.join(salida, `${version}_${pantalla}_${nombreVp}.png`), fullPage: false});
          await context.close();
        }
      }
    }
    console.log(JSON.stringify({ok: true, pantallas: Object.keys(cookies)}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
