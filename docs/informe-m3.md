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
