# Voces de ElevenLabs para Zoonauta 6.0

Fecha: 2026-11-13 (modelo actualizado el 2026-11-14) · Rama: `experimental/zoonauta-v6-modern-web`

**Estado (2026-11-14): grabaciones completas en español.** Las 350 grabaciones de Marcela
(modelo `eleven_v4`) están en `assets/voz/grabada/es-419/` y cubren los 353 mensajes del juego
(tres reutilizan un duplicado); `tests/test_voz_grabada_cobertura.py` lo comprueba jugando todos los
animales. En pt-BR no hay grabaciones y la voz está bloqueada en la 6.0.

## Reglas

1. **Cada audio contiene un mensaje completo**: el `texto_voz` íntegro que la partida lee de una vez,
   con su entonación natural.
2. **Prohibido**: dividir oraciones en palabras, unir MP3 para formar frases, concatenar nombres de
   animales, hábitats o conectores, o reutilizar un audio solo porque comparte palabras con otro.
3. **Se permite reutilizar** un audio únicamente si el mensaje es **exactamente igual** y su contexto
   de reproducción es compatible (columna `duplicado_de`).
4. **Orden de reproducción**: Zoonauta reproduce la grabación completa del mensaje exacto. En la 6.0
   es la única voz: si faltara una grabación, la guía no lee ese mensaje con otra voz. (La 5.0, en
   `/v5/`, usaba antes Piper, Kokoro o la voz del navegador como alternativa.) Nunca deja una frase
   a medias ni mezcla motores dentro de un mensaje.
5. No se modifica el contenido educativo. Los textos del inventario se obtienen con el mismo
   generador y la misma traducción que usa el servidor.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `catalogo_voces.csv` | Inventario completo: una fila por mensaje e idioma (UTF-8; abre bien en Excel). |
| `resumen_catalogo.json` | Totales de caracteres y créditos por idioma y prioridad. |
| `codigo/interfaz/catalogo_voz.py` | Genera el inventario y verifica los audios descargados. |
| `codigo/interfaz/voz_grabada.py` | Busca la grabación del mensaje exacto durante la partida. |
| `assets/voz/grabada/es-419/`, `assets/voz/grabada/pt-BR/` | Carpeta donde se guardan los MP3 (o WAV) descargados. |

Para regenerar el inventario (se conservan las columnas que hayas rellenado: voz, `voice_id`, modelo,
estado, revisión y observaciones):

```bash
PYTHONUTF8=1 python -m codigo.interfaz.catalogo_voz
```

Si un texto cambia en los datos, su fila vuelve a `pendiente` y se borra la revisión humana, para que
no se use un audio antiguo.

### Columnas del CSV

`orden`, `id`, `idioma`, `texto` (exacto; copiar tal cual), `categoria`, `tipo_texto`
(`fijo` / `variable` / `dinamico`), `prioridad`, `contexto_reproduccion`, `voz_elevenlabs`,
`voice_id`, `modelo_elevenlabs`, `archivo`, `estado_generacion`, `caracteres`, `creditos_estimados`,
`duplicado_de`, `grabar`, `componentes_origen` (IDs originales de los que procede el mensaje),
`origen` (archivo de datos), `nota_pronunciacion`, `revision_humana`, `observaciones`.

Estados: `pendiente` → `generado` → `descargado` → `verificado` (o `rechazado`). Las filas
`usa_duplicado` no se graban.

### Identificadores

Se conservan los IDs originales. Los mensajes formados por varias piezas de datos llevan sus IDs
unidos con `__`, y el MP3 se llama igual que el ID:

| Tipo | Ejemplo de ID | Mensaje |
|---|---|---|
| Fijo | `MSG_PAUSA` | Partida en pausa. Puedes reanudarla. |
| Pista (botón Pista) | `AY_H01_L1` | Busca un bosque cálido y húmedo. |
| Apoyo + pista (hábitat no confirmado) | `MSG_APOYO_AUTO__AY_H01_L1` | Vamos a buscar otro lugar. Busca un bosque cálido y húmedo. |
| Confirmación | `MSG_VALIDA__H01` | ¡Sí! Este animal puede vivir en la selva tropical húmeda. |
| Confirmación con contexto | `MSG_VALIDA__H04__A01` | ¡Sí! … hojas anchas. Algunas poblaciones del norte de México usan bosques de encinos. |
| Pregunta del selector | `INTERFAZ_MODALIDAD` | ¿Quién elige el animal? (no tenía ID; procede de `servicio.py`) |

## Inventario

Todas las combinaciones dinámicas son pocas, así que se pueden grabar completas. No hace falta
recurrir a Piper o Kokoro por exceso de combinaciones.

| Prioridad | Contenido | Audios es-419 | Audios pt-BR | Caracteres (ambos) |
|---|---|---:|---:|---:|
| P1 | 6 mensajes fijos + selector de modalidad + los 8 hábitats de la portada (confirmación, 3 pistas y 3 apoyos con pista) | 63 | 63 | 6.707 |
| P2 | Los otros 40 hábitats: confirmaciones y pistas | 159 | 159 | 14.330 |
| P2 | Los otros 40 hábitats: apoyo + pista | 119 | 119 | 16.734 |
| P3 | Confirmaciones con contexto educativo (10 casos; 1 duplicado) | 9 | 9 | 1.850 |
| **Total** | 353 mensajes por idioma, 3 duplicados exactos | **350** | **350** | **39.621** |

Cada partida elige animales de los 288 y puede llegar a cualquiera de los 48 hábitats. Para cubrir
cualquier partida hacen falta P1 + P2 + P3. Lo que falte se lee entero con la voz alternativa.

Duplicados exactos (se graban una vez): `AY_H05_L1` = `AY_H04_L1`,
`MSG_APOYO_AUTO__AY_H05_L1` = `MSG_APOYO_AUTO__AY_H04_L1` y `MSG_VALIDA__H12__A27` =
`MSG_VALIDA__H12__A26`.

### Qué no se graba y por qué

- **Nombres de animales y hábitats sueltos.** Hoy no se leen en voz alta; solo se muestran. Grabarlos
  solo serviría para concatenarlos, lo que está prohibido. Ya forman parte de los mensajes completos
  cuando corresponde (p. ej. en las confirmaciones).
- **El saludo de «Probar voz».** Ese botón sirve para probar la voz alternativa elegida en
  Preferencias, así que sigue usando Piper, Kokoro o el navegador.
- **`MSG_PENDIENTE` y `MSG_INCORRECTA_VALIDADA`.** Solo los usan la consola y el catálogo original
  (`--catalogo-original`). Esos modos siguen con voz sintética.
- **Textos de botones y avisos.** Son visuales; la partida no los lee en voz alta.

## Créditos

**Modelo elegido: Eleven v4 (`eleven_v4`)**, decidido por el propietario el 2026-11-14. En la web
cuesta 1 crédito por carácter, igual que los demás modelos de voz completos (tarifas consultadas el
2026-11-14; **confírmalas en la pantalla de generación antes de empezar**):

| Modelo | Créditos/carácter | Todo el inventario | Con 50 % de margen para repeticiones |
|---|---:|---:|---:|
| **Eleven v4 (`eleven_v4`)** | 1 | 39.621 | 59.432 |
| Eleven Multilingual v2 / Eleven v3 | 1 | 39.621 | 59.432 |
| Flash / Turbo v2.5 | 0,5 | 19.811 | 29.716 |

Saldo disponible: **36.698 créditos**, con renovación el **15 de noviembre de 2026**.

Plan decidido el 2026-11-14: **primero solo español; el portugués, otro día.**

- **Ahora — es-419 completo** (P1, P2 y P3): 350 audios, **19.912 créditos**. Quedan unos 16.800
  para repeticiones (≈ 84 %). Orden: P1 → P2 → P3, siguiendo la columna `orden`.
- **Más adelante — pt-BR completo**: 350 audios, 19.709 créditos, con el saldo de un ciclo
  posterior. Mientras tanto, el portugués se lee entero con Piper, Kokoro o el navegador.

Si los créditos no usados no pasan al ciclo siguiente en tu plan (compruébalo en *Subscription*),
conviene grabar el español antes del 15. Recomiendo escuchar primero una muestra de P1.

## Elegir voz y modelo (una sola vez por idioma)

1. Graba 5 o 6 mensajes de P1 con 2 o 3 voces candidatas y escúchalos antes de grabar en serie:
   `MSG_PREGUNTA`, `MSG_VALIDA__H01`, `AY_H01_L3`, `MSG_APOYO_AUTO__AY_H01_L3` y `MSG_PAUSA`.
   Estas pruebas también consumen créditos.
2. **es-419**: usa una voz con acento latinoamericano (en *Voice Library*, filtra por idioma Spanish
   y acento Latin American o Mexican). **pt-BR**: usa una voz con acento brasileño (Portuguese,
   acento Brazilian). No uses voces de España ni de Portugal.
3. Modelo: **Eleven v4** (`eleven_v4`). En la lista de modelos de la página, elige *Eleven v4*, no
   *v4 Turbo*. Comprueba en la muestra que la voz mantenga el acento es-419 o pt-BR y que no añada
   ni omita palabras. Los modelos expresivos pueden variar entre tomas, así que hay que escuchar cada
   audio completo. Si en algún mensaje usas otro modelo, anótalo en `modelo_elevenlabs`: el CSV
   recalcula los créditos.
4. Fija los ajustes y no los cambies durante la serie. Anota voz, `voice_id` y ajustes en la primera
   fila de cada idioma. Punto de partida: *Stability* ≈ 50–60 %, *Similarity* ≈ 75 %, *Style* 0 %,
   *Speaker boost* activado y velocidad 1,0. En el juego, la velocidad la controla el usuario.
5. Revisa la licencia de uso comercial y educativo de tu plan y de la voz elegida en los términos
   vigentes de ElevenLabs. Guarda una copia de los audios fuera del equipo.

## Generar y descargar desde la web (paso a paso)

1. Abre el CSV y filtra por `idioma`, `grabar = si` y la prioridad de la fase. Ordena por `orden`.
2. En ElevenLabs, abre **Text to Speech** y elige la voz y el modelo acordados.
3. Copia la celda `texto` **tal cual**, sin editarla, sin añadir puntos ni etiquetas y sin cambiar
   comillas o signos. Pega un solo mensaje por generación.
4. Pulsa *Generate* y escucha el audio completo. Comprueba la pronunciación con la columna
   `nota_pronunciacion` (ver más abajo).
5. Si no es correcto, genera otra toma. Si un error se repite, **no cambies el texto**: anótalo en
   `observaciones` y marca la fila `rechazado` para revisarla.
6. Descarga el audio en MP3 (44,1 kHz; el formato predeterminado vale). Renómbralo exactamente como
   la columna `archivo` (p. ej. `MSG_APOYO_AUTO__AY_H01_L1.mp3`) y guárdalo en
   `assets/voz/grabada/es-419/` o `assets/voz/grabada/pt-BR/`. También se aceptan WAV con el mismo
   nombre.
7. Cambia `estado_generacion` a `descargado`. Cuando lo hayas escuchado dentro del juego, cámbialo a
   `verificado`.
8. Al final de cada sesión, comprueba los nombres y lo que falta:

```bash
PYTHONUTF8=1 python -m codigo.interfaz.catalogo_voz --verificar
```

El informe muestra cuántos audios hay, cuáles de P1 faltan, cuáles tienen un nombre que no coincide
y cuáles pesan menos de 1 KB.

## Integración en el juego (ya preparada)

- `POST /api/voz/grabada` recibe la misma entrada que `/api/voz`, pero sin `voz`. El servidor obtiene
  el `texto_voz` de la sesión (nunca acepta texto del cliente) y busca la grabación de ese mensaje
  exacto en el idioma activo. Si existe, devuelve el MP3 o WAV; si no, responde 404.
- `GET /api/voz/config` incluye `grabadas: {"es": n, "pt-BR": n}`. Si n = 0, el cliente no pide
  grabaciones.
- `app.js` (`hablar`) prueba primero la grabación. Si responde 404, sigue el flujo anterior: voz del
  navegador o Piper/Kokoro con el mensaje completo. Se mantienen una sola voz a la vez, la cancelación
  al cambiar de mensaje o pausar, la velocidad elegida y el interruptor de voz.
- Los audios nuevos se detectan al recargar la página.
- Pendiente de decidir: si los MP3 se confirman en Git (≈ 700 archivos, varias decenas de MB) o se
  distribuyen aparte. Sin esa decisión, `assets/voz/grabada/` queda fuera del manifiesto.

## Revisión de pronunciación y naturalidad

Revisión automática y lectura de los textos. **Ningún texto se ha cambiado.** Las sugerencias quedan
para tu revisión humana.

- **es-419**: el registro es coherente: tuteo («Elige», «Puedes»), sin vosotros ni formas
  peninsulares. Sin cifras, siglas ni abreviaturas. El código usa la etiqueta `es`; en el inventario
  se graba como es-419.
- **pt-BR**: no hay formas de pt-PT. Dos frases usan ênclise, correcta pero formal en el habla
  brasileña: `MSG_PAUSA` («Você pode retomá-la.») y `MSG_VALIDA__H34__A39` («Alimenta-se nas águas
  do oceano Antártico.»). En una revisión humana se podría valorar «Se alimenta…». Hoy no se cambia:
  es contenido traducido y requiere revisión en ambos idiomas.
- **Pistas de nivel 3** (96 por idioma): el hábitat va entre comillas «…». La voz no lee las
  comillas, pero puede marcar una pausa o un tono de cita. Escucha que suene natural.
- **Exclamaciones** («¡Sí!», «Sim!»): entonación alegre y breve, sin gritar. Si una toma suena
  exagerada, genera otra.
- **Mensajes con varias oraciones** (apoyo + pista, confirmación + contexto): pausa breve entre
  oraciones, sin cortes.
- **Nombres geográficos** (México, Antártico, ártica): comprueba la sílaba tónica.
