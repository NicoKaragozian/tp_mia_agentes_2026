"""Tests del OllamaProvider — mockean `ollama.Client`, no requieren un servidor.

Verifican la traducción de mensajes, herramientas, formato de respuesta y
metadata (tokens, raw_response) entre el formato interno del framework y el
SDK de Ollama.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from mia_agents.llm_client import OllamaProvider


def _fake_response(
    text: str | None = None,
    tool_calls: list | None = None,
    prompt_eval_count: int = 10,
    eval_count: int = 5,
    done_reason: str | None = "stop",
) -> dict:
    return {
        "message": {
            "role": "assistant",
            "content": text,
            "tool_calls": tool_calls or [],
        },
        "prompt_eval_count": prompt_eval_count,
        "eval_count": eval_count,
        "done_reason": done_reason,
    }


def _fake_tool_call(name: str, arguments) -> dict:
    return {"function": {"name": name, "arguments": arguments}}


@pytest.fixture
def fake_client():
    with patch("mia_agents.llm_client.ollama.Client") as cls:
        instance = MagicMock()
        cls.return_value = instance
        yield instance


# ---------------------------------------------------------------------------
# Respuesta de texto simple
# ---------------------------------------------------------------------------


def test_simple_text_response_parsed(fake_client) -> None:
    fake_client.chat.return_value = _fake_response(text="Hola mundo")
    provider = OllamaProvider(model="llama3.1")

    result = provider.chat(messages=[{"role": "user", "content": "hola"}])

    assert result.content == "Hola mundo"
    assert result.tool_calls == []
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.raw_response is not None
    assert result.raw_response.get("done_reason") == "stop"


def test_empty_content_becomes_none(fake_client) -> None:
    fake_client.chat.return_value = _fake_response(text="")
    provider = OllamaProvider(model="llama3.1")
    result = provider.chat(messages=[{"role": "user", "content": "x"}])
    assert result.content is None


# ---------------------------------------------------------------------------
# Tool calls — entrante (respuesta del modelo) y saliente (historial)
# ---------------------------------------------------------------------------


def test_tool_call_response_synthesizes_id(fake_client) -> None:
    tc = _fake_tool_call(name="examine", arguments={"target": "alfombra"})
    fake_client.chat.return_value = _fake_response(text=None, tool_calls=[tc])
    provider = OllamaProvider(model="llama3.1")

    result = provider.chat(messages=[{"role": "user", "content": "explora"}])

    assert result.content is None
    assert len(result.tool_calls) == 1
    out_tc = result.tool_calls[0]
    assert out_tc.name == "examine"
    assert json.loads(out_tc.arguments) == {"target": "alfombra"}
    assert out_tc.id.startswith("call_"), "el provider debe sintetizar un id"


def test_tool_call_string_arguments_passthrough(fake_client) -> None:
    """Algunos modelos emiten `arguments` como string JSON en vez de dict."""
    tc = _fake_tool_call(name="examine", arguments='{"target":"x"}')
    fake_client.chat.return_value = _fake_response(text=None, tool_calls=[tc])
    provider = OllamaProvider(model="llama3.1")

    result = provider.chat(messages=[{"role": "user", "content": "x"}])

    assert json.loads(result.tool_calls[0].arguments) == {"target": "x"}


def test_outgoing_history_translates_tool_calls(fake_client) -> None:
    """Mensajes de historial con tool_calls deben llegar a Ollama con args como dict."""
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1")

    provider.chat(
        messages=[
            {"role": "user", "content": "hola"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {
                            "name": "examine",
                            "arguments": json.dumps({"target": "alfombra"}),
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "c1", "content": "Hay una llave."},
        ]
    )

    sent = fake_client.chat.call_args.kwargs["messages"]
    assistant_msg = sent[1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["tool_calls"][0]["function"]["arguments"] == {
        "target": "alfombra"
    }
    assert "id" not in assistant_msg["tool_calls"][0]
    assert sent[2] == {"role": "tool", "content": "Hay una llave."}


def test_outgoing_handles_malformed_json_arguments(fake_client) -> None:
    """Si un modelo previo dejó argumentos malformados, no debe explotar."""
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1")

    provider.chat(
        messages=[
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "x", "arguments": "{not json"}}
                ],
            }
        ]
    )

    sent = fake_client.chat.call_args.kwargs["messages"]
    assert sent[0]["tool_calls"][0]["function"]["arguments"] == {}


# ---------------------------------------------------------------------------
# Mensaje de sistema, herramientas y opciones
# ---------------------------------------------------------------------------


def test_system_prompt_prepended(fake_client) -> None:
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1")

    provider.chat(
        messages=[{"role": "user", "content": "hola"}],
        system="Eres un asistente.",
    )

    sent = fake_client.chat.call_args.kwargs["messages"]
    assert sent[0] == {"role": "system", "content": "Eres un asistente."}
    assert sent[1] == {"role": "user", "content": "hola"}


def test_embedded_system_in_messages_is_dropped(fake_client) -> None:
    """Si el agente embebe system en la lista de mensajes, se ignora (lo
    enviamos por el parámetro `system`)."""
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1")

    provider.chat(
        messages=[
            {"role": "system", "content": "viejo system embebido"},
            {"role": "user", "content": "hola"},
        ],
        system="nuevo system",
    )

    sent = fake_client.chat.call_args.kwargs["messages"]
    assert sent == [
        {"role": "system", "content": "nuevo system"},
        {"role": "user", "content": "hola"},
    ]


def test_tools_formatted_for_ollama_function_calls(fake_client) -> None:
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1")

    provider.chat(
        messages=[{"role": "user", "content": "x"}],
        tools=[
            {
                "name": "look",
                "description": "Mira",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
    )

    sent_tools = fake_client.chat.call_args.kwargs["tools"]
    assert sent_tools == [
        {
            "type": "function",
            "function": {
                "name": "look",
                "description": "Mira",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]


def test_options_include_num_ctx_and_temperature(fake_client) -> None:
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1", num_ctx=32768)

    provider.chat(messages=[{"role": "user", "content": "x"}], temperature=0.5)

    options = fake_client.chat.call_args.kwargs["options"]
    assert options == {"temperature": 0.5, "num_ctx": 32768}


# ---------------------------------------------------------------------------
# response_format
# ---------------------------------------------------------------------------


def test_response_format_schema_passed(fake_client) -> None:
    schema = {"type": "object", "properties": {"k": {"type": "integer"}}}
    fake_client.chat.return_value = _fake_response(text='{"k":1}')
    provider = OllamaProvider(model="llama3.1")

    provider.chat(
        messages=[{"role": "user", "content": "x"}],
        response_format=schema,
    )

    assert fake_client.chat.call_args.kwargs["format"] == schema


def test_no_response_format_means_no_format_kwarg(fake_client) -> None:
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1")

    provider.chat(messages=[{"role": "user", "content": "x"}])

    assert "format" not in fake_client.chat.call_args.kwargs


def test_default_format_used_when_no_explicit(fake_client) -> None:
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1", default_format=schema)

    provider.chat(messages=[{"role": "user", "content": "x"}])

    assert fake_client.chat.call_args.kwargs["format"] == schema


def test_explicit_format_overrides_default(fake_client) -> None:
    schema = {"type": "object"}
    default_schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
    fake_client.chat.return_value = _fake_response(text="ok")
    provider = OllamaProvider(model="llama3.1", default_format=default_schema)

    provider.chat(messages=[{"role": "user", "content": "x"}], response_format=schema)

    assert fake_client.chat.call_args.kwargs["format"] == schema


# ---------------------------------------------------------------------------
# Tolerancia a formas alternativas de respuesta (futuras versiones del SDK)
# ---------------------------------------------------------------------------


def test_dict_response_form_handled(fake_client) -> None:
    """Si una versión futura del SDK devuelve dicts en vez de Pydantic, seguimos."""
    fake_client.chat.return_value = {
        "message": {"role": "assistant", "content": "Hola", "tool_calls": []},
        "prompt_eval_count": 7,
        "eval_count": 3,
        "done_reason": "stop",
    }
    provider = OllamaProvider(model="llama3.1")

    result = provider.chat(messages=[{"role": "user", "content": "hi"}])

    assert result.content == "Hola"
    assert result.input_tokens == 7
    assert result.output_tokens == 3
    assert result.raw_response is not None
    assert result.raw_response.get("done_reason") == "stop"
