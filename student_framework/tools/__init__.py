"""Registro de herramientas por auto-descubrimiento (M1).

Cada módulo de herramienta en este paquete expone una constante::

    TOOLS: list[tuple[Callable[..., str], ToolSchema]]

y este ``__init__`` los recolecta automáticamente en ``REGISTRY``.
``build_agent`` registra todo lo que haya en ``REGISTRY``, por lo que
**agregar una herramienta = crear su módulo con ``TOOLS``**, sin tocar
este archivo ni ``student_framework/__init__.py``. Así nadie edita el
archivo de otro y el trabajo queda desacoplado (ver CLAUDE.md).

Convención por módulo (plantilla viva en ``tools/example.py``)::

    from typing import Annotated
    from pydantic import Field
    from mia_agents.types import ToolSchema

    def mi_tool(arg: Annotated[str, Field(description="Qué hace.")]) -> str:
        \"\"\"Descripción de la herramienta para el LLM.\"\"\"
        return "resultado como string"

    mi_tool_schema = ToolSchema.from_callable(mi_tool)
    TOOLS = [(mi_tool, mi_tool_schema)]   # <- línea load-bearing: sin esto no se descubre

Garantías del descubrimiento (fail-fast con módulo culpable nombrado):
  - Orden determinista: módulos ordenados por nombre, así el orden en que
    se exponen las tools al LLM es estable entre máquinas.
  - Cada módulo de tool DEBE importar limpio en aislamiento. Si un módulo
    falla al importarse, se re-lanza ``ImportError`` nombrando el archivo
    (un módulo roto de un integrante no deja un traceback genérico).
  - ``TOOLS`` malformado o nombres de tool duplicados entre módulos cortan
    el arranque con un error que apunta al módulo culpable.
  - Un módulo sin ``TOOLS`` emite un ``warning`` (probable olvido); un
    ``TOOLS = []`` explícito se ignora en silencio (intención clara).
  - ``example`` está excluido: es ilustrativo, no una tool obligatoria.
    Si borran ``example.py`` pueden vaciar ``_EXCLUDE``.
"""

from __future__ import annotations

import importlib
import pkgutil
import warnings
from typing import Callable

from mia_agents.types import ToolSchema

#: Una entrada del registro: el callable de la tool y su esquema para el LLM.
ToolEntry = tuple[Callable[..., str], ToolSchema]

#: Módulos del paquete que NO se auto-descubren (ejemplos / helpers privados).
#: Si se borra example.py, este set puede quedar vacío.
_EXCLUDE = frozenset({"example"})


def _validate_entry(module: str, index: int, entry: object) -> ToolEntry:
    """Valida que ``entry`` sea ``(callable, ToolSchema)``, nombrando el módulo."""
    if not (isinstance(entry, tuple) and len(entry) == 2):
        raise TypeError(
            f"TOOLS malformado en tools/{module}.py: cada entrada debe ser una "
            f"tupla (callable, ToolSchema); TOOLS[{index}] = {entry!r}"
        )
    fn, schema = entry
    if not callable(fn):
        raise TypeError(
            f"TOOLS malformado en tools/{module}.py: TOOLS[{index}] — el primer "
            f"elemento debe ser un callable, recibí {fn!r}"
        )
    if not isinstance(schema, ToolSchema):
        raise TypeError(
            f"TOOLS malformado en tools/{module}.py: TOOLS[{index}] — el segundo "
            f"elemento debe ser un ToolSchema, recibí {schema!r}"
        )
    return fn, schema


def _discover() -> list[ToolEntry]:
    """Importa cada módulo del paquete y recolecta su constante ``TOOLS``."""
    registry: list[ToolEntry] = []
    seen: dict[str, str] = {}  # schema.name -> módulo que lo definió primero
    names = sorted(
        info.name
        for info in pkgutil.iter_modules(__path__)
        if info.name not in _EXCLUDE and not info.name.startswith("_")
    )
    for name in names:
        try:
            module = importlib.import_module(f"{__name__}.{name}")
        except Exception as exc:  # re-lanzar atribuyendo el módulo culpable
            raise ImportError(
                f"No se pudo importar la herramienta tools/{name}.py: {exc}"
            ) from exc

        if not hasattr(module, "TOOLS"):
            warnings.warn(
                f"tools/{name}.py no define TOOLS = [(fn, schema)]; se ignora. "
                f"¿Olvidaste exponerla? Ver tools/example.py.",
                stacklevel=2,
            )
            continue

        tools = module.TOOLS
        if not isinstance(tools, (list, tuple)):
            raise TypeError(
                f"TOOLS en tools/{name}.py debe ser una lista de (callable, "
                f"ToolSchema); recibí {tools!r}"
            )
        for index, entry in enumerate(tools):
            fn, schema = _validate_entry(name, index, entry)
            if schema.name in seen:
                raise ValueError(
                    f"Herramienta duplicada {schema.name!r}: definida en "
                    f"tools/{seen[schema.name]}.py y en tools/{name}.py. "
                    f"Renombrá una (ToolSchema.from_callable(fn, name=...))."
                )
            seen[schema.name] = name
            registry.append((fn, schema))
    return registry


#: Lista de ``(callable, ToolSchema)`` recolectada de todos los módulos de tools.
REGISTRY: list[ToolEntry] = _discover()

__all__ = ["REGISTRY", "ToolEntry"]
