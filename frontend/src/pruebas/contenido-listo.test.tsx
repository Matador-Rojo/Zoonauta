import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useContenidoListo } from "../componentes/Pictograma";

// Imagen simulada cuya decodificación controla la prueba.
const pendientes: Array<() => void> = [];
class ImagenFalsa {
  src = "";
  decode() {
    return new Promise<void>((resolver) => pendientes.push(resolver));
  }
}

const pictos = { P1: { etiqueta: "a", imagen: "/1" }, P2: { etiqueta: "b", imagen: "/2" } };

describe("useContenidoListo (antiparpadeo de Pista)", () => {
  beforeEach(() => vi.stubGlobal("Image", ImagenFalsa));
  afterEach(() => {
    vi.unstubAllGlobals();
    pendientes.length = 0;
  });

  it("mantiene la guía anterior hasta decodificar los pictogramas nuevos", async () => {
    const inicial = { texto: "pregunta", pictogramas: ["P1"] };
    const { result, rerender } = renderHook(({ v }) => useContenidoListo(v, pictos), { initialProps: { v: inicial } });
    const pista = { texto: "pista", pictogramas: ["P2"] };
    rerender({ v: pista });
    expect(result.current.texto).toBe("pregunta");
    await act(async () => pendientes.forEach((r) => r()));
    expect(result.current.texto).toBe("pista");
  });

  it("Repetir (mismos pictogramas) se muestra al instante", () => {
    const inicial = { texto: "pista", pictogramas: ["P1"] };
    const { result, rerender } = renderHook(({ v }) => useContenidoListo(v, pictos), { initialProps: { v: inicial } });
    const repetida = { texto: "pista", pictogramas: ["P1"], revision: 2 };
    rerender({ v: repetida });
    expect(result.current).toBe(repetida);
    expect(pendientes).toHaveLength(0);
  });
});
