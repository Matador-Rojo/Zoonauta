# Imágenes por capas para la portada 6.0

> **Superado el 2026-11-14.** La portada 6.0 ya no es el carrusel de ocho paisajes: es
> «Bosque de luz» (ver `docs/interfaz/6.0/identidad.md` y CLAUDE.md). Este documento se
> conserva como historial; los paisajes y capas siguen en `fondos/` sin uso en la 6.0.


> **Estado (2026-11-13):** recibidas e integradas las cinco capas de la tabla
> (`codigo/interfaz/web/fondos/capas/`, procedencia y ajustes en `procedencia.json`).
> Pendientes y opcionales: los recortes verticales para móvil.

Hoy el movimiento de la portada usa luz y copias recortadas de la misma foto. Para que
la hierba, las hojas, las algas o las nubes se muevan de verdad, hace falta separar
ese elemento en su propia capa con transparencia. Estas capas **se añaden** a las
fotos existentes; no las reemplazan. Ninguna incluye animales.

## Cómo generarlas (ChatGPT Image)

1. Sube a ChatGPT el fondo original correspondiente (`codigo/interfaz/web/fondos/catalogo/HXX.webp`).
2. Pega el texto de la tabla y pide **PNG con fondo transparente, 1920 × 1080**.
3. Comprueba que la capa encaja encima de la foto original (misma perspectiva,
   tamaño y posición). Si no encaja, es mejor no usarla.
4. Guárdala con el nombre indicado y pásamela. Yo la convierto a WebP con alfa, la
   pruebo con movimiento reducido y registro su procedencia.

Requisitos comunes para todas:

- PNG RGBA, 1920 × 1080, fondo totalmente transparente fuera del elemento.
- Mismo estilo fotográfico, luz y color que la foto original.
- Bordes suaves (sin halos blancos ni contornos recortados).
- Sin texto, sin animales, sin personas, sin marcas de agua.

## Capas propuestas (por prioridad)

| Archivo | Basado en | Qué debe contener | Movimiento previsto |
|---|---|---|---|
| `H09-hierba.png` | H09 Sabana seca | Solo la franja de hierba seca del primer plano (tercio inferior), recortada sobre transparente, que coincida con la de la foto. | Oscilación ±0,5° desde la base, ciclo de 7 s |
| `H01-hojas.png` | H01 Selva tropical | Solo 2–3 grupos de hojas grandes en las esquinas inferior derecha y superior izquierda, en primer plano y algo desenfocadas. | Balanceo muy leve, ciclo de 9 s |
| `H01-niebla.png` | H01 Selva tropical | Solo bancos de niebla blanca suave y semitransparente (opacidad 20–40 %) en la mitad izquierda, sin bordes definidos. | Deriva horizontal lenta, 50 s |
| `H37-algas.png` | H37 Arrecife de coral | Solo 3–4 algas o abanicos de mar en el borde inferior, delante del coral, sobre transparente. | Oscilación suave, ciclo de 8 s |
| `H20-nubes.png` | H20 Alta montaña | Solo 2 nubes bajas, suaves y semitransparentes, a media altura del cielo; sin tapar la cumbre. | Cruce lateral muy lento, 90 s |

Texto sugerido para pedir cada una (ejemplo para la sabana):

> Usando esta foto como referencia exacta, genera SOLO la franja de hierba seca del
> primer plano (tercio inferior de la imagen) como PNG de 1920×1080 con fondo
> transparente. Debe coincidir en posición, perspectiva, color y luz con la foto
> original para poder superponerla. Sin animales, sin texto, sin el árbol, sin el cielo.

## Opcional: recortes verticales para móvil

En móvil la escena 16:9 se recorta y se ve ampliada. Si quieres fotos más nítidas en
el teléfono, pide versiones verticales **de la misma escena**, 1080 × 1920, centradas
en el sujeto: `H01-vertical`, `H09-vertical`, …, `H25-vertical` (las 8). Son
opcionales; sin ellas la portada funciona igual.

## Lo que no hace falta generar

- Animales, pictogramas, robot y logo: se conservan los originales.
- Versiones ligeras de los pictogramas (hoy unos 500 KB cada uno): las puedo derivar
  yo de los originales sin generar nada.
