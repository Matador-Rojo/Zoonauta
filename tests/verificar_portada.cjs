/* Verifica todos los fondos de la expedición ampliada en un navegador real. */
const assert = require("node:assert/strict");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = process.env.INTERFAZ_URL || "http://127.0.0.1:8000";

async function comprobarFoto(page, habitat) {
  const foto = await page.locator(".hero-paisaje").evaluate(async imagen => {
    await imagen.decode();
    return [imagen.dataset.habitat, imagen.getAttribute("src"),
      imagen.naturalWidth, imagen.naturalHeight];
  });
  assert.deepEqual(foto, [habitat.id, `/fondos/catalogo/${habitat.id}.webp`, 1920, 1080]);
  assert.equal(await page.locator(".hero-ficha strong").textContent(), habitat.nombre);
}

(async () => {
  const browser = await chromium.launch({
    headless: true, ...(process.env.CHROMIUM_EXECUTABLE && {
      executablePath: process.env.CHROMIUM_EXECUTABLE
    })
  });
  try {
    const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
    const errores = [];
    page.on("pageerror", error => errores.push(error.message));
    page.on("response", respuesta => {
      if (respuesta.status() >= 400 || new URL(respuesta.url()).pathname.startsWith("/habitats/")) {
        errores.push(respuesta.url());
      }
    });
    await page.goto(base);
    const siguiente = page.getByRole("button", {name: "Siguiente paisaje", exact: true});
    await siguiente.waitFor();
    const {opciones_habitat: habitats} = await page.evaluate(async () =>
      (await fetch("/api/vista")).json());
    assert.equal(habitats.length, 48);
    for (const habitat of habitats) {
      await comprobarFoto(page, habitat);
      await siguiente.click();
    }
    await comprobarFoto(page, habitats[0]);
    assert.equal(await page.locator(".ficha-numero").count(), 0);
    await page.getByRole("button", {name: "Paisaje anterior", exact: true}).click();
    await comprobarFoto(page, habitats.at(-1));
    await page.getByRole("button", {name: "Preferencias", exact: true}).click();
    await page.locator("#idioma").selectOption("pt-BR");
    await page.waitForFunction(() => document.documentElement.lang === "pt-BR");
    await page.locator("#cerrar-preferencias").click();
    const {opciones_habitat: traducidos} = await page.evaluate(async () =>
      (await fetch("/api/vista")).json());
    await comprobarFoto(page, traducidos.at(-1));
    assert.deepEqual(errores, []);
    console.log("48 fondos exclusivos de 1920 × 1080 verificados en el carrusel.");
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
