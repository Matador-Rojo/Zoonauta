# Manual de usuario de Zoonauta

## Preparar una sesión

1. Extrae el ZIP y abre la carpeta que contiene `codigo`, `datos` y `assets`.
2. En Windows abre `iniciar_juego.bat`. En Linux/macOS ejecuta `bash iniciar_juego.sh`.
   No se descarga ni se instala nada: solo hace falta Python 3.10 o posterior.
3. Mantén la terminal abierta mientras juegas. El navegador abre la portada
   «Bosque de luz» de Zoonauta 6.0. La versión 5.0 sigue en `/v5/`.

## Elegir preferencias

Abre **Preferencias** (arriba a la derecha) antes de comenzar. Se abre encima de la
pantalla, sin moverla. En computadora muestra dos columnas; en el móvil, una.

- **Idioma:** español o portugués brasileño.
- **La partida:** cuántos animales explorar (1 a 48, con los botones − y +) y
  **hábitats para elegir** (2, 4 u 8). Para empezar con menos alternativas, elige 2.
- **Voz:** *Una guía con voz* activa o desactiva la lectura; puedes elegir entre
  **Marcela · ElevenLabs**, **Valeria · ElevenLabs** y **Gaby · ElevenLabs** (las tres con los 412 mensajes
  completos en español). **Probar voz** reproduce el mensaje que está en pantalla. En
  portugués todavía no hay voz.
- **Ritmo de lectura:** despacio, natural o más ágil.
- **Sonidos del bosque:** activa o desactiva el paisaje suave del bosque durante el
  juego, la **música tranquila de descanso en pausa** (con brisa y gotas de rocío), la
  **música alegre de victoria al completar la partida** (con melodía cálida y cantos de
  aves) y los tonos de aviso. Todo se atenúa automáticamente mientras habla la guía y se
  silencia al ocultar la pestaña.
- **Aspecto visual:** *Bosque de noche* (predeterminado), *Bosque de día* (claro) o
  *Alto contraste* (negro y blanco puros, WCAG AAA 21:1).
- **Tamaño de texto:** *Normal* o *Grande*.
- **Reducir movimiento:** desactiva las animaciones y el video de portada, mostrando las
  portadas estáticas en alta nitidez. Respeta la preferencia del sistema al abrir, pero
  se puede cambiar manualmente en cualquier momento.

Usa **Volver al juego**, la ×, Escape o toca fuera para cerrar Preferencias. Tab y
Mayús+Tab recorren sus controles. Las preferencias no reemplazan el acompañamiento del
educador.

## Jugar

1. Pulsa **Comenzar**.
2. Elige **Yo elijo** para buscar un animal, o **El agente elige** para que lo proponga.
3. Observa el animal y la pregunta. Selecciona un hábitat donde pueda vivir.
4. Puedes pedir **Pista**, **Repetir** el mensaje o **Pausar** en cualquier momento del reto.
5. Cuando se confirme un hábitat, pulsa **Continuar**.
6. Al terminar, **Comenzar otra partida** vuelve a la portada.

En el catálogo de escritorio, búsqueda, filtros rápidos por letra inicial (`Todas`,
`A–C`, `D–G`, `H–L`, `M–P`, `Q–Z`), páginas, progreso, Pausar y Salir están
a la izquierda y seis animales grandes a la derecha. Puedes recorrer las páginas con los
botones, con las flechas `←`/`→`, deslizando en pantalla táctil o buscando por nombre.
Están disponibles los 288 animales. Cada pantalla ocupa la ventana completa, sin tener
que subir ni bajar. Al terminar la partida, la pantalla de cierre muestra el carrusel
**Hallazgos de esta partida** con los animales y hábitats descubiertos. Para revisión
técnica o pedagógica de la sesión, el educador puede abrir `/revision` en el mismo
navegador y exportar el registro en JSON, CSV o JSON anonimizado.
La partida sigue comenzando al tocar un animal, uno por reto.

Cada reto toma 2, 4 u 8 opciones del catálogo de 48 hábitats. Incluye el principal,
los secundarios documentados que quepan y completa el panel de forma **aleatoria con
ambientes claramente distintos entre sí**, evitando paisajes muy parecidos para que el
reto sea más claro y accesible. Si eliges un hábitat secundario documentado, también
completas el reto.

No hay límite de tiempo ni castigos por pedir ayuda. Una relación pendiente no
significa que el animal no pueda vivir allí: el juego orienta hacia una relación
documentada. Pausar y reanudar conservan el reto. Salir termina la partida.

## Si ocurre un problema

- **No comienza:** revisa en Preferencias que la cantidad sea un entero del 1 al 48.
  El aviso se cierra con × o desaparece a los ocho segundos.
- **No se escucha:** comprueba el volumen, activa la guía y usa Probar voz. La voz solo
  existe en español; en portugués se juega con texto y pictogramas.
- **La página no responde:** comprueba que la terminal siga abierta. Si el servidor
  sigue funcionando, recarga la página para recuperar la partida de ese navegador.
- **Se cerró el servidor:** vuelve a iniciarlo. Las partidas activas se conservan
  en memoria y no se recuperan después de reiniciar el servidor.
- **La ventana es muy pequeña** (zoom grande, móvil apaisado o pequeño): se permite
  desplazamiento para no aplastar imágenes ni controles. En una ventana normal no hace
  falta desplazar.

El educador debe comprobar que la persona comprenda las imágenes e instrucciones,
ofrecer una pausa cuando sea necesario y evitar responder por ella.
