"""Tests propios del Milestone 2.

Complementan a `tests/conformance/test_m2.py` cubriendo los bordes de
nuestro diseño que la conformidad no mira:

- la ventana deslizante nunca rompe pares <tool_call, tool_response>;
- el último mensaje del usuario entra SIEMPRE (invariante de recencia),
  incluso con presupuestos mínimos o runs con muchas tools;
- el ancla (primer mensaje del usuario) sobrevive al recorte.

Como en el resto de la suite, todo corre con `MockLLMClient` (sin API).
"""

from __future__ import annotations

import json

from mia_agents.testing import MockLLMClient, make_recording_tool
from mia_agents.types import LLMResponse, ToolCall

from student_framework import build_agent


def _tool_call(schema_name: str, call_id: str) -> LLMResponse:
    """Respuesta guionada: el LLM pide una tool con argumentos triviales."""
    return LLMResponse(
        content=None,
        tool_calls=[
            ToolCall(
                id=call_id,
                name=schema_name,
                arguments=json.dumps({"text": "x"}),
            )
        ],
    )


def _sin_tools_huerfanas(messages: list[dict]) -> bool:
    """True si todo mensaje `tool` tiene antes su turno assistant con ese id."""
    ids_declarados: set[str] = set()
    for m in messages:
        if m.get("role") == "assistant":
            for tc in m.get("tool_calls") or []:
                ids_declarados.add(tc.get("id"))
        elif m.get("role") == "tool":
            if m.get("tool_call_id") not in ids_declarados:
                return False
    return True


# ---------------------------------------------------------------------------
# Estado conversacional
# ---------------------------------------------------------------------------


def test_conversacion_persiste_a_lo_largo_de_varios_runs():
    """El tercer turno ve el contenido de los dos anteriores."""
    mock = MockLLMClient(
        [
            LLMResponse(content="anotado"),
            LLMResponse(content="también anotado"),
            LLMResponse(content="el código era ROJO-9"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    agent.run("guardá el código ROJO-9")
    agent.run("y también el código AZUL-2")
    agent.run("¿cuál era el primer código?")

    payload = str(mock.calls[2]["messages"])
    assert "ROJO-9" in payload, "el turno 3 debe ver el contenido del turno 1"
    assert "AZUL-2" in payload, "el turno 3 debe ver el contenido del turno 2"


# ---------------------------------------------------------------------------
# Sliding window: tope, coherencia estructural y ancla
# ---------------------------------------------------------------------------


def test_tope_y_coherencia_con_tools_en_el_medio():
    """Con presupuesto chico y runs que usan tools, ninguna llamada supera
    el tope y ninguna ventana contiene resultados de tool huérfanos."""
    tope = 6
    tool, schema = make_recording_tool()
    respuestas: list[LLMResponse] = []
    for i in range(8):
        respuestas.append(_tool_call(schema.name, call_id=f"c{i}"))
        respuestas.append(LLMResponse(content=f"listo {i}"))
    mock = MockLLMClient(respuestas)
    agent = build_agent({"llm_client": mock, "max_history_messages": tope})
    agent.register_tool(tool, schema)

    for i in range(8):
        result = agent.run(f"turno {i}: usá la herramienta")
        assert result.answer == f"listo {i}"

    for llamada in mock.calls:
        messages = llamada["messages"]
        assert len(messages) <= tope, (
            f"una llamada envió {len(messages)} mensajes; el tope era {tope}"
        )
        assert _sin_tools_huerfanas(messages), (
            "la ventana dejó un resultado de tool sin su tool_call: "
            f"{messages!r}"
        )


def test_invariante_de_recencia_dentro_de_un_run_con_tools():
    """Aun cuando el presupuesto no cubre el turno completo de tools, el
    último mensaje del usuario sigue entrando en la llamada al LLM."""
    tope = 3
    tool, schema = make_recording_tool()
    mock = MockLLMClient(
        [
            LLMResponse(content="hola"),
            _tool_call(schema.name, call_id="c1"),
            LLMResponse(content="listo"),
        ]
    )
    agent = build_agent({"llm_client": mock, "max_history_messages": tope})
    agent.register_tool(tool, schema)

    agent.run("primer turno")
    agent.run("segundo turno: usá la herramienta")

    # La llamada que sigue a la ejecución de la tool (la última) trabaja
    # con historial [u1, a1, u2, assistant+tool_call, tool] y tope 3: el
    # recorte debe priorizar a u2 por encima del ancla u1.
    ultima = mock.calls[-1]["messages"]
    assert len(ultima) <= tope
    assert any(
        m.get("role") == "user" and "segundo turno" in str(m.get("content"))
        for m in ultima
    ), f"el último mensaje del usuario quedó fuera de la ventana: {ultima!r}"
    assert _sin_tools_huerfanas(ultima)


def test_ancla_conserva_el_primer_mensaje_del_usuario():
    """Cuando hay presupuesto de sobra para ancla + cola, el primer mensaje
    del usuario (goal) encabeza la ventana aunque el medio se descarte."""
    tope = 6
    mock = MockLLMClient([LLMResponse(content=f"r{i}") for i in range(10)])
    agent = build_agent({"llm_client": mock, "max_history_messages": tope})

    for i in range(10):
        agent.run(f"turno {i}")

    ultima = mock.calls[-1]["messages"]
    assert len(ultima) <= tope
    assert ultima[0]["role"] == "user" and "turno 0" in ultima[0]["content"], (
        f"la ventana debería arrancar con el goal (turno 0): {ultima!r}"
    )
    assert "turno 9" in str(ultima), "la cola reciente debe incluir el turno actual"


def test_presupuesto_minimo_envia_solo_el_ultimo_user():
    """Caso extremo tope=1: cada llamada lleva exactamente el último user."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient(
        [
            LLMResponse(content="a"),
            _tool_call(schema.name, call_id="c1"),
            LLMResponse(content="b"),
        ]
    )
    agent = build_agent({"llm_client": mock, "max_history_messages": 1})
    agent.register_tool(tool, schema)

    agent.run("uno")
    agent.run("dos: usá la herramienta")

    for llamada in mock.calls:
        messages = llamada["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
    assert "dos" in mock.calls[-1]["messages"][0]["content"]
