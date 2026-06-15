"""Tests del BedrockProvider — mockean `boto3.client`, no requieren AWS.

Verifican la traducción entre el formato interno del framework y el
formato de la API Converse de AWS Bedrock (mensajes, herramientas,
resultados, tokens, raw_response).
"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from mia_agents.llm_client import BedrockProvider
from mia_agents.types import ToolSchema


def _converse_response(
    text: str | None = None,
    tool_uses: list[dict] | None = None,
    input_tokens: int = 10,
    output_tokens: int = 5,
    stop_reason: str = "end_turn",
) -> dict:
    blocks: list[dict] = []
    if text is not None:
        blocks.append({"text": text})
    for tu in tool_uses or []:
        blocks.append({"toolUse": tu})
    return {
        "output": {"message": {"role": "assistant", "content": blocks}},
        "stopReason": stop_reason,
        "usage": {
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
            "totalTokens": input_tokens + output_tokens,
        },
    }


@pytest.fixture
def fake_client():
    with patch("mia_agents.llm_client.boto3.client") as factory:
        instance = MagicMock()
        factory.return_value = instance
        yield instance


@pytest.fixture
def provider(fake_client) -> BedrockProvider:
    return BedrockProvider(
        model="amazon.nova-lite-v1:0",
        region="us-east-1",
    )


# ---------------------------------------------------------------------------
# Construcción
# ---------------------------------------------------------------------------


def test_missing_model_id_raises(monkeypatch) -> None:
    monkeypatch.delenv("BEDROCK_MODEL_ID", raising=False)
    with pytest.raises(RuntimeError, match="BEDROCK_MODEL_ID"):
        BedrockProvider()


def test_constructor_uses_env_when_args_absent(fake_client, monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_MODEL_ID", "foo-model-id")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    provider = BedrockProvider()
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(messages=[{"role": "user", "content": "hola"}])
    assert fake_client.converse.call_args.kwargs["modelId"] == "foo-model-id"


# ---------------------------------------------------------------------------
# Respuesta de texto simple
# ---------------------------------------------------------------------------


def test_simple_text_response_parsed(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(
        text="Hola mundo", input_tokens=100, output_tokens=50
    )

    result = provider.chat(messages=[{"role": "user", "content": "hola"}])

    assert result.content == "Hola mundo"
    assert result.tool_calls == []
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.raw_response is not None
    assert result.raw_response.get("stopReason") == "end_turn"


def test_empty_content_becomes_none(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response()
    result = provider.chat(messages=[{"role": "user", "content": "x"}])
    assert result.content is None


def test_multiple_text_blocks_concatenated(provider, fake_client) -> None:
    fake_client.converse.return_value = {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "primera. "}, {"text": "segunda."}],
            }
        },
        "stopReason": "end_turn",
        "usage": {"inputTokens": 5, "outputTokens": 3, "totalTokens": 8},
    }
    result = provider.chat(messages=[{"role": "user", "content": "x"}])
    assert result.content == "primera. segunda."


# ---------------------------------------------------------------------------
# Tool calls — respuesta entrante (de Bedrock)
# ---------------------------------------------------------------------------


def test_tool_use_parsed_to_tool_call(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(
        text=None,
        tool_uses=[
            {
                "toolUseId": "tooluse_abc123",
                "name": "examine",
                "input": {"target": "alfombra"},
            }
        ],
        stop_reason="tool_use",
    )

    result = provider.chat(messages=[{"role": "user", "content": "explora"}])

    assert result.content is None
    assert len(result.tool_calls) == 1
    tc = result.tool_calls[0]
    assert tc.id == "tooluse_abc123"
    assert tc.name == "examine"
    assert json.loads(tc.arguments) == {"target": "alfombra"}
    assert result.raw_response is not None
    assert result.raw_response.get("stopReason") == "tool_use"


def test_tool_use_without_id_synthesizes_one(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(
        text=None,
        tool_uses=[{"name": "look", "input": {}}],
    )
    result = provider.chat(messages=[{"role": "user", "content": "x"}])
    assert result.tool_calls[0].id.startswith("call_")


# ---------------------------------------------------------------------------
# Mensaje saliente: usuario, asistente, herramientas
# ---------------------------------------------------------------------------


def test_user_message_wrapped_in_text_block(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(messages=[{"role": "user", "content": "hola"}])
    sent = fake_client.converse.call_args.kwargs["messages"]
    assert sent == [{"role": "user", "content": [{"text": "hola"}]}]


def test_system_prompt_goes_to_dedicated_field(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[{"role": "user", "content": "x"}],
        system="Eres un asistente.",
    )
    kwargs = fake_client.converse.call_args.kwargs
    assert kwargs["system"] == [{"text": "Eres un asistente."}]
    # System NO debería aparecer en messages.
    assert all(m["role"] != "system" for m in kwargs["messages"])


def test_assistant_with_tool_calls_translated_to_tooluse_blocks(
    provider, fake_client
) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[
            {"role": "user", "content": "hola"},
            {
                "role": "assistant",
                "content": "voy a examinar",
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
            {"role": "tool", "tool_call_id": "c1", "content": "Tienes una llave."},
        ]
    )

    sent = fake_client.converse.call_args.kwargs["messages"]
    # 0: user, 1: assistant w/ text+toolUse, 2: user w/ toolResult.
    assert sent[0]["role"] == "user"
    assert sent[1]["role"] == "assistant"
    blocks = sent[1]["content"]
    assert blocks[0] == {"text": "voy a examinar"}
    assert blocks[1] == {
        "toolUse": {
            "toolUseId": "c1",
            "name": "examine",
            "input": {"target": "alfombra"},
        }
    }
    assert sent[2] == {
        "role": "user",
        "content": [
            {
                "toolResult": {
                    "toolUseId": "c1",
                    "content": [{"text": "Tienes una llave."}],
                }
            }
        ],
    }


def test_multiple_tool_results_aggregated_in_one_user_message(
    provider, fake_client
) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "c1", "function": {"name": "a", "arguments": "{}"}},
                    {"id": "c2", "function": {"name": "b", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "c1", "content": "res-1"},
            {"role": "tool", "tool_call_id": "c2", "content": "res-2"},
        ]
    )

    sent = fake_client.converse.call_args.kwargs["messages"]
    tool_user_msg = sent[1]
    assert tool_user_msg["role"] == "user"
    assert len(tool_user_msg["content"]) == 2
    assert tool_user_msg["content"][0]["toolResult"]["toolUseId"] == "c1"
    assert tool_user_msg["content"][1]["toolResult"]["toolUseId"] == "c2"


def test_tool_arguments_string_parsed_to_dict_in_outgoing(
    provider, fake_client
) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "c1",
                        "function": {
                            "name": "x",
                            "arguments": '{"foo": "bar"}',
                        },
                    }
                ],
            }
        ]
    )
    sent = fake_client.converse.call_args.kwargs["messages"]
    assert sent[0]["content"][0]["toolUse"]["input"] == {"foo": "bar"}


# ---------------------------------------------------------------------------
# Esquemas de herramientas
# ---------------------------------------------------------------------------


def test_tools_wrapped_in_toolspec_with_inputschema_json(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[{"role": "user", "content": "x"}],
        tools=[
            {
                "name": "look",
                "description": "Mira la sala.",
                "parameters": {"type": "object", "properties": {}},
            }
        ],
    )
    tool_config = fake_client.converse.call_args.kwargs["toolConfig"]
    assert tool_config == {
        "tools": [
            {
                "toolSpec": {
                    "name": "look",
                    "description": "Mira la sala.",
                    "inputSchema": {
                        "json": {"type": "object", "properties": {}}
                    },
                }
            }
        ]
    }


def test_format_tools_accepts_tool_schema_instance(provider, fake_client) -> None:
    def look() -> str:
        """Mira la sala actual."""
        return "ok"

    schema = ToolSchema.from_callable(look)
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(messages=[{"role": "user", "content": "x"}], tools=[schema])
    spec = fake_client.converse.call_args.kwargs["toolConfig"]["tools"][0][
        "toolSpec"
    ]
    assert spec["name"] == "look"
    assert "Mira la sala" in spec["description"]
    assert spec["inputSchema"]["json"]["type"] == "object"


def test_no_tools_means_no_toolconfig_kwarg(provider, fake_client) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(messages=[{"role": "user", "content": "x"}])
    assert "toolConfig" not in fake_client.converse.call_args.kwargs


# ---------------------------------------------------------------------------
# inferenceConfig
# ---------------------------------------------------------------------------


def test_inference_config_includes_temperature_and_max_tokens(
    provider, fake_client
) -> None:
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[{"role": "user", "content": "x"}],
        temperature=0.7,
    )
    cfg = fake_client.converse.call_args.kwargs["inferenceConfig"]
    assert cfg["temperature"] == 0.7
    assert cfg["maxTokens"] == 4096  # default


def test_custom_max_tokens(fake_client) -> None:
    provider = BedrockProvider(model="m", region="r", max_tokens=8192)
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(messages=[{"role": "user", "content": "x"}])
    cfg = fake_client.converse.call_args.kwargs["inferenceConfig"]
    assert cfg["maxTokens"] == 8192


# ---------------------------------------------------------------------------
# response_format como JSON Schema
# ---------------------------------------------------------------------------


def test_response_format_not_handled_by_provider(provider, fake_client) -> None:
    """`response_format` es responsabilidad del agente en M2, no del provider."""
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }
    fake_client.converse.return_value = _converse_response(text="ok")
    provider.chat(
        messages=[{"role": "user", "content": "x"}],
        system="Respondé breve.",
        response_format=schema,
    )
    kwargs = fake_client.converse.call_args.kwargs
    assert kwargs["system"] == [{"text": "Respondé breve."}]
    assert "format" not in kwargs
    assert "responseFormat" not in kwargs
