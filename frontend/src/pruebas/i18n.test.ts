import { describe, expect, it } from "vitest";
import { crearTraductor, TEXTOS_NUEVOS_PENDIENTES } from "../i18n";

describe("traductor", () => {
  const dic = {
    es: {},
    "pt-BR": { Comenzar: "Começar", "Página {pagina} de {total}": "Página {pagina} de {total}" },
    en: { Comenzar: "Start", "Página {pagina} de {total}": "Page {pagina} of {total}" },
  };

  it("devuelve el texto en español sin cambios", () => {
    expect(crearTraductor(dic, "es").t("Comenzar")).toBe("Comenzar");
  });
  it("usa el diccionario pt-BR del servidor", () => {
    expect(crearTraductor(dic, "pt-BR").t("Comenzar")).toBe("Começar");
  });
  it("usa el diccionario en del servidor", () => {
    expect(crearTraductor(dic, "en").t("Comenzar")).toBe("Start");
    expect(crearTraductor(dic, "en").t("Página {pagina} de {total}", { pagina: 2, total: 48 })).toBe("Page 2 of 48");
  });
  it("sustituye variables", () => {
    expect(crearTraductor(dic, "pt-BR").t("Página {pagina} de {total}", { pagina: 2, total: 48 })).toBe(
      "Página 2 de 48",
    );
  });
  it("recurre a los borradores pendientes solo en pt-BR (si los hay)", () => {
    for (const [clave, borrador] of Object.entries(TEXTOS_NUEVOS_PENDIENTES)) {
      expect(crearTraductor(dic, "pt-BR").t(clave)).toBe(borrador);
      expect(crearTraductor(dic, "es").t(clave)).toBe(clave);
    }
  });
  it("sin traducción ni borrador muestra el texto en español, nunca vacío", () => {
    expect(crearTraductor(dic, "pt-BR").t("Texto sin traducir")).toBe("Texto sin traducir");
  });
});
