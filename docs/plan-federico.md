# Plan — Federico · Tool libre + integración + tests + informe

> Este es mi plan. Escribo el código en `student_framework/tools/creativa.py`,
> `student_framework/tools/__init__.py` (registro) y `student_framework/__init__.py` (`build_agent`),
> más los tests propios y el informe. No toco `mia_agents/**` ni `tests/conformance/**` (FIJOS).

## Objetivo

Cerrar la integración del agente sin acoplar a nadie, aportar la tercera tool (libre) y dejar los
entregables transversales: escenarios de test (≥2 tools) y el informe.

## 1. Tool libre — cifrado César (`tools/creativa.py`)

- **Qué hace:** desplaza cada letra N posiciones en el alfabeto; conserva mayúsculas/minúsculas y
  deja intactos los no-alfabéticos. Desplazamiento negativo = descifrar.
- **Entrada:** `texto: str`, `desplazamiento: int` (ambos con `Annotated` + `Field`).
- **Salida:** `str`. Misma estructura que el resto: docstring como descripción, `_schema` con
  `from_callable`, y `TOOLS = [(cifrado_cesar, cifrado_cesar_schema)]`.
- **Por qué esta:** creativa, determinista y fácil de testear con el `MockLLMClient`; distinta en
  naturaleza de la calculadora y el lector. (Alternativas si la cambiamos: conversor de unidades,
  número→palabras, búsqueda en JSON local, contador de palabras.)

## 2. Registro por auto-descubrimiento (`tools/__init__.py`)

> Se escribe **una vez** (en el Sprint 0) y no se vuelve a tocar al agregar tools.

- Recorrer los módulos del paquete `tools` (con `pkgutil.iter_modules`), ignorando `example`.
- Importar cada módulo y juntar su atributo `TOOLS` (lista de pares `(callable, ToolSchema)`) en una
  lista única `REGISTRY`. Si un módulo no expone `TOOLS`, se ignora (default lista vacía).
- Exponer `REGISTRY` para que `build_agent` lo consuma.

**Por qué desacopla:** agregar una tool = crear un archivo nuevo con su `TOOLS`. Nadie edita este
archivo ni `build_agent`. Cero conflictos de merge.

## 3. `build_agent` (`student_framework/__init__.py`)

- No tocar las líneas marcadas `#NO CAMBIAR` (resolución del `llm_client` y armado de `kwargs`).
- Instanciar `MyAgent(**kwargs)` y **registrar iterando sobre `REGISTRY`** (`for fn, schema in REGISTRY: agent.register_tool(fn, schema)`).
- Devolver el agente. Queda fijo: no cambia cuando se agregan/quitan tools.

## 4. Escenarios de test propios (entregable)

- Al menos un escenario con **≥2 tools** usando `MockLLMClient`: programar una secuencia de
  `LLMResponse` (tool_call calculadora → tool_call cifrado → texto final) y verificar `answer`,
  la secuencia de `tool_name` en `steps`, un `tool_output` exacto y `call_count`.
- Escenarios de robustez: (a) tool desconocida → `AgentStep.error` no nulo y el agente sigue;
  (b) división por cero → la tool devuelve el error como string; (c) corte por `max_iterations`.
- Smoke test opcional contra LLM real con la CLI:
  `python -m mia_agents.cli run --module student_framework --message "..."`.

## 5. Informe (entregable escrito)

1. **Diagrama de arquitectura** (cajas y flechas) — partir del diagrama del bucle de la página de
   Notion de M1 y pasarlo a una herramienta de dibujo.
2. **Diseño de la interfaz de herramientas:** qué se guarda en `register_tool`, qué se pasa a
   `chat(tools=...)` y qué hace el `LLMClient` con cada esquema (`to_llm_spec()` → formato nativo
   de Ollama/Bedrock).
3. **Limitaciones conocidas:** single-turn (sin memoria entre `run`), sin reintentos transitorios,
   sin límite de tokens, tools síncronas, `max_iterations` fijo, lector acotado a `data/`, el LLM
   puede alucinar argumentos.

## Coordinación / no-bloqueo

- El registro lo puedo desarrollar y testear con **stubs** que expongan `TOOLS` (no necesito las
  tools reales de Valentino ni el bucle final de Nicolás).
- Mis tests de integración pasan a verde a medida que las otras piezas se mergean, pero los puedo
  escribir desde el día 1 contra la interfaz acordada.

## Definition of Done

- [ ] Cifrado César implementado (función pura → `str`) con su `_schema` y `TOOLS`.
- [ ] `tools/__init__.py` descubre todas las tools en `REGISTRY`.
- [ ] `build_agent` registra iterando `REGISTRY`, sin tocar líneas `#NO CAMBIAR`.
- [ ] ≥1 escenario de test con 2+ tools + escenarios de robustez.
- [ ] Informe con diagrama, diseño de interfaz y limitaciones.
- [ ] `pytest tests/conformance/test_m1.py` en verde con las 3 tools.
- [ ] No toqué archivos FIJOS.
