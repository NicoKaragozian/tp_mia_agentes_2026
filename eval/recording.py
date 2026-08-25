"""Cliente LLM que graba cada llamada (captura de trazas del M3).

El enunciado pide capturar entradas, salidas, llamadas a herramientas y
errores por caso. En vez de instrumentar el agente —que obligaría a tocar
`student_framework/agent.py` y a mezclar medición con lógica— envolvemos
el **cliente LLM**: es la misma sustitución por protocolo que usan los
tests con `MockLLMClient`, y deja tanto al agente como a `mia_agents/`
intactos.

Qué se graba y qué no: por llamada guardamos metadatos (cuántos mensajes
se enviaron, qué herramientas se ofrecieron, qué devolvió el modelo,
tokens, latencia). NO guardamos la lista de mensajes completa en cada
llamada: como el historial crece turno a turno, eso haría que el archivo
creciera de forma cuadrática (y `extreme-archive` arrastra ~16K tokens de
prosa).

Sí guardamos, una sola vez, el **contexto de la última llamada**
(`ultimo_contexto`): la lista de mensajes tal como la recibió el modelo al
final de la corrida, ya recortada por la ventana deslizante. Está acotada
por `max_history_messages`, así que no crece, y es lo que permite verificar
después qué vio realmente el modelo — la evidencia con la que se analizó el
experimento de memoria.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from mia_agents.types import LLMResponse, ToolSchema


def _recortar(texto: str | None, tope: int = 2000) -> str | None:
    """Acota un texto largo dejando constancia de cuánto se recortó."""
    if texto is None or len(texto) <= tope:
        return texto
    return f"{texto[:tope]}… [recortado, {len(texto)} caracteres en total]"


@dataclass
class LlamadaLLM:
    """Una invocación a `chat(...)` con lo que entró y lo que salió."""

    indice: int
    n_mensajes: int
    herramientas_ofrecidas: list[str]
    ultimo_mensaje: dict[str, Any] | None
    contenido: str | None
    tool_calls: list[dict[str, str]] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    latencia_s: float = 0.0
    excepcion: str | None = None


class ClienteGrabador:
    """Envuelve un `LLMClient` y registra cada `chat` en `self.llamadas`.

    Cumple el protocolo `mia_agents.protocols.LLMClient` (misma firma), así
    que el agente no puede distinguirlo del cliente real.
    """

    def __init__(self, interno: Any) -> None:
        self._interno = interno
        self.llamadas: list[LlamadaLLM] = []
        #: Mensajes de la última llamada, ya recortados por la ventana.
        self.ultimo_contexto: list[dict[str, Any]] = []

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[ToolSchema | dict[str, Any]] | None = None,
        system: str | None = None,
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        indice = len(self.llamadas)
        self.ultimo_contexto = [
            {**m, "content": _recortar(m["content"], 400)}
            if isinstance(m.get("content"), str)
            else dict(m)
            for m in messages
        ]
        ultimo = dict(messages[-1]) if messages else None
        if ultimo is not None and isinstance(ultimo.get("content"), str):
            ultimo["content"] = _recortar(ultimo["content"], 600)
        registro = LlamadaLLM(
            indice=indice,
            n_mensajes=len(messages),
            herramientas_ofrecidas=[
                t.name if isinstance(t, ToolSchema) else str(t.get("name"))
                for t in (tools or [])
            ],
            ultimo_mensaje=ultimo,
            contenido=None,
        )
        self.llamadas.append(registro)

        inicio = time.perf_counter()
        try:
            respuesta = self._interno.chat(
                messages=messages,
                tools=tools,
                system=system,
                temperature=temperature,
                response_format=response_format,
            )
        except Exception as exc:  # se graba y se re-lanza: el agente decide
            registro.latencia_s = time.perf_counter() - inicio
            registro.excepcion = f"{type(exc).__name__}: {exc}"
            raise

        registro.latencia_s = time.perf_counter() - inicio
        registro.contenido = _recortar(respuesta.content)
        registro.tool_calls = [
            {"id": tc.id, "name": tc.name, "arguments": _recortar(tc.arguments, 500)}
            for tc in respuesta.tool_calls
        ]
        registro.input_tokens = respuesta.input_tokens
        registro.output_tokens = respuesta.output_tokens
        return respuesta

    # -- agregados útiles para las métricas -------------------------------

    @property
    def latencia_total_s(self) -> float:
        return sum(ll.latencia_s for ll in self.llamadas)

    def como_dicts(self) -> list[dict[str, Any]]:
        return [asdict(ll) for ll in self.llamadas]
