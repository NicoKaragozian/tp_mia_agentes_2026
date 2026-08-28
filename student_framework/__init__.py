"""Paquete propio del grupo.

Implementen el agente en `agent.py` y registren sus herramientas a
continuación, en `build_agent`. Tanto el runner de la CLI como los tests
de conformidad llaman a `build_agent`, por lo que esta es la única puerta
de entrada pública de su entrega.
"""

from __future__ import annotations

from typing import Any

from mia_agents.llm_client import LLMClient
from mia_agents.protocols import Agent

from .agent import MyAgent


def build_agent(config: dict[str, Any] | None = None) -> Agent:
    """Construye y configura su agente.

    `config` es opcional. Si se proporciona `config["llm_client"]`, el
    agente debe usarlo (así es como los tests de conformidad inyectan un
    cliente mock). Si no, se construye a partir del entorno.

    TODO (M1): instancien su agente y llamen a `agent.register_tool(...)`
    por cada una de sus herramientas antes de devolverlo.
    """

    config = config or {} #NO CAMBIAR
    llm = config.get("llm_client") or LLMClient.from_env() #NO CAMBIAR
    kwargs: dict[str, Any] = {"llm_client": llm} #NO CAMBIAR
    
    # Parámetros opcionales del agente: se rutean solo si vienen en config,
    # así los defaults viven en un único lugar (el constructor de MyAgent).
    for clave in (
        "system_prompt",
        "max_iterations",
        "max_history_messages",
        "max_retries",
        "retry_base_delay",
        "memoria_de_acciones",
        "bloquear_repeticiones",
        "planificar",
        "reflexionar",
    ):
        if clave in config:
            kwargs[clave] = config[clave]

    agent = MyAgent(**kwargs)

    # Registro por auto-descubrimiento: cada módulo en `tools/` que exponga
    # `TOOLS = [(fn, schema)]` se recolecta en `REGISTRY`. Agregar una tool
    # NO requiere tocar este archivo (ver student_framework/tools/__init__.py).
    #
    # `tools_por_defecto=False` devuelve el agente sin ninguna herramienta,
    # para que quien lo construye registre solo las del dominio. Lo usa la
    # evaluación del M3: al correr la sala de escape, las tools de M1/M2
    # (calculadora, lector, contador de palabras) no resuelven nada.
    #
    # Una versión anterior de este comentario afirmaba además que distraen al
    # modelo y le cuestan contexto. E9 lo midió y es falso: con 50 corridas por
    # rama, agregarlas dio 39/50 contra 36/50 sin ellas (p = 0,65), con un 7 %
    # más de tokens de entrada. Se las excluye por higiene experimental, una
    # condición menos que explicar, y no porque perjudiquen.
    # El valor por defecto es `True`, así que el comportamiento de M1/M2 y de
    # `mia_world.cli` no cambia.
    if config.get("tools_por_defecto", True):
        from student_framework.tools import REGISTRY

        for tool, schema in REGISTRY:
            agent.register_tool(tool, schema)

    return agent
