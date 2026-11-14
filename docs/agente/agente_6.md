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

## 4. Las políticas nuevas y cómo se integran

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
   confirmados distintos en el reto (como el selector probabilístico del catálogo original,
   que cuenta todas las elecciones, incluso repetidas) o si ya vio **tres** ayudas.
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
4. Si ninguna candidata aporta nada (o todas tienen utilidad ≤ 0): **sin errores previos**
   sigue la secuencia editorial (pista 1, luego 2), de modo que la primera Pista nunca revela
   la respuesta; **tras un error** ofrece la pista 3. Si ya no quedan opciones no
   confirmadas, sigue la secuencia editorial sin repetir lo elegido.
5. Una ayuda por rasgo con la misma frase que una pista del hábitat (hoy «Busca un lugar con
   arbustos.» = `AY_H13_L1`) no se ofrece aparte para ese hábitat: ninguna frase se repite en
   un reto.

Los parámetros (0,5 / 0,25 / 0,85 / 0,6 / 1 / 1, tres ayudas, dos elecciones) **se fijaron a
mano** con los criterios anteriores; no se ajustaron con datos de jugadores, que no existen.
**No hay aprendizaje en vivo**: el agente decide igual en la primera y en la milésima partida.

### Qué no cambia

- **Repetir** devuelve exactamente el mensaje mostrado (mismo texto, pictogramas e ID) y no
  cambia lo mostrado. Sí activa la señal de dificultad del agente, que dura el resto del
  reto (también si se repite la pregunta antes de pedir pistas).
- **Pausar** y **Reanudar** no alteran la decisión siguiente.
- **Salir**, Continuar, las opciones visibles y el progreso siguen igual. No hay tiempo,
  puntos ni castigos.
- Los 288 animales, 48 hábitats, 2/4/8 opciones y los secundarios documentados se conservan;
  cualquier secundario visible completa el reto.

### Qué cambia también en la 5.0 (`/v5/`)

La 5.0 comparte servidor, API y sesión con la 6.0, así que **también usa el agente**: ya no
muestra siempre la secuencia pista 1 → 2 → 3. Para recuperar la secuencia anterior hay que
arrancar el servidor con `--agente PISTAS_PROGRESIVAS`, lo que afecta a las dos versiones a la
vez. Sus pruebas de navegador (`--hito2`, `--hito3`, `--catalogo`, general, `--voz-v5`) pasan
con el agente.

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
(265, 833 y 1985 casos). «Documentado» significa que la diferencia consta en los rasgos;
«sin valor», que todo lo que muestra la pista aparece también en las pistas de todas las
opciones no confirmadas.

| Política | Opciones | 1.ª pista descarta algo (documentado) | 1.ª pista sin valor | 1.ª pista es «Señala» | Ideas en la 1.ª | Tras un error: distingue lo elegido | Tras un error: también lo describe | Tras un error: pasa a «Señala» | 1.ª pista aleja de un secundario visible | Incompatibles |
|---|---|---|---|---|---|---|---|---|---|---|
| PISTAS_PROGRESIVAS | 2 | 20 % | 36 % | 0 % | 2,02 | 20 % | 68 % | 0 % | 9 | 0 |
| PISTAS_PROGRESIVAS | 4 | 40 % | 2 % | 0 % | 2,02 | 18 % | 63 % | 0 % | 10 | 0 |
| PISTAS_PROGRESIVAS | 8 | 60 % | 0 % | 0 % | 2,02 | 21 % | 48 % | 0 % | 10 | 0 |
| ID3_OPCIONES (grabadas) | 2 | 40 % | 26 % | 0 % | 2,08 | 40 % | 51 % | 0 % | 16 | 0 |
| ID3_OPCIONES (grabadas) | 4 | 61 % | 0 % | 0 % | 2,10 | 30 % | 49 % | 0 % | 17 | 0 |
| ID3_OPCIONES (grabadas) | 8 | 83 % | 0 % | 0 % | 2,11 | 32 % | 36 % | 0 % | 15 | 0 |
| **AGENTE (grabadas)** | 2 | 40 % | 0 % | 0 % | 2,08 | 40 % | 0 % | 16 % | 1 | 0 |
| **AGENTE (grabadas)** | 4 | 49 % | 0 % | 0 % | 2,05 | 31 % | 0 % | 14 % | 1 | 0 |
| **AGENTE (grabadas)** | 8 | 69 % | 0 % | 0 % | 2,09 | 34 % | 0 % | 9 % | 1 | 0 |
| AGENTE (todas) | 2 | 40 % | 0 % | 0 % | 1,44 | 40 % | 0 % | 13 % | 1 | 0 |
| AGENTE (todas) | 4 | 55 % | 0 % | 0 % | 1,53 | 31 % | 0 % | 10 % | 0 | 0 |
| AGENTE (todas) | 8 | 74 % | 0 % | 0 % | 1,63 | 34 % | 0 % | 6 % | 0 | 0 |

(`ID3_OPCIONES (todas)` da casi los mismos números que con grabadas; están en el JSON.)

Lectura:

- **Frente a la secuencia anterior.**
  - El agente nunca da una primera pista sin valor. La secuencia fija lo hace en el 36 % de
    los retos de 2 opciones.
  - Nunca revela la respuesta en la primera petición.
  - Tras un error, nunca repite algo que también describe lo elegido; la secuencia lo hace
    en el 48–68 % de los casos.
  - Distingue lo elegido con un rasgo documentado más a menudo (31–40 % frente a 18–21 %) y
    casi nunca aleja de un secundario visible.
- **Frente a ID3.** ID3 descarta más opciones con la primera pista con 4 y 8 opciones (61 % y
  83 % frente a 49 % y 69 %), porque solo maximiza la diferencia documentada. El agente
  además pondera la comprensión, las diferencias no comprobadas y los secundarios. ID3 da
  pistas sin valor (26 % con 2 opciones) y repite lo elegido en el 36–51 % de los casos.
- **Coste.** Tras el primer error, cuando ninguna ayuda restante distingue lo elegido sin
  describirlo también, el agente pasa al apoyo explícito: en el 9–16 % de los casos con las
  grabaciones de hoy y en el 6–13 % con todas las ayudas. La secuencia fija nunca lo hace tan
  pronto, pero en esos casos ofrecía una pista que también valía para lo elegido.
- **Límite de los datos.** Con 2 opciones, solo el 40 % de los retos tiene alguna diferencia
  documentada. Ninguna política puede superar ese techo sin rasgos nuevos (apartado 8).
- **Cero ayudas incompatibles** en todas las políticas: siempre hablan del hábitat guía visible
  y solo afirman rasgos documentados de él.

### 5.2 Jugador sintético (datos simulados, no personas)

Tres perfiles inventados (`autonomo`, `apoyo_medio`, `apoyo_alto`) con probabilidades fijas de
acertar sin ayuda, entender una frase de una idea y pedir pista (`PERFILES` en el script). Se
simulan 5 réplicas × 288 animales × 3 tamaños × 3 perfiles por política (12 960 retos), con
los mismos sorteos para todas.

- Si entiende la ayuda, el jugador simulado descarta siempre las opciones con una diferencia
  documentada y, a veces, las de una diferencia no documentada.
- Tras «Señala» acierta con probabilidad 0,95.
- Todos los retos se resuelven en todas las políticas.

| Política | Perfil | Elecciones no confirmadas por reto (2/4/8) | Ayudas por reto (2/4/8) | Llega a «Señala» (2/4/8) | Ideas por ayuda |
|---|---|---|---|---|---|
| PISTAS_PROGRESIVAS | autonomo | 0,23 / 0,50 / 0,66 | 0,72 / 1,07 / 1,29 | 6 / 14 / 22 % | 2,06 |
| PISTAS_PROGRESIVAS | apoyo_medio | 0,25 / 0,51 / 0,74 | 1,28 / 1,71 / 2,00 | 22 / 36 / 49 % | 2,06 |
| PISTAS_PROGRESIVAS | apoyo_alto | 0,26 / 0,44 / 0,59 | 1,96 / 2,34 / 2,54 | 49 / 65 / 75 % | 2,06 |
| ID3_OPCIONES (grabadas) | autonomo | 0,23 / 0,49 / 0,64 | 0,71 / 1,06 / 1,26 | 6 / 13 / 21 % | 2,09 |
| ID3_OPCIONES (grabadas) | apoyo_medio | 0,25 / 0,50 / 0,72 | 1,27 / 1,69 / 1,97 | 21 / 36 / 48 % | 2,08 |
| ID3_OPCIONES (grabadas) | apoyo_alto | 0,25 / 0,43 / 0,59 | 1,94 / 2,32 / 2,54 | 48 / 64 / 75 % | 2,07 |
| **AGENTE (grabadas)** | autonomo | 0,22 / 0,44 / 0,58 | 0,68 / 0,95 / 1,14 | 12 / 26 / 32 % | 2,06 |
| **AGENTE (grabadas)** | apoyo_medio | 0,24 / 0,45 / 0,66 | 1,20 / 1,51 / 1,75 | 27 / 44 / 54 % | 2,06 |
| **AGENTE (grabadas)** | apoyo_alto | 0,24 / 0,40 / 0,57 | 1,84 / 2,15 / 2,35 | 51 / 68 / 77 % | 2,05 |
| AGENTE (todas) | autonomo | 0,22 / 0,44 / 0,61 | 0,69 / 0,98 / 1,21 | 8 / 19 / 25 % | 1,66 |
| AGENTE (todas) | apoyo_medio | 0,23 / 0,47 / 0,71 | 1,25 / 1,65 / 1,98 | 19 / 31 / 42 % | 1,69 |
| AGENTE (todas) | apoyo_alto | 0,24 / 0,45 / 0,66 | 2,02 / 2,54 / 2,87 | 42 / 58 / 70 % | 1,72 |

Lectura, con cautela:

- **Con las grabaciones de hoy:**
  - Elecciones no confirmadas: el agente necesita menos que la secuencia anterior en los
    nueve casos. Con 2 opciones la diferencia es mínima (0,22–0,24 frente a 0,23–0,26).
  - Ayudas: también necesita menos.
  - Apoyo explícito: llega a «Señala» más veces (p. ej. autónomo, 12/26/32 % frente a
    6/14/22 %). Parte de la reducción de ayudas viene de ahí.
- **Con las 32 ayudas por rasgo:**
  - Las frases son más cortas (1,7 ideas frente a 2,1) y se llega menos a «Señala» que con
    las grabadas.
  - En el perfil `apoyo_alto` hacen falta más ayudas que con la secuencia (2,02 / 2,54 / 2,87
    frente a 1,96 / 2,34 / 2,54), y con 8 opciones algo más de elecciones: cada frase corta
    lleva menos información.
  - Es un cambio de compromiso que habría que observar con personas.
- **Límites.**
  - Los perfiles y probabilidades son inventados.
  - El jugador simulado usa la misma representación de rasgos que el agente, lo que favorece
    a las políticas que la usan.
  - No mide comprensión real, motivación, fatiga ni el papel del educador.
  - **No son resultados de usuarios** ni se usaron para entrenar nada.

## 5 bis. Aprendizaje fuera de la partida (Hito 2)

El enunciado del curso (TP-TF 1ASI0404, 2026-20, págs. 4-5) pide para el Hito 2 un modelo
principal de decisión «capaz de modular la asistencia» y un informe con su formulación y
**entrenamiento**: tasa de éxito, eficiencia de la guía y análisis de convergencia. Por eso el
agente tiene una tercera política, `AGENTE_APRENDIDO` (`codigo/motores/aprendizaje6.py`).

### Qué aprende

Es un **sistema experto probabilístico Beta-Bernoulli**: para cada *tipo* de ayuda estima la
probabilidad de que la siguiente acción del jugador sea elegir un hábitat confirmado. Un tipo
de ayuda combina cinco datos (72 tipos en total), no el hábitat concreto, para que los datos
alcancen:
- pista revisada o ayuda por rasgo;
- una idea o varias;
- 2, 4 u 8 opciones;
- si hubo señal de dificultad;
- si la ayuda distingue lo visible de forma documentada, sin comprobar o nada.

Cada tipo empieza en Beta(1, 1) y se actualiza con cada resultado.

- **Recompensa** (decidida por el propietario el 2026-11-14):
  - **1** si tras la ayuda se elige un hábitat confirmado;
  - **0** si se pide otra pista o se elige un hábitat no confirmado. El 0 significa que la
    ayuda no llevó a una respuesta confirmada, no que ese hábitat sea incorrecto;
  - **sin dato** si se sale.
- **Qué decide.** Solo elige entre las ayudas que el agente ya considera seguras e
  informativas: la de mayor probabilidad aprendida. Las reglas fijas siguen fuera del
  aprendizaje:
  - solo frases verdaderas del hábitat guía;
  - solo ayudas con grabación;
  - la primera Pista nunca revela la respuesta;
  - nunca describir lo ya elegido;
  - no alejar de otra respuesta válida visible (p. ej. el bosque templado del jaguar) si hay
    otra ayuda útil que no lo haga;
  - apoyo explícito tras dos elecciones o tres pistas.
- **Cuándo aprende.** Solo fuera de la partida. Al jugar, el modelo está **congelado** (media
  posterior) y no cambia. El archivo del modelo guarda la huella de los rasgos y de las
  pistas; si cambian, se niega a cargar y hay que volver a entrenar.

### Un único camino de datos, para sesiones reales y simuladas

`registro de la partida (JSONL) → etiquetas() → modelo Beta-Bernoulli → modelo congelado`
(`codigo/entrenamiento/entrenar_agente6.py`). La partida web ya guarda cada ayuda con su tipo
(`clave_aprendizaje`) y su cierre en `registros/interfaz/`.

```console
# Con sesiones reales (cuando existan, con el consentimiento que corresponda):
PYTHONUTF8=1 python -m codigo.entrenamiento.entrenar_agente6 entrenar --registros registros/interfaz --salida resultados_nuevos/modelo_sesiones.json
# Experimento con jugadores simulados (1 min 25 s):
PYTHONUTF8=1 python -m codigo.entrenamiento.entrenar_agente6 simular --salida docs/experimentos/agente6/aprendizaje
# Jugar con el modelo congelado (por defecto, el de demostración):
python -m codigo.interfaz.servidor --agente AGENTE_APRENDIDO --puerto 8005
python -m codigo.interfaz.servidor --agente AGENTE_APRENDIDO --modelo-agente resultados_nuevos/modelo_sesiones.json
```

Hoy **no hay sesiones reales**: `registros/interfaz/` solo tiene unas pocas partidas de prueba,
de origen desconocido. Por eso el entrenamiento de esta entrega es **simulado**.

### Experimento con jugadores simulados

- **Probabilidades plantadas.** El jugador simulado tiene, para cada tipo de ayuda, una
  probabilidad de acertar después de ella. Son valores inventados que el agente no conoce,
  en tres condiciones:
  - `IDEAS`: cada idea extra pesa mucho;
  - `RASGOS`: las frases por rasgo se entienden mejor;
  - `PISTAS`: las pistas editadas se entienden mejor.
- **Comportamiento del jugador simulado:**
  - antes de cualquier ayuda pide pista la mitad de las veces y acierta sin ayuda el 20 %;
  - si no acierta tras una ayuda, pide otra o elige un hábitat no confirmado;
  - tras «Señala» acierta el 95 %.
- **Protocolo**, el mismo del proyecto para el catálogo original:
  - 3 condiciones × 3 réplicas = 9 modelos;
  - cada modelo se entrena con 4320 retos (288 animales × 3 tamaños × 5 vueltas), con
    exploración por Thompson sampling y las 32 ayudas por rasgo activas;
  - después se congela y se evalúa con otras semillas sobre los mismos 864 retos (288 animales
    × 3 tamaños, con las mismas opciones), en otro orden y con otros sorteos del jugador. El
    modelo no ve el animal, así que repetir los retos no le da ventaja;
  - en la evaluación, cada reto usa la misma semilla para todas las políticas. Las secuencias
    de sorteos se separan en cuanto dos políticas deciden distinto.
- El modelo de demostración que carga el juego es `IDEAS_R01`, la primera réplica, elegida
  por orden y no por sus resultados.
- Datos completos en
  [`docs/experimentos/agente6/aprendizaje/experimento.json`](../experimentos/agente6/aprendizaje/experimento.json).

**Convergencia.** La tabla da el error medio, ponderado por observaciones, entre lo aprendido
y lo plantado (media de 3 réplicas).

| Condición | 144 retos | 432 retos | 864 retos | 1728 retos | 2592 retos | 4320 retos | Tipos vistos | Tipos con ≥30 obs. | Variación en los 3 últimos tramos |
|---|---|---|---|---|---|---|---|---|---|
| IDEAS | 0,081 | 0,057 | 0,049 | 0,030 | 0,025 | 0,020 | 37 de 72 | 16 | ≤ 0,003 |
| RASGOS | 0,092 | 0,060 | 0,046 | 0,036 | 0,027 | 0,020 | 35 de 72 | 15 | ≤ 0,002 |
| PISTAS | 0,097 | 0,051 | 0,042 | 0,034 | 0,026 | 0,021 | 34 de 72 | 16 | ≤ 0,003 |

- **Converge:** el error baja de 0,08–0,10 a 0,02, y en los tres últimos tramos cambia
  ≤ 0,003.
- **Cobertura parcial:** solo hay datos de los tipos de ayuda que llegan a mostrarse, tanto
  los que elige el modelo como los de las reglas fijas: unos 35 de 72, y 15–16 con 30 o más
  observaciones. Los demás siguen en su valor inicial. Varios tipos no pueden darse nunca;
  por ejemplo, casi todas las ayudas por rasgo tienen una sola idea.
- Es convergencia sobre datos simulados, no prueba de que el modelo acierte con personas.

**Tasa de éxito y eficiencia** (congelado, media de 3 réplicas). Todas las políticas resuelven
el 100 % de los retos en ≤ 10 acciones, porque al final se señala la respuesta. La medida
exigente es **acertar sin llegar a «Señala»**.

| Condición | Política | Acierta sin «Señala» (2/4/8) | Acciones por reto (2/4/8) | Elecciones no confirmadas (2/4/8) | Llega a «Señala» (2/4/8) |
|---|---|---|---|---|---|
| IDEAS | PISTAS_PROGRESIVAS | 62 / 65 / 56 % | 2,82 / 2,81 / 3,03 | 0,55 / 0,87 / 0,97 | 38 / 35 / 44 % |
| IDEAS | ID3_OPCIONES | 63 / 65 / 55 % | 2,77 / 2,79 / 3,01 | 0,54 / 0,86 / 0,95 | 37 / 35 / 45 % |
| IDEAS | AGENTE_ADAPTATIVO | 72 / 68 / 63 % | 2,40 / 2,53 / 2,80 | 0,48 / 0,73 / 0,84 | 28 / 32 / 37 % |
| IDEAS | **AGENTE_APRENDIDO** | 72 / 71 / 70 % | 2,40 / 2,46 / 2,62 | 0,48 / 0,69 / 0,73 | 28 / 29 / 30 % |
| RASGOS | PISTAS_PROGRESIVAS | 72 / 68 / 61 % | 2,66 / 2,79 / 2,89 | 0,53 / 0,85 / 0,93 | 28 / 32 / 39 % |
| RASGOS | ID3_OPCIONES | 73 / 68 / 62 % | 2,59 / 2,75 / 2,84 | 0,51 / 0,83 / 0,91 | 27 / 32 / 38 % |
| RASGOS | AGENTE_ADAPTATIVO | 78 / 73 / 72 % | 2,23 / 2,42 / 2,54 | 0,45 / 0,66 / 0,74 | 22 / 27 / 28 % |
| RASGOS | **AGENTE_APRENDIDO** | 78 / 77 / 76 % | 2,23 / 2,34 / 2,40 | 0,45 / 0,62 / 0,67 | 22 / 23 / 24 % |
| PISTAS | PISTAS_PROGRESIVAS | 88 / 90 / 86 % | 2,28 / 2,30 / 2,40 | 0,44 / 0,58 / 0,64 | 12 / 10 / 14 % |
| PISTAS | ID3_OPCIONES | 90 / 91 / 86 % | 2,22 / 2,26 / 2,36 | 0,44 / 0,56 / 0,62 | 10 / 9 / 14 % |
| PISTAS | AGENTE_ADAPTATIVO | 81 / 77 / 75 % | 2,33 / 2,38 / 2,52 | 0,46 / 0,63 / 0,70 | 19 / 23 / 25 % |
| PISTAS | **AGENTE_APRENDIDO** | 82 / 81 / 80 % | 2,26 / 2,26 / 2,38 | 0,43 / 0,57 / 0,63 | 18 / 19 / 20 % |

Lectura:
- **Frente al agente con parámetros fijos:** en promedio, el aprendido mejora o iguala en
  las tres condiciones. En alguna réplica con 2 opciones queda ligeramente por debajo. La diferencia aparece con 4 y 8 opciones (p. ej. `IDEAS` con 8 opciones: acierta
  sin «Señala» el 70 % frente al 63 %, con 2,62 acciones frente a 2,80). Con 2 opciones suelen
  elegir lo mismo.
- **Frente a la secuencia anterior y a ID3:** gana en `IDEAS` y `RASGOS`, pero **pierde en
  `PISTAS`** (80–82 % frente a 86–91 % sin «Señala»).
  - En esa condición, las pistas editadas, que la secuencia muestra siempre, son justo las
    que mejor se entienden.
  - Las reglas fijas del agente (apoyo explícito antes, no repetir lo que describe lo
    elegido) llevan antes a «Señala».
  - El aprendizaje reduce esa desventaja, pero no la elimina.
- Nada de esto mide comprensión real, motivación ni el papel del educador.

### Límites

- Los datos son simulados y las probabilidades, inventadas: el experimento muestra que el
  método aprende lo que hay en los datos, no qué ayuda funciona con las personas de Kallpa.
- **La comparación no es neutral.** Las probabilidades plantadas dependen de si la ayuda
  distingue de forma documentada, y eso se calcula con los rasgos y relaciones del propio
  agente: la secuencia y ID3 se puntúan con el criterio que el agente maximiza.
  - En sentido contrario, el jugador simulado no castiga una pista que también describe lo
    ya elegido. El agente paga un coste por evitarla que en la simulación no se ve.
- **No refleja la partida de hoy.** El experimento usa las 32 ayudas por rasgo, pero hoy
  solo una tiene grabación. Con las grabaciones actuales, la condición `RASGOS` casi no se
  da. Aun así, el modelo de demostración cambia alguna decisión frente al agente fijo.
- **Etiqueta de las elecciones no confirmadas.** El registro de la partida marca la elección
  de un hábitat no confirmado como «sin etiqueta», según el protocolo del catálogo original.
  El entrenamiento la cuenta como 0, por la recompensa decidida para la 6.0. Quien lea los
  JSONL verá esa diferencia.
- **Repetir y la señal de dificultad.** La clave de una ayuda se fija al mostrarla: si
  después se pulsa Repetir, la señal de dificultad no se añade a esa ayuda. No afecta a la
  simulación (el jugador simulado no repite), pero sí a los datos reales.
- `entrenar` descarta las ayudas jugadas con otros rasgos o pistas (por la huella), pero no
  distingue quién jugó: mezcla la 6.0, `/v5/` y las pruebas de navegador. Hay que preparar la
  carpeta de registros antes de entrenar.
- **Entrenar con sesiones reales** exigirá:
  - sesiones con educadores y el consentimiento que corresponda;
  - revisar antes los rasgos (apartado 8), porque el modelo aprende sobre ellos;
  - comparar el modelo nuevo con el actual antes de usarlo.
- Con pocas sesiones, la mayoría de los tipos seguirán sin datos y el agente decidirá casi
  como el de parámetros fijos.
- No hay aprendizaje en vivo: explorar con personas reales supondría darles a propósito
  ayudas peores.

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

**Automáticas** (`tests/test_agente6.py`, 15 pruebas, y `tests/test_aprendizaje6.py`, 11 pruebas
del aprendizaje: etiquetas desde el registro, Beta-Bernoulli, modelo congelado y seguro,
recuperación de lo plantado; con el resto, 121 en total):

- datos: cada rasgo cita una pista revisada del mismo hábitat; ayudas breves, con
  pictogramas existentes y traducción; lo desconocido nunca descarta;
- exhaustiva: los 288 animales con 2, 4 y 8 opciones y las tres políticas. Las opciones
  conservan los confirmados que caben, toda ayuda habla del hábitat guía visible y solo
  afirma rasgos documentados, y la del agente tras un error nunca describe lo elegido;
- exhaustiva: la primera Pista nunca es «Señala» y ninguna frase se repite en un reto;
- casos: salta la pista 1 idéntica entre H04 y H05; distingue la última elección (H06 frente a
  H05); no aleja del secundario documentado (jaguar y H04); apoyo explícito tras dos elecciones
  o tres ayudas; Repetir exacto; Pausar y Reanudar sin efecto; sin grabación no se usa la ayuda
  por rasgo y, con una grabación de prueba, sí; ID3 elige la mayor ganancia de información;
- cobertura de voz con el agente en la partida real (`test_voz_grabada_cobertura`). Lee unos
  300 mensajes distintos, porque el agente no recorre todas las pistas en orden. Las demás
  ramas quedan cubiertas porque el agente solo construye candidatas con grabación: las pistas
  y apoyos ya grabados, y las ayudas por rasgo filtradas por `ayudas_con_grabacion`, que
  `test_sin_grabacion_no_se_usa_la_ayuda_por_rasgo` comprueba;
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
   ejemplo «agua dulce» en H24 y H30 o «templado» en H13. Esta entrega **no** los añade.
4. **Lecturas apoyadas solo en un pictograma:** en H19 y H26, «agua dulce» consta en el
   pictograma `P_AGUA_DULCE` de la pista, no en el texto. H41 «costa» se deduce de «desemboca…
   se mezcla con el mar».
5. **Los valores sin revisar ya deciden qué pista se muestra.** Las frases que ve el jugador
   son las pistas revisadas (y, cuando haya audio, las ayudas por rasgo), pero el orden y el
   paso al apoyo explícito dependen de estas lecturas, todavía sin confirmar por una persona.
   Si el propietario prefiere esperar a la revisión, `--agente PISTAS_PROGRESIVAS` restablece
   la secuencia anterior sin tocar código.
6. `codigo/interfaz/generar_voces_api.py` no genera las ayudas por rasgo mientras la columna
   `revision_humana` de `catalogo_voces.csv` esté vacía.

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
| H16 Pastizal de alta montaña | Paisaje: abierto (pista 1); Ubicación: montana (pista 1); Plantas que dominan: pasto (pista 2) |
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
