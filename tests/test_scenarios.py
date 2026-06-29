"""Escenarios de prueba propios (M1).

Demuestran el agente usando dos o más herramientas en una sola corrida.
Usan el MockLLMClient para guionar las decisiones del LLM de forma determinista.
"""

from __future__ import annotations

import json

from mia_agents.testing import MockLLMClient
from mia_agents.types import LLMResponse, ToolCall

from student_framework import build_agent


def test_escenario_dos_herramientas():
    """El agente usa calculator y luego word_counter en una misma corrida."""

    # Guionamos qué va a "decir" el LLM en cada turno (en orden):
    mock = MockLLMClient([
        # Turno 1: el LLM decide usar la calculadora
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(id="c1", name="calculadora",
                         arguments=json.dumps({"operando_a": 10, "operando_b": 5, "operador": "+"})),
            ],
        ),
        # Turno 2: el LLM decide contar palabras de una frase
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(id="c2", name="word_counter",
                         arguments=json.dumps({"text": "el agente funciona bien"})),
            ],
        ),
        # Turno 3: el LLM da la respuesta final (sin tool_calls)
        LLMResponse(content="Listo: la suma es 15 y la frase tiene 4 palabras."),
    ])

    agent = build_agent({"llm_client": mock})
    result = agent.run("Sumá 10 + 5 y contá las palabras de 'el agente funciona bien'.")

    # El LLM fue llamado 3 veces (2 tools + respuesta final)
    assert mock.call_count == 3

    # Se registraron exactamente 2 pasos (uno por herramienta)
    assert len(result.steps) == 2

    # Primer paso: la calculadora devolvió 15
    assert result.steps[0].tool_name == "calculadora"
    assert result.steps[0].tool_output == "15"
    assert result.steps[0].error is None

    # Segundo paso: el contador devolvió 4
    assert result.steps[1].tool_name == "word_counter"
    assert result.steps[1].tool_output == "4"
    assert result.steps[1].error is None

    # La respuesta final es el texto del último turno
    assert result.answer == "Listo: la suma es 15 y la frase tiene 4 palabras."