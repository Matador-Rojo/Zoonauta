---
name: cerrar-cambio
description: Lista de cierre obligatoria antes de dar por terminado un cambio en Zoonauta (verificación, comparación 5.0/6.0, revisor, commit seguro).
---

Sigue en orden; no declares «terminado» si un paso falla.

1. `git status`: separa lo tuyo de lo ajeno. Nunca toques ni confirmes `prototipo-*`,
   `referencias-externas/`, `assets/voz/`, `.claude/launch.json` ni cambios que no hiciste.
2. Pruebas relevantes (ver CLAUDE.md): `npm run check` si tocaste `frontend/`, unittest,
   y la prueba de navegador de la pantalla afectada.
3. Si el cambio es visual: `python -m tests.comparar_versiones --salida <carpeta temporal>`,
   MIRA las imágenes y escribe qué es mejor y qué es peor frente a la 5.0
   (contrato: `docs/interfaz/6.0/identidad.md`).
4. Lista explícita de rasgos quitados o cambiados, aunque sean pequeños.
5. Si el cambio es grande: subagente `revisor`; consulta al advisor antes de cerrar.
6. Si cambiaste archivos de `datos/manifest.json`: `python -m codigo.nucleo.actualizar_manifiesto`
   y `python -m codigo.nucleo.verificar_paquete`.
7. Commit solo con rutas explícitas (`git add ruta1 ruta2`), nunca `-A`/`.`; sin push.
