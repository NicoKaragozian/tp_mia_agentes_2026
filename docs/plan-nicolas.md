# Plan — Nicolás · Núcleo del agente (`agent.py`)

> Este es mi plan de trabajo. El código lo escribo yo en `student_framework/agent.py`.
> No toco `mia_agents/**` ni `tests/conformance/**` (FIJOS).

## Objetivo

Implementar el *agent loop* (ReAct) de M1: registrar herramientas, exponerlas al LLM, decidir si
invocar, ejecutar, observar el resultado y continuar hasta una respuesta final, sin loops infinitos.

## Mi archivo

- `student_framework/agent.py` → clase `MyAgent`: `__init__`, `register_tool`, `run`, `_dispatch`
  (helper interno), y `structured_call` como stub (`NotImplementedError`, es M2).

## Interfaces que consumo (fijas — no las defino yo)

- `mia_agents.types`: `AgentResult(answer, steps, error, input_tokens, output_tokens)`,
  `AgentStep(tool_name, tool_input, tool_output, error)`, `ToolCall(id, name, arguments)`,
  `LLMResponse(content, tool_calls, ...)`, `ToolSchema`.
- `mia_agents.protocols.LLMClient.chat(messages, tools=None, system=None, temperature=0.2, response_format=None) -> LLMResponse`.
- El cliente llega por constructor (`llm_client`); en tests es un `MockLLMClient`. **Nunca** creo un
  cliente propio: uso el inyectado.

## Tareas (paso a paso)

1. **Estado interno** en `__init__`: dos diccionarios, `self._tools` (name → callable) y
   `self._schemas` (name → `ToolSchema`). Guardar también `system_prompt`, `max_iterations`,
   `max_history_messages` (este último se acepta pero **se ignora en M1**).
2. **`register_tool(tool, schema)`**: guardar el callable bajo `schema.name` y el schema bajo el
   mismo nombre. (Es la clave de que el `tool_name` del step coincida con el nombre del esquema.)
3. **`run(user_message)`** — el bucle:
   - Inicializar `messages = [{"role": "user", "content": user_message}]` y `steps = []`.
   - Iterar hasta `max_iterations`:
     - Llamar `self._llm.chat(messages=messages, tools=list(self._schemas.values()) if hay tools else None, system=self._system)`.
     - **Si NO hay `tool_calls`** → devolver `AgentResult(answer=content or "", steps=steps)` y cortar.
     - **Si hay `tool_calls`**: agregar a `messages` el turno del assistant con sus `tool_calls`,
       ejecutar cada uno por `_dispatch`, registrar un `AgentStep` por invocación, y volcar el
       resultado como mensaje `role:"tool"` (con `tool_call_id`).
   - Si se agota `max_iterations` → devolver un `AgentResult` válido igual (con `error` indicando el corte).
4. **`_dispatch(tool_call)`**: buscar el callable por `name`; si no existe → devolver error (tool
   desconocida). Parsear `arguments` (JSON) → invocar `tool(**kwargs)` → devolver el resultado como
   `str`. Capturar excepciones de parseo y de ejecución y devolverlas como error (sin romper).

## Formato interno de `messages` (lo defino yo, vive dentro de `agent.py`)

Lo que ambos providers (Bedrock/Ollama) saben normalizar:
- Turno del assistant con tool calls: `{"role": "assistant", "content": ..., "tool_calls": [{"id", "function": {"name", "arguments"}}]}`.
- Resultado de tool: `{"role": "tool", "tool_call_id": <id>, "content": <output str>}`.

> Este formato **no lo ven las tools** → no acopla a Valentino ni a Federico.

## Comportamientos exactos a respetar (contrato)

- Sin `tool_calls`: `answer == content`, `steps == []`, **una sola** llamada al LLM.
- Ejecutar una tool ⇒ **dos** llamadas al LLM (la del tool_call y la de la respuesta final).
- El output de la tool **aparece en los `messages`** de la segunda llamada.
- Un `AgentStep` por invocación: `tool_name == schema.name`, `tool_output ==` valor exacto (string),
  `error == None` si fue exitosa.
- Tool desconocida (alucinada): no romper; `AgentStep` con `error` no nulo.
- Corte por texto-final o por `max_iterations`; siempre devolver `AgentResult` válido.

## Edge cases que debo cubrir

- `arguments` con JSON inválido → error en el step, el agente sigue.
- `content` `None` en la respuesta final → `answer = ""`.
- Sin tools registradas → pasar `tools=None`.
- Varias `tool_calls` en una sola respuesta → un step por cada una.

## Cómo lo testeo solo (sin tools reales)

Con `MockLLMClient` (lista de `LLMResponse` prefabricados) + `make_recording_tool`:

- `test_no_tool_no_loop`: una respuesta de solo texto → answer correcto, steps vacío, `call_count == 1`.
- Tool ejecutada: respuesta con `tool_call` + respuesta de texto → `tool.calls` recibió los kwargs,
  `len(steps) == 1`, `steps[0].tool_name` correcto, `call_count == 2`.
- Tool desconocida: `tool_call` a un nombre no registrado → step con `error` no nulo, sin excepción.
- `max_iterations`: mock que siempre devuelve `tool_calls` → corta sin loop infinito, devuelve `AgentResult`.

## Definition of Done

- [ ] Pasa todos los tests de `run`/`register_tool` de `tests/conformance/test_m1.py`.
- [ ] Mis tests propios del bucle (los de arriba) pasan.
- [ ] `structured_call` queda como stub `NotImplementedError`.
- [ ] No toqué archivos FIJOS.
