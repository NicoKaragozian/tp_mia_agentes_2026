"""Tests de conformidad del Milestone 2.

Para ejecutarlos durante el M2:

    pytest tests/conformance/test_m2.py

Estos tests deben pasar para aprobar el M2, pero **no son la lista completa**:
la corrección ejecuta además otros casos sobre el mismo contrato. El contrato
de M2 está descrito de punta a punta en `ENUNCIADO_M2.md`; tomen ese documento
como la definición de "aprobado" y no se limiten a pasar este archivo.

No modifiquen este archivo. Usa un `MockLLMClient` determinista (sin claves de
API), por lo que pueden ejecutarlo en cualquier máquina.
"""

from __future__ import annotations

import json

import pytest

from mia_agents.testing import MockLLMClient
from mia_agents.tool_schema import FINAL_RESULT_TOOL_NAME
from mia_agents.types import LLMResponse, ToolCall, ToolSchema

from student_framework import build_agent


def _final_result_response(
    arguments: dict[str, object] | str,
    *,
    call_id: str = "fr-1",
) -> LLMResponse:
    if isinstance(arguments, dict):
        arguments = json.dumps(arguments)
    return LLMResponse(
        content=None,
        tool_calls=[
            ToolCall(
                id=call_id,
                name=FINAL_RESULT_TOOL_NAME,
                arguments=arguments,
            )
        ],
    )


def _tool_names(tools: list[ToolSchema] | list[dict[str, object]] | None) -> list[str]:
    if not tools:
        return []
    return [
        t.name if isinstance(t, ToolSchema) else str(t.get("name"))
        for t in tools
    ]


# ---------------------------------------------------------------------------
# Statefulness y gestión del historial
# ---------------------------------------------------------------------------


def test_agent_is_stateful_across_runs() -> None:
    """Llamadas sucesivas a run(...) continúan la misma conversación.

    Comprobamos statefulness pidiendo al agente dos turnos y verificando
    que en el segundo turno los mensajes enviados al LLM incluyen el
    contenido del primer turno.
    """
    mock = MockLLMClient(
        [
            LLMResponse(content="respuesta al primer turno"),
            LLMResponse(content="respuesta al segundo turno"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    agent.run("primer turno: recuerda el código ALFA-7")
    agent.run("segundo turno: ¿cuál era el código?")

    second_call_payload = str(mock.calls[1]["messages"])
    assert "primer turno" in second_call_payload or "ALFA-7" in second_call_payload, (
        "el segundo turno debe ver el contenido del primero — el agente debe ser estatal"
    )


def test_bounded_history_growth() -> None:
    """La lista de mensajes enviada al LLM nunca supera max_history_messages.

    Configuramos un presupuesto deliberadamente pequeño. Una
    implementación naíf que apila el historial sin recortarlo lo supera
    rápidamente. Cualquier estrategia razonable (ventana deslizante,
    resumen, recuperación) lo respeta.
    """
    budget = 6
    mock = MockLLMClient(
        [LLMResponse(content=f"respuesta {i}") for i in range(30)]
    )
    agent = build_agent({"llm_client": mock, "max_history_messages": budget})

    for i in range(20):
        agent.run(f"turno {i}: cuéntame algo")

    max_seen = max(len(call["messages"]) for call in mock.calls)
    assert max_seen <= budget, (
        f"el historial creció hasta {max_seen} mensajes; el presupuesto era {budget}. "
        "Una estrategia de memoria razonable debería respetar este límite."
    )


# ---------------------------------------------------------------------------
# Salida estructurada (`final_result` obligatorio)
# ---------------------------------------------------------------------------


def test_structured_call_offers_final_result_tool() -> None:
    """La primera llamada de `structured_call` debe exponer `final_result`."""
    from pydantic import BaseModel

    class Answer(BaseModel):
        result: int

    mock = MockLLMClient([_final_result_response({"result": 1})])
    agent = build_agent({"llm_client": mock})
    agent.structured_call(prompt="dame un objeto", schema=Answer)

    tools = mock.calls[0]["tools"]
    assert FINAL_RESULT_TOOL_NAME in _tool_names(tools), (
        f"esperado tool {FINAL_RESULT_TOOL_NAME!r} en la primera llamada, "
        f"obtuvo {_tool_names(tools)!r}"
    )


def test_structured_output_max_retries() -> None:
    """Tras agotar reintentos, `structured_call` debe levantar una excepción.

    El tipo exacto se deja abierto — pueden ser `ValidationError`,
    `JSONDecodeError`, o una excepción específica del estudiante. Lo que
    no se acepta es devolver `None`, devolver una instancia parcial, o
    colgarse en bucle.
    """
    from pydantic import BaseModel

    class Answer(BaseModel):
        result: int

    mock = MockLLMClient(
        [
            LLMResponse(content="no JSON 1"),
            LLMResponse(content="no JSON 2"),
            LLMResponse(content="no JSON 3"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    with pytest.raises(Exception):
        agent.structured_call(
            prompt="dame un objeto",
            schema=Answer,
            max_repair_attempts=2,
        )

    assert mock.call_count == 3, (
        "con max_repair_attempts=2 esperamos 1 intento inicial + 2 reparaciones"
    )


def test_structured_output_repairs_schema_validation_error() -> None:
    """Argumentos de `final_result` inválidos para el schema deben repararse."""
    from pydantic import BaseModel

    class Answer(BaseModel):
        result: int
        comment: str

    mock = MockLLMClient(
        [
            _final_result_response({"result": "cuarenta y dos", "comment": "x"}),
            _final_result_response({"result": 42, "comment": "ok"}, call_id="fr-2"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    parsed = agent.structured_call(prompt="dame un objeto", schema=Answer)

    assert isinstance(parsed, Answer)
    assert parsed.result == 42
    assert parsed.comment == "ok"
    assert mock.call_count == 2



# ---------------------------------------------------------------------------
# Tracking de tokens
# ---------------------------------------------------------------------------


def test_token_accounting() -> None:
    """`AgentResult.{input,output}_tokens` deben sumar lo reportado por el
    cliente LLM a lo largo de la llamada a `run`.

    Si ninguna `LLMResponse` reporta tokens, el agente puede devolver `None`
    en ambos campos. Si alguna lo hace, debe sumar lo reportado tratando
    `None` por respuesta como 0.
    """
    from mia_agents.testing import make_recording_tool
    from mia_agents.types import ToolCall
    import json

    tool, schema = make_recording_tool(return_value="ok")
    mock = MockLLMClient(
        [
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="c1", name=schema.name, arguments=json.dumps({"text": "x"}))
                ],
                input_tokens=100,
                output_tokens=50,
            ),
            LLMResponse(content="hecho", input_tokens=200, output_tokens=30),
        ]
    )
    agent = build_agent({"llm_client": mock})
    agent.register_tool(tool, schema)
    result = agent.run("dispara la herramienta y termina")

    assert result.input_tokens == 300, (
        f"esperado 100+200=300, obtuvo {result.input_tokens!r}"
    )
    assert result.output_tokens == 80, (
        f"esperado 50+30=80, obtuvo {result.output_tokens!r}"
    )


def test_token_accounting_treats_missing_values_as_zero_after_first_report() -> None:
    """Una vez hay tokens reportados, las respuestas sin tokens suman 0."""
    from mia_agents.testing import make_recording_tool
    from mia_agents.types import ToolCall
    import json

    tool, schema = make_recording_tool(return_value="ok")
    mock = MockLLMClient(
        [
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name=schema.name,
                        arguments=json.dumps({"text": "x"}),
                    )
                ],
                input_tokens=100,
            ),
            LLMResponse(content="hecho", output_tokens=30),
        ]
    )
    agent = build_agent({"llm_client": mock})
    agent.register_tool(tool, schema)
    result = agent.run("dispara la herramienta y termina")

    assert result.input_tokens == 100
    assert result.output_tokens == 30
