/* Captura cada pantalla en la 5.0 («/») y en la 6.0 («/v6/») con la MISMA sesión, en escritorio,
   portátil y móvil. Lo usa tests/comparar_versiones.py, que las junta lado a lado.
   Además mide el desplazamiento de cada página (medidas.json): la 6.0 no debe desplazarse.
   Uso: node comparar_versiones.cjs <url base> <carpeta de salida> <json de cookies por pantalla> */
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [, , base, salida, cookiesJson] = process.argv;
const cookies = JSON.parse(cookiesJson);
const VIEWPORTS = {
  escritorio: {width: 1440, height: 900},
  portatil: {width: 1280, height: 720},
  movil: {width: 390, height: 844},
  // Vistas bajas: comprueban que nada se aplasta (zoom 200 % de 1440×900, móvil pequeño y apaisado).
  zoom200: {width: 720, height: 450},
  'movil-pequeno': {width: 360, height: 640},
  apaisado: {width: 844, height: 390},
};
const MOVILES = new Set(['movil', 'movil-pequeno', 'apaisado']);
const VERSIONES = {'5.0': '/', '6.0': '/v6/'};
// Pantallas que se abren desde la interfaz (no desde la API): botón a pulsar en cada versión.
const PULSAR = {modalidad: {'5.0': 'button.comenzar', '6.0': 'main [aria-haspopup="dialog"]'}};

(async () => {
  fs.mkdirSync(salida, {recursive: true});
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  const medidas = [];
  try {
    for (const [pantalla, valor] of Object.entries(cookies)) {
      for (const [nombreVp, viewport] of Object.entries(VIEWPORTS)) {
        for (const [version, ruta] of Object.entries(VERSIONES)) {
          // Movimiento reducido: capturas estables, sin fundidos a medias.
          const context = await browser.newContext({viewport, reducedMotion: 'reduce', isMobile: MOVILES.has(nombreVp), deviceScaleFactor: 1});
          await context.addCookies([{name: 'habitats', value: valor, url: base}]);
          const page = await context.newPage();
          await page.goto(base + ruta);
          await page.waitForLoadState('load');
          await page.waitForTimeout(2200);
          if (PULSAR[pantalla]) { await page.click(PULSAR[pantalla][version]); await page.waitForTimeout(800); }
          medidas.push({version, pantalla, vista: nombreVp, ...(await page.evaluate(() => ({
            desplazamientoVertical: Math.max(0, document.documentElement.scrollHeight - innerHeight),
            desplazamientoHorizontal: Math.max(0, document.documentElement.scrollWidth - innerWidth),
            // Alto mínimo de lo que se pulsa o se mira (solo selectores de la 6.0). Que no haya
            // desplazamiento no basta: también debe verse y poder pulsarse cada elemento.
            aplastados: [...document.querySelectorAll('.tarjeta-habitat, .tarjeta-animal, .control, .animal-actual img, .cierre-visual img, .tarjeta-imagen img, .tarjeta-habitat .paisaje, .opcion-modalidad, dialog[open]')]
              .filter(e => getComputedStyle(e).display !== 'none' && !e.closest('dialog:not([open])'))
              .map(e => {
                const r = e.getBoundingClientRect();
                // Controles ≥ 44 px (objetivo táctil); fotos e ilustraciones ≥ 48 px; tarjetas ≥ 56 px.
                // Un diálogo abierto no debe desplazarse por dentro (se aplica abajo, no por altura).
                if (e.matches('dialog')) return e.scrollHeight > e.clientHeight + 1 ? `dialogo-con-desplazamiento:${e.scrollHeight - e.clientHeight}px` : null;
                const minimo = e.matches('.control') ? 44 : e.matches('img') ? 48 : 56;
                const texto = e.querySelector('span:not(.tarjeta-numero)');
                const recortado = texto && e.matches('.tarjeta-habitat') && texto.getBoundingClientRect().height > r.height + 0.5;
                return r.height < minimo || recortado ? `${e.className.split(' ')[0]}:${Math.round(r.height)}px` : null;
              }).filter(Boolean),
          })))});
          await page.screenshot({path: path.join(salida, `${version}_${pantalla}_${nombreVp}.png`), fullPage: false});
          await context.close();
        }
      }
    }
    fs.writeFileSync(path.join(salida, 'medidas.json'), JSON.stringify(medidas, null, 1));
    console.log(JSON.stringify({ok: true, pantallas: Object.keys(cookies)}));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
