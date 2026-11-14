import { describe, expect, it } from "vitest";
import { crearTraductor, TEXTOS_NUEVOS_PENDIENTES } from "../i18n";

describe("traductor", () => {
  const dic = { es: {}, "pt-BR": { Comenzar: "Começar", "Página {pagina} de {total}": "Página {pagina} de {total}" } };

  it("devuelve el texto en español sin cambios", () => {
    expect(crearTraductor(dic, "es").t("Comenzar")).toBe("Comenzar");
  });
  it("usa el diccionario pt-BR del servidor", () => {
    expect(crearTraductor(dic, "pt-BR").t("Comenzar")).toBe("Começar");
  });
  it("sustituye variables", () => {
    expect(crearTraductor(dic, "pt-BR").t("Página {pagina} de {total}", { pagina: 2, total: 48 })).toBe(
      "Página 2 de 48",
    );
  });
  it("recurre a los borradores pendientes solo en pt-BR", () => {
    const [clave, borrador] = Object.entries(TEXTOS_NUEVOS_PENDIENTES)[0];
    expect(crearTraductor(dic, "pt-BR").t(clave)).toBe(borrador);
    expect(crearTraductor(dic, "es").t(clave)).toBe(clave);
  });
});
