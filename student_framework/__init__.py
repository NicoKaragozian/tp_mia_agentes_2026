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
    ):
        if clave in config:
            kwargs[clave] = config[clave]

    agent = MyAgent(**kwargs)

    # Registro por auto-descubrimiento: cada módulo en `tools/` que exponga
    # `TOOLS = [(fn, schema)]` se recolecta en `REGISTRY`. Agregar una tool
    # NO requiere tocar este archivo (ver student_framework/tools/__init__.py).
    #
    # `tools_por_defecto=False` devuelve el agente sin ninguna herramienta,
    # para que quien lo construye registre solo las del dominio. Lo pide la
    # evaluación del M3: al correr la sala de escape, las tools de M1/M2
    # (calculadora, lector, contador de palabras) son distractores que no
    # resuelven nada, ocupan contexto en cada llamada y ensucian la medición.
    # El valor por defecto es `True`, así que el comportamiento de M1/M2 y de
    # `mia_world.cli` no cambia.
    if config.get("tools_por_defecto", True):
        from student_framework.tools import REGISTRY

        for tool, schema in REGISTRY:
            agent.register_tool(tool, schema)

    return agent
