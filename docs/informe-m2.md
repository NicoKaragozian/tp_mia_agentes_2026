# Informe M2 — Memoria, prompting y robustez

M2 mantiene la fachada de M1 (`build_agent`, `register_tool`, `run`) y agrega,
adentro del agente: estado conversacional con gestión de contexto (Sliding
Window), salida estructurada con reparación (`structured_call` + `final_result`),
reintentos ante fallos transitorios, errores accionables en las herramientas y
conteo de tokens. Este informe cubre las cuatro secciones pedidas.

---

## 1. Estrategia de memoria

### 1.1. Historial vs. ventana (la separación central)

En M1 la lista `messages` se armaba y se tiraba dentro de cada `run`. En M2 la
partimos en dos piezas con responsabilidades distintas:

- **`self._history` (el store):** la conversación completa, persistente entre
  llamadas a `run`/`structured_call` sobre la misma instancia. Solo crece; acá
  no se pierde nada.
- **`_ventana()` (la política de lectura):** la vista que se envía al LLM en
  cada `chat(...)`. Se recalcula en cada llamada y **nunca** supera
  `max_history_messages`, sin importar cuántos turnos tenga la conversación.

El tope rige para *toda* llamada al cliente LLM: las del bucle de `run` y las
de `structured_call` (que le pasa a `_ventana` su lista de trabajo local).

### 1.2. Qué conserva la ventana y por qué (Sliding Window)

Si el historial entra completo, va completo. Si no, el recorte decide con
estas prioridades:

1. **Recencia (invariante del enunciado):** el último mensaje del usuario
   entra siempre. Si el presupuesto es tan chico que la cola reciente ya no lo
   incluye (p. ej. un turno con muchas tools), el último user pasa a encabezar
   la ventana desplazando al ancla.
2. **Ancla:** se conserva el primer mensaje del usuario — el "goal" de la
   conversación — para que el objetivo no se olvide aunque el medio se
   descarte (recorte visto en clase: `preserve_first_user`).
3. **Cola reciente:** el resto del presupuesto se llena con los últimos
   `N-1` mensajes.
4. **Coherencia estructural:** un mensaje `role:"tool"` sin el turno assistant
   que emitió su `tool_call` es un huérfano. Si el corte deja huérfanos al
   inicio de la cola, se descartan: quedar **por debajo** del tope es válido;
   superarlo o mandar pares `<tool_call, tool_response>` rotos, no. (Además de
   confundir al modelo, un `toolResult` sin su `toolUse` rompe el formato de
   la API Converse de Bedrock.)

Dos decisiones complementarias:

- **El system prompt y los esquemas de tools no gastan presupuesto:** viajan
  por los parámetros `system=` y `tools=` de `chat(...)`, fuera de la lista
  `messages`. Son estables turno a turno; recortarlos sería perder
  comportamiento, no memoria.
- **Qué se descarta:** el medio de la conversación (los turnos entre el ancla
  y la cola). Es el tramo con menor probabilidad de ser referido por el turno
  actual; lo reciente sostiene la continuidad y el ancla sostiene el objetivo.

### 1.3. Problemas que encontramos

- **Pares tool_call/tool_response partidos.** El recorte ingenuo "últimos N"
  deja resultados de tool huérfanos al inicio de la ventana. Lo resolvimos
  limpiando huérfanos después del corte, y lo cubrimos con un test que revisa
  *todas* las llamadas de un escenario con tools (`_sin_tools_huerfanas`).
- **La recencia se pierde dentro de un run con tools.** Con presupuesto chico,
  los mensajes assistant/tool de la iteración actual pueden empujar afuera al
  propio mensaje del usuario que originó el turno. Por eso la invariante de
  recencia se fuerza explícitamente (el último user se "pinnea").
- **Orden de las operaciones al pinnear.** Primera versión del pinneo:
  prepender el último user y *después* limpiar huérfanos — el user quedaba
  tapando a los huérfanos y la limpieza no los veía. Quedó al revés (limpiar,
  después prepender) y con test de regresión.
- **Presupuestos extremos degradan la observabilidad.** Con
  `max_history_messages` menor que un grupo `assistant + tool_responses`, la
  ventana puede quedar reducida al último mensaje del usuario (sin los
  resultados de tools). El agente no se rompe y respeta el tope, pero el
  modelo puede repetir trabajo; lo documentamos como límite en la sección 4.

---

## 2. Salida estructurada

### 2.1. Cómo se ofrece `final_result`

`structured_call(prompt, schema, max_repair_attempts)` construye la tool
sintética con el helper fijo `final_result_tool_schema(schema)`
(`mia_agents/tool_schema.py`), que deriva los `parameters` del propio modelo
Pydantic: **el schema es a la vez la firma de la tool y la condición de
aceptación**. En cada llamada a `chat` dentro del método se pasa
`tools=[esa tool]` — y solo esa: no se registra con `register_tool` porque no
ejecuta nada; es el mecanismo de cierre. "Responder" pasa de "texto libre" a
"invocar `final_result` con argumentos válidos".

### 2.2. Cómo se validan los argumentos

Cuando llega un `tool_call` a `final_result`: `json.loads(arguments)` y
`schema.model_validate(datos)`. Si ambos pasan, se devuelve la instancia
tipada. La validación es la de Pydantic: tipos, campos requeridos, coerciones
estándar.

### 2.3. Cómo se reparan los errores

Cada modo de fallo recibe una respuesta distinta, para que el modelo tenga
contexto real de corrección (mismo principio que los errores de tools: el
error vuelve al loop como observación):

| Fallo | Reparación enviada |
|---|---|
| Argumentos inválidos (JSON roto o `ValidationError`) | Mensaje `role:"tool"` con el detalle del error ("qué campo, qué recibió") y la instrucción de reinvocar corrigiendo esos campos |
| Texto libre (sin `tool_calls`) | Mensaje `role:"user"` de reparación: "invocá `final_result` con argumentos que respeten su schema; no respondas con texto" |
| Tool alucinada (otro nombre) | Mensaje `role:"tool"` a ese call: "la única herramienta disponible es `final_result`" |

Presupuesto: `1 + max_repair_attempts` llamadas exactas al LLM.

Memoria: el prompt y el resultado validado se **persisten** en la conversación
(`run` y `structured_call` intercalados mantienen contexto), pero los intentos
fallidos de reparación quedan **locales** a la llamada: no contaminan la
memoria de la conversación. La ventana de la sección 1 aplica igual acá.

### 2.4. Qué ocurre al agotar los reintentos

Se levanta `SalidaEstructuradaError` (excepción propia, con la causa original
encadenada en `__cause__` cuando existe: `ValidationError`, `JSONDecodeError`).
Nunca se devuelve `None` ni una instancia parcial — el contrato es "instancia
válida o excepción limpia" — y el historial de la conversación queda intacto.

---

## 3. Errores en herramientas

Criterio general: un error es **recuperable** si el mensaje le da al LLM lo
necesario para corregirse en el siguiente intento — qué parámetro falló, qué
valor llegó, por qué no sirve y cómo se vería uno válido. Las tools siguen
devolviendo `str` (nunca lanzan): el bucle realimenta ese texto como
observación.

### 3.1. Calculadora

| Error detectado | Información devuelta |
|---|---|
| Operando no numérico | Qué parámetro (`operando_a`/`operando_b`), qué valor llegó, y un ejemplo de valor válido. Los strings numéricos ("7", " 10 ") se aceptan por coerción: es un error de formato trivial del LLM que no vale la pena rebotar. Los booleanos se rechazan explícitamente (casi siempre son un argumento mal armado). |
| Operador no soportado | El valor recibido y la lista completa de permitidos: `+ - * % /` |
| División / módulo por cero | Que `operando_b` vale 0, que la operación no está definida con divisor 0, y que reintente con un divisor distinto |

**Ejemplo de recuperación:** el LLM invoca `calculadora(operando_a="cuarenta y
dos", operando_b=2, operador="+")` → recibe `Error: el parámetro 'operando_a'
recibió 'cuarenta y dos', que no es un número ni un texto numérico. Pasá un
valor numérico, p. ej. operando_a=3.5.` → reintenta con `operando_a=42` y la
operación sale.

### 3.2. Lector de archivos

Cada regla del sandbox tiene su mensaje propio (antes había un único "acceso
denegado" genérico):

| Error detectado | Información devuelta |
|---|---|
| Ruta vacía | La regla ("pasá una ruta relativa al directorio de datos") y un ejemplo (`'notas.txt'`) |
| Ruta absoluta | Que la ruta es absoluta y que solo se aceptan relativas al directorio permitido |
| Ruta con `..` | Que `..` permitiría escapar del sandbox y cómo se ve una ruta válida |
| Escape del sandbox (p. ej. symlinks) | Que la ruta resuelve fuera del directorio permitido |
| Archivo inexistente (directorio existente) | **La lista de archivos disponibles en ese directorio**, para que el LLM elija un nombre real y reintente |
| La ruta es un directorio | Que es un directorio y **su contenido listado**, con un ejemplo de cómo referirse a un archivo interno |
| Archivo demasiado grande / no UTF-8 / error de E/S | El límite (100 KB), o la codificación esperada, o el error del sistema |

**Ejemplo de recuperación:** el LLM invoca `leer_archivo(ruta="notas.md")` y
el archivo no existe → recibe `Error: el archivo 'notas.md' no existe.
Archivos disponibles en ese directorio: notas.txt, ventas.csv. Elegí uno de
esos nombres y reintentá.` → reinvoca con `ruta="notas.txt"` y obtiene el
contenido.

### 3.3. Resiliencia (fallos transitorios)

Complementario a lo anterior: las llamadas al cliente LLM y la ejecución de
cada tool van envueltas en `_con_reintentos`, que reintenta **solo** fallos
transitorios con backoff exponencial (`base * 2^intento`, configurables
`max_retries` y `retry_base_delay`). La clasificación (`_es_error_transitorio`)
no importa SDKs de proveedores: usa la jerarquía estándar (`TimeoutError`,
`ConnectionError`), duck-typing de códigos HTTP (408, 429, 5xx en
`status_code`/`status`/`response`), el `Error.Code` estilo botocore y una
heurística por nombre de clase. Un error no transitorio (`ValueError`,
`TypeError`...) se propaga limpio sin reintentos: repetir un bug no lo
arregla. Agotados los reintentos: si falló el LLM, la excepción se propaga
(sin modelo no hay plan B); si falló una tool, el error va a `AgentStep.error`
y vuelve al loop como observación — un solo fallo no rompe el bucle.

### 3.4. Tokens

`AgentResult.input_tokens/output_tokens` acumulan lo reportado por los
`LLMResponse` **de ese `run`** (se reinician por llamada). Si ninguna
respuesta reportó tokens quedan en `None` (un mock sin tokens no inventa
ceros); si alguna reportó, se suma tratando los `None` individuales como 0.

---

## 4. Modos de fallo

### Dentro del alcance (el agente los maneja)

- Conversaciones que exceden el presupuesto de contexto (Sliding Window).
- Salida estructurada malformada: texto libre, JSON roto, argumentos que no
  validan, tool alucinada → reparación con reintentos acotados.
- Fallos transitorios del LLM y de las tools: timeouts, errores de conexión,
  408/429/5xx, throttling → reintentos con backoff.
- Errores de uso de las tools (operandos inválidos, rutas fuera del sandbox,
  archivos inexistentes) → mensajes accionables realimentados al LLM.
- Tool desconocida, JSON de argumentos inválido, excepción dentro de una tool
  → `AgentStep.error`, el bucle sigue (heredado de M1).
- Bucles sin fin → `max_iterations` (heredado de M1).

### Fuera del alcance (decisiones explícitas)

- **Fallo definitivo del LLM:** agotados los reintentos, la excepción se
  propaga al llamador; no inventamos una respuesta sin modelo.
- **Presupuestos extremos:** con `max_history_messages` menor que un grupo
  `assistant + tools`, la ventana degrada a "solo el último user" y el modelo
  puede repetir tool calls. Se respeta el tope, no la eficiencia.
- **El ancla es el primer mensaje:** si el objetivo del usuario cambia a mitad
  de una conversación larga, el ancla puede quedar desactualizada (limitación
  conocida del recorte con `preserve_first_user`).
- **Tokens de `structured_call`:** no hay dónde exponerlos — devuelve la
  instancia validada, no un `AgentResult`.
- **El presupuesto es en mensajes, no en tokens:** un mensaje individual
  enorme puede seguir siendo caro; contar tokens por mensaje excede M2.
- **Sin paralelismo de tools ni persistencia a disco** del historial (la
  memoria vive en la instancia).

---

## Verificación

- Suite completa: `python -m pytest tests/ --ignore=tests/conformance/test_m3_world.py`
  → **105/105 en verde** con `MockLLMClient` (sin claves de API).
- Conformidad: `test_m1.py` **5/5** (el cierre de `run` sigue siendo el de M1)
  y `test_m2.py` **7/7**. Archivos FIJOS sin modificar.
- Tests propios de M2 (`tests/test_m2_propios.py`, 19 casos): tope y
  coherencia de la ventana con tools en el medio, invariante de recencia
  dentro de un run, ancla, presupuesto mínimo, reparación de texto
  libre / JSON roto / tool alucinada, ventana dentro de `structured_call`,
  persistencia del intercambio limpio (y no de los intentos fallidos),
  reintentos de LLM y tools (transitorio vs. no transitorio, agotamiento),
  clasificador por código HTTP, tokens (`None` si nadie reportó, reinicio
  por run).
- Herramientas (`tests/test_tools.py`, +11 casos): mensajes accionables de
  calculadora (parámetro y valor en el error, coerción de strings numéricos,
  booleanos, división por cero accionable) y del lector (regla violada
  nombrada, listado de disponibles ante inexistente, contenido ante
  directorio).
- Criterios de aprobación del enunciado, uno a uno: conversación que supera el
  presupuesto ✓ (`test_bounded_history_growth` + propios), prompt estructurado
  roto que se repara o falla limpio ✓, fallo transitorio simulado que se
  reintenta y termina bien ✓ (`test_timeout_del_llm_se_reintenta...`),
  mensajes claros de calculadora y lector ✓, tokens correctos ✓, informe ✓.
