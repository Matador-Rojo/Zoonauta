# Zoonauta

Juego de animales y hábitats con pictogramas y guía de inteligencia artificial.

Versión 3.2.0. Python 3.10 o superior.

![Inicio ilustrado de Zoonauta](docs/interfaz/01_inicio.png)

Clona este repositorio o descarga y extrae su ZIP. Abre la terminal en la carpeta
que contiene `codigo`, `datos`, `docs`, `assets` y `tests`. Al extraer el ZIP en
Windows, esa carpeta puede quedar dentro de otra `Zoonauta-main`. Para jugar:

```console
python -m codigo.interfaz.servidor --abrir
```

En Windows puedes usar `py` en lugar de `python`. Si el navegador no se abre,
entra en http://127.0.0.1:8000. Mantén la terminal abierta; Ctrl+C detiene el servidor.
No necesitas instalar paquetes de Python para jugar.

Si Windows muestra `WinError 10013` o el puerto 8000 no está disponible, usa otro puerto:

```console
py -m codigo.interfaz.servidor --abrir --puerto 8765
```

En ese caso abre http://127.0.0.1:8765. Para actualizar una copia descargada como
ZIP, detén el servidor, descarga el ZIP actual del repositorio y extrae la nueva
versión en otra carpeta. Un ZIP anterior no se actualiza automáticamente.

Abre `docs/guia_interfaz.md` para los comandos, alcance y evidencias actuales.
La pantalla incluye selección por clic/toque, 95 imágenes, texto, síntesis de voz,
Ayuda, Repetir, Pausar, Reanudar, Continuar y Salir. Preferencias permite elegir
de 1 a 48 retos antes del inicio y ajustar la voz. La voz requiere una voz española
disponible en el dispositivo; si falta, se muestra un aviso y continúa el juego.
El ZIP no contiene voces instalables ni audio grabado.

El inicio tiene una escena estática de selva a todo el ancho, tipografía amplia
y un recorrido visual por los ocho paisajes. El catálogo permite buscar
animales por nombre, incluso sin tildes. El tablero separa el animal, la guía y los
ocho hábitats, que combinan paisajes decorativos y sus pictogramas originales;
el progreso indica retos completados. Se adapta a móvil y admite
selección con teclado. No necesita vídeos, GIF ni recursos visuales externos.
Puedes ver el [tablero de juego](docs/interfaz/03_reto_escritorio.png) y el
[inicio en móvil](docs/interfaz/06_inicio_movil.png).

La interfaz carga el modelo sintético contextual R01, congelado, elegido por su
posición como primera réplica y no por su rendimiento. Para revisar los registros
de la sesión abre http://127.0.0.1:8000/revision en el mismo navegador.

Otros comandos desde esta carpeta, que contiene codigo, datos, docs, assets y tests:

```console
python -m codigo.poc.consola --modalidad JUGADOR --retos 2
python -m codigo.interfaz.servidor --politica ID3 --puerto 8001
python -m codigo.interfaz.servidor --politica ROTACION --puerto 8002
python -m codigo.poc.consola --modalidad AGENTE --retos 2
python -m codigo.entrenamiento.experimento --salida resultados_nuevos
python -m codigo.poc.aceptacion
python -m unittest discover -s tests -v
```

El núcleo conserva 48 animales, ocho opciones por reto y ambas modalidades.
No hay puntos competitivos ni límite de tiempo o intentos. ID3 construye el árbol
calculando ganancias. Se ejecutó aprendizaje probabilístico con interacciones
sintéticas y evaluación separada: 34 560 retos de entrenamiento, 51 840 de
evaluación. Ahora hay 35 pruebas de Python y diez casos de navegador correctos.

La consola utiliza los priors originales salvo que indiques un modelo con
--parametros; conserva sus parámetros congelados durante la sesión.
El simulador y el informe no requieren paquetes externos. Volver a exportar
el PNG mediante --grafico requiere matplotlib; el gráfico ya está incluido.

Esta versión contiene el código, los datos, los modelos, la interfaz y sus imágenes.
La voz se probó con una síntesis controlada en navegador; no certifica sonido audible
en otros dispositivos. La comprensión CAA de las secuencias requiere validación
con usuarios. Los documentos V1/V2 son antecedentes; esta guía y la de interfaz
describen el estado actual. Los experimentos conservan su procedencia sintética.

Créditos: 28 PNG ARASAAC sin modificación, Sergio Palao, Gobierno de Aragón,
CC BY-NC-SA; 67 SVG originales del prototipo, CC BY-NC-SA 4.0.
Consulta `docs/creditos_pictogramas.md` y `datos/fuentes_pictogramas.json`.
La portada y los ocho paisajes son imágenes decorativas generadas con IA,
incluidas en dos archivos WebP. No forman parte de los 95 pictogramas educativos.
Las referencias visuales, los prompts y las rutas están en
`docs/interfaz/diseno_visual.md`. El mapa SVG anterior se conserva como antecedente.
