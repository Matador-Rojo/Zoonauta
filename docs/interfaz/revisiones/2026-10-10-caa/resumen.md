# Revisión de los tres ajustes de accesibilidad

10 de octubre de 2026. Preguntas y pistas utilizan los pictogramas originales;
los recortes de animales se conservan en catálogo, retratos y cierre. Los símbolos
de hábitat se centran y aumentan a 96–112 px. Los 48 animales están disponibles
en ocho páginas de seis, con búsqueda global en español y portugués brasileño.

Verificación ejecutada:

- 66 pruebas Python correctas: `.venv-voz/Scripts/python -m unittest discover -s tests -q`.
- 15 casos de navegador correctos: `python -m tests.ejecutar_navegador`, Edge 155.0.4283.45.
- Acceso a los 48 animales sin duplicados, retroceso y límites de página, conservación
  de página al pausar, búsqueda sin tildes, resultados vacíos y navegación en portugués.
- Las rutas de imágenes de las secuencias coinciden con los pictogramas de la respuesta;
  el retrato conserva el animal fotorrealista. No se altera el estado del reto al navegar.
- Ocho símbolos de hábitat de al menos 96 px, contenidos dentro de las tarjetas,
  sin desplazamiento horizontal en vistas de 320, 390, 768, 1024 y 1280 px.
- Capturas de catálogo y tablero revisadas visualmente en escritorio y móvil.

El audio de los casos de navegador utiliza síntesis controlada. Esta comprobación
no acredita comprensión CAA o resultados educativos con personas de Kallpa.
