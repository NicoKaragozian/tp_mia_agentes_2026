# CLAUDE.md — TP Agentes Autónomos (MIA303, UdeSA 2026)

Guía para Claude / asistentes y para el equipo. Léela antes de tocar código.

## Qué es este proyecto

Construimos **desde cero** (sin LangChain/LangGraph) un framework mínimo de
agentes en Python, a lo largo de **tres milestones** sobre el mismo codebase.
El objetivo del curso es entender el *agent loop* por dentro: cliente LLM,
registro de herramientas, bucle ReAct, manejo de contexto y evaluación.

- **M1 (este):** agente funcional — `LLMClient` + registro de tools + agent loop.
- **M2:** robustez — estado conversacional, context management, `structured_call`
  con `final_result` y reparación, manejo de errores, conteo de tokens/costos.
- **M3:** sistema completo — mundo simulado, workflows, suite de evals, guardrails y demo.

Equipo: **Nicolás Karagozian**, **Valentino**, **Federico**.

Plan completo y teoría: ver la página de Notion **"Trabajo Final"** (subpáginas por milestone).

## Regla de oro: archivos FIJOS (no editar)

La corrección re-ejecuta los tests de conformidad tal cual están. Si modificamos
archivos FIJOS y eso causa divergencia, **el milestone no aprueba**.

- `mia_agents/**` — FIJO. Tipos, protocolos, `ToolSchema.from_callable`, `LLMClient`, CLI, testing.
- `tests/conformance/**` — FIJO. Tests que toda entrega debe pasar.
- `mia_world/**`, `scenarios/**` — FIJO (aparecen en M3).
- En `student_framework/__init__.py`, las líneas marcadas `#NO CAMBIAR` no se tocan.

**Lo nuestro (editable):** `student_framework/` (agente y tools), nuestros tests
propios y los informes.

## Dónde escribimos código (M1)

```
student_framework/
├── __init__.py     # build_agent(config): instancia MyAgent y registra las tools (único entrypoint)
├── agent.py        # MyAgent: register_tool + run (el bucle)  ← núcleo de M1
└── tools/
    ├── example.py      # ejemplo (reverse_string). NO cuenta como tool obligatoria; se puede borrar
    ├── calculadora.py  # tool 1: calculadora
    ├── lector.py       # tool 2: lector de archivos de texto
    └── creativa.py     # tool 3: herramienta libre (cifrado César)
```

## Contrato M1 (resumen operativo — la fuente de verdad es `ENUNCIADO_M1.md`)

- `build_agent(config)`: si `config["llm_client"]` está presente, **usar ese cliente**
  (los tests inyectan un `MockLLMClient`). No crear uno propio cuando lo pasan.
- `agent.run(user_message)` devuelve **siempre** un `AgentResult`.
- **Sin tool_calls:** `result.answer == content`, `result.steps == []`, **una sola** llamada al LLM.
- **Registro:** en cada `run` se pasa `tools=list(self._schemas.values())` a `chat(...)`.
  Los esquemas coinciden con los registrados vía `register_tool(tool, schema)`.
- **Ejecución de tool:** parsear `arguments` (JSON) → invocar el callable con esos kwargs
  → volcar el resultado como mensaje `role:"tool"` → **volver a llamar** a `chat`.
  Ejecutar una tool implica **dos** llamadas al LLM (tool_call + respuesta final).
- **AgentStep** por cada invocación: `tool_name == schema.name`, `tool_output ==` valor exacto
  devuelto por la tool (string), `error == None` si fue exitosa.
- **Tool desconocida (alucinada):** no romper; registrar un `AgentStep` con `error` no nulo.
- **Terminación:** cortar al devolver texto sin tool_calls **o** al alcanzar `max_iterations`
  (default 10). Aun cortando por límite, devolver un `AgentResult` válido. Sin loops infinitos.
- M1 **no** usa `final_result` ni `structured_call` (eso es M2; dejar como `NotImplementedError`).

### Patrón de tool (no escribir JSON Schema a mano)

```python
from typing import Annotated
from pydantic import Field
from mia_agents.types import ToolSchema

def mi_tool(arg: Annotated[str, Field(description="Qué hace.")]) -> str:
    """Descripción de la herramienta para el LLM (docstring completo)."""
    return "resultado como string"

mi_tool_schema = ToolSchema.from_callable(mi_tool)
```

El docstring → descripción de la tool. Los tipos + `Field(description=...)` → JSON Schema de args.
Las tools **siempre devuelven `str`**.

## Setup del entorno

```bash
cd tp_mia_agentes_2026
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Proveedor LLM (solo para correr el agente de verdad; los tests usan MockLLMClient):

```bash
# Ollama local (sin clave)
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama3.1"
# o AWS Bedrock
export BEDROCK_MODEL_ID="amazon.nova-lite-v1:0"
export AWS_REGION="us-east-1"   # + credenciales AWS
```

## Comandos frecuentes

```bash
pytest tests/conformance/test_m1.py        # M1 (no consume API; MockLLMClient)
python -m mia_agents.cli run --module student_framework --message "¿Cuánto es 17 * 23? Usá la calculadora."
```

Antes de implementar, los tests deben **fallar con `NotImplementedError`** (confirma que el entorno está OK).

## División de trabajo (M1)

Asignación balanceada; cada quien defiende su parte en la oral. Detalle y criterios en Notion.

- **Nicolás — Núcleo del agente (`agent.py`):** `run` (bucle ReAct), dispatch de tools,
  feedback del resultado al LLM, manejo de tool desconocida y de `max_iterations`, armado de `AgentStep`.
- **Valentino — Herramientas (`tools/`):** calculadora, lector de archivos y sus `ToolSchema`,
  con validaciones (división por cero, ruta inexistente, acceso acotado).
- **Federico — Integración y tooling:** `build_agent` + registro por auto-descubrimiento
  (`tools/__init__.py`), herramienta libre (cifrado César), escenarios de test propios (≥2 tools)
  e informe (diagrama de arquitectura).

### Trabajo no-bloqueante

El reparto está diseñado para que **nadie bloquee a nadie**: todos programan contra interfaces
fijas (`mia_agents/types.py`, `protocols.py`), no contra implementaciones.

- Las **tools** son funciones puras `fn(...) -> str` + `ToolSchema.from_callable(fn)`: no conocen el
  bucle ni el formato interno de `messages`. Se testean solas.
- El **bucle** (`agent.py`) depende solo de los tipos fijos y del protocolo `LLMClient`: se testea
  entero con `MockLLMClient` + `make_recording_tool`, sin ninguna tool real.
- La integración se desacopla con un **registro por auto-descubrimiento** en `tools/__init__.py`
  (cada módulo expone `TOOLS = [(fn, schema)]`; el `__init__` los recolecta en `REGISTRY`).
  Así `build_agent` no cambia al agregar tools y **nadie edita el archivo de otro**.
- **Sprint 0** (una vez, juntos): mergear el esqueleto (stubs + registro + `build_agent`). Desde ese
  commit, cada quien trabaja en sus archivos en paralelo. Detalle y código en la sección 11 de Notion.

Mapa de archivos disjuntos: Nicolás → `agent.py`; Valentino → `tools/calculadora.py` + `tools/lector.py`;
Federico → `tools/creativa.py` + `tools/__init__.py` + `build_agent`.

## Git / fork

- `upstream` → repo de la cátedra (`fcastellacci/tp_mia_agentes_2026`). Para traer cambios: `git pull upstream main`.
- Crear el fork propio en GitHub y agregarlo como `origin`:
  `git remote add origin <url-del-fork>` y luego `git push -u origin main`.
- Trabajar en ramas por feature (`m1/agent-loop`, `m1/tools`, `m1/integration`) y mergear con PR.

## Convenciones

- Python 3.10+. Type hints en todo. Tools devuelven `str`.
- No tocar archivos FIJOS. No commitear `.env`, credenciales ni `.venv/`.
- Mensajes de commit claros y en lo posible chicos/atómicos.
- Correr `pytest tests/conformance/test_m1.py` antes de cada PR.
