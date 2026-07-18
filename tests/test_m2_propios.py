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

import pytest
from pydantic import BaseModel

from mia_agents.testing import MockLLMClient, make_recording_tool
from mia_agents.tool_schema import FINAL_RESULT_TOOL_NAME
from mia_agents.types import LLMResponse, ToolCall

from student_framework import build_agent
from student_framework.agent import SalidaEstructuradaError


class Respuesta(BaseModel):
    """Schema chico para los tests de salida estructurada."""

    valor: int
    comentario: str


def _final_result(arguments: dict | str, call_id: str = "fr-1") -> LLMResponse:
    """Respuesta guionada: el LLM invoca `final_result` con esos argumentos."""
    if isinstance(arguments, dict):
        arguments = json.dumps(arguments)
    return LLMResponse(
        content=None,
        tool_calls=[
            ToolCall(id=call_id, name=FINAL_RESULT_TOOL_NAME, arguments=arguments)
        ],
    )


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


# ---------------------------------------------------------------------------
# Salida estructurada: modos de fallo y reparación
# ---------------------------------------------------------------------------


def test_structured_call_repara_texto_libre():
    """Texto libre => mensaje user de reparación => el modelo se corrige."""
    mock = MockLLMClient(
        [
            LLMResponse(content="claro, el valor es 7"),
            _final_result({"valor": 7, "comentario": "ok"}),
        ]
    )
    agent = build_agent({"llm_client": mock})

    parsed = agent.structured_call(prompt="dame un objeto", schema=Respuesta)

    assert isinstance(parsed, Respuesta) and parsed.valor == 7
    assert mock.call_count == 2
    # El segundo intento debe ver la instrucción de reparación como user.
    reparacion = mock.calls[1]["messages"][-1]
    assert reparacion["role"] == "user"
    assert FINAL_RESULT_TOOL_NAME in reparacion["content"]


def test_structured_call_repara_tool_alucinada():
    """Un tool_call a otra herramienta se responde con error y se reintenta."""
    mock = MockLLMClient(
        [
            LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="x1", name="calculadora", arguments="{}")
                ],
            ),
            _final_result({"valor": 1, "comentario": "ok"}),
        ]
    )
    agent = build_agent({"llm_client": mock})

    parsed = agent.structured_call(prompt="dame un objeto", schema=Respuesta)

    assert parsed.valor == 1
    assert mock.call_count == 2
    # La reparación viajó como respuesta de tool al call alucinado.
    ultimo = mock.calls[1]["messages"][-1]
    assert ultimo["role"] == "tool" and ultimo["tool_call_id"] == "x1"


def test_structured_call_repara_json_invalido():
    """Argumentos que ni siquiera son JSON disparan la misma reparación."""
    mock = MockLLMClient(
        [
            _final_result("{esto no es json"),
            _final_result({"valor": 3, "comentario": "ok"}, call_id="fr-2"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    parsed = agent.structured_call(prompt="dame un objeto", schema=Respuesta)

    assert parsed.valor == 3
    assert mock.call_count == 2


def test_structured_call_respeta_la_ventana():
    """El tope de mensajes rige también dentro de structured_call."""
    tope = 4
    mock = MockLLMClient(
        [
            LLMResponse(content="hola"),  # run previo para poblar historial
            LLMResponse(content="texto libre 1"),
            LLMResponse(content="texto libre 2"),
            _final_result({"valor": 9, "comentario": "ok"}),
        ]
    )
    agent = build_agent({"llm_client": mock, "max_history_messages": tope})

    agent.run("un turno previo cualquiera")
    parsed = agent.structured_call(
        prompt="dame un objeto", schema=Respuesta, max_repair_attempts=3
    )

    assert parsed.valor == 9
    for llamada in mock.calls:
        assert len(llamada["messages"]) <= tope, (
            f"structured_call superó el tope: {llamada['messages']!r}"
        )


def test_structured_call_persiste_solo_el_intercambio_limpio():
    """El prompt y el resultado validado entran a la conversación; los
    intentos fallidos de reparación no la contaminan."""
    mock = MockLLMClient(
        [
            LLMResponse(content="bla bla texto libre"),
            _final_result({"valor": 5, "comentario": "listo"}),
            LLMResponse(content="respuesta posterior"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    agent.structured_call(prompt="calculá el objeto", schema=Respuesta)
    agent.run("¿qué valor habías calculado?")

    payload = str(mock.calls[-1]["messages"])
    assert "calculá el objeto" in payload, "el prompt debe quedar en la conversación"
    assert '"valor":5' in payload.replace(" ", ""), (
        "el resultado validado debe quedar en la conversación"
    )
    assert "bla bla" not in payload, "los intentos fallidos no se persisten"


def test_structured_call_fallido_no_toca_el_historial():
    """Si se agotan los reintentos, la conversación queda como estaba."""
    mock = MockLLMClient(
        [
            LLMResponse(content="no"),
            LLMResponse(content="tampoco"),
            LLMResponse(content="menos"),
            LLMResponse(content="respuesta posterior"),
        ]
    )
    agent = build_agent({"llm_client": mock})

    with pytest.raises(SalidaEstructuradaError):
        agent.structured_call(prompt="dame un objeto", schema=Respuesta)

    agent.run("seguimos")
    payload = str(mock.calls[-1]["messages"])
    assert "dame un objeto" not in payload
    assert "seguimos" in payload


# ---------------------------------------------------------------------------
# Tracking de tokens
# ---------------------------------------------------------------------------


def test_tokens_quedan_en_none_si_nadie_reporto():
    """Un mock sin tokens programados no debe inventar ceros."""
    mock = MockLLMClient([LLMResponse(content="hola")])
    agent = build_agent({"llm_client": mock})

    result = agent.run("hola")

    assert result.input_tokens is None
    assert result.output_tokens is None


def test_tokens_se_reinician_en_cada_run():
    """El enunciado pide acumular 'durante una llamada a run': el segundo
    run reporta solo sus propios tokens, no arrastra los del primero."""
    mock = MockLLMClient(
        [
            LLMResponse(content="r1", input_tokens=100, output_tokens=10),
            LLMResponse(content="r2", input_tokens=7, output_tokens=3),
        ]
    )
    agent = build_agent({"llm_client": mock})

    primero = agent.run("uno")
    segundo = agent.run("dos")

    assert (primero.input_tokens, primero.output_tokens) == (100, 10)
    assert (segundo.input_tokens, segundo.output_tokens) == (7, 3)


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
