# Trabajo Práctico Final — Escape Room Agent

**Agentes Autónomos y Sistemas de Decisión**

HOFMANN · PIVOTTO · KARAGOZIAN

Universidad de San Andrés — Maestría en Inteligencia Artificial

Buenos Aires, Agosto de 2026

---

## 0. Marco teórico — Arquitectura del agente

El framework construido a lo largo de M1 y M2 sigue el paradigma ReAct que
intercala razonamiento y acción en un mismo bucle en lugar de separarlos en
etapas independientes de planificación y ejecución. En cada turno el agente
atraviesa el ciclo genérico de percepción, actualización de estado, decisión y
acción que se vio en la materia como el estilo arquitectónico común a cualquier
agente, desde un termostato hasta un sistema con un modelo de lenguaje. En este
framework, sense es la observación que llega como resultado de la última
herramienta invocada, state es el historial acumulado en la conversación, decide
es la llamada al modelo con ese historial y los esquemas de herramientas
disponibles, y act es la ejecución real de la herramienta elegida, que nunca
corre dentro del modelo sino en el runtime que lo rodea. El framework no
implementa una etapa explícita de reflect, lo cual es consistente con lo visto
en clase, ReAct en su forma original tampoco la incluye, esa etapa aparece
recién en arquitecturas posteriores.

Esta forma de operar encaja con el problema de M3 de un modo particular. Una
sala de escape es un entorno parcialmente observable, el agente no tiene acceso
directo al estado completo del mundo, solo puede reconstruirlo invocando
herramientas. Un objeto guardado dentro de un cofre no existe para el agente
hasta que un `examine` lo revela, y una sala contigua no forma parte de su
representación del mundo hasta que un `go` lo lleva ahí. El agente debe
sostener, turno a turno, un modelo interno del entorno construido únicamente a
partir de lo que sus propias acciones le devuelven, exactamente el problema que
la clase describe como memoria de trabajo operando sobre un entorno que no se
revela de una sola vez.

El sistema tiene cuatro componentes con responsabilidades separadas.

| Componente | Responsabilidad | Ubicación |
| :---- | :---- | :---- |
| **Cliente del LLM** | Abstrae el proveedor concreto detrás de un único método `chat`, que recibe mensajes, herramientas disponibles y system prompt. Es el contrato de API descripto en la materia, messages, system, tools y la respuesta con su contenido y sus tool calls. | `mia_agents/llm_client.py` (fijo) |
| **Registro de herramientas** | Cada herramienta es una función pura de Python que devuelve un string, acompañada de un esquema JSON derivado automáticamente de su firma y su docstring. El docstring se convierte en la descripción que el modelo lee para decidir cuándo usar la herramienta, el mismo mecanismo que la materia señala como el factor que más afecta la performance del tool use. | `agent.register_tool` |
| **Bucle del agente** | Llama al modelo, y si la respuesta trae una o más invocaciones de herramientas las ejecuta y devuelve cada resultado como observación nueva. Si la respuesta es texto sin invocaciones, ese texto es la respuesta final. El número de iteraciones está acotado. | `student_framework/agent.py`, método `run` |
| **Memoria conversacional** | El historial se conserva entre llamadas sucesivas, de modo que la tarea se extiende a lo largo de muchos turnos sin perder contexto previo. | `MyAgent`, atributo `_history` |

### El tool use como protocolo

El uso de herramientas sigue exactamente el protocolo de dos turnos visto en la
materia. En el primer turno el modelo no ejecuta nada, emite una invocación
estructurada con el nombre de la herramienta y sus argumentos. El runtime
intercepta esa invocación, valida los argumentos contra el esquema registrado y
ejecuta la función real. En el segundo turno el resultado vuelve al modelo como
una observación, y recién ahí el modelo continúa. Este protocolo, repetido
muchas veces, es el agent loop. La separación de responsabilidades es estricta,
el modelo decide qué herramienta usar, el código la ejecuta, y esa separación es
la que permite que un error de herramienta se trate como una observación más y
no como un fallo que interrumpe la ejecución, un punto que retoma la sección 1
al describir un bug real del framework.

### Gestión de contexto

La materia describe cuatro estrategias para administrar una ventana de contexto
que crece sin límite, truncado simple, ventana deslizante, resumen y
almacenamiento externo con recuperación bajo demanda. El framework de M2 eligió
la segunda, una ventana deslizante con anclaje, por dos razones que coinciden
con las discutidas en clase. Resumir exige una llamada adicional al modelo por
cada recorte, lo que suma costo y latencia, y además introduce una compresión
con pérdida, un resumen puede omitir justo el detalle que la tarea necesita más
adelante, y si se resume varias veces puede aparecer lo que la materia llama
summary drift, una deformación progresiva de lo que realmente ocurrió.
Recuperar información desde un almacenamiento externo es la estrategia más
cercana a una memoria de largo plazo genuina, pero exige infraestructura
adicional que el problema de M3 no requiere, porque el estado relevante de la
tarea entra completo en una ventana razonable de mensajes.

La ventana deslizante con anclaje que implementa el framework preserva en cada
llamada el último mensaje del usuario, un mensaje ancla con el objetivo original
de la tarea, y la coherencia estructural entre una invocación de herramienta y
su resultado. La decisión de anclar el objetivo al principio de la ventana, en
lugar de dejar que se pierda en un recorte simple, también encuentra respaldo en
el fenómeno de lost in the middle, que muestra que un modelo recupera mejor la
información ubicada al principio o al final del contexto que la que queda en el
medio, así que mantener el objetivo fijo en un extremo de la ventana no es
arbitrario. El experimento E1, en la sección 4, mide exactamente el costo de
esta estrategia frente a la alternativa de recortarla más agresivamente.

### Condiciones de parada y errores como observaciones

La materia enumera cinco condiciones de parada canónicas para un agent loop,
meta alcanzada, límite de iteraciones, presupuesto de costo, deadlock por
repetición, y cascada de errores de herramienta. El framework implementa las
primeras tres de forma directa, el cierre por texto sin tool calls, el tope de
`max_iterations`, y el seguimiento de tokens de entrada y salida en cada
`AgentResult`. La cuarta, deadlock por repetición, no está implementada como
condición de parada en el bucle base, y esa ausencia resultó ser precisamente el
modo de fallo dominante en los resultados de la sección 3, y el objeto del
experimento E5 en la sección 4. La quinta, tratar los errores de herramienta
como observación y no como un fallo fatal que interrumpe la ejecución, sí está
presente desde M1, y es la que permitió detectar y corregir el bug de despacho
descripto en la sección 1.

---

## 1. Aproximación

El problema que resuelve este milestone puede plantearse así. El framework de M1
y M2 se diseñó y se validó exclusivamente contra herramientas de propósito
general, una calculadora y un lector de archivos, sin ninguna noción de un
dominio particular. La pregunta que abre M3 es si ese mismo núcleo, sin
modificaciones, puede resolver un problema completamente distinto, una sala de
escape con un conjunto de herramientas ajeno, usando únicamente la superficie de
configuración que el framework ya exponía, tools, system prompt, presupuesto de
iteraciones y tamaño de ventana. El bucle del agente no se tocó en ningún
momento del proceso.

El mundo simulado y los escenarios son provistos por los profesores y se
consideran fijos. La sala de escape se resuelve con cuatro verbos genéricos,
`look`, `examine`, `take` y `use`, más un quinto verbo, `go`, que aparece solo en
los escenarios de varias salas. La conexión con el framework reutiliza el mismo
patrón de registro que ya existía desde M1.

```python
escenario = load_scenario(path)
mundo     = escenario.initial_world
agente    = build_agent(config)

for fn, schema in make_world_tools(mundo):
    agente.register_tool(fn, schema)

resultado      = agente.run(escenario.user_message)
logrado, razon = check_goal(mundo, escenario.goal)
```

Las herramientas del mundo llegan ya empaquetadas como pares de función y
esquema, exactamente la forma que `register_tool` esperaba desde el primer
milestone. No hizo falta adaptar nada del bucle para que hablara con este
dominio nuevo, la especialización ocurrió en tres decisiones de configuración.

* **Un system prompt específico del dominio.** El prompt por defecto del
  framework producía una conducta indeseada, el modelo describía la sala con un
  `look` y luego le preguntaba al usuario qué hacer. Como la condición de cierre
  del bucle es texto sin invocaciones de herramientas, esa pregunta terminaba la
  corrida de inmediato, con la puerta todavía cerrada. El prompt especializado
  fija el objetivo, describe el ciclo de observar, explorar, tomar y usar, y
  exige una acción por turno, siguiendo la estructura de secciones para un system
  prompt que se vio en clase, identidad, capacidades, restricciones, formato de
  salida y manejo de casos borde. Conviene anticipar acá un resultado que el
  experimento E2 documenta en detalle: esta especialización fue decisiva con
  llama3.1 e irrelevante con Nova Lite, donde el prompt genérico obtiene
  exactamente la misma tasa de éxito. La conducta de asistente conversacional que
  el prompt corregía era un defecto del modelo chico, no una carencia del
  framework.

* **Un presupuesto de iteraciones ajustado al tamaño del problema.** El valor por
  defecto del framework, diez iteraciones, resultaba insuficiente para escenarios
  cuya solución óptima ya requiere más de diez llamadas. Con ese límite, buena
  parte del desglose de errores habría medido el techo impuesto por la
  configuración en lugar del comportamiento real del modelo.

* **La desactivación de las herramientas propias de M1 y M2.** La calculadora y
  el lector de archivos no tienen ningún rol en una sala de escape, ofrecerlas
  solo agrega opciones de distracción y consume tokens en cada llamada sin
  aportar nada a la tarea.

Durante las primeras corridas contra un modelo real apareció un problema que
ningún test con el cliente simulado había detectado. El agente entraba en un
ciclo repitiendo `examine` sin avanzar. La causa no estaba en el modelo sino en
el manejo de errores del propio framework. El modelo invocaba `examine` con el
argumento `objeto` en lugar de `target`, el nombre real del parámetro, y el
despacho de herramientas devolvía la excepción cruda de Python, un mensaje que no
indicaba cuál era el nombre correcto. Esto contradice directamente el principio
de tratar los errores como observaciones útiles para que el agente corrija su
siguiente paso, que la materia distingue de un crash fatal, un error mal
formulado es tan inútil para el modelo como no tener error en absoluto. La
corrección validó los argumentos contra el esquema registrado antes de invocar la
función, devolviendo un mensaje que sugiere explícitamente el nombre correcto. El
efecto fue inmediato, en la misma corrida el modelo se equivocó dos veces de
nombre y se corrigió las dos, resolviendo el escenario en ocho pasos donde antes
fallaba después de catorce.

El punto que vale la pena subrayar no es la corrección en sí, sino que
doscientos diez tests con el cliente simulado habían pasado, antes y después, sin
detectar el problema, porque ese cliente nunca se equivoca de nombre de
argumento. Solo un modelo real produce ese tipo de error, y por eso una
evaluación de agentes que se apoya únicamente en mocks tiene un punto ciego
estructural.

---

## 2. Evals

La materia propone descomponer la evaluación de un agente en un conjunto de
preguntas sucesivas, qué significa que funcione, dónde se observa esa calidad,
cómo se convierte lo observado en un número, quién emite el juicio, y sobre qué
casos se mide. Esta sección sigue esa misma estructura, porque separar esas
preguntas es lo que evita confundir instrumentos que miden cosas distintas.

### 2.1. Dimensiones de calidad

| Dimensión de calidad | Qué mide |
| :---- | :---- |
| Correctitud | ¿Llegó a la meta? Estado del mundo, no texto del agente. |
| Eficiencia | ¿Cuántas llamadas usó contra el óptimo conocido? |
| Coherencia del plan | ¿Las acciones se relacionan con el objetivo? |
| Recuperación ante errores | ¿Corrige después de un error, o repite? |
| Eficiencia de la exploración | ¿Cada acción aporta información nueva, o repite lo ya hecho? |

Las dos primeras son propiedades del resultado y del costo. Las tres últimas son
propiedades de la conducta, y sólo tienen sentido mirando el camino completo, no
el desenlace.

Correctitud se calcula con `check_goal`, que inspecciona el estado interno del
mundo, por ejemplo si la puerta principal quedó abierta, y no el texto que el
agente produce. En varias corridas el agente afirmó haber abierto la puerta
cuando el estado del mundo indicaba lo contrario. Medir sobre el estado del mundo
es la aplicación directa de la regla de diseño vista en clase, llevar todo lo que
se pueda hacia verificación determinística y reservar el juicio de un modelo para
lo que realmente requiere interpretación.

Eficiencia es el cociente entre el número óptimo de llamadas del escenario y las
que efectivamente usó el agente, acotado a uno y calculado sólo sobre corridas
exitosas, para no premiar el abandono temprano de una corrida fallida como si
fuera eficiencia.

### 2.2. Dónde se observa cada dimensión

| Dimensión de calidad | Dónde se observa |
| :---- | :---- |
| Correctitud | Output. Estado final del mundo (`check_goal`). |
| Eficiencia | Trace. Cuenta de pasos de la traza completa. |
| Coherencia, recuperación, exploración | Trace. Requieren ver la secuencia de acciones, no solo el resultado. |

Correctitud se lee del estado final, sin necesidad de la traza completa. Las
otras cuatro exigen ver la secuencia de acciones paso a paso.

### 2.3. Quién juzga cada dimensión

| Dimensión de calidad | Judge | Por qué |
| :---- | :---- | :---- |
| Correctitud | Código (`check_goal`) | Verificación objetiva y determinística. Abrir o no una puerta no requiere interpretación. |
| Eficiencia | Código (cálculo aritmético) | Óptimo dividido llamadas usadas. Tampoco requiere interpretación. |
| Coherencia, recuperación, exploración | LLM judge | Requieren juicio sobre la conducta, no una verificación exacta. |

El LLM judge puntúa de forma pointwise, recibe una única traza y la puntúa contra
la rúbrica, sin compararla con otra traza (no se usó pairwise, queda anotado en
la sección 5). Recibe un resumen compacto, con el escenario, si la meta fue
alcanzada, óptimo contra llamadas usadas, y la secuencia de acciones con su
desenlace, acotada a cuarenta pasos. Su system prompt, tal como aparece en el
código:

> *"Sos un evaluador de agentes autónomos. Recibís la traza de un agente que
> intentó resolver una sala de escape y la puntuás con la rúbrica indicada. Sé
> estricto y objetivo, puntuás la conducta observable, no el resultado. Un agente
> puede fallar y aun así haber explorado con criterio, y puede acertar habiendo
> dado muchas vueltas."*

Conviene señalar una tensión que la propia implementación introduce, el resumen
que recibe el juez incluye si la meta fue alcanzada antes de que puntúe, lo que
abre la puerta a que el juicio quede correlacionado con el desenlace aunque se le
pida lo contrario. En la campaña con llama3.1 se observó ese efecto (sección 5).

La salida se obtiene mediante `structured_call`, la tool sintética
`final_result` de M2, en vez de pedir prosa y parsear con regex. Es la evidencia
más clara de que el mecanismo de M2 funciona sobre un problema real.

La rúbrica usa escala ordinal de uno a cinco para las tres dimensiones de
conducta, no binaria. La materia recomienda binario por defecto y reserva las
escalas ordinales para cuando existe una gradación legítima, con cada nivel
definido, el caso de coherencia y exploración.

| Dimensión de calidad | Ancla en 1 | Ancla en 5 |
| :---- | :---- | :---- |
| **Coherencia del plan** | Las acciones no guardan relación con el objetivo. | El plan es claro y progresa hacia la meta. |
| **Recuperación ante errores** | El agente repite la acción que falló sin cambiar nada. | El agente lee el error y corrige su siguiente acción. |
| **Eficiencia de la exploración** | El agente repite acciones que ya había hecho. | Cada acción nueva aporta información distinta. |

### 2.4. Modos de fallo

Cuando correctitud falla (la corrida no llegó a la meta), conviene saber por qué.
Eso es error analysis, y acá está automatizado con una taxonomía de código sobre
la traza, en vez del proceso manual de observar cada traza, describirla en una
oración, y agrupar. La automatización gana escala sobre cientos de corridas, pero
pierde la posibilidad de encontrar un modo de fallo que ninguna regla anticipó.

Los modos, en orden de prioridad para el caso de una corrida que exhiba varios a
la vez:

* **Llamada escrita como texto.** El modelo redacta la invocación como texto
  plano en vez de emitirla por tool calling, el bucle la lee como respuesta final
  y cierra.
* **Orden incorrecto.** La meta exige una secuencia de sub-objetivos y no se
  respetó.
* **Desborde de contexto.** Algún prompt se acercó al techo de la ventana.
* **Bucle.** Una fracción relevante de las llamadas repite una combinación ya
  ejecutada. Este modo es, específicamente, el fracaso de la dimensión de
  eficiencia de la exploración, y en el vocabulario de la materia, la ausencia de
  una condición de parada por deadlock.
* **Acción inválida.** La herramienta corrió sin excepción pero el mundo la
  rechazó.
* **Argumentos inválidos.** JSON mal formado o nombres de parámetro que no
  coinciden con el esquema.
* **Herramienta inexistente.** Nombre no registrado.
* **Límite de iteraciones.** Se agotó el tope configurado.
* **Parada prematura.** Cerró con texto sin cumplir la meta, sin que ninguna
  categoría anterior lo explique.

Una corrida exitosa no recibe ninguna categoría, aunque haya cometido errores en
el camino, si se recuperó y llegó a la meta, esos errores no cuentan como fallo.

### 2.5. Meta evaluación del juez (faltante)

La materia insiste en que un juez basado en un modelo no debería aceptarse por
default, hay que calibrarlo contra un golden set etiquetado por humanos y medir
el acuerdo con una métrica corregida por azar, como el coeficiente Kappa, antes
de confiar en sus veredictos. Ese paso no se hizo en este proyecto, no existe un
conjunto de trazas con etiquetas humanas contra el cual se haya medido el acuerdo
del juez. Es una limitación real, reconocida en la sección 5, y significa que las
dimensiones de calidad reportadas más abajo deben leerse como señal comparativa
entre condiciones, nunca como una medición calibrada.

---

## 3. Resultados

### 3.1. Por qué se mide con repeticiones y no con una corrida

El sistema es estocástico, el mismo agente, con exactamente la misma
configuración, puede resolver o no resolver el mismo escenario en dos intentos
distintos. Una única corrida es, en términos de la materia, una observación, no
una medición, y reportar el resultado de esa única extracción como si fuera el
desempeño del agente es exactamente la generalización apresurada que se advirtió
en la parte teórica del curso.

La materia distingue además dos preguntas distintas que pueden hacerse sobre un
mismo conjunto de repeticiones. Pass@k pregunta si el agente es capaz de resolver
el problema alguna vez entre k intentos, y tiene sentido cuando el usuario puede
reintentar o elegir entre varias propuestas. Pass^k pregunta si el agente
resuelve el problema de manera consistente en todos los intentos, y es la
pregunta relevante para un agente autónomo que actúa sin supervisión humana en el
momento, exactamente el caso de este problema, nadie corrige al agente mientras
intenta escapar de la sala. Por eso lo que reporta este informe no es si el
agente logró resolver cada escenario alguna vez, sino con qué tasa lo resuelve de
forma consistente.

A esto se suma una segunda razón, propia de la estructura del problema. Cada
escenario es una sala de escape distinta, sin estado compartido ni dependencia
con los demás, son eventos independientes entre sí. Exigir que las cinco tareas
obligatorias se resuelvan dentro de una única secuencia conjunta no aportaría
información adicional sobre la capacidad del agente, mezclaría cinco mediciones
independientes en una sola sin ninguna justificación. Por eso este informe
reporta la tasa de éxito de cada escenario por separado, sobre un número fijo de
repeticiones independientes.

### 3.2. Metodología de medición

| Parámetro | Valor |
| :---- | :---- |
| **Modelo evaluado** | `amazon.nova-lite-v1:0` sobre Amazon Bedrock |
| **Configuración** | Idéntica para los ocho escenarios, mismo prompt de dominio, misma ventana de historial, mismo presupuesto de iteraciones |
| **Repeticiones por escenario** | 30 corridas en los cinco escenarios hasta hard, 10 en los tres extreme |
| **Corridas totales de la campaña** | 180 sobre los ocho escenarios del dataset |
| **Corridas descartadas por fallo de infraestructura** | 0 |

Las corridas descartadas se cuentan aparte y se excluyen de todos los agregados.
Una corrida que se interrumpe por una falla del proveedor tiene sus pasos, tokens
y latencia truncados en un punto arbitrario, así que promediarla junto al resto
ensuciaría cada métrica. Que el contador sea visible obliga a mirar cuántas se
perdieron en lugar de que desaparezcan en silencio.

### 3.3. Tasa de éxito por escenario

| Escenario | Dificultad | Éxito | Intervalo de confianza aproximado (%) |
| :---- | :---- | :---- | :---- |
| **study with key** | easy | 29 de 30 (97 %) | 83 a 100 |
| **color locks** | medium | 20 de 30 (67 %) | 47 a 83 |
| **apartment keys** | medium | 24 de 30 (80 %) | 61 a 92 |
| **library search** | hard | 21 de 30 (70 %) | 51 a 85 |
| **office sequence** | hard | 24 de 30 (80 %) | 61 a 92 |
| **extreme archive** | extreme | 9 de 10 (90 %) | 60 a 99 |
| **backtracking vault** | extreme | 2 de 10 (20 %) | 4 a 52 |
| **vault combination** | extreme | 1 de 10 (10 %) | 1 a 40 |
| **Total, 180 corridas** | | **130 de 180 (72 %)** | **66 a 79** |

![Tasa de éxito por escenario](figuras/exito-por-escenario.svg)

Agrupando por dificultad declarada: easy 97 %, medium 73 %, hard 75 %, extreme 40 %. Los cinco escenarios obligatorios hasta hard suman 118 de 150 (78,7 %, intervalo de 72 a 85); los tres extreme, que la consigna reserva para la competencia, bajan el promedio general a 72 %.

Las 150 corridas provienen de tres mediciones independientes de 50, realizadas en
momentos distintos de la campaña con configuración idéntica. Sus tasas globales
fueron 80 %, 80 % y 76 %, lo que da una idea directa de la varianza del sistema:
la misma configuración, medida tres veces con cincuenta repeticiones cada una,
oscila cuatro puntos.

Ningún escenario alcanza el 100 %, es decir, medido como pass^k ningún
escenario es perfectamente confiable. El ordenamiento general acompaña la
dificultad declarada, con una excepción que vale la pena analizar aparte.

**El caso de extreme archive.** Este escenario esconde una llave entre veinte
expedientes con prosa burocrática y está descripto en la consigna como diseñado para no caber en la ventana de contexto de los modelos chicos. Con
Nova Lite se resuelve el 90 % de las veces, por encima de cuatro de los cinco
escenarios obligatorios. La instrumentación explica por qué: los picos de
tokens de entrada de esas corridas van de 15.304 a 16.468, justo alrededor de
los 16.384 que el proveedor local imponía como techo de ventana y que Bedrock
no impone. La dificultad de ese escenario no era una propiedad de la tarea
sino del modelo con el que se lo corriera, y es la confirmación más literal de
la tesis de la sección 3.4.

Los dos escenarios extreme que sí resisten son los de horizonte largo y varias
salas, vault combination con 10 % y backtracking vault con 20 %. Ambos exigen
combinar objetos hallados en salas distintas y volver sobre los pasos, y ambos
fallan exclusivamente por bucle, agotando el presupuesto de cien iteraciones con 98 y 86 pasos medios respectivamente.

### 3.4. El modelo domina sobre las decisiones de framework

Además de la campaña Nova Lite de la sección anterior, se corrió antes una
campaña independiente con la misma configuración del agente sobre llama3.1 de 8B
de parámetros ejecutado en local con Ollama. Comparando ambas campañas, el cambio
de modelo, por sí solo, movió la tasa de éxito global de 25 % a 78,7 %, sin
modificar una sola línea del framework. Es un efecto mayor que el de cualquiera
de los seis experimentos de la sección siguiente, incluso sumados.

| Modo de fallo | llama3.1 8B | Nova Lite |
| :---- | :---- | :---- |
| **Bucle, repite acciones ya ejecutadas** | 46 % de los fracasos | 100 % |
| **Llamada escrita como texto** | 33 % | 0 % |
| **Otros modos combinados** | 21 % | 0 % |

Con Nova Lite desaparecen por completo los modos de fallo asociados a una
disciplina débil de tool calling, y el único modo que persiste es el bucle, la
ausencia de una condición de parada por deadlock que la materia lista entre las
cinco canónicas.

El cambio de modelo no solo mueve el número agregado, cambia qué conclusiones se
obtienen de los experimentos. Los experimentos E1 y E2 se corrieron completos
sobre ambas campañas y arrojan resultados distintos en cada una, en un caso
opuestos. Esa es la advertencia metodológica más importante de este trabajo, y se
desarrolla en la sección 4: **las conclusiones de un experimento de ablación
sobre un agente no transfieren automáticamente entre modelos.**

### 3.5. Eficiencia

La tasa de éxito responde si el agente llega. La eficiencia responde a qué costo.

| Escenario | Óptimo | Pasos medios (éxitos) | Eficiencia | Tokens de entrada | Latencia mediana |
| :---- | ----: | ----: | ----: | ----: | ----: |
| **study with key** | 3 | 4,7 | 0,67 | 22.701 | 4,4 s |
| **color locks** | 11 | 23,6 | 0,49 | 192.023 | 24,1 s |
| **apartment keys** | 7 | 14,5 | 0,50 | 114.190 | 12,8 s |
| **library search** | 7 | 17,0 | 0,42 | 276.068 | 15,4 s |
| **office sequence** | 13 | 77,2 | **0,27** | 318.242 | 87,9 s |
| **extreme archive** | 4 | 31,5 | **0,17** | — | — |
| **backtracking vault** | 18 | 85,6 | 0,64 | — | — |
| **vault combination** | 21 | 97,8 | 0,78 | — | — |
| **Global, cinco obligatorios** | | | **0,48** | | |

![Eficiencia por escenario](figuras/eficiencia-por-escenario.svg)

La eficiencia decrece de forma monótona con la dificultad declarada del
escenario, y el caso extremo es office sequence: figura entre los mejores por
tasa de éxito (80 %) y es con diferencia el peor por eficiencia, resuelve usando
casi seis veces el camino óptimo, con una latencia mediana de 88 segundos frente
a los 4 segundos del escenario más simple.

Ese contraste es la justificación empírica de haber definido dos métricas
cuantitativas en lugar de una. Medido solo por correctitud, office sequence y
apartment keys son indistinguibles, ambos al 80 %. Medido también por eficiencia,
uno resuelve cerca del camino ideal y el otro da vueltas hasta casi agotar el
presupuesto.

Extreme archive vuelve a ser el caso instructivo, ahora por el otro extremo:
es el escenario con mejor tasa de éxito después del más simple, y a la vez el
de peor eficiencia de las ocho, 0,17. Su solución óptima son cuatro llamadas y
el agente usa treinta y uno. Resuelve examinando expedientes por fuerza bruta
hasta dar con el correcto, no razonando sobre cuál examinar. Medido solo por
correctitud parecería uno de los escenarios mejor resueltos del conjunto;
medido también por eficiencia queda claro que llega sin haber entendido el
problema.

Las eficiencias altas de vault combination y backtracking vault, 0,78 y 0,64,
se calculan sobre una y dos corridas exitosas respectivamente, así que no
admiten lectura, se reportan por completitud.

La latencia se reporta por mediana y no por media. Durante la campaña una corrida
quedó registrada en 6.207 segundos, frente a una mediana de 12, porque la máquina
estuvo inactiva mientras la evaluación corría desatendida. Esa única observación
multiplicaba por treinta la media de su condición sin que nada en el resultado lo
delatara.

### 3.6. Dimensiones de conducta según el juez

Las tres dimensiones de conducta definidas en la sección 2.1 se midieron sobre
las cincuenta corridas del baseline de la campaña Nova Lite. Las cincuenta
produjeron un veredicto válido, sin un solo fallo de formato, lo que constituye
además la evidencia más directa de que el mecanismo de salida estructurada de M2,
la tool sintética `final_result` con validación y reparación, funciona de forma
confiable sobre un problema real.

| Grupo | Coherencia del plan | Recuperación ante errores | Eficiencia de la exploración | n |
| :---- | ----: | ----: | ----: | ----: |
| Todas las corridas | 3,40 | 3,38 | 3,30 | 50 |
| Corridas que lograron la meta | 3,75 | 3,80 | 3,52 | 40 |
| Corridas que fallaron | 2,00 | 1,70 | 2,40 | 10 |

El juez discrimina con claridad entre corridas exitosas y fallidas en las tres
dimensiones, y la separación es más pronunciada en recuperación ante errores, de
3,80 a 1,70. Eso es coherente con el modo de fallo dominante que reporta la
sección 3.4: una corrida que entra en bucle es, por definición, una corrida que
no se recupera.

![Rúbrica del juez por condición](figuras/juez-por-condicion.svg)

Las corridas exitosas obtienen 3,52 en eficiencia de la exploración, la nota más
baja de las tres dimensiones dentro de ese grupo. El agente llega a la meta pero
explorando con redundancia, exactamente lo que la sección 3.5 muestra en términos
cuantitativos con una eficiencia global de 0,48.

---

## 4. Experimentos

Las hipótesis de cada experimento se redactaron y se dejaron registradas antes de
ejecutar las corridas correspondientes, cada una en un commit anterior al de sus
resultados. Cada comparación siguió el protocolo de comparación apareada que
describe la materia, mismos casos, misma cantidad de corridas por condición,
mismo entorno, cambiando una única variable por experimento.

Cuando un experimento se corrió sobre las dos campañas, se reportan las dos, y la
discrepancia entre ambas es en varios casos el resultado más informativo.

### E1. Presupuesto de memoria conversacional

Se varió únicamente el tamaño de la ventana deslizante, de 50 a 8 y luego a 4
mensajes. La hipótesis previa era que una ventana más chica produciría más
repeticiones, porque el agente perdería de vista lo que ya había intentado.

**Campaña llama3.1** (16 corridas por condición). El resultado fue el opuesto al
esperado: la tasa de éxito cae a cero por debajo de 8 mensajes, pero la fracción
de llamadas repetidas también baja a medida que la ventana se achica. La
explicación aparece al mirar el número de pasos que llega a dar cada corrida: con
la ventana chica el agente no acumula suficientes turnos como para caer en un
bucle, simplemente colapsa antes, emitiendo la llamada como texto en lugar de
invocarla.

**Campaña Nova Lite** (50 corridas por condición).

| Ventana | Éxito | Llamadas repetidas | Pasos medios | Tokens de entrada |
| :---- | ----: | ----: | ----: | ----: |
| 50 mensajes | 35/50 (70 %) | 48 % | 50,5 | 218.744 |
| 8 mensajes | 29/50 (58 %) | 58 % | 60,5 | 120.376 |
| 4 mensajes | 17/50 (34 %) | 77 % | 78,4 | 138.797 |

![E1, efecto del tamaño de la ventana](figuras/e1-memoria.svg)

Acá la hipótesis original **se confirma**: recortar la ventana aumenta la
repetición de forma monótona, de 48 % a 77 %, y el agente en lugar de colapsar
antes da más pasos, no menos. Las notas del juez acompañan la degradación en las
tres dimensiones de conducta.

| Ventana | Coherencia del plan | Recuperación ante errores | Eficiencia de la exploración |
| :---- | ----: | ----: | ----: |
| 50 mensajes | 3,16 | 3,20 | 3,12 |
| 8 mensajes | 2,88 | 2,78 | 2,88 |
| 4 mensajes | 1,96 | 1,76 | 1,86 |

El mismo experimento, sobre el mismo código, produce mecanismos opuestos según el
modelo: con un modelo débil, quitarle memoria lo hace colapsar; con un modelo
capaz, lo hace repetirse. La conclusión compartida por ambas campañas es que
recortar la ventana de más no produce una degradación gradual, y esa es la
evidencia empírica del costo de la estrategia elegida en la sección 0.

### E2. Prompt genérico contra prompt especializado

Se varió únicamente el system prompt.

**Campaña llama3.1** (16 corridas por condición). El prompt especializado resultó
ser la diferencia entre resolver una fracción de las tareas y no resolver
ninguna, 25 % contra 0 %, y además redujo a la mitad la proporción de llamadas
repetidas.

**Campaña Nova Lite** (50 corridas por condición).

| Condición | Éxito | Llamadas repetidas | Pasos medios |
| :---- | ----: | ----: | ----: |
| Prompt especializado | 35/50 (70 %) | 50 % | 51,6 |
| Prompt genérico | 35/50 (70 %) | 48 % | 50,4 |

**El efecto desaparece por completo.** Idéntica tasa de éxito, idéntica fracción
de repeticiones, idéntico número de pasos. La conducta de asistente conversacional
que el prompt especializado venía a corregir, el modelo que describe la sala y le
pregunta al usuario qué hacer, sencillamente no aparece con Nova Lite ni siquiera
bajo el prompt genérico.

El efecto nulo no se limita a la correctitud. Las cien corridas de este
experimento fueron puntuadas por el juez, y las tres dimensiones de conducta
también resultan indistinguibles entre condiciones.

| Condición | Coherencia del plan | Recuperación ante errores | Eficiencia de la exploración |
| :---- | ----: | ----: | ----: |
| Prompt genérico | 3,20 | 3,22 | 3,10 |
| Prompt especializado | 3,16 | 3,06 | 2,98 |

Restringiendo la comparación a las corridas exitosas, para separar la calidad de
la conducta del desenlace, la coincidencia se mantiene: 3,71, 3,80 y 3,54 con el
prompt genérico contra 3,74, 3,71 y 3,46 con el especializado, sobre 35 corridas
exitosas en cada condición. Es decir que el prompt especializado no mejora ni el
resultado ni el camino: con un modelo de esta capacidad, la especialización del
prompt no aporta nada por sobre el prompt por defecto del framework.

Junto con E1, este es el segundo experimento que muestra que una intervención de
framework con efecto grande y bien medido sobre un modelo puede tener efecto nulo
sobre otro.

### E3. Memoria episódica de acciones ejecutadas

Se implementó un registro deduplicado de cada combinación de herramienta y
argumentos junto con su desenlace, inyectado en el system prompt para no consumir
presupuesto de la ventana deslizante. En el vocabulario de la materia, este
registro funciona como memoria procedural, información sobre qué ya se intentó,
colocada fuera del presupuesto de la memoria de trabajo. La hipótesis era que
hacer explícito ese registro reduciría el bucle.

Con 25 corridas por rama sobre la campaña Nova Lite, la tasa de éxito fue idéntica
entre tener y no tener el mecanismo, 18 de 25 en ambos casos, con un 52 % más de
tokens de entrada en la condición con memoria de acciones, 136.515 contra 89.595.

El modelo ya contaba con esa información dentro de su ventana habitual y no la
estaba usando para evitar la repetición, lo que sugiere que la causa del bucle no
es la disponibilidad del dato sino una limitación de razonamiento sobre un dato
que el modelo ya tenía disponible.

### E4. Presupuesto de iteraciones

Se comparó un presupuesto de 25, 50 y 100 iteraciones sobre los dos escenarios
más exigentes, con 8 corridas por celda, observándose una mejora monótona a
medida que crecía el presupuesto, de 38 % a 56 % y a 81 %. Al repetir la medición
sobre el conjunto completo de escenarios con más repeticiones, esa mejora no se
sostuvo: los fracasos se redistribuyeron entre escenarios sin cambiar la tasa
global.

Con un número tan bajo de repeticiones por celda, una tendencia que parece clara
puede ser ruido reordenado, y este experimento sirve como advertencia
metodológica sobre el riesgo de sacar conclusiones de pocas corridas, el mismo
riesgo que la materia señala cuando insiste en que el intervalo de confianza tiene
que estar por encima del ruido antes de aceptar una diferencia como real.

### E5. Bloqueo de repeticiones estériles

Dado que el bucle es, con Nova Lite, el único modo de fallo observado, se probó
agregar directamente la condición de parada por deadlock que el framework no
tenía: impedir la tercera ejecución idéntica de una misma combinación de
herramienta y argumentos, permitiendo dos ejecuciones porque recién en la segunda
queda comprobado empíricamente que el resultado no cambia. La marca de esterilidad
se levanta sola si el resultado vuelve a cambiar, lo que evita romper la
navegación entre salas, donde un mismo `look` devuelve descripciones distintas
según dónde esté el agente.

Con 50 corridas por rama, el mecanismo se activó 550 veces y el resultado fue una
caída de la tasa de éxito, de 80 % a 70 %, en lugar de una mejora.

La conclusión es más informativa que el número: el agente no falla porque repite,
repite porque se quedó sin alternativas razonables que probar, y bloquearle el
camino que ya conocía no le genera un camino nuevo, simplemente lo empuja a
ciclar entre otras acciones igual de estériles. Es un resultado que matiza la
recomendación general de la materia: agregar una condición de parada por deadlock
es una buena práctica de seguridad, evita que una corrida se cuelgue
indefinidamente, pero no es, por sí sola, una intervención que mejore la tasa de
éxito.

### E6. Planificador explícito de sub-objetivos

Los cinco experimentos anteriores comparten una característica: todos ajustan un
parámetro del mismo bucle reactivo. E5 sugirió por qué ninguno alcanzaba, el
agente se queda sin ideas, y ningún parámetro le da ideas. E6 es el único
experimento arquitectónico del conjunto.

Antes de tocar el mundo, el agente escribe un plan de sub-objetivos usando
`structured_call`, con un schema Pydantic que garantiza una lista de pasos
utilizable. Ese plan se mantiene en el system prompt durante toda la corrida, de
modo que permanece visible aun cuando la ventana deslizante ya recortó el
historial, que es precisamente el momento en que aparecen los bucles. Si la
planificación falla, el agente continúa sin plan, porque un agente sin plan es el
comportamiento base, que resuelve cerca del 80 % de las corridas.

Este camino es el que el enunciado sugiere para office sequence, cuya meta es
compuesta y ordenada, y corresponde al experimento de planner explícito contra
ReAct puro.

Con 50 corridas por rama, el resultado fue 39 de 50 con planificador contra 38 de
50 sin él, una diferencia de dos puntos porcentuales que queda muy por dentro del
margen de error.

La refutación registrada de antemano se cumplió: el problema no es la falta de un
plan sino la incapacidad del modelo para ejecutarlo. Dárselo explícito, en un
formato validado y sostenido fuera del presupuesto de la ventana, no cambió su
conducta.

### Lectura conjunta de los seis experimentos

| Intervención | Efecto sobre la tasa de éxito |
| :---- | :---- |
| **Reemplazar llama3.1 por Nova Lite** | **25 % → 78,7 %** |
| E1, recortar la ventana de contexto | Negativo y monótono en ambas campañas |
| E2, prompt especializado | Decisivo con llama3.1, nulo con Nova Lite |
| E3, memoria episódica de acciones | Nulo, con 52 % más de tokens |
| E4, ampliar el presupuesto de iteraciones | Nulo sobre el conjunto completo |
| E5, bloquear repeticiones estériles | Negativo, de 80 % a 70 % |
| E6, planificador explícito | Nulo, dos puntos dentro del error |

Las decisiones de M2 sí importan, una ventana demasiado chica hunde al agente por
completo en las dos campañas. Pero una vez que la configuración se encuentra en un
régimen razonable, seguir ajustando el framework no movió el resultado de forma
apreciable, y la intervención que sí produjo un cambio grande y consistente fue
reemplazar el modelo subyacente.

Conviene además señalar lo que E1 y E2 muestran en conjunto, porque es una
conclusión que ninguno de los dos permite por separado: **el efecto de una
intervención de framework depende del modelo sobre el que se mide, al punto de
poder invertirse.** Un informe que hubiera evaluado únicamente con llama3.1 habría
concluido que el prompt especializado es una pieza crítica del sistema y que
quitarle memoria al agente reduce sus repeticiones. Las dos conclusiones son
falsas con el modelo que exige la consigna.

---

## 5. Limitaciones y próximos pasos

* Ningún escenario alcanza el 100 % sobre las repeticiones medidas, es decir,
  medido como pass^k, ningún escenario es todavía perfectamente confiable. La
  causa dominante identificada, el bucle, no es un defecto del framework sino una
  limitación de razonamiento del modelo sobre información que ya tiene disponible,
  y así lo sugieren de forma convergente E3, que le dio el dato de manera
  explícita, E5, que le impidió repetirlo, y E6, que le dio un plan. Ninguna de
  las tres intervenciones cambió el resultado.

* El juez no fue calibrado. No existe un golden set de trazas etiquetadas por
  humanos contra el cual se haya medido el acuerdo del juez con un coeficiente
  corregido por azar, como recomienda la materia. Sus dimensiones de calidad deben
  leerse como señal comparativa entre condiciones, no como una medición absoluta.

* El juez comparte modelo con el agente evaluado en ambas campañas, lo que
  mantiene el riesgo de self preference que la materia señala. En la campaña con
  llama3.1 se observó además una inversión llamativa, la condición que resolvía
  menos tareas recibía en promedio mejores notas, porque la rúbrica puntúa calidad
  de conducta y ninguna de sus tres dimensiones premia explícitamente el avance
  hacia el objetivo. Esa inversión **no se reproduce con Nova Lite**, donde las
  notas caen de forma monótona junto con la tasa de éxito. La explicación es que
  la rúbrica resulta sensible al modo de fallo del modelo, no solo a la calidad de
  la conducta: con llama3.1 las corridas fallidas eran cortas y exhibían poca mala
  conducta observable, mientras que con Nova Lite son largas y cicladas, y el
  bucle es precisamente lo que la dimensión de exploración penaliza. No se
  corrigió la rúbrica después de ver los resultados, para no ajustar la métrica a
  la conclusión ya obtenida.

* Las comparaciones entre condiciones se hicieron todas de forma pointwise, contra
  la tasa de éxito determinística. No se usó evaluación pairwise con el juez para
  decidir directamente cuál de dos versiones del agente exhibe mejor conducta, una
  herramienta adicional que la materia recomienda específicamente para comparar
  versiones.

* El modelo no se aisló por completo como variable. Se compararon dos modelos de
  familias y capacidades muy distintas, llama3.1 de 8B en local contra Nova Lite
  sobre Bedrock, pero no se probó un modelo de mayor capacidad dentro de la misma
  familia, lo que permitiría separar con más precisión qué parte del techo
  observado corresponde al framework y qué parte al modelo. Dado el peso que el
  modelo demostró tener en los resultados, esta es probablemente la limitación más
  importante del trabajo.

* La varianza del sistema es alta y quedó documentada de forma directa: la misma
  configuración, medida tres veces con cincuenta repeticiones cada una, arrojó
  80 %, 80 % y 76 %. Con menos repeticiones por celda las diferencias son
  fácilmente confundibles con ruido, y E4 es el caso testigo de ese riesgo dentro
  de este mismo informe.

* Como próximos pasos, los dos más prometedores son la calibración del juez contra
  un golden set humano, que es requisito para poder confiar en las dimensiones de
  conducta como medición y no solo como señal comparativa, y la evaluación sobre
  un tercer modelo de capacidad intermedia, que permitiría estimar dónde está el
  techo del framework con independencia del modelo.

---

## Reproducibilidad

Toda la evaluación se regenera sin pasos manuales:

```bash
# Proveedor (o un .env con las mismas claves)
export BEDROCK_MODEL_ID="amazon.nova-lite-v1:0" AWS_REGION="us-east-2"

python eval/run.py --juez                       # baseline sobre los escenarios
python eval/run.py --experimento e1-memoria     # y análogo para e2 … e6
```

Las figuras de este informe se regeneran con `python eval/figuras.py`, que las
construye en SVG desde los resúmenes versionados sin ninguna dependencia de
graficación y sin llamar al modelo: reproducirlas no requiere credenciales ni
proveedor.

Las trazas crudas de cada corrida quedan en `eval/results/`, y los resúmenes
agregados de cada campaña están versionados en el repositorio
(`eval/results/*/summary.json` e `informe.md`). La infraestructura de evaluación
está cubierta por sus propios tests (`tests/test_eval.py`), porque la taxonomía de
modos de fallo y las métricas son las que sostienen todas las afirmaciones de las
secciones 3 y 4: si clasificaran mal, el análisis entero quedaría viciado.
