# Informe M3 — Evaluación sobre la sala de escape

Aplicación del framework de M1+M2 a un problema objetivo (mundo simulado tipo
sala de escape), con infraestructura de evaluación reproducible, métricas
cuantitativas y cualitativas, análisis de errores y dos experimentos.

Todo lo que sigue se reproduce con:

```bash
export OLLAMA_HOST="http://localhost:11434" OLLAMA_MODEL="llama3.1:8b"
python eval/run.py --juez                       # baseline sobre los 8 escenarios
python eval/run.py --experimento e1-memoria     # E1
python eval/run.py --experimento e2-prompt      # E2
```

---

## 1. Aproximación

### 1.1. Cómo se conecta el framework con el mundo

El mundo (`mia_world/`) y los escenarios (`scenarios/`) son fijos y los provee
la cátedra. La conexión con nuestro agente es deliberadamente delgada, y usa
el mismo patrón que ya usábamos en M1 para registrar nuestras herramientas:

```python
escenario = load_scenario(path)          # mundo + meta + mensaje del usuario
mundo     = escenario.initial_world
agente    = build_agent(config)          # nuestro MyAgent de M1+M2
for fn, schema in make_world_tools(mundo):
    agente.register_tool(fn, schema)     # mismo (fn, schema) que el REGISTRY
resultado = agente.run(escenario.user_message)
lograda, razon = check_goal(mundo, escenario.goal)
```

Las herramientas del mundo llegan como pares `(callable, ToolSchema)`, que es
exactamente la forma que `register_tool` espera desde M1. **No hizo falta
adaptar nada del agente para que hablara con el mundo**: la interfaz de
herramientas que diseñamos en M1 ya servía.

Usamos `mia_world` como biblioteca en lugar de invocar su CLI, porque la
evaluación necesita dos cosas que la CLI no expone: inyectar configuración en
el agente (cada condición experimental es una config distinta) y quedarse con
la traza completa de la corrida.

### 1.2. Qué especializamos

Tres cosas, todas por configuración y ninguna tocando el bucle del agente.

**a) System prompt del dominio** (`student_framework/prompts.py`). El default
del framework (`"Eres un asistente útil."`) produce conducta de asistente
conversacional: en las primeras pruebas el modelo hacía un `look`, describía
la sala y **le preguntaba al usuario qué hacer**. Como la condición de parada
del bucle es "texto sin `tool_calls`", esa pregunta terminaba la corrida con
la puerta cerrada. Un asistente útil pregunta; un agente actúa. El prompt
especializado fija el objetivo, el ciclo observar→explorar→tomar→usar, la
disciplina de una acción por turno y el uso de ids exactos. Su efecto se mide
en el experimento E2 (sección 4).

**b) Presupuesto de iteraciones proporcional al escenario**
(`eval/config.py::presupuesto_iteraciones`). Cada iteración del bucle es una
llamada al LLM; si el modelo pide una herramienta por turno, un escenario de
21 llamadas óptimas necesita al menos 22 iteraciones. Con el default de M1
(`max_iterations=10`), la mitad de los escenarios habría fallado **por nuestro
techo antes de que el modelo tuviera oportunidad de razonar mal**, y el
análisis de errores estaría midiendo nuestra configuración en vez del agente.
La fórmula es `2 × óptimo + 8`: margen para explorar y equivocarse sin
volverse infinita, y escala con la dificultad en lugar de regalarle
presupuesto de escenario difícil a uno fácil.

**c) Agente sin las herramientas de M1/M2** (`tools_por_defecto=False`).
`build_agent` auto-registra las herramientas propias (calculadora, lector de
archivos, contador de palabras) desde el `REGISTRY`. En la sala de escape son
distractores: no resuelven nada, agregan chances de elegir mal y ocupaban
461 tokens extra **en cada llamada** (1419 → 958 en el primer turno). El
parámetro es opcional y su default es `True`, así que el comportamiento de
M1, M2 y de la CLI de la cátedra no cambia.

### 1.3. Una corrección al framework que solo apareció con un LLM real

Al correr los primeros escenarios, el agente entraba en bucle sobre `examine`
sin lograr nada. La causa no era el modelo: era **nuestro manejo de errores**.
El modelo invocaba `examine({"objeto": "alfombra"})` — traduciendo al español
el nombre del parámetro, que en realidad es `target` — y nuestro `_dispatch`
le devolvía la excepción cruda de CPython:

```
Error al ejecutar 'examine': _make_examine.<locals>.examine_impl() got an
unexpected keyword argument 'objeto'
```

Ese mensaje filtra internals y, sobre todo, **no dice cuál era el nombre
correcto**, así que el modelo seguía adivinando (`objeto`, `id`, `objeto`…)
hasta agotar el presupuesto. Contradecía de lleno el principio de errores
accionables que habíamos aplicado en M2 a nuestras herramientas: la capa de
*despacho* había quedado afuera.

Ahora los argumentos se validan contra el `ToolSchema` registrado **antes** de
invocar, y el mensaje es accionable:

```
Argumentos inválidos para 'examine'. No existe(n) el/los parámetro(s): objeto.
Falta(n) el/los requerido(s): target. Probablemente quisiste decir 'target' en
lugar de 'objeto'. Parámetros válidos: target.
```

El efecto fue inmediato: en la misma corrida el modelo se equivocó dos veces
de nombre de parámetro y **se corrigió las dos**, resolviendo el escenario en
8 llamadas donde antes fallaba tras 14.

Lo importante para el informe no es el arreglo, sino **por qué no lo habíamos
detectado**: los 210 tests de M1 y M2 pasaban antes y después, porque
`MockLLMClient` nunca se equivoca de nombre de argumento. Hizo falta un modelo
real para que apareciera. Es la limitación estructural de evaluar un agente
solo con mocks.

---

## 2. Métricas

### 2.1. Cuantitativa principal — tasa de éxito sobre el estado del mundo

`check_goal(mundo, meta)` inspecciona el **estado del mundo simulado**, no lo
que el agente dice haber hecho. Esa distinción no es teórica: en nuestras
corridas el agente respondió *"¡Lo logré! Abriendo la puerta principal"* en
casos donde la puerta seguía cerrada. Cualquier métrica basada en su texto
—exact match sobre la respuesta, por ejemplo— habría contado esos casos como
éxitos. Medir sobre el mundo hace la métrica inmune a la elocuencia del
modelo, que es justamente la propiedad que uno quiere de una métrica de
agentes.

El mundo soporta metas compuestas (`all_of`, `any_of`, `sequence`), así que la
misma métrica cubre desde "abrí la puerta" hasta "conseguí el documento
**antes** de abrir la puerta" sin cambiar de instrumento.

### 2.2. Cuantitativa secundaria — eficiencia contra el óptimo

El enunciado publica la cantidad de llamadas de la solución óptima de cada
escenario, así que podemos medir `eficiencia = óptimo / llamadas usadas`
(acotada a 1.0). Sin ella, "resolvió" y "resolvió dando vueltas" se ven
iguales: `color-locks` se resuelve en 11 llamadas y nuestro agente lo logró en
23, o sea eficiencia 0.48 — un éxito, pero caro.

Se calcula **solo sobre corridas exitosas**, a propósito: en una corrida
fallida "pocos pasos" no significa eficiencia sino rendición temprana, y
promediarlas juntas premiaría al agente que abandona rápido.

Como métricas de costo acompañan tokens de entrada/salida y latencia, que ya
veníamos acumulando desde M2 en `AgentResult`.

### 2.3. Cualitativa — rúbrica vía LLM-as-judge con salida estructurada

La tasa de éxito dice *si* el agente llegó, no *cómo se comportó*. Dos
corridas fallidas pueden ser muy distintas: una que exploró con criterio y se
quedó sin presupuesto, y otra que repitió la misma acción veinte veces. Para
el análisis de errores esa diferencia es exactamente lo que importa.

El juez puntúa tres dimensiones de 1 a 5 —coherencia del plan, recuperación
ante errores y eficiencia de la exploración— más una justificación en texto.

**El juez usa nuestro propio `structured_call` del M2.** Un juez que responde
en prosa hay que parsearlo con expresiones regulares y confiar en que respete
el formato. Ofreciéndole la herramienta sintética `final_result` con el schema
`Veredicto`, la salida llega como un modelo Pydantic ya validado, y si el
modelo se desvía, el mecanismo de reparación lo corrige automáticamente. Es la
maquinaria de M2 resolviendo un problema real, no una función construida para
pasar un test.

**Limitación asumida:** el juez corre sobre el mismo modelo local que el
agente evaluado. Un modelo chico juzgándose a sí mismo es un juez ruidoso, y
sus notas se leen como señal comparativa entre condiciones, no como verdad
absoluta. Con credenciales de Bedrock, usar un modelo más fuerte como juez es
cambiar una variable de entorno.

### 2.4. Reproducibilidad

`python eval/run.py` corre sin pasos manuales: toma el proveedor del entorno
(la misma convención que `LLMClient.from_env`), ejecuta los casos, guarda una
traza JSON por corrida y emite `summary.json` + `informe.md`.

La captura de trazas se hace envolviendo el **cliente LLM**
(`eval/recording.py`), no instrumentando el agente: es la misma sustitución por
protocolo que usan los tests con `MockLLMClient`, y deja tanto `agent.py` como
`mia_agents/` intactos. Por llamada se guardan metadatos (mensajes enviados,
herramientas ofrecidas, respuesta, tokens, latencia) en vez del historial
completo, que crecería de forma cuadrática al acumularse turno a turno.

La propia infraestructura está testeada (`tests/test_eval.py`, 27 casos con
trazas sintéticas): si la taxonomía clasificara mal, todas las afirmaciones de
la sección 3 quedarían viciadas.

---

## 3. Resultados

Modelo: `llama3.1:8b` sobre Ollama local. Baseline = 32 corridas (los 8
escenarios × 2 repeticiones, agrupando las corridas de baseline de ambos
experimentos, que comparten configuración).

### 3.1. Números principales

| Métrica | Valor |
|---|---|
| Tasa de éxito | **25 %** (8/32) |
| Eficiencia media (sobre éxitos) | 0.43 |
| Fracción de llamadas repetidas | 27 % |
| Pasos medios | 18.7 |
| Tokens de entrada / salida por corrida | 33 927 / 399 |
| Latencia mediana | 14 s |

### 3.2. Desglose por dificultad

| Dificultad | Éxito | Repetidas |
|---|---|---|
| easy | **100 %** (4/4) | 0 % |
| medium | 50 % (4/8) | 40 % |
| hard | 0 % (0/8) | 18 % |
| extreme | 0 % (0/12) | 33 % |

### 3.3. Desglose por escenario

| Escenario | Óptimo | Éxito | Pasos | Repetidas | Modo de fallo |
|---|---:|---|---:|---:|---|
| study-with-key | 3 | 4/4 | 7.8 | 0 % | — |
| color-locks | 11 | 4/4 | 23.2 | 23 % | — |
| apartment-keys | 7 | 0/4 | 20.8 | 58 % | bucle, argumentos_invalidos |
| library-search | 7 | 0/4 | 22.0 | 36 % | bucle, accion_invalida |
| office-sequence | 13 | 0/4 | 1.0 | 0 % | tool_call_en_texto |
| extreme-archive | 4 | 0/4 | 2.0 | 0 % | tool_call_en_texto |
| vault-combination | 21 | 0/4 | 50.0 | 73 % | bucle |
| backtracking-vault | 18 | 0/4 | 22.5 | 26 % | bucle, parada_prematura |

Lo más informativo de esta tabla no son los promedios sino su **consistencia**:
cada escenario da 4/4 o 0/4, nunca 2/4. El agente no es errático — tiene un
techo nítido. Resuelve `easy` siempre, resuelve `color-locks` (11 llamadas
óptimas, cadena de cofres en una sola sala) siempre, y a partir de ahí no
resuelve nada. El salto que no cruza es la **navegación multi-sala**:
`apartment-keys` es *medium* y tiene menos llamadas óptimas que `color-locks`
(7 contra 11), pero exige recordar el mapa, ir a otra sala y volver. Ahí falla
sistemáticamente. La dificultad que frena a este agente no es la longitud de
la cadena: es tener que sostener un modelo del espacio.

### 3.4. Análisis de errores

Modo de fallo principal de las 24 corridas fallidas del baseline:

| Modo | Corridas |
|---|---:|
| bucle | 11 |
| tool_call_en_texto | 8 |
| accion_invalida | 2 |
| parada_prematura | 2 |
| argumentos_invalidos | 1 |

**`bucle` (11/24).** El agente reinvoca acciones que ya ejecutó hasta agotar
el presupuesto. El caso extremo es `vault-combination`: 73 % de sus llamadas
son repeticiones. Una traza de `color-locks` con ventana recortada muestra el
patrón en su forma más pura — un ciclo de dos pasos, `examine(llave_plateada)`
→ error, `examine(puerta_principal)` → ok, repetido doce veces seguidas. El
agente no está eligiendo mal: está eligiendo **sin ver que ya eligió eso**.

**`tool_call_en_texto` (8/24).** El modelo escribe la llamada como texto plano
—literalmente `{"name": "look"}`— en vez de emitirla por la API de
tool-calling. Como la condición de parada del bucle es "texto sin
`tool_calls`", eso termina la corrida. Es el modo que fulmina `office-sequence`
y `extreme-archive`, ambos 4/4 con apenas 1 o 2 pasos.

Vale precisar qué **no** lo causa: revisamos los tokens de esas corridas y
están en ~1000, muy por debajo del techo de 16 384 de la ventana de contexto.
No es desborde. Lo que sí observamos es que el 86 % de las corridas con este
modo terminan justo después de una acción fallida, contra un 68 % en el resto
de las fallidas. Es una correlación sugestiva, no una causa demostrada: con
este tamaño de muestra la diferencia no alcanza para afirmar que el error
previo lo provoca.

Decidimos **no** tolerar este formato (parsear el texto y ejecutarlo igual),
aunque es una técnica habitual. Modificar la condición de parada tocaría un
contrato de M1 verificado por los tests de conformidad, y M3 es un milestone
de medición: preferimos que el modo de fallo quede medido y explicado antes
que tapado. Queda anotado en la sección 5 como lo primero a construir.

### 3.5. Rúbrica cualitativa, y por qué contradice a la métrica dura

El juez puntuó las 48 corridas de E1 **sin un solo fallo de formato**: 48/48
devolvieron un `Veredicto` válido. Es, de paso, la mejor evidencia de que el
mecanismo de `final_result` + reparación de M2 funciona en producción y no
solo en los tests.

Sobre el conjunto completo, el juez discrimina bien:

| Grupo | Coherencia | Recuperación | Exploración |
|---|---:|---:|---:|
| Corridas que lograron la meta (n=4) | 4.00 | 3.50 | 4.50 |
| Corridas fallidas (n=44) | 2.64 | 1.82 | 2.70 |

Pero al comparar **condiciones** aparece una inversión incómoda: la condición
que resuelve el 0 % recibe mejores notas que la que resuelve el 25 %. Mirando
solo corridas fallidas, para aislar el efecto:

| Condición (solo fallidas) | Coherencia | Recuperación | Exploración | Repetidas | Pasos |
|---|---:|---:|---:|---:|---:|
| baseline (50) | 1.83 | 1.42 | 2.08 | 37 % | 22.6 |
| memoria_ajustada (8) | 2.50 | 1.50 | 2.62 | 21 % | 12.8 |
| memoria_minima (4) | **3.38** | **2.44** | **3.25** | 15 % | 6.0 |

La nota sigue casi exactamente a la tasa de repetición. Y eso es coherente: el
juez puntúa lo que le pedimos —coherencia del plan, recuperación ante errores,
redundancia de la exploración—, tres dimensiones de **calidad de conducta**.
Una traza que se desarma a los seis pasos simplemente exhibe menos mala
conducta observable que una que da vueltas veintidós veces.

O sea que el juez no está equivocado: **la rúbrica está incompleta**. Le falta
una dimensión de *avance hacia el objetivo* que penalice rendirse temprano, no
solo insistir mal. Descartamos ajustarla después de ver los resultados —sería
elegir la métrica que confirma la conclusión que ya sacamos—; queda anotado
como corrección para la próxima iteración.

La lección metodológica es la que importa: una métrica cualitativa mide lo que
su rúbrica define, no lo que uno espera que mida. Contrastarla contra una
métrica dura e independiente (`check_goal` sobre el estado del mundo) es lo que
permitió detectar el desacople. Con el juez solo, habríamos concluido que
recortar la memoria mejora al agente.

---

## 4. Experimentos

Las hipótesis de ambos experimentos se escribieron y commitearon **antes** de
ejecutarlos (`eval/config.py::HIPOTESIS`, commit `fe13512`, anterior al de los
resultados), junto con qué observación las refutaría.

### 4.1. E1 — Presupuesto de memoria

Se varía `max_history_messages` manteniendo todo lo demás fijo. 16 corridas
por condición.

| Condición | Ventana | Éxito | Repetidas | Pasos | Tokens entrada | Latencia mediana |
|---|---:|---|---:|---:|---:|---:|
| baseline | 50 | **25 %** (4/16) | 31 % | 20.8 | 38 535 | 21 s |
| memoria_ajustada | 8 | 0 % (0/16) | 21 % | 12.8 | 12 023 | 12 s |
| memoria_minima | 4 | 0 % (0/16) | 15 % | 6.0 | 5 236 | 6 s |

**Hipótesis: parcialmente refutada — y el modo en que falla es el hallazgo.**

Acertamos la dirección: recortar la ventana degrada el desempeño de forma
monótona, y basta bajar de 50 a 8 mensajes para que la tasa de éxito caiga a
cero. Pero predijimos que el mecanismo sería **más repetición**, y los datos
dicen lo contrario: la fracción de llamadas repetidas **baja** con la ventana
(31 % → 21 % → 15 %).

La explicación está en los pasos: 20.8 → 12.8 → 6.0. Con la ventana chica el
agente no repite más, **colapsa antes**, así que ni llega a tener oportunidad
de repetirse. Y el modo de fallo cambia de naturaleza:

| Condición | bucle | tool_call_en_texto |
|---|---:|---:|
| baseline (50) | 7 | 4 |
| memoria_ajustada (8) | 3 | 13 |
| memoria_minima (4) | 2 | 14 |

Con memoria amplia el agente fracasa *actuando* (da vueltas); con memoria
mínima fracasa *desarmándose* (deja de emitir tool calls y escribe texto).

La instrumentación muestra por qué. Registrando cuántos mensajes recibe el
modelo en cada llamada de un mismo escenario:

- **baseline**: 1 → 3 → 5 → 7 → 9 → 11 → 13 → 15 → 17 (crece; resuelve)
- **memoria_ajustada**: 1 → 3 → 5 → 7 → 7 → 7 → 7 (se estanca)
- **memoria_minima**: 1 → 3 → 3 (apenas un intercambio)

Con tres mensajes por llamada, el agente ve `[objetivo, acción, resultado]` y
nada más: no tiene visión de su propia trayectoria. Perder la traza de la
conversación no solo le borra lo que hizo — le borra también el patrón de que
está en un bucle de herramientas, y el modelo retrocede a describir la acción
en prosa en lugar de invocarla.

(Detalle de implementación visible en esos números: las ventanas se estabilizan
en 7 y 3, no en 8 y 4. Es el recorte de M2 descartando un resultado de
herramienta que quedó sin su `tool_call`, para no enviar pares rotos. Quedar
por debajo del tope es válido; superarlo, no.)

**Lectura de costos.** La ventana mínima consume 7× menos tokens de entrada y
es 3.5× más rápida. Como optimización de costo funciona perfecto; como
configuración de producto resuelve el 0 % de las tareas. Es el argumento más
claro a favor del trabajo de M2: la gestión de contexto no es gratis, pero
recortarla de más no es "un poco peor", es binariamente peor.

### 4.2. E2 — System prompt especializado

Se varía únicamente el `system_prompt`. 16 corridas por condición.

| Condición | Éxito | Repetidas | Pasos | Latencia mediana |
|---|---|---:|---:|---:|
| prompt_generico | 0 % (0/16) | 44 % | 22.3 | 12 s |
| baseline (especializado) | **25 %** (4/16) | 23 % | 16.5 | 14 s |

**Hipótesis: confirmada en el resultado, refutada en el mecanismo.**

El prompt especializado es la diferencia entre resolver algo y no resolver
nada: 25 % contra 0 %. Y casi duplica la disciplina — la fracción de llamadas
repetidas baja de 44 % a 23 %.

Pero habíamos predicho que el prompt genérico fallaría por **paradas
prematuras** (el modelo preguntándole al usuario qué hacer, como pasó en las
pruebas manuales). No fue así:

| Condición | bucle | accion_invalida | tool_call_en_texto | parada_prematura |
|---|---:|---:|---:|---:|
| prompt_generico | 9 | 7 | 0 | 0 |
| baseline | 4 | 2 | 4 | 2 |

Con presupuesto de iteraciones amplio, el prompt genérico no se rinde: da
vueltas (bucle) e insiste con acciones que el mundo rechaza
(`accion_invalida`). La parada prematura que habíamos visto a mano aparecía
porque aquellas pruebas corrían con presupuestos chicos. Es un recordatorio
metodológico útil: **una observación anecdótica sugiere una hipótesis, no la
confirma**, y el experimento controlado la corrigió.

Un detalle contraintuitivo: el prompt genérico consume **menos** tokens de
entrada (16 613 contra 29 320). No es una virtud — refleja que sus corridas
mueren antes y con contextos más chicos. Mide fracaso, no eficiencia; por eso
el costo nunca se lee sin la tasa de éxito al lado.

---

## 5. Limitaciones y qué construiríamos a continuación

### 5.1. Limitaciones de la evaluación

**El modelo es el techo más probable, y no lo aislamos.** Todo se corrió con
`llama3.1:8b` local. Los experimentos muestran que el prompt y la memoria
mueven el resultado, pero no permiten separar "nuestro framework se queda
corto" de "el modelo se queda corto". El propio andamiaje sugiere un
experimento que no hicimos —comparar `nova-micro` contra `nova-lite`— y con
credenciales de Bedrock sería cambiar una variable de entorno, porque el
harness elige proveedor desde el entorno y nada en `eval/` supone Ollama.

**El juez comparte modelo con el evaluado.** Un modelo chico puntuando sus
propias trazas es un juez ruidoso y probablemente sesgado. Sus notas se leen
como señal comparativa entre condiciones, no como medición absoluta.

**La rúbrica del juez está incompleta** (sección 3.5). Sus tres dimensiones
miden calidad de conducta y ninguna mide avance hacia el objetivo, así que
premia a la condición que falla rápido y limpio por encima de la que insiste
mal. No la corregimos post-hoc a propósito: cambiar la métrica después de ver
los resultados es elegir la que confirma la conclusión deseada.

**Dos repeticiones por celda.** Es poco para un sistema estocástico. Lo
atenúa la consistencia observada —los escenarios dan 4/4 o 0/4, nunca
resultados partidos—, pero no alcanza para poner intervalos de confianza sobre
las diferencias. Tampoco controlamos la temperatura: se usó la del protocolo
(0.2) en todas las condiciones.

**Una corrida quedó contaminada por el entorno.** Un caso registró 6 207 s
frente a una mediana de 12 s: la máquina estuvo inactiva mientras la
evaluación corría desatendida. No afecta la corrección de la corrida (los
pasos y la meta son válidos), pero destruía la media de latencia de su
condición. Por eso la latencia se reporta por **mediana**, con la media a la
vista para que la discrepancia entre ambas delate estos casos.

**El presupuesto de iteraciones es una decisión nuestra que afecta los
resultados.** `2 × óptimo + 8` es defendible pero arbitrario en el margen. Con
presupuestos chicos habríamos visto más paradas prematuras y menos bucles: de
hecho eso explica la discrepancia entre nuestras pruebas manuales y E2.

### 5.2. Qué construiríamos a continuación

**1. Tolerar la tool call escrita como texto.** Es el arreglo con mejor
relación esfuerzo/beneficio: hoy explica 8 de las 24 corridas fallidas del
baseline, y fulmina dos escenarios completos en 1 o 2 pasos. Si el `content`
tiene la forma de una llamada, parsearlo y ejecutarlo en lugar de terminar el
bucle. Lo dejamos afuera a propósito —cambia una condición de parada que los
tests de conformidad verifican— así que iría detrás de un flag, apagado por
defecto, y medido como un experimento más en vez de asumido.

**2. Memoria episódica de acciones ya ejecutadas.** El bucle es el modo de
fallo dominante (11 de 24) y su causa es visible: el agente reinvoca lo que ya
hizo porque no lo ve. En vez de agrandar la ventana —que cuesta tokens
linealmente y choca con el techo de contexto— mantener un registro compacto de
`(herramienta, argumentos) → resultado` e inyectarlo en el system prompt, que
queda **fuera** del presupuesto de la ventana deslizante. Es la jerarquía de
memoria episódica que se discutió en clase, separando lo que el usuario pidió
de las herramientas que se ejecutaron, y ataca directamente el 46 % de
nuestros fracasos.

**3. Un planificador explícito para las metas ordenadas.** `office-sequence`
exige conseguir un documento *antes* de abrir la puerta. Un agente puramente
reactivo no tiene por qué respetar un orden que nadie le hizo explícito;
descomponer la meta en sub-objetivos y verificarlos en secuencia es el
experimento natural de "planner contra ReAct puro" que el enunciado sugiere.

**4. Un juez más fuerte y más repeticiones.** Con un modelo grande como juez y
5 repeticiones por celda, las diferencias entre condiciones admitirían un test
estadístico en vez de una lectura cualitativa.

### 5.3. Lo que este milestone nos enseñó sobre los dos anteriores

El hallazgo más útil de M3 no fue un número sino un bug: nuestro despacho de
herramientas devolvía excepciones crudas de Python cuando el modelo erraba el
nombre de un parámetro, sin decirle cuál era el correcto. El agente quedaba
adivinando hasta agotar el presupuesto.

Los 210 tests de M1 y M2 pasaban antes y después del arreglo, porque
`MockLLMClient` siempre invoca las herramientas con los nombres correctos. Un
mock solo comete los errores que uno le programa; un modelo real comete los
que se le ocurren. Esa es, en una frase, la razón por la que un milestone de
evaluación sobre un problema real no es un adorno sobre M1 y M2: es lo que
descubre lo que los tests no podían ver.
