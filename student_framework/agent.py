"""Implementación de su agente.

Completen `register_tool` y `run` para el Milestone 1.
En el Milestone 2 amplíen `MyAgent` para que sea estatal y respete
`max_history_messages`.

Los tests de conformidad en `tests/conformance/test_m1.py` y
`test_m2.py` describen con precisión qué comportamientos deben funcionar
— léanlos antes de empezar.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from mia_agents.protocols import LLMClient
from mia_agents.types import AgentResult, AgentStep, LLMResponse, ToolCall, ToolSchema


class MyAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str = "Eres un asistente útil.",
        max_iterations: int = 10,
        max_history_messages: int = 50,
    ) -> None:
        """Inicializa el agente.

        Parameters
        ----------
        llm_client : LLMClient
            Cliente LLM (real o mock) que el agente utilizará.
        system_prompt : str
            System prompt por defecto.
        max_iterations : int
            Tope de iteraciones del bucle del agente (M1).
        max_history_messages : int
            Número máximo de mensajes que se permiten en la lista
            `messages` enviada al LLM en una única llamada. En M1 este
            valor es ignorado; el agente sólo necesita aceptarlo en su
            constructor. En M2 deben respetarlo: la longitud de la
            lista de mensajes pasada a `self._llm.chat(...)` no puede
            superar este número en ninguna llamada, sin importar la
            estrategia de memoria que elijan.
        """
        self._llm = llm_client
        self._system = system_prompt
        self._max_iterations = max_iterations
        self._max_history_messages = max_history_messages
        # Estado de las herramientas registradas. Indexamos por el nombre
        # del esquema para que, al ejecutar un tool_call, podamos buscar el
        # callable por `tool_call.name` y para que `AgentStep.tool_name`
        # coincida exactamente con `schema.name`.
        self._tools: dict[str, Callable[..., str]] = {}
        self._schemas: dict[str, ToolSchema] = {}

    def register_tool(
        self,
        tool: Callable[..., str],
        schema: ToolSchema,
    ) -> None:
        """Registra una herramienta callable junto a su esquema.

        El esquema suele obtenerse con `ToolSchema.from_callable(fn)`. En
        `run`, pasá `tools=list(self._schemas.values())`; el cliente LLM
        aplica `to_llm_spec()` al llamar al proveedor.

        El callable se invoca con kwargs que coinciden con la firma.
        Debe devolver una cadena.
        """
        self._tools[schema.name] = tool
        self._schemas[schema.name] = schema

    def run(self, user_message: str) -> AgentResult:
        """Ejecuta el bucle del agente hasta una respuesta final o hasta max_iterations.

        Comportamiento esperado (consulta tests/conformance/test_m1.py
        para el contrato exacto del M1):
          - Llama a `self._llm.chat(..., tools=list(self._schemas.values()))`.
          - Si la respuesta contiene tool_calls, ejecuta cada uno y vuelca
            los resultados en la siguiente llamada al chat.
          - Si la respuesta solo contiene texto (sin `tool_calls`),
            devuélvelo en `AgentResult.answer`. En M1 no uses la tool
            sintética `final_result`; ese patrón es de M2 (ver README y
            ENUNCIADO_M2.md).
          - Limita el bucle a `self._max_iterations` y termina de forma
            limpia cuando se alcance.
          - Registra cada invocación de herramienta como un `AgentStep`
            dentro de `result.steps`.

        En el M2, además, llamadas sucesivas sobre la misma instancia
        deben continuar la conversación, y la longitud de la lista de
        mensajes enviada al LLM no debe superar `self._max_history_messages`.
        Acumula los tokens de entrada/salida reportados por los
        `LLMResponse` y exponlos en `AgentResult.input_tokens` /
        `AgentResult.output_tokens`.
        """
        # Historial local de esta llamada a `run` (en M1 no hay estado
        # persistente entre llamadas). Arranca con el mensaje del usuario.
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
        steps: list[AgentStep] = []

        # El `for` (en vez de `while True`) es nuestra garantía de no tener
        # bucles infinitos: como mucho hacemos `max_iterations` llamadas al LLM.
        for _ in range(self._max_iterations):
            response = self._llm.chat(
                messages=messages,
                # Sin tools registradas pasamos None; el contrato exige que,
                # si hay tools, su nombre aparezca en la lista enviada.
                tools=list(self._schemas.values()) or None,
                system=self._system,
            )

            # Condición de parada de M1: texto sin tool_calls => respuesta final.
            if not response.tool_calls:
                return AgentResult(answer=response.content or "", steps=steps)

            # El LLM pidió herramientas. Registramos su turno (con los
            # tool_calls) y luego ejecutamos cada una.
            messages.append(self._assistant_turn(response))
            for call in response.tool_calls:
                output, error = self._dispatch(call)
                steps.append(
                    AgentStep(
                        tool_name=call.name,
                        tool_input=call.arguments,
                        tool_output=output,
                        error=error,
                    )
                )
                # Realimentamos el resultado (o el error) al LLM como un
                # mensaje `role: "tool"` antes de volver a llamar a `chat`.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": output if error is None else error,
                    }
                )

        # Se agotó `max_iterations` sin una respuesta de texto final. Aun así
        # devolvemos un `AgentResult` válido, con `error` indicando el corte.
        return AgentResult(
            answer="",
            steps=steps,
            error=f"Se alcanzó el máximo de iteraciones ({self._max_iterations}).",
        )

    def _dispatch(self, call: ToolCall) -> tuple[str | None, str | None]:
        """Ejecuta un único `tool_call`. Devuelve `(output, error)` y nunca lanza.

        - Tool desconocida (alucinada por el LLM) => `(None, mensaje)`.
        - `arguments` con JSON inválido => `(None, mensaje)`.
        - La tool lanza una excepción (p. ej. división por cero) => `(None, mensaje)`.
        - Éxito => `(resultado_str, None)`.
        """
        tool = self._tools.get(call.name)
        if tool is None:
            return None, f"Herramienta desconocida: {call.name!r}."

        try:
            kwargs = json.loads(call.arguments) if call.arguments else {}
        except json.JSONDecodeError as exc:
            return None, f"Argumentos JSON inválidos para {call.name!r}: {exc}."

        try:
            return tool(**kwargs), None
        except Exception as exc:  # noqa: BLE001 — una tool puede fallar; no rompemos el bucle.
            return None, f"Error al ejecutar {call.name!r}: {exc}."

    @staticmethod
    def _assistant_turn(response: LLMResponse) -> dict[str, Any]:
        """Arma el turno del assistant con sus tool_calls.

        Usa el formato que los providers fijos (Ollama y Bedrock) saben
        normalizar. Este formato es interno al bucle: las tools no lo ven,
        así que no acopla la implementación de las herramientas.
        """
        return {
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in response.tool_calls
            ],
        }

    def structured_call(
        self,
        prompt: str,
        schema: Any,
        max_repair_attempts: int = 2,
    ) -> Any:
        """Pide al LLM una respuesta validada contra `schema` (M2).

        Obligatorio: herramienta sintética `final_result` (ver
        `mia_agents.final_result_tool_schema` / `FINAL_RESULT_TOOL_NAME`).
        El agente ofrece esa tool al LLM, valida los `arguments` del
        `tool_call` y reintenta con contexto de reparación si el modelo
        responde con texto libre o con argumentos inválidos.

        Implementa esto en el M2:
          - Pasa `tools=[final_result_tool_schema(schema)]` en cada
            llamada a `chat` dentro de este método.
          - Termina solo cuando llega un `tool_call` a `final_result`
            cuyos argumentos validan con `schema.model_validate(...)`.
          - Reintenta hasta `max_repair_attempts` incluyendo el fallo en
            los mensajes (respuesta previa, mensaje `tool`, o user de
            reparación).
          - Si tras los reintentos sigue fallando, levanta una excepción
            limpia (no devuelvas valores parciales ni `None` sin avisar).

        El M1 deja esto como stub; los tests de M2 verifican el contrato.
        """
        raise NotImplementedError("M2: implementa salida estructurada con reparación")
