# Apoyos pictográficos y guía automática

10 de octubre de 2026. Versión 3.4.0.

La interfaz añade una pista automática ante cada selección no confirmada,
manteniendo el mensaje neutral y el reto abierto. No penaliza, no interpreta
las relaciones pendientes como incorrectas ni modifica el modelo. La observación
anterior se cierra sin etiqueta; la nueva pista abre su propia observación.
Repetir y reanudar conservan el contenido completo. El nivel llega hasta 3.

El catálogo presenta los pictogramas originales junto a los recortes de animales.
Mantiene seis por página, los 48 animales y la búsqueda global. Ayuda, Repetir,
Pausar, Reanudar, Continuar y Salir usan los pictogramas del banco. Pausa,
salida y cierre presentan sus secuencias. Las preguntas y pistas aumentan a
84–96 px, los controles a 56 px y los hábitats conservan 96–112 px.

## Verificación

- 68 pruebas Python correctas, incluida ayuda automática en las 315 relaciones
  pendientes, repetición, pausa, duplicados, límites y parámetros congelados.
- Ocho casos de aceptación del protocolo original de consola correctos.
- 17 casos de interfaz y cuatro de voces del navegador correctos en Edge
  155.0.4283.45, con audio controlado.
- Todas las variantes de ayuda con prefijo neutral disponen de traducción a
  portugués brasileño; se comprobó un recorrido con ayuda automática y repetición.
- Catálogo sin imágenes superpuestas al nombre, seis opciones y pictogramas
  originales correspondientes en las ocho páginas. Sin desbordamiento horizontal
  en anchos de 320, 390, 768, 1024 y 1280 px.
- Capturas inspeccionadas: catálogo de escritorio y móvil, pista automática,
  pausa y cierre. Los recursos originales se conservan.

Consola y simulador mantienen su protocolo de solicitud explícita de ayuda para
reproducir las evidencias sintéticas anteriores. La interfaz activa la asistencia
automática mediante una opción del gestor compartido.

Esta revisión comprueba funcionamiento y coherencia visual. La comprensión de
los pictogramas, la escucha en otros dispositivos y el impacto educativo requieren
evaluación con educadores y usuarios del perfil definido.
