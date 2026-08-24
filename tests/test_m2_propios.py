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
from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from mia_agents.testing import MockLLMClient, make_recording_tool
from mia_agents.tool_schema import FINAL_RESULT_TOOL_NAME
from mia_agents.types import LLMResponse, ToolCall, ToolSchema

from student_framework import build_agent
from student_framework.agent import SalidaEstructuradaError, _es_error_transitorio


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


def _empieza_en_user(messages: list[dict]) -> bool:
    """La API Converse de Bedrock rechaza una conversación que no arranca
    con un turno de usuario; la ventana nunca debe producir eso."""
    return bool(messages) and messages[0].get("role") == "user"


@pytest.mark.parametrize("tope", [1, 2, 3, 4, 5, 6, 7, 12])
def test_ventana_es_valida_para_los_proveedores_reales(tope: int):
    """Toda ventana debe empezar en `user`, no tener tools huérfanas y
    sobrevivir a los normalizadores de Ollama y Bedrock.

    La suite corre con `MockLLMClient`, que acepta cualquier lista de
    mensajes: sin este test, un formato inválido solo aparecería al correr
    contra un proveedor real.
    """
    from mia_agents.llm_client import BedrockProvider, OllamaProvider

    tool, schema = make_recording_tool()
    respuestas: list[LLMResponse] = []
    for i in range(5):
        respuestas += [_tool_call(schema.name, f"c{i}"), LLMResponse(content=f"ok {i}")]
    mock = MockLLMClient(respuestas)
    agent = build_agent({"llm_client": mock, "max_history_messages": tope})
    agent.register_tool(tool, schema)

    for i in range(5):
        agent.run(f"turno {i}: consulta con texto de relleno " + "x" * 40)

    for n, llamada in enumerate(mock.calls):
        messages = llamada["messages"]
        assert len(messages) <= tope, f"llamada {n}: {len(messages)} > {tope}"
        assert _empieza_en_user(messages), f"llamada {n} arranca en no-user: {messages!r}"
        assert _sin_tools_huerfanas(messages), f"llamada {n}: tool huérfana"
        # Los normalizadores reales no deben lanzar con nuestro formato.
        BedrockProvider._normalize_messages(messages)
        OllamaProvider._normalize_messages(messages, "system")


@pytest.mark.parametrize("tope", [2, 3, 4, 5, 7])
@pytest.mark.parametrize("previos", [0, 1, 4])
def test_el_prompt_sobrevive_a_las_reparaciones(tope: int, previos: int):
    """El prompt es el ancla mientras dura `structured_call`.

    Sin esto, en una conversación con historial y presupuesto ajustado el
    modelo recibía "corregí tu respuesta" sin la pregunta que debía
    responder, y las reparaciones quedaban condenadas a fallar.
    """
    mock = MockLLMClient(
        [LLMResponse(content=f"r{i}") for i in range(previos)]
        + [
            LLMResponse(content="texto libre"),
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="mal", name="otra_tool", arguments="{}")],
            ),
            _final_result('{"valor":', call_id="f1"),
            _final_result({"valor": 5, "comentario": "ok"}, call_id="f2"),
        ]
    )
    agent = build_agent({"llm_client": mock, "max_history_messages": tope})
    for i in range(previos):
        agent.run(f"previo {i}")

    desde = mock.call_count
    agent.structured_call(
        prompt="PROMPT-CLAVE", schema=Respuesta, max_repair_attempts=3
    )

    for n, llamada in enumerate(mock.calls[desde:]):
        messages = llamada["messages"]
        assert len(messages) <= tope
        assert _empieza_en_user(messages)
        assert "PROMPT-CLAVE" in str(messages), (
            f"intento {n}: el prompt se cayó de la ventana — el modelo estaría "
            f"reparando a ciegas. Ventana: {messages!r}"
        )


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
# Resiliencia del historial: answer nunca vacío
# ---------------------------------------------------------------------------


def test_conversacion_larga_siempre_devuelve_answer_no_vacio():
    """Criterio del enunciado: decenas de turnos con mensajes extensos, y
    cada run sigue devolviendo un AgentResult con answer no vacío."""
    turnos = 30
    largo = "detalle " * 200  # mensajes extensos, no de una línea
    mock = MockLLMClient([LLMResponse(content=f"respuesta {i}") for i in range(turnos)])
    agent = build_agent({"llm_client": mock, "max_history_messages": 8})

    for i in range(turnos):
        result = agent.run(f"turno {i}: {largo}")
        assert result.answer, f"el turno {i} devolvió un answer vacío"
        assert len(mock.calls[-1]["messages"]) <= 8


def test_corte_por_max_iterations_devuelve_answer_informativo():
    """Aun cortando por límite, `answer` no queda vacío: explica el corte y
    qué herramientas se llegaron a usar (y `error` sigue seteado)."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient(
        [_tool_call(schema.name, call_id=f"c{i}") for i in range(3)]
    )
    agent = build_agent({"llm_client": mock, "max_iterations": 3})
    agent.register_tool(tool, schema)

    result = agent.run("entrá en loop")

    assert result.answer, "answer no puede quedar vacío ni al cortar por límite"
    assert schema.name in result.answer, "debería listar las tools usadas"
    assert result.error is not None, "el corte debe seguir siendo detectable"
    assert mock.call_count == 3


def test_respuesta_vacia_del_modelo_no_propaga_answer_vacio():
    """Si el LLM cierra con content vacío, devolvemos un texto de cierre."""
    mock = MockLLMClient([LLMResponse(content=None)])
    agent = build_agent({"llm_client": mock})

    result = agent.run("hola")

    assert result.answer, "content=None no debe convertirse en answer vacío"


def test_content_con_texto_se_devuelve_exactamente():
    """El contrato de M1 sigue intacto: si hay texto, va tal cual."""
    mock = MockLLMClient([LLMResponse(content="La respuesta es 4.")])
    agent = build_agent({"llm_client": mock})

    assert agent.run("¿2+2?").answer == "La respuesta es 4."


# ---------------------------------------------------------------------------
# Validación de la configuración
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tope", [0, -1])
def test_tope_de_historial_invalido_falla_al_construir(tope: int):
    """Un tope de 0 mensajes es incompatible con la invariante de recencia:
    se rechaza en el constructor en vez de violar el contrato en silencio."""
    mock = MockLLMClient([LLMResponse(content="x")])

    with pytest.raises(ValueError, match="max_history_messages"):
        build_agent({"llm_client": mock, "max_history_messages": tope})


def test_parametros_de_reintento_invalidos_fallan_al_construir():
    mock = MockLLMClient([LLMResponse(content="x")])

    with pytest.raises(ValueError, match="max_retries"):
        build_agent({"llm_client": mock, "max_retries": -1})
    with pytest.raises(ValueError, match="retry_base_delay"):
        build_agent({"llm_client": mock, "retry_base_delay": -0.5})
    with pytest.raises(ValueError, match="max_iterations"):
        build_agent({"llm_client": mock, "max_iterations": 0})


@pytest.mark.parametrize(
    "clave, valor",
    [
        ("max_history_messages", 1.5),  # rompía recién en el 2do run, al slicear
        ("max_history_messages", True),
        ("max_iterations", 1.5),
        ("max_retries", 1.5),
    ],
)
def test_contadores_no_enteros_fallan_al_construir(clave: str, valor: object):
    """Los contadores indexan listas y alimentan `range`: un float reventaría
    más tarde y lejos de la causa, con el historial a medio escribir."""
    mock = MockLLMClient([LLMResponse(content="x")])

    with pytest.raises(ValueError, match=clave):
        build_agent({"llm_client": mock, clave: valor})


@pytest.mark.parametrize("valor", [float("nan"), float("inf")])
def test_demora_no_finita_falla_al_construir(valor: float):
    """NaN o infinito dejarían el backoff esperando para siempre."""
    mock = MockLLMClient([LLMResponse(content="x")])

    with pytest.raises(ValueError, match="retry_base_delay"):
        build_agent({"llm_client": mock, "retry_base_delay": valor})


def test_max_repair_attempts_negativo_falla_claro():
    """Antes terminaba en 'agotó 0 intentos' sin haber llamado al LLM."""
    mock = MockLLMClient([_final_result({"valor": 1, "comentario": "ok"})])
    agent = build_agent({"llm_client": mock})

    with pytest.raises(ValueError, match="max_repair_attempts"):
        agent.structured_call(
            prompt="dame un objeto", schema=Respuesta, max_repair_attempts=-1
        )
    assert mock.call_count == 0


# ---------------------------------------------------------------------------
# Resiliencia: reintentos ante fallos transitorios
# ---------------------------------------------------------------------------


def test_timeout_del_llm_se_reintenta_y_el_run_termina_bien():
    """Criterio del enunciado: un timeout simulado se reintenta solo."""
    mock = MockLLMClient([TimeoutError("se colgó"), LLMResponse(content="ok")])
    agent = build_agent({"llm_client": mock, "retry_base_delay": 0})

    result = agent.run("hola")

    assert result.answer == "ok"
    assert mock.call_count == 2, "el timeout debió consumir un reintento"


def test_error_no_transitorio_del_llm_propaga_sin_reintentar():
    """Un bug (ValueError) no se reintenta: se propaga limpio al llamador."""
    mock = MockLLMClient([ValueError("request mal armado"), LLMResponse(content="x")])
    agent = build_agent({"llm_client": mock, "retry_base_delay": 0})

    with pytest.raises(ValueError):
        agent.run("hola")
    assert mock.call_count == 1


def test_transitorio_agotado_propaga_la_ultima_excepcion():
    """max_retries acota el optimismo: agotados, la excepción sale."""
    mock = MockLLMClient(
        [TimeoutError("1"), TimeoutError("2"), TimeoutError("3"), TimeoutError("4")]
    )
    agent = build_agent(
        {"llm_client": mock, "retry_base_delay": 0, "max_retries": 2}
    )

    with pytest.raises(TimeoutError):
        agent.run("hola")
    assert mock.call_count == 3, "1 intento inicial + 2 reintentos"


def test_tool_con_fallo_transitorio_se_reintenta():
    """Una tool que falla por red una vez termina ejecutándose bien."""
    intentos = {"n": 0}

    def fragil(
        text: Annotated[str, Field(description="Texto cualquiera.")],
    ) -> str:
        """Tool de test que falla con error de red en el primer intento."""
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise ConnectionError("red caída")
        return "ok"

    schema = ToolSchema.from_callable(fragil)
    mock = MockLLMClient(
        [_tool_call(schema.name, call_id="c1"), LLMResponse(content="listo")]
    )
    agent = build_agent({"llm_client": mock, "retry_base_delay": 0})
    agent.register_tool(fragil, schema)

    result = agent.run("usá la herramienta")

    assert intentos["n"] == 2
    assert result.steps[0].error is None
    assert result.steps[0].tool_output == "ok"
    assert result.answer == "listo"


def test_tool_con_error_no_transitorio_no_se_reintenta():
    """Un bug en la tool va a AgentStep.error (el loop sigue, como en M1)."""
    intentos = {"n": 0}

    def rota(
        text: Annotated[str, Field(description="Texto cualquiera.")],
    ) -> str:
        """Tool de test que siempre pincha con un error de programación."""
        intentos["n"] += 1
        raise ValueError("bug adentro de la tool")

    schema = ToolSchema.from_callable(rota)
    mock = MockLLMClient(
        [_tool_call(schema.name, call_id="c1"), LLMResponse(content="me recupero")]
    )
    agent = build_agent({"llm_client": mock, "retry_base_delay": 0})
    agent.register_tool(rota, schema)

    result = agent.run("usá la herramienta")

    assert intentos["n"] == 1, "un ValueError no debe reintentarse"
    assert result.steps[0].error is not None
    assert result.answer == "me recupero"


def test_clasificador_de_transitorios_por_codigo_http():
    """El duck-typing de status code funciona sin importar el SDK."""

    class ErrorConStatus(Exception):
        def __init__(self, status_code: int) -> None:
            super().__init__(f"HTTP {status_code}")
            self.status_code = status_code

    assert _es_error_transitorio(ErrorConStatus(503))
    assert _es_error_transitorio(ErrorConStatus(429))
    assert not _es_error_transitorio(ErrorConStatus(400))
    assert not _es_error_transitorio(ValueError("no tiene nada de HTTP"))
    assert _es_error_transitorio(TimeoutError("timeout pelado"))


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


# ---------------------------------------------------------------------------
# Memoria de acciones (M3): registro compacto en el system prompt
# ---------------------------------------------------------------------------


def _llamada_a(nombre: str, args: dict, call_id: str = "c1") -> LLMResponse:
    return LLMResponse(
        content=None,
        tool_calls=[ToolCall(id=call_id, name=nombre, arguments=json.dumps(args))],
    )


def test_memoria_de_acciones_apagada_por_defecto():
    """El comportamiento de M1 y M2 no cambia si no se pide explícitamente."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient([_llamada_a(schema.name, {"text": "x"}), LLMResponse(content="ok")])
    agent = build_agent({"llm_client": mock, "system_prompt": "BASE."})
    agent.register_tool(tool, schema)
    agent.run("dale")

    assert mock.calls[-1]["system"] == "BASE.", "sin pedirlo, el system no se toca"


def test_memoria_registra_lo_ejecutado_en_el_system():
    tool, schema = make_recording_tool(return_value="resultado")
    mock = MockLLMClient([_llamada_a(schema.name, {"text": "x"}), LLMResponse(content="ok")])
    agent = build_agent(
        {"llm_client": mock, "system_prompt": "BASE.", "memoria_de_acciones": True}
    )
    agent.register_tool(tool, schema)
    agent.run("dale")

    system = mock.calls[-1]["system"]
    assert system.startswith("BASE."), "el prompt original se conserva al inicio"
    assert schema.name in system
    assert "resultado" in system


def test_memoria_separa_fallidas_de_exitosas():
    """Las que fallaron van en su propia sección: son las que el agente
    tiende a reintentar en bucle."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient(
        [
            _llamada_a("inexistente", {}, "c1"),
            _llamada_a(schema.name, {"text": "x"}, "c2"),
            LLMResponse(content="ok"),
        ]
    )
    agent = build_agent(
        {"llm_client": mock, "system_prompt": "BASE.", "memoria_de_acciones": True}
    )
    agent.register_tool(tool, schema)
    agent.run("dale")

    system = mock.calls[-1]["system"]
    assert "YA FALLARON" in system and "CON ÉXITO" in system
    assert system.index("YA FALLARON") < system.index("CON ÉXITO"), (
        "las fallidas van primero, que es lo que hay que dejar de repetir"
    )


def test_memoria_deduplica_y_cuenta_repeticiones():
    """Diez llamadas idénticas ocupan una línea, no diez."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient(
        [_llamada_a(schema.name, {"text": "x"}, f"c{i}") for i in range(4)]
        + [LLMResponse(content="ok")]
    )
    agent = build_agent(
        {"llm_client": mock, "system_prompt": "BASE.", "memoria_de_acciones": True}
    )
    agent.register_tool(tool, schema)
    agent.run("dale")

    system = mock.calls[-1]["system"]
    assert system.count(f"- {schema.name}(") == 1, "la acción repetida aparece una vez"
    assert "ya intentada 4 veces" in system


def test_memoria_no_consume_presupuesto_de_ventana():
    """Va en `system=`, fuera de la lista `messages`: ese es el punto."""
    tool, schema = make_recording_tool()
    mock = MockLLMClient(
        [_llamada_a(schema.name, {"text": "x"}, f"c{i}") for i in range(3)]
        + [LLMResponse(content="ok")]
    )
    agent = build_agent(
        {
            "llm_client": mock,
            "system_prompt": "BASE.",
            "memoria_de_acciones": True,
            "max_history_messages": 4,
        }
    )
    agent.register_tool(tool, schema)
    agent.run("dale")

    for llamada in mock.calls:
        assert len(llamada["messages"]) <= 4, "el tope de la ventana sigue rigiendo"
    assert len(mock.calls[-1]["system"]) > len("BASE."), "y la memoria llegó igual"


def test_accion_improductiva_avisa_pero_no_altera_el_step():
    """Repetir una acción con resultado idéntico agrega un aviso al mensaje
    que ve el modelo, pero el `AgentStep` conserva la salida exacta de la
    herramienta (contrato de M1)."""
    tool, schema = make_recording_tool(return_value="siempre lo mismo")
    mock = MockLLMClient(
        [
            _llamada_a(schema.name, {"text": "x"}, "c1"),
            _llamada_a(schema.name, {"text": "x"}, "c2"),
            LLMResponse(content="ok"),
        ]
    )
    agent = build_agent({"llm_client": mock, "memoria_de_acciones": True})
    agent.register_tool(tool, schema)
    result = agent.run("dale")

    assert [s.tool_output for s in result.steps] == ["siempre lo mismo"] * 2, (
        "el AgentStep debe guardar el valor exacto que devolvió la tool"
    )
    mensajes_tool = [
        m for m in mock.calls[-1]["messages"] if m.get("role") == "tool"
    ]
    assert "AVISO DEL SISTEMA" not in mensajes_tool[0]["content"], (
        "la primera vez no hay nada que avisar"
    )
    assert "AVISO DEL SISTEMA" in mensajes_tool[1]["content"], (
        "la repetición idéntica sí debe avisarse"
    )


def test_misma_accion_con_resultado_distinto_no_se_marca():
    """`look()` después de moverse de sala devuelve otra cosa: eso NO es una
    repetición improductiva y no debe desalentarse."""
    from typing import Annotated

    from pydantic import Field

    from mia_agents.types import ToolSchema

    salidas = iter(["sala A", "sala B"])

    def mirar() -> str:
        """Describe la sala actual."""
        return next(salidas)

    schema = ToolSchema.from_callable(mirar)
    mock = MockLLMClient(
        [
            LLMResponse(content=None, tool_calls=[ToolCall(id="c1", name="mirar", arguments="{}")]),
            LLMResponse(content=None, tool_calls=[ToolCall(id="c2", name="mirar", arguments="{}")]),
            LLMResponse(content="ok"),
        ]
    )
    agent = build_agent({"llm_client": mock, "memoria_de_acciones": True})
    agent.register_tool(mirar, schema)
    agent.run("dale")

    mensajes_tool = [m for m in mock.calls[-1]["messages"] if m.get("role") == "tool"]
    assert all("AVISO DEL SISTEMA" not in m["content"] for m in mensajes_tool), (
        "misma firma con resultado distinto es información nueva, no un bucle"
    )


# ---------------------------------------------------------------------------
# Bloqueo de repeticiones estériles (M3)
# ---------------------------------------------------------------------------


def test_bloqueo_recien_actua_a_la_tercera():
    """Las dos primeras ejecuciones corren: hace falta la segunda para
    comprobar que el resultado no cambia. La tercera se bloquea."""
    tool, schema = make_recording_tool(return_value="siempre igual")
    mock = MockLLMClient(
        [_llamada_a(schema.name, {"text": "x"}, f"c{i}") for i in range(3)]
        + [LLMResponse(content="fin")]
    )
    agent = build_agent({"llm_client": mock, "bloquear_repeticiones": True})
    agent.register_tool(tool, schema)
    result = agent.run("dale")

    assert len(tool.calls) == 2, "la tercera no debe llegar a ejecutarse"
    assert result.steps[0].error is None and result.steps[1].error is None
    assert "bloqueada" in (result.steps[2].error or "").lower()


def test_bloqueo_se_levanta_si_el_resultado_cambia():
    """`look()` tras moverse de sala devuelve otra cosa: deja de ser estéril
    y se puede volver a llamar. Sin esto, se rompería la navegación."""
    from mia_agents.types import ToolSchema

    salidas = iter(["sala A", "sala A", "sala B", "sala B"])

    def mirar() -> str:
        """Describe la sala actual."""
        return next(salidas)

    schema = ToolSchema.from_callable(mirar)
    mock = MockLLMClient(
        [
            LLMResponse(content=None, tool_calls=[ToolCall(id=f"c{i}", name="mirar", arguments="{}")])
            for i in range(4)
        ]
        + [LLMResponse(content="fin")]
    )
    agent = build_agent({"llm_client": mock, "bloquear_repeticiones": True})
    agent.register_tool(mirar, schema)
    result = agent.run("dale")

    errores = [s.error for s in result.steps]
    assert errores[0] is None and errores[1] is None
    assert "bloqueada" in (errores[2] or "").lower(), "la 3ra idéntica se bloquea"
    assert errores[3] is None, (
        "tras cambiar el resultado la marca se levanta y vuelve a ejecutarse"
    )


def test_bloqueo_apagado_por_defecto():
    tool, schema = make_recording_tool(return_value="igual")
    mock = MockLLMClient(
        [_llamada_a(schema.name, {"text": "x"}, f"c{i}") for i in range(3)]
        + [LLMResponse(content="fin")]
    )
    agent = build_agent({"llm_client": mock})
    agent.register_tool(tool, schema)
    agent.run("dale")

    assert len(tool.calls) == 3, "sin el flag, nada se bloquea"
