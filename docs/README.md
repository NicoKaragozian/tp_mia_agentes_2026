# docs/ — Planes de trabajo (M1)

Esta carpeta contiene **el plan de cada integrante** para el Milestone 1. Son planes, no
código: cada uno usa su `.md` como guía para escribir su parte. El código lo escribe cada
quien en sus propios archivos.

- [plan-nicolas.md](./plan-nicolas.md) — Núcleo del agente (`agent.py`: bucle `run`).
- [plan-valentino.md](./plan-valentino.md) — Herramientas obligatorias (calculadora + lector).
- [plan-federico.md](./plan-federico.md) — Tool libre + registro + `build_agent` + tests + informe.

Contexto completo y teoría: ver `CLAUDE.md` (raíz) y la página de Notion **"Trabajo Final"**.

## Principio: nadie bloquea a nadie

Todos programan **contra interfaces fijas, no contra implementaciones**. El contrato ya está
congelado en `mia_agents/types.py` y `mia_agents/protocols.py` (archivos FIJOS, no editar).

- Las **tools** son funciones puras `fn(...) -> str` + `ToolSchema.from_callable(fn)`. No conocen
  el bucle ni el formato interno de `messages`; se testean solas.
- El **bucle** (`agent.py`) depende solo de los tipos fijos y del protocolo `LLMClient`; se testea
  entero con `MockLLMClient` + `make_recording_tool`, sin ninguna tool real.
- La integración se desacopla con un **registro por auto-descubrimiento** (ver Sprint 0): cada
  módulo de tool expone `TOOLS = [(fn, schema)]` y `build_agent` los recolecta. Agregar una tool =
  crear un archivo nuevo. Nadie edita el archivo de otro.

Mapa de archivos disjuntos (un dueño por archivo):

| Persona | Archivo(s) | Testea solo con |
| --- | --- | --- |
| Nicolás | `student_framework/agent.py` | `MockLLMClient` + `make_recording_tool` |
| Valentino | `student_framework/tools/calculadora.py`, `student_framework/tools/lector.py` | pytest unitario de cada función |
| Federico | `student_framework/tools/creativa.py`, `student_framework/tools/__init__.py`, `student_framework/__init__.py` (`build_agent`) | con cualquier stub que exponga `TOOLS` |

## Sprint 0 (una vez, juntos — ~15 min)

Antes de repartirse, se crea y mergea el **esqueleto** para que todos los imports resuelvan desde
el primer commit:

1. Stubs vacíos de los 3 archivos de tools, cada uno con `TOOLS = []` (placeholder).
2. `student_framework/tools/__init__.py` con el **registro por auto-descubrimiento**: recorre los
   módulos del paquete (ignorando `example`) y junta los `TOOLS` de cada uno en una lista `REGISTRY`
   de pares `(callable, ToolSchema)`.
3. `student_framework/__init__.py` (`build_agent`): instancia `MyAgent` y registra **iterando sobre
   `REGISTRY`** (no nombra tools una por una; así no cambia al agregar tools). No tocar las líneas
   marcadas `#NO CAMBIAR`.

Desde ese commit, cada quien trabaja en su archivo en paralelo, sin esperar a nadie.

## Convenciones

- **No editar archivos FIJOS:** `mia_agents/**`, `tests/conformance/**`.
- Una rama por feature: `m1/agent-loop` (Nico), `m1/tools` (Vale), `m1/integration` (Fede). Merge a
  `main` vía PR chico.
- Correr `pytest tests/conformance/test_m1.py` antes de cada PR.
- No commitear `.env`, credenciales ni `.venv/`.
- Tools devuelven siempre `str`. Type hints en todo. Python 3.10+.

## Definition of Done compartida (M1)

- [ ] `pytest tests/conformance/test_m1.py` en verde.
- [ ] Las 3 tools implementadas y descubiertas por el registro.
- [ ] `run` corta por texto-final y por `max_iterations`; arma bien los `AgentStep`.
- [ ] Tool desconocida y argumentos inválidos no rompen el agente.
- [ ] ≥1 escenario propio con 2+ tools.
- [ ] Informe (diagrama + diseño de interfaz + limitaciones).
