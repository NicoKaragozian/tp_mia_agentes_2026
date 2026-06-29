# Informe M1 — Núcleo del agente (sección de Nicolás)

> **Aporte para el informe obligatorio de M1.** Lo integra Federico en el
> documento final (ver división de trabajo en `CLAUDE.md`). Esta sección
> cubre lo que corresponde a mi parte —el bucle del agente, en
> `student_framework/agent.py`— y responde los puntos **1** (diagrama),
> el núcleo del **2** (registro/exposición de tools desde el agente) y el
> **3** (terminación del bucle) del enunciado (`ENUNCIADO_M1.md`).

---

## 1. Diagrama de arquitectura

### 1.1. Componentes (cajas y flechas)

```
                build_agent(config)                  [student_framework/__init__.py]
                       │
                       │  1) elige el LLMClient: usa config["llm_client"] si lo
                       │     inyectan (tests → MockLLMClient); si no, from_env()
                       │  2) registra cada (fn, schema) del REGISTRY auto-descubierto
                       ▼
        ┌───────────────────────────────────────────────────┐
        │                     MyAgent                         │   [agent.py]  ← mi parte
        │                                                     │
        │   estado:  _tools   : name → callable               │
        │            _schemas : name → ToolSchema             │
        │                                                     │
        │   run(user_message) → AgentResult                   │
        └───────────────────────────────────────────────────┘
              │  expone tools                  ▲  ejecuta tools
              │  llm.chat(...)                 │  _dispatch(tool_call)
              ▼                                │
   ┌─────────────────────────┐        ┌────────────────────────────┐
   │   LLMClient (protocolo)  │        │   herramientas registradas  │
   │   .chat(messages, tools, │        │   calculadora / lector /    │
   │         system) →        │        │   creativa  (fn -> str)     │
   │        LLMResponse       │        └────────────────────────────┘
   │                          │            [tools/*.py — Valentino/Federico]
   │  impl. FIJA:             │
   │   Ollama / Bedrock /     │
   │   MockLLMClient (tests)  │   [mia_agents/llm_client.py — FIJO]
   └─────────────────────────┘
```

Idea clave: **el bucle depende sólo del protocolo `chat(...)`**, no de un
proveedor concreto. Por eso los tests pueden sustituir el cliente real por
`MockLLMClient` sin tocar el agente, y el agente corre igual contra
Ollama o Bedrock.

### 1.2. Flujo de una llamada a `run` (bucle ReAct)

```
 run("¿Cuánto es 17*23? Usá la calculadora")
   │
   ├─ messages = [ {user: "..."} ]   ;   steps = []
   │
   ▼  for _ in range(max_iterations):          ◄──────────────────────┐
   │                                                                   │
   │   response = llm.chat(messages, tools=_schemas, system)           │
   │                                                                   │
   │   ¿response.tool_calls?                                           │
   │     ── NO ──►  return AgentResult(answer = content or "", steps)  │  ← parada normal
   │                                                                   │
   │     ── SÍ ──►  messages += turno assistant (con tool_calls)       │
   │                por cada tool_call:                                │
   │                   output, error = _dispatch(call)                 │
   │                   steps += AgentStep(name, args, output, error)   │
   │                   messages += {role:"tool", content: output|error}┘
   │
   └─ (se agota el for) → AgentResult(answer="", steps, error="máx iteraciones")  ← parada por límite
```

**Ejecutar una herramienta = dos llamadas al LLM:** la primera devuelve el
`tool_call`; tras ejecutar la tool y volcar su resultado en `messages`, la
segunda llamada produce la respuesta final de texto.

---

## 2. Registro y exposición de herramientas (parte del núcleo)

> El diseño de la *interfaz* de tools (`ToolSchema.from_callable`,
> `Annotated`/`Field`, qué hace el `LLMClient` con cada esquema) lo
> desarrolla la sección de tools/integración. Acá documento sólo lo que
> ocurre **dentro del agente**.

- **`register_tool(fn, schema)`** guarda la tool en dos diccionarios
  indexados por `schema.name`:
  - `self._tools[schema.name] = fn` → para poder localizar el callable
    cuando llega un `tool_call` (lo único que trae es `call.name`).
  - `self._schemas[schema.name] = schema` → para exponer el esquema al LLM.

  Indexar por nombre es lo que hace que `AgentStep.tool_name == schema.name`
  salga directo, sin lógica extra.

- **Exposición en cada `run`:** se pasa
  `tools = list(self._schemas.values()) or None` a `chat(...)`. Si no hay
  tools registradas, se manda `None`; si las hay, va la lista y el nombre
  registrado aparece en ella (lo exige el contrato). El `LLMClient` fijo
  traduce cada `ToolSchema` al formato nativo de Ollama/Bedrock con
  `to_llm_spec()`; el agente nunca escribe JSON Schema a mano.

- **Realimentación del resultado:** la tool ejecutada se devuelve al LLM
  como un mensaje `{"role": "tool", "tool_call_id": ..., "content": ...}`.
  Ese mensaje aparece en los `messages` de la siguiente llamada a `chat`,
  que es como el modelo "observa" lo que pasó.

---

## 3. Terminación del bucle y límite de iteraciones

El bucle tiene **dos formas de cortar**, ambas devolviendo siempre un
`AgentResult` válido (nunca lanza, nunca cicla infinito):

1. **Parada normal (respuesta final).** El LLM responde con texto y **sin**
   `tool_calls`. Ese texto es `AgentResult.answer` (con `content or ""`
   para cubrir `content == None`), `steps` lleva un paso por cada tool que
   se haya ejecutado, y `error is None`. Si no hubo tools, esto ocurre en
   la **primera** llamada → `steps == []` y una sola llamada al LLM.

2. **Parada por límite (`max_iterations`, default 10).** El bucle es un
   `for _ in range(self._max_iterations)`, no un `while True`: esa elección
   es la garantía estructural de que **no hay loops infinitos**. Si el
   modelo se queda pidiendo tools sin cerrar nunca, tras `max_iterations`
   llamadas al LLM salimos del `for` y devolvemos un `AgentResult` con
   `answer == ""`, los `steps` acumulados y `error` indicando el corte por
   límite. El agente **deja de llamar al LLM** exactamente al alcanzar ese
   número de llamadas.

**Robustez ante fallos de tool (no rompe el bucle).** El despacho de cada
`tool_call` está aislado en `_dispatch`, que nunca lanza y devuelve
`(output, error)`. Cubre los tres modos de fallo del contrato:

| Situación                                   | Resultado                          |
|---------------------------------------------|------------------------------------|
| Tool desconocida (alucinada por el LLM)     | `AgentStep` con `error` no nulo    |
| `arguments` con JSON inválido               | `AgentStep` con `error` no nulo    |
| La tool lanza excepción (p. ej. división/0) | `AgentStep` con `error` no nulo    |
| Éxito                                        | `tool_output` = string, `error=None` |

En caso de error, al LLM se le devuelve el mensaje de error como contenido
del mensaje `tool`, para que pueda recuperarse o reformular en la siguiente
iteración en lugar de quedarse a ciegas.

---

## 4. Limitaciones conocidas (del núcleo, M1)

- **Sin estado entre llamadas.** Cada `run` es una interacción
  independiente: el historial vive sólo dentro de esa llamada. La
  conversación multi-turno y el recorte por `max_history_messages` son M2
  (el parámetro se acepta en el constructor pero se ignora en M1).
- **Sin conteo de tokens.** `AgentResult.input_tokens` /
  `output_tokens` quedan en `None`. La acumulación de tokens reportados por
  los `LLMResponse` es M2 (el contrato de M1 no la pide).
- **Sin salida estructurada.** `structured_call` (tool sintética
  `final_result` + reparación) es un stub con `NotImplementedError`; se
  implementa en M2.
- **Ejecución secuencial de tool_calls.** Si una respuesta trae varios
  `tool_calls`, se ejecutan en orden, uno por uno (un `AgentStep` por
  cada uno). No hay paralelismo —innecesario para el alcance de M1.

---

## Verificación

- `pytest tests/conformance/test_m1.py` → **5/5** en verde (con
  `MockLLMClient`, sin claves de API).
- Edge cases del contrato no incluidos en el archivo de conformidad
  (tool desconocida, JSON inválido, excepción de tool, corte por
  `max_iterations`, string vacío, varios `tool_calls`, `content == None`)
  verificados a mano: todos OK.
