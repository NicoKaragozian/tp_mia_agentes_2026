# Informe M1 — Bucle del agente y herramientas

Framework mínimo de agentes (sin LangChain/LangGraph). Este informe cubre los
cuatro puntos pedidos: (1) diagrama de arquitectura, (2) diseño de la interfaz
de herramientas, (3) terminación del bucle, (4) limitaciones conocidas.

Mapa de autoría: núcleo del agente (`student_framework/agent.py`) → Nicolás;
herramientas (`student_framework/tools/`) → Valentino (calculadora, lector) y
Federico (word_counter + integración).

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
        │                     MyAgent                         │   [student_framework/agent.py]
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
   │   .chat(messages, tools, │        │   calculadora / leer_archivo│
   │         system) →        │        │   / word_counter  (fn->str) │
   │        LLMResponse       │        └────────────────────────────┘
   │                          │            [student_framework/tools/*.py]
   │  impl. FIJA:             │
   │   Ollama / Bedrock /     │
   │   MockLLMClient (tests)  │   [mia_agents/llm_client.py — FIJO]
   └─────────────────────────┘
```

Idea clave: **el bucle depende sólo del protocolo `chat(...)`**, no de un
proveedor concreto. Por eso los tests pueden sustituir el cliente real por
`MockLLMClient` sin tocar el agente, y el agente corre igual contra Ollama o
Bedrock.

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

## 2. Diseño de la interfaz de herramientas

### 2.1. Cómo se define una herramienta (patrón de autoría)

Cada herramienta es una **función pura** `fn(...) -> str` (las tools siempre
devuelven `str`) con los tipos en la firma y una descripción por argumento:

```python
def calculadora(
    operando_a: Annotated[float, Field(description="Primer operando numérico.")],
    operando_b: Annotated[float, Field(description="Segundo operando numérico.")],
    operador:   Annotated[str,   Field(description="Operador aritmético: + - * % /.")],
) -> str:
    """Realiza una operación aritmética binaria entre dos números. ..."""
    ...

calculadora_schema = ToolSchema.from_callable(calculadora)
TOOLS = [(calculadora, calculadora_schema)]
```

`ToolSchema.from_callable(fn)` deriva el esquema **sin escribir JSON Schema a
mano**:

- el **docstring** completo → `description` de la tool (lo que el LLM lee para
  decidir cuándo usarla);
- los **tipos** de la firma + `Field(description=...)` → `parameters`
  (JSON Schema de los argumentos, con sus `required`);
- el **nombre** por defecto es `fn.__name__` (se puede sobreescribir con
  `name=...` si hiciera falta desambiguar).

Las tools **no conocen** el bucle ni el formato interno de `messages`: por eso
se testean solas (`tests/test_tools.py`).

**Registro por auto-descubrimiento.** Cada módulo de `student_framework/tools/`
expone `TOOLS = [(fn, schema)]`; `student_framework/tools/__init__.py` recolecta
todos en `REGISTRY`
(orden determinista por nombre de módulo, fail-fast ante `TOOLS` malformado o
nombres duplicados). `build_agent` registra todo lo que haya en `REGISTRY`, así
**agregar una tool = crear su módulo**, sin tocar `build_agent` ni el archivo
de otro integrante.

### 2.2. Qué guarda el agente y qué expone al LLM

- **`register_tool(fn, schema)`** guarda la tool en dos diccionarios indexados
  por `schema.name`:
  - `self._tools[schema.name] = fn` → para localizar el callable cuando llega
    un `tool_call` (que sólo trae `call.name`);
  - `self._schemas[schema.name] = schema` → para exponer el esquema al LLM.

  Indexar por nombre es lo que hace que `AgentStep.tool_name == schema.name`
  salga directo, sin lógica extra.

- **Exposición en cada `run`:** se pasa `tools = list(self._schemas.values())
  or None` a `chat(...)`. Si no hay tools, se manda `None`; si las hay, va la
  lista y el nombre registrado aparece en ella (lo exige el contrato).

- **Qué hace el `LLMClient` con cada esquema:** el cliente fijo aplica
  `ToolSchema.to_llm_spec()` y traduce cada esquema al formato nativo de
  Ollama/Bedrock dentro de `_format_tools`. El agente nunca habla el dialecto
  del proveedor.

- **Realimentación del resultado:** la tool ejecutada se devuelve al LLM como
  `{"role": "tool", "tool_call_id": ..., "content": ...}`. Ese mensaje aparece
  en los `messages` de la siguiente llamada a `chat`, que es como el modelo
  "observa" lo que pasó.

---

## 3. Terminación del bucle y límite de iteraciones

El bucle tiene **dos formas de cortar**, ambas devolviendo siempre un
`AgentResult` válido (nunca lanza, nunca cicla infinito):

1. **Parada normal (respuesta final).** El LLM responde con texto y **sin**
   `tool_calls`. Ese texto es `AgentResult.answer` (`content or ""` para cubrir
   `content == None`), `steps` lleva un paso por cada tool ejecutada y
   `error is None`. Si no hubo tools, esto ocurre en la **primera** llamada →
   `steps == []` y una sola llamada al LLM.

2. **Parada por límite (`max_iterations`, default 10).** El bucle es un
   `for _ in range(self._max_iterations)`, no un `while True`: esa elección es
   la garantía estructural de que **no hay loops infinitos**. Si el modelo se
   queda pidiendo tools sin cerrar, tras `max_iterations` llamadas salimos del
   `for` y devolvemos un `AgentResult` con `answer == ""`, los `steps`
   acumulados y `error` indicando el corte. El agente **deja de llamar al LLM**
   exactamente al alcanzar ese número de llamadas.

**Robustez ante fallos de tool (no rompe el bucle).** El despacho de cada
`tool_call` está aislado en `_dispatch`, que nunca lanza y devuelve
`(output, error)`:

| Situación                                   | Resultado                            |
|---------------------------------------------|--------------------------------------|
| Tool desconocida (alucinada por el LLM)     | `AgentStep` con `error` no nulo      |
| `arguments` con JSON inválido               | `AgentStep` con `error` no nulo      |
| La tool lanza excepción                     | `AgentStep` con `error` no nulo      |
| Éxito                                       | `tool_output` = string, `error=None` |

En caso de error, al LLM se le devuelve el mensaje de error como contenido del
mensaje `tool`, para que pueda recuperarse en la siguiente iteración en lugar
de quedarse a ciegas.

---

## 4. Limitaciones conocidas

### 4.1. Del núcleo (M1)

- **Sin estado entre llamadas.** Cada `run` es independiente: el historial vive
  sólo dentro de esa llamada. La conversación multi-turno y el recorte por
  `max_history_messages` son M2 (el parámetro se acepta en el constructor pero
  se ignora en M1).
- **Sin conteo de tokens.** `AgentResult.input_tokens` / `output_tokens` quedan
  en `None`; la acumulación es M2.
- **Sin salida estructurada.** `structured_call` (`final_result` + reparación)
  es un stub con `NotImplementedError`; se implementa en M2.
- **Ejecución secuencial de `tool_calls`.** Si una respuesta trae varios, se
  ejecutan en orden, uno por uno. No hay paralelismo (innecesario en M1).

### 4.2. De las herramientas

- **Calculadora.** Sólo operación binaria; operadores `+ - * /` (y además `%`),
  sin `eval`. Los errores se devuelven **como string**, no como excepción:
  operador no soportado y división/módulo por cero. Los resultados enteros se
  normalizan (`4.0` → `"4"`).
- **Lector de archivos.** Acceso **acotado** a un directorio base (`data/`,
  sandbox): rechaza path traversal (`../`) y rutas absolutas externas; tope de
  tamaño (100 KB) chequeado con `stat()` **antes** de leer; sólo texto UTF-8.
  El directorio `data/` no se versiona (se crea al usarse), así que para una
  demo en vivo del lector hay que crear `data/` y poner un archivo. Es una
  decisión defensiva que anticipa los guardrails de M3.
- **word_counter.** Cuenta palabras separando por espacios en blanco
  (`str.split()`); definición simple, sin tokenización lingüística.

---

## Verificación

- `pytest tests/conformance/test_m1.py tests/test_tool_schema.py
  tests/test_tools.py tests/test_scenarios.py` → **35/35** en verde, con
  `MockLLMClient` (sin claves de API).
- Conformidad `test_m1.py`: **5/5**. Archivos FIJOS (`mia_agents/**`,
  `tests/conformance/**`) sin modificar.
- Edge cases del contrato verificados: tool desconocida, JSON inválido,
  excepción de tool, corte por `max_iterations`, string vacío, varios
  `tool_calls`, `content == None`.
