"""Tests de conformidad del Milestone 1.

Estos tests deben pasar para aprobar el M1, pero **no son la lista completa**:
la corrección ejecuta además otros casos sobre el mismo contrato. El contrato
de M1 está descrito de punta a punta en `ENUNCIADO_M1.md`; tomen ese documento
como la definición de "aprobado" y no se limiten a pasar este archivo.

No modifiquen este archivo. Usa un `MockLLMClient` determinista (sin claves de
API), por lo que pueden ejecutarlo en cualquier máquina.
"""

from __future__ import annotations

import json

import pytest

from mia_agents.protocols import Agent
from mia_agents.testing import MockLLMClient, make_recording_tool
from mia_agents.types import AgentResult, AgentStep, LLMResponse, ToolCall, ToolSchema

from student_framework import build_agent


def _agent_with(mock: MockLLMClient) -> Agent:
    return build_agent({"llm_client": mock})


def test_build_agent_factory_exists() -> None:
    mock = MockLLMClient([LLMResponse(content="hola")])
    agent = _agent_with(mock)
    assert isinstance(agent, Agent)


def test_run_returns_agent_result() -> None:
    mock = MockLLMClient([LLMResponse(content="hola")])
    agent = _agent_with(mock)
    result = agent.run("hola")
    assert isinstance(result, AgentResult)


def test_no_tool_no_loop() -> None:
    """Si el LLM devuelve texto sin tool_calls, el agente devuelve ese texto en un único turno."""
    mock = MockLLMClient([LLMResponse(content="La respuesta es 4.")])
    agent = _agent_with(mock)
    result = agent.run("¿cuánto es 2+2?")
    assert result.answer == "La respuesta es 4."
    assert result.steps == []
    assert mock.call_count == 1


def test_register_tool_signature() -> None:
    """register_tool acepta (callable, ToolSchema) y expone la herramienta al LLM."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient([LLMResponse(content="hecho")])
    agent = _agent_with(mock)
    agent.register_tool(tool, schema)
    agent.run("disparar")
    sent_tools = mock.calls[0]["tools"]
    assert sent_tools is not None, "el agente debería pasar los esquemas de herramientas al cliente LLM"
    names = [
        t.name if isinstance(t, ToolSchema) else t.get("name") for t in sent_tools
    ]
    assert schema.name in names


def test_tool_is_executed_when_called() -> None:
    """Cuando el LLM emite un tool_call, el agente ejecuta el callable y vuelca el resultado."""
    tool, schema = make_recording_tool(return_value="recorded:hola")
    mock = MockLLMClient(
        [
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="c1", name=schema.name, arguments=json.dumps({"text": "hola"}))
                ],
            ),
            LLMResponse(content="La herramienta se ejecutó."),
        ]
    )
    agent = _agent_with(mock)
    agent.register_tool(tool, schema)
    result = agent.run("invoca la herramienta")

    assert tool.calls == [{"text": "hola"}]
    assert result.answer == "La herramienta se ejecutó."
    assert len(result.steps) == 1
    assert result.steps[0].tool_name == schema.name

