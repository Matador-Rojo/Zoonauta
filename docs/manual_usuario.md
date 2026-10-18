# Manual de usuario de Zoonauta

## Preparar una sesión

1. Extrae el ZIP y abre la carpeta que contiene `codigo`, `datos` y `assets`.
2. En Windows abre `iniciar_juego.bat`. En Linux/macOS ejecuta `bash iniciar_juego.sh`.
3. Mantén la terminal abierta mientras juegas. El navegador abre la portada.
4. Si no puedes instalar voces o no tienes conexión, usa `iniciar_sin_descargas.bat`
   o `python3 -m codigo.interfaz.iniciar --sin-descargas`. El texto y las imágenes
   siguen disponibles. La voz depende de los recursos que tenga ese equipo.

## Elegir preferencias

Abre **Preferencias** antes de comenzar. En computadora, la columna izquierda
agrupa idioma y partida; la derecha reúne los controles de voz. En pantallas
pequeñas se muestran una debajo de otra para conservar los controles completos.

- **Idioma:** español o portugués brasileño.
- **Animales por partida:** un número entero entre 1 y 48.
- **Hábitats para elegir:** 2, 4 u 8. Para empezar con menos alternativas, elige 2.
- **Una guía con voz:** activa o desactiva la lectura.
- **Voz y ritmo de lectura:** elige una voz disponible y prueba que se escuche.

Usa **Volver al juego**, la × o Escape para cerrar Preferencias. Tab y Mayús+Tab
recorren sus controles. Las preferencias no reemplazan el acompañamiento del educador.

## Jugar

1. Pulsa **Comenzar**.
2. Elige **Yo elijo** para buscar un animal, o **El agente elige** para que lo proponga.
3. Observa el animal y la pregunta. Selecciona un hábitat donde pueda vivir.
4. Puedes pedir **Pista**, **Repetir** el mensaje o **Pausar** en cualquier momento del reto.
5. Cuando se confirme un hábitat, pulsa **Continuar**.
6. Al terminar, **Comenzar otra partida** vuelve a la portada.

No hay límite de tiempo ni castigos por pedir ayuda. Una relación pendiente no
significa que el animal no pueda vivir allí: el juego orienta hacia una relación
documentada. Pausar y reanudar conservan el reto. Salir termina la partida.

## Si ocurre un problema

- **No comienza:** revisa en Preferencias que la cantidad sea un entero del 1 al 48.
  El aviso se cierra con × o desaparece a los ocho segundos.
- **No se escucha:** comprueba el volumen, activa la guía y usa Probar voz.
  Selecciona otra voz disponible si la elegida requiere recursos que faltan.
- **La página no responde:** comprueba que la terminal siga abierta. Si el servidor
  sigue funcionando, recarga la página para recuperar la partida de ese navegador.
- **Se cerró el servidor:** vuelve a iniciarlo. Las partidas activas se conservan
  en memoria y no se recuperan después de reiniciar el servidor.
- **La ventana es pequeña:** se permite desplazamiento para mostrar controles
  completos. Aumenta la ventana si prefieres ver más contenido simultáneamente.

El educador debe comprobar que la persona comprenda las imágenes e instrucciones,
ofrecer una pausa cuando sea necesario y evitar responder por ella.
