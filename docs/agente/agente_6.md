# El agente de Zoonauta 6.0

Fecha: 2026-11-14 · Código: [`codigo/motores/agente.py`](../../codigo/motores/agente.py) ·
Datos: [`datos/expedicion/atributos_habitats.json`](../../datos/expedicion/atributos_habitats.json) ·
Pruebas: [`tests/test_agente6.py`](../../tests/test_agente6.py) ·
Evaluación: [`codigo/entrenamiento/evaluar_agente6.py`](../../codigo/entrenamiento/evaluar_agente6.py),
[`docs/experimentos/agente6/evaluacion.json`](../experimentos/agente6/evaluacion.json)

## 1. Qué había antes (comprobado en el código)

- **Catálogo original** (48 animales, ocho hábitats, `--catalogo-original`): `MotorGuia`
  (`codigo/motores/guia.py`) con tres políticas: ID3 sobre ocho perfiles didácticos,
  rotación y un selector probabilístico (Beta-Bernoulli) entrenado con jugadores sintéticos y
  congelado. Sus contextos (hábitat, nivel, repetición, variante V1–V3) solo existen para esos
  ocho hábitats.
- **Catálogo ampliado** (288 animales, 48 hábitats; la partida de la 6.0 y de `/v5/`):
  `MotorPistas`, que mostraba siempre la misma secuencia editorial **pista 1 → pista 2 →
  pista 3** del hábitat guía. No miraba las opciones visibles ni lo elegido. Su interfaz
  `decidir(hábitat, nivel, …)` ni siquiera recibía esa información.

Por tanto, el ID3 y el modelo probabilístico existentes **no podían reutilizarse tal cual**:
sus parámetros dependen de los ocho perfiles y de variantes que el catálogo ampliado no tiene.
Sí se reutilizan el árbol ID3 (`codigo/motores/id3.py`: entropía y ganancia), el gestor de la
partida, las 144 pistas revisadas, los pictogramas, el generador de mensajes y las grabaciones.

## 2. Representación: qué sabe el agente de cada hábitat

`datos/expedicion/atributos_habitats.json` define **12 atributos** (temperatura, tipo de agua,
humedad del clima, plantas que dominan, paisaje, tipo de árbol, ubicación, movimiento y
velocidad del agua, luz, zona del mar, suelo o superficie) con **32 valores**.

- **Cada valor cita la pista revisada que lo dice.** Por ejemplo, `H06 temperatura = frio`
  procede de `AY_H06_L1` («Busca un bosque de una región fría.»). No se añadió información
  biológica nueva. El cargador (`codigo/nucleo/catalogo.py`, `cargar_rasgos`) rechaza
  cualquier evidencia que no sea una pista 1 o 2 del mismo hábitat.
- **Tres estados:** un hábitat documenta un valor, documenta otro valor del mismo atributo
  (los valores de un atributo se tratan como excluyentes) o **no documenta nada** sobre ese
  atributo. Lo no documentado es **desconocido**: nunca se usa para descartar una opción.
- Además, el agente conoce los **conceptos** (pictogramas) de las pistas 1 y 2 de cada hábitat.

Al comparar una ayuda con otra opción visible `d`, el agente obtiene una de cuatro relaciones:

| Relación | Significado | Peso al descartar |
|---|---|---|
| `conflicto` | `d` documenta otro valor del mismo rasgo: la ayuda las distingue | 1 |
| `propia` | nada de lo que dice la ayuda consta en `d` (probable diferencia, no comprobada) | 0,5 |
| `parcial` | parte de lo que dice también vale para `d`; el resto no consta | 0,25 |
| `compartida` | todo lo que dice también vale para `d` | 0 |

Estas relaciones son internas. **El jugador solo oye y ve frases positivas sobre el hábitat
guía**; nunca una afirmación sobre las otras opciones. Un hábitat no confirmado para el
animal es una relación desconocida, no incorrecta: el mensaje tras elegirlo sigue siendo el
neutro «Vamos a buscar otro lugar.», como antes.

La tabla completa de rasgos por hábitat está en el apartado 8.

## 3. Qué puede decir: las candidatas

Para el hábitat guía del animal (siempre visible entre las opciones):

1. Sus **pistas revisadas 1 y 2** (texto, pictogramas y grabaciones existentes).
2. Sus **ayudas breves por rasgo**: una idea y uno o dos pictogramas ya existentes («Busca un
   lugar frío.», «Busca agua que corre despacio.»). Solo las de rasgos documentados de ese
   hábitat, y **solo si existen sus dos grabaciones** (ver apartado 6).
3. Su **pista 3** («Señala el hábitat …»), el apoyo explícito, como último recurso.

No hay ninguna frase sobre otro hábitat ni sobre si un hábitat es incorrecto.

## 4. Las dos políticas nuevas y cómo se integran

El gestor (`codigo/nucleo/gestor.py`, `_ayuda`) llama a `decidir_reto(contexto)` cuando el
motor lo ofrece. El contexto contiene el animal, el hábitat guía, las **opciones visibles**
(2, 4 u 8), las **confirmadas** entre ellas (principal y secundarios documentados), las
**elecciones** del reto, las **ayudas ya mostradas** y si se pulsó **Repetir**. El motor
devuelve la plantilla de la ayuda y una traza completa (candidatas, puntuaciones y regla
aplicada) que se guarda en el registro y se ve en `/revision`. Las reglas, el progreso, las
opciones y la evaluación de cada elección siguen siendo del gestor: el agente solo elige la
ayuda.

### Línea base: `ID3_OPCIONES`

Al empezar el reto construye un árbol **ID3** (el de `codigo/motores/id3.py`, con entropía y
ganancia de información) sobre las opciones visibles. Cada candidata es un atributo binario
(«la descarta de forma documentada» o «la mantiene») y cada opción es una clase. Presenta las
ayudas del camino del hábitat guía con ganancia positiva y después la secuencia editorial y
la pista 3. **No mira lo que hace el jugador.**

### Modelo principal: `AGENTE_ADAPTATIVO`

Decide en cada petición con el estado actual del reto:

1. **Apoyo explícito (pista 3)** si ya se mostró, si el jugador eligió **dos** hábitats no
   confirmados en el reto (la misma regla que el selector probabilístico del catálogo
   original) o si ya vio **tres** ayudas.
2. **Excluye** las ayudas que también describen (del todo o en parte) un hábitat ya elegido
   en el reto: parecerían señalarlo otra vez.
3. Para cada candidata restante calcula una **utilidad esperada**:
   `U = comprensión × ganancia + bono − penalización`.
   - **ganancia** = `log2(|R| / (|R| − E))` bits, con `R` las opciones que quedan (sin las ya
     elegidas) y `E` el número esperado de opciones no confirmadas que descarta (pesos de la
     tabla del apartado 2);
   - **comprensión** = `0,85^(ideas − 1)` (cada idea extra de la frase la hace más difícil);
     `0,6^(ideas − 1)` si hay señales de dificultad: se pulsó Repetir, o se eligió un hábitat
     que una ayuda anterior ya distinguía;
   - **bono** = 1 si la ayuda distingue de forma documentada el hábitat recién elegido (0,5 si
     la diferencia no está comprobada);
   - **penalización** = 1 por cada otra respuesta válida visible (secundario documentado) de
     la que la ayuda alejaría.
4. Si ninguna candidata aporta nada, ofrece la pista 3. Si ya no quedan opciones no
   confirmadas, sigue la secuencia editorial sin repetir lo elegido.

Los parámetros (0,5 / 0,25 / 0,85 / 0,6 / 1 / 1, tres ayudas, dos elecciones) **se fijaron a
mano** con los criterios anteriores; no se ajustaron con datos de jugadores, que no existen.
**No hay aprendizaje en vivo**: el agente decide igual en la primera y en la milésima partida.

### Qué no cambia

- **Repetir** devuelve exactamente el mensaje mostrado (mismo texto, pictogramas e ID) y no
  cambia el estado; solo marca la señal de dificultad para la siguiente ayuda.
- **Pausar** y **Reanudar** no alteran la decisión siguiente.
- **Salir**, Continuar, las opciones visibles y el progreso siguen igual. No hay tiempo,
  puntos ni castigos.
- Los 288 animales, 48 hábitats, 2/4/8 opciones y los secundarios documentados se conservan;
  cualquier secundario visible completa el reto.

### Cómo se ejecuta

```console
py -3 -m codigo.interfaz.iniciar                                 # el agente es el predeterminado
python -m codigo.interfaz.servidor --agente ID3_OPCIONES --puerto 8003        # línea base
python -m codigo.interfaz.servidor --agente PISTAS_PROGRESIVAS --puerto 8004  # secuencia anterior
```

La consola y el simulador del catálogo original no cambian. En código,
`GestorPartida(BancoDatos(ampliado=True))` usa el agente por defecto.

## 5. Evaluación

Reproducible con:

```console
PYTHONUTF8=1 python -m codigo.entrenamiento.evaluar_agente6 --salida docs/experimentos/agente6 --replicas 5
```

Compara cinco variantes con el gestor real: la secuencia anterior (`PISTAS_PROGRESIVAS`),
`ID3_OPCIONES` y `AGENTE` con las ayudas que tienen grabación hoy (`grabadas`: pistas y una
ayuda por rasgo) y con las 32 ayudas por rasgo (`todas`, como quedará cuando lleguen los
audios).

### 5.1 Estructural y exhaustiva (sin personas, sin azar)

Los 288 animales con 2, 4 y 8 opciones (864 retos por política). Para cada reto se mide la
primera pista y, por separado, la ayuda que sigue a elegir cada hábitat no confirmado visible
(265, 833 y 1985 casos). «Documentado» significa que la diferencia consta en los rasgos.

| Política | Opciones | 1.ª pista descarta algo (documentado) | 1.ª pista sin valor | Ideas en la 1.ª | Tras un error: distingue lo elegido | Tras un error: también lo describe | Tras un error: pasa a «Señala» | 1.ª pista aleja de un secundario visible | Incompatibles |
|---|---|---|---|---|---|---|---|---|---|
| PISTAS_PROGRESIVAS | 2 | 23 % | 52 % | 2,02 | 23 % | 66 % | 0 % | 9 | 0 |
| PISTAS_PROGRESIVAS | 4 | 42 % | 19 % | 2,02 | 20 % | 62 % | 0 % | 10 | 0 |
| PISTAS_PROGRESIVAS | 8 | 62 % | 2 % | 2,02 | 22 % | 47 % | 0 % | 10 | 0 |
| ID3_OPCIONES (grabadas) | 2 | 40 % | 38 % | 2,08 | 40 % | 51 % | 0 % | 16 | 0 |
| ID3_OPCIONES (grabadas) | 4 | 61 % | 8 % | 2,10 | 30 % | 50 % | 0 % | 17 | 0 |
| ID3_OPCIONES (grabadas) | 8 | 83 % | 0 % | 2,11 | 32 % | 37 % | 0 % | 15 | 0 |
| **AGENTE (grabadas)** | 2 | 40 % | **0 %** | 2,08 | 40 % | **0 %** | 16 % | 1 | 0 |
| **AGENTE (grabadas)** | 4 | 49 % | **0 %** | 2,04 | 30 % | **0 %** | 17 % | 5 | 0 |
| **AGENTE (grabadas)** | 8 | 69 % | **0 %** | 2,07 | 34 % | **0 %** | 8 % | 1 | 0 |
| AGENTE (todas) | 2 | 40 % | 0 % | 1,44 | 40 % | 0 % | 13 % | 1 | 0 |
| AGENTE (todas) | 4 | 55 % | 0 % | 1,38 | 30 % | 0 % | 13 % | 3 | 0 |
| AGENTE (todas) | 8 | 74 % | 0 % | 1,49 | 34 % | 0 % | 5 % | 0 | 0 |

(«1.ª pista sin valor»: todo lo que dice también vale para todas las opciones no confirmadas.
`ID3_OPCIONES (todas)` da casi los mismos números que con grabadas; están en el JSON.)

Lectura:

- **Mejor que la secuencia anterior.** El agente nunca da una primera pista sin valor
  (la secuencia fija: 52 % con 2 opciones). Tras un error, nunca repite algo que también
  describe lo elegido (la secuencia: 47–66 %). Distingue lo elegido con un rasgo documentado
  más a menudo (30–40 % frente a 20–23 %) y casi nunca aleja de un secundario visible.
- **Frente a ID3.** ID3 descarta más opciones con la primera pista con 4 y 8 opciones (61 % y
  83 % frente a 49 % y 69 %), porque solo maximiza la diferencia documentada. El agente
  además pondera la comprensión, las diferencias no comprobadas y los secundarios. Ese ID3
  da pistas sin valor (38 % con 2 opciones) y repite lo elegido en el 37–51 % de los casos.
- **Coste.** Cuando ninguna ayuda restante distingue lo elegido sin describirlo también, el
  agente pasa al apoyo explícito: tras el primer error, en el 8–17 % de los casos. La
  secuencia fija nunca lo hace tan pronto, pero en esos casos ofrecía una pista que también
  valía para lo elegido.
- **Límite de los datos:** con 2 opciones, solo el 40 % de los retos tiene alguna diferencia
  documentada. Ninguna política puede superar ese techo sin rasgos nuevos (apartado 8).
- **Cero ayudas incompatibles** en todas las políticas: siempre hablan del hábitat guía visible
  y solo afirman rasgos documentados de él.

### 5.2 Jugador sintético (datos simulados, no personas)

Tres perfiles inventados (`autonomo`, `apoyo_medio`, `apoyo_alto`) con probabilidades fijas de
acertar sin ayuda, entender una frase de una idea y pedir pista (`PERFILES` en el script). Se
simulan 5 réplicas × 288 animales × 3 tamaños × 3 perfiles por política (12 960 retos), con
los mismos sorteos para todas. El jugador simulado descarta siempre las opciones con una
diferencia documentada si entiende la ayuda, a veces las de una diferencia no documentada, y
acierta tras «Señala» con probabilidad 0,95. Todos los retos se resuelven en todas las
políticas.

| Política | Perfil | Elecciones no confirmadas por reto (2/4/8) | Ayudas por reto (2/4/8) | Llega a «Señala» (2/4/8) | Ideas por ayuda |
|---|---|---|---|---|---|
| PISTAS_PROGRESIVAS | autonomo | 0,23 / 0,50 / 0,68 | 0,72 / 1,07 / 1,31 | 6 / 14 / 23 % | 2,06 |
| PISTAS_PROGRESIVAS | apoyo_medio | 0,26 / 0,53 / 0,75 | 1,28 / 1,73 / 2,01 | 22 / 37 / 50 % | 2,06 |
| PISTAS_PROGRESIVAS | apoyo_alto | 0,27 / 0,45 / 0,60 | 1,96 / 2,35 / 2,54 | 49 / 66 / 75 % | 2,06 |
| ID3_OPCIONES (grabadas) | autonomo | 0,23 / 0,50 / 0,65 | 0,72 / 1,07 / 1,28 | 6 / 14 / 22 % | 2,08 |
| ID3_OPCIONES (grabadas) | apoyo_medio | 0,25 / 0,52 / 0,74 | 1,27 / 1,71 / 1,99 | 22 / 37 / 49 % | 2,08 |
| ID3_OPCIONES (grabadas) | apoyo_alto | 0,26 / 0,44 / 0,60 | 1,95 / 2,33 / 2,54 | 48 / 65 / 75 % | 2,07 |
| **AGENTE (grabadas)** | autonomo | 0,21 / 0,44 / 0,59 | 0,64 / 0,94 / 1,14 | 17 / 27 / 31 % | 2,06 |
| **AGENTE (grabadas)** | apoyo_medio | 0,22 / 0,44 / 0,67 | 1,07 / 1,47 / 1,77 | 34 / 46 / 55 % | 2,06 |
| **AGENTE (grabadas)** | apoyo_alto | 0,20 / 0,39 / 0,57 | 1,56 / 2,06 / 2,37 | 58 / 70 / 77 % | 2,05 |
| AGENTE (todas) | autonomo | 0,21 / 0,44 / 0,61 | 0,66 / 0,98 / 1,20 | 12 / 20 / 25 % | 1,61 |
| AGENTE (todas) | apoyo_medio | 0,21 / 0,46 / 0,72 | 1,14 / 1,63 / 2,00 | 25 / 33 / 43 % | 1,64 |
| AGENTE (todas) | apoyo_alto | 0,20 / 0,45 / 0,67 | 1,78 / 2,49 / 2,89 | 48 / 59 / 70 % | 1,67 |

Lectura, con cautela:

- **Con las grabaciones de hoy**, el agente necesita menos elecciones no confirmadas y menos
  ayudas que la secuencia anterior y que ID3 en los nueve casos, pero llega más veces al apoyo
  explícito «Señala».
- **Con las 32 ayudas por rasgo** las frases son más cortas (1,6 ideas frente a 2,1) y se llega
  menos a «Señala» que con las grabadas. En el perfil `apoyo_alto` con 4 y 8 opciones hacen
  falta más ayudas (2,49 y 2,89) que con la secuencia (2,35 y 2,54), y con 8 opciones algo más
  de elecciones: cada frase corta lleva menos información. Es el cambio de compromiso que
  habría que observar con personas.
- **Límites.** Los perfiles y probabilidades son inventados. El jugador simulado usa la misma
  representación de rasgos que el agente, lo que favorece a las políticas que la usan. No mide
  comprensión real, motivación, fatiga ni el papel del educador. **No son resultados de
  usuarios** ni se usaron para entrenar nada.

## 6. Voces

- **Se reutilizan** las 350 grabaciones: las 144 pistas solas, las 144 precedidas del apoyo y
  el resto de mensajes. El agente nunca une audios.
- **Hacen falta 62 grabaciones nuevas** (2669 caracteres): las 32 ayudas por rasgo, solas y
  tras «Vamos a buscar otro lugar.», menos «Busca un lugar con arbustos.», idéntica a
  `AY_H13_L1`, que reutiliza su audio. Están en
  [`docs/voz/elevenlabs/textos_pendientes_es-419.txt`](../voz/elevenlabs/textos_pendientes_es-419.txt)
  (una línea con el nombre exacto del MP3 y otra con el texto) y se regeneran con
  `PYTHONUTF8=1 python -m codigo.interfaz.catalogo_voz --pendientes`.
- **Mientras falten**, el agente no usa esas ayudas (`ayudas_con_grabacion`): la guía nunca
  muestra un mensaje que la voz no pueda leer. `tests/test_voz_grabada_cobertura.py` juega
  todos los animales con el agente y comprueba que cada mensaje tenga grabación.
- **Cuando lleguen**, basta con copiarlas en `assets/voz/grabada/es-419/` con su nombre:
  el agente las usa al reiniciar el juego, sin cambiar código. Los pasos de verificación están
  en [`docs/voz/elevenlabs/README.md`](../voz/elevenlabs/README.md).
- En pt-BR la voz sigue bloqueada. Las ayudas por rasgo tienen una traducción propuesta,
  marcada como pendiente en `docs/traducciones/revision_es_pt.csv` (grupo `ayuda_rasgo`).

## 7. Pruebas

**Automáticas** (`tests/test_agente6.py`, 14 pruebas; con el resto, 109 en total):

- datos: cada rasgo cita una pista revisada del mismo hábitat; ayudas breves, con
  pictogramas existentes y traducción; lo desconocido nunca descarta;
- exhaustiva: los 288 animales con 2, 4 y 8 opciones y las tres políticas. Las opciones
  conservan los confirmados que caben, toda ayuda habla del hábitat guía visible y solo
  afirma rasgos documentados, y la del agente tras un error nunca describe lo elegido;
- casos: salta la pista 1 idéntica entre H04 y H05; distingue la última elección (H06 frente a
  H05); no aleja del secundario documentado (jaguar y H04); apoyo explícito tras dos elecciones
  o tres ayudas; Repetir exacto; Pausar y Reanudar sin efecto; sin grabación no se usa la ayuda
  por rasgo y, con una grabación de prueba, sí; ID3 elige la mayor ganancia de información;
- cobertura de voz con el agente en la partida real (`test_voz_grabada_cobertura`);
- navegador: las suites de la 6.0 (`--v6`, `--partidas-v6`, `--voz-v6`, `--portada`) y de la
  5.0 en `/v5/` (`--hito2`, `--hito3`, `--catalogo`, general, `--voz-v5`, `--voces-navegador`).

**Validación con usuarios: no se ha hecho.** Ninguna prueba ni simulación sustituye observar
a personas con discapacidad intelectual jugando con sus educadores. Queda pendiente.

## 8. Pendiente de revisión humana

1. **Lectura de cada rasgo y exclusividad de los valores** (tabla siguiente). Por ejemplo,
   ¿«poca luz» (cueva) excluye «con luz del sol» (mar abierto)? ¿«época seca» excluye
   «húmedo»?
2. **Textos nuevos** de las 32 ayudas por rasgo (es-419) y su **traducción pt-BR**,
   redactados con IA. No se deben grabar antes de revisarlos.
3. **Huecos de datos.** H28 (turbera) y H30 (río estacional) no tienen rasgos documentados en
   sus pistas. En el **65 %** de las apariciones de una opción no confirmada (2002 de 3083),
   ninguna ayuda puede distinguirla de forma documentada. Los pares más frecuentes están en la
   segunda tabla. Distinguirlos exigiría documentar rasgos nuevos con fuente y revisión, por
   ejemplo «agua dulce» en H24, H26 y H30 o «templado» en H13. Esta entrega **no** los añade.

### Rasgos documentados por hábitat

| Hábitat | Rasgos documentados (pista que lo dice) |
|---|---|
| H01 Selva tropical húmeda | Humedad del clima: humedo (pista 1); Paisaje: bosque (pista 1); Temperatura: calido (pista 1) |
| H02 Bosque tropical seco | Humedad del clima: epoca_seca (pista 1); Paisaje: bosque (pista 1); Temperatura: calido (pista 1) |
| H03 Bosque nuboso | Humedad del clima: humedo (pista 1); Paisaje: bosque (pista 1); Ubicación: montana (pista 1) |
| H04 Bosque templado de hojas anchas | Paisaje: bosque (pista 1); Temperatura: templado (pista 1); Tipo de árbol: hojas_anchas (pista 2) |
| H05 Bosque templado de coníferas | Paisaje: bosque (pista 1); Temperatura: templado (pista 1); Tipo de árbol: coniferas (pista 2) |
| H06 Bosque boreal o taiga | Paisaje: bosque (pista 1); Temperatura: frio (pista 1); Tipo de árbol: coniferas (pista 2) |
| H07 Manglar | Paisaje: bosque (pista 1); Ubicación: costa (pista 1) |
| H08 Bosque tropical inundable | Tipo de agua: dulce (pista 1); Paisaje: bosque (pista 1); Temperatura: calido (pista 1) |
| H09 Sabana seca | Humedad del clima: epoca_seca (pista 2); Paisaje: abierto (pista 1); Temperatura: calido (pista 1); Plantas que dominan: pasto (pista 2) |
| H10 Sabana inundable | Paisaje: abierto (pista 1); Plantas que dominan: pasto (pista 1) |
| H11 Pradera templada | Paisaje: abierto (pista 1); Temperatura: templado (pista 2); Plantas que dominan: pasto (pista 1) |
| H12 Tundra | Paisaje: abierto (pista 1); Temperatura: frio (pista 1) |
| H13 Matorral mediterráneo | Humedad del clima: epoca_seca (pista 2); Plantas que dominan: arbustos (pista 1) |
| H14 Matorral tropical seco | Humedad del clima: epoca_seca (pista 2); Temperatura: calido (pista 1); Plantas que dominan: arbustos (pista 1) |
| H15 Matorral de alta montaña | Ubicación: montana (pista 1); Plantas que dominan: arbustos (pista 2) |
| H16 Pastizal de alta montaña | Paisaje: abierto (pista 1); Ubicación: montana (pista 1); Plantas que dominan: pasto (pista 1) |
| H17 Desierto cálido | Humedad del clima: seco (pista 1); Temperatura: calido (pista 1); Plantas que dominan: pocas_plantas (pista 2) |
| H18 Desierto frío | Humedad del clima: seco (pista 1); Temperatura: frio (pista 1); Plantas que dominan: pocas_plantas (pista 2) |
| H19 Oasis | Tipo de agua: dulce (pista 1) |
| H20 Alta montaña rocosa | Ubicación: montana (pista 1); Suelo o superficie: roca (pista 2); Plantas que dominan: pocas_plantas (pista 2) |
| H21 Cueva terrestre | Luz: oscuro (pista 1) |
| H22 Hielo marino polar | Tipo de agua: salada (pista 1); Suelo o superficie: hielo (pista 2); Temperatura: frio (pista 1); Zona del mar: superficie (pista 2) |
| H23 Río de corriente lenta | Tipo de agua: dulce (pista 1); Velocidad del agua: lenta (pista 2); Movimiento del agua: corre (pista 1) |
| H24 Arroyo de montaña | Velocidad del agua: rapida (pista 2); Movimiento del agua: corre (pista 2); Ubicación: montana (pista 1) |
| H25 Lago de agua dulce | Tipo de agua: dulce (pista 1); Movimiento del agua: quieta (pista 2) |
| H26 Charca temporal | Tipo de agua: dulce (pista 1) |
| H27 Pantano de agua dulce | Tipo de agua: dulce (pista 1); Movimiento del agua: quieta (pista 2) |
| H28 Turbera | **sin rasgos documentados** |
| H29 Humedal de alta montaña | Ubicación: montana (pista 1) |
| H30 Río estacional | **sin rasgos documentados** |
| H31 Río subterráneo | Tipo de agua: dulce (pista 1); Movimiento del agua: corre (pista 2) |
| H32 Lago salado | Tipo de agua: salada (pista 2) |
| H33 Aguas marinas costeras | Tipo de agua: salada (pista 1); Ubicación: costa (pista 1) |
| H34 Mar abierto superficial | Tipo de agua: salada (pista 1); Luz: con_luz (pista 2); Ubicación: lejos_costa (pista 2); Zona del mar: superficie (pista 2) |
| H35 Aguas oceánicas profundas | Tipo de agua: salada (pista 1); Luz: oscuro (pista 1); Zona del mar: agua_profunda (pista 2) |
| H36 Fondo marino profundo | Tipo de agua: salada (pista 1); Zona del mar: fondo (pista 2) |
| H37 Arrecife de coral | Tipo de agua: salada (pista 1); Zona del mar: fondo (pista 2) |
| H38 Pradera marina | Tipo de agua: salada (pista 1); Zona del mar: fondo (pista 2) |
| H39 Bosque de algas | Tipo de agua: salada (pista 1); Zona del mar: fondo (pista 2) |
| H40 Arrecife rocoso | Tipo de agua: salada (pista 1); Suelo o superficie: roca (pista 1); Zona del mar: fondo (pista 2) |
| H41 Estuario | Tipo de agua: salobre (pista 1); Ubicación: costa (pista 2) |
| H42 Laguna costera salobre | Tipo de agua: salobre (pista 1); Ubicación: costa (pista 1) |
| H43 Marisma costera | Ubicación: costa (pista 1); Suelo o superficie: barro (pista 2); Plantas que dominan: pasto (pista 2) |
| H44 Costa rocosa | Ubicación: costa (pista 1); Suelo o superficie: roca (pista 1) |
| H45 Poza de marea | Ubicación: costa (pista 1); Suelo o superficie: roca (pista 1) |
| H46 Playa arenosa | Ubicación: costa (pista 1); Suelo o superficie: arena (pista 1) |
| H47 Duna costera | Ubicación: costa (pista 1); Suelo o superficie: arena (pista 1) |
| H48 Acantilado costero | Ubicación: costa (pista 1); Suelo o superficie: roca (pista 1) |

### Pares parecidos sin diferencia documentada (los 25 más frecuentes)

| Hábitat guía | Opción parecida sin diferencia documentada | Apariciones (288 animales × 2, 4 y 8) |
|---|---|---|
| H03 Bosque nuboso | H01 Selva tropical húmeda | 18 |
| H13 Matorral mediterráneo | H14 Matorral tropical seco | 18 |
| H19 Oasis | H30 Río estacional | 18 |
| H21 Cueva terrestre | H31 Río subterráneo | 18 |
| H26 Charca temporal | H30 Río estacional | 18 |
| H28 Turbera | H27 Pantano de agua dulce | 18 |
| H31 Río subterráneo | H24 Arroyo de montaña | 18 |
| H37 Arrecife de coral | H40 Arrecife rocoso | 18 |
| H39 Bosque de algas | H38 Pradera marina | 18 |
| H41 Estuario | H42 Laguna costera salobre | 18 |
| H42 Laguna costera salobre | H41 Estuario | 18 |
| H43 Marisma costera | H41 Estuario | 18 |
| H44 Costa rocosa | H45 Poza de marea | 18 |
| H45 Poza de marea | H44 Costa rocosa | 18 |
| H46 Playa arenosa | H47 Duna costera | 18 |
| H47 Duna costera | H46 Playa arenosa | 18 |
| H40 Arrecife rocoso | H37 Arrecife de coral | 17 |
| H25 Lago de agua dulce | H27 Pantano de agua dulce | 17 |
| H08 Bosque tropical inundable | H27 Pantano de agua dulce | 17 |
| H27 Pantano de agua dulce | H08 Bosque tropical inundable | 17 |
| H30 Río estacional | H23 Río de corriente lenta | 17 |
| H48 Acantilado costero | H44 Costa rocosa | 17 |
| H38 Pradera marina | H39 Bosque de algas | 16 |
| H10 Sabana inundable | H09 Sabana seca | 16 |
| H29 Humedal de alta montaña | H28 Turbera | 16 |
