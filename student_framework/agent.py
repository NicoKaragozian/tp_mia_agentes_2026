"""Implementación de su agente.

M1: bucle ReAct (`register_tool` + `run` + `_dispatch`).
M2: el agente pasa a ser estatal — llamadas sucesivas a `run` continúan
la misma conversación — y gestiona su contexto con una ventana deslizante
(Sliding Window) que garantiza que la lista `messages` enviada al LLM
nunca supere `max_history_messages`.

La separación clave de M2 es historial vs. ventana:

- `self._history` es la memoria completa de la conversación (el *store*:
  solo crece, nunca se recorta);
- `_ventana()` es la vista acotada que se envía al LLM en cada `chat`
  (la *política de lectura*: se recalcula en cada llamada).

Los tests de conformidad en `tests/conformance/test_m1.py` y `test_m2.py`
describen con precisión los comportamientos exigidos.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, TypeVar

from pydantic import ValidationError

from mia_agents.protocols import LLMClient
from mia_agents.tool_schema import FINAL_RESULT_TOOL_NAME, final_result_tool_schema
from mia_agents.types import AgentResult, AgentStep, LLMResponse, ToolCall, ToolSchema

_T = TypeVar("_T")

#: Códigos HTTP que se consideran transitorios: timeout del servidor,
#: rate limit y familia 5xx (el resto de 4xx es culpa del request: no
#: tiene sentido repetirlo igual).
_ESTADOS_TRANSITORIOS = frozenset({408, 429, 500, 502, 503, 504})

#: Fragmentos de nombre de clase / código de error de proveedor que
#: delatan un fallo transitorio (ThrottlingException, ReadTimeout, ...).
_MARCAS_TRANSITORIAS = (
    "timeout",
    "throttl",
    "ratelimit",
    "rate_limit",
    "serviceunavailable",
    "connection",
    "temporar",
)


def _codigo_http(exc: Exception) -> int | None:
    """Extrae un código de estado HTTP del objeto excepción, si lo trae.

    Duck-typing deliberado: el agente está programado contra el protocolo
    `chat(...)` y no importa los SDKs de los proveedores, pero sus
    excepciones suelen cargar el estado como `status_code` (ollama,
    httpx), `status`, o dentro de `response` (requests / botocore).
    """
    for attr in ("status_code", "status"):
        valor = getattr(exc, attr, None)
        if isinstance(valor, int):
            return valor
    respuesta = getattr(exc, "response", None)
    valor = getattr(respuesta, "status_code", None)
    if isinstance(valor, int):
        return valor
    if isinstance(respuesta, dict):  # estilo botocore: response["ResponseMetadata"]
        valor = (respuesta.get("ResponseMetadata") or {}).get("HTTPStatusCode")
        if isinstance(valor, int):
            return valor
    return None


def _es_error_transitorio(exc: Exception) -> bool:
    """True si reintentar tiene sentido (red, timeout, 5xx, rate limit).

    Un error de programación (TypeError, ValueError, ...) devuelve False:
    reintentarlo solo escondería el bug. Ante la duda, False — mejor
    propagar limpio que reintentar a ciegas.
    """
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    codigo = _codigo_http(exc)
    if codigo is not None:
        return codigo in _ESTADOS_TRANSITORIOS
    # Código de error simbólico estilo botocore: response["Error"]["Code"].
    respuesta = getattr(exc, "response", None)
    if isinstance(respuesta, dict):
        simbolo = str((respuesta.get("Error") or {}).get("Code", "")).lower()
        if any(marca in simbolo for marca in _MARCAS_TRANSITORIAS):
            return True
    nombre = type(exc).__name__.lower()
    return any(marca in nombre for marca in _MARCAS_TRANSITORIAS)


class SalidaEstructuradaError(RuntimeError):
    """`structured_call` agotó los reintentos sin lograr una salida válida.

    Se levanta en lugar de devolver `None` o una instancia parcial: el
    contrato de `structured_call` es "instancia válida o excepción limpia".
    La causa original (ValidationError, JSONDecodeError, ...) queda
    encadenada en `__cause__` cuando existe.
    """


class MyAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str = "Eres un asistente útil.",
        max_iterations: int = 10,
        max_history_messages: int = 50,
        max_retries: int = 2,
        retry_base_delay: float = 0.2,
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
            Tope duro para la lista `messages` enviada al LLM: la
            longitud de lo pasado a `self._llm.chat(...)` no supera este
            número en ninguna llamada (ver `_ventana`), sin importar
            cuántos turnos acumule la conversación.
        max_retries : int
            Reintentos automáticos ante fallos transitorios (además del
            intento inicial), tanto para el cliente LLM como para las
            herramientas. Ver `_con_reintentos`.
        retry_base_delay : float
            Espera base (segundos) del backoff exponencial entre
            reintentos: base, 2*base, 4*base, ... Con 0 no se duerme
            (útil en tests).
        """
        # Validación de la configuración: un tope de 0 (o negativo) mensajes
        # es CONTRADICTORIO con la invariante de recencia — no se puede a la
        # vez "no enviar mensajes" y "que el último mensaje del usuario
        # siempre aparezca". Ante una configuración imposible preferimos
        # fallar acá, explícito, antes que violar un contrato en silencio.
        if max_history_messages < 1:
            raise ValueError(
                "max_history_messages debe ser >= 1: con 0 mensajes no se "
                "puede cumplir la invariante de recencia (el último mensaje "
                f"del usuario siempre debe llegar al LLM); recibí "
                f"{max_history_messages!r}."
            )
        if max_iterations < 1:
            raise ValueError(
                f"max_iterations debe ser >= 1; recibí {max_iterations!r}."
            )
        if max_retries < 0:
            raise ValueError(f"max_retries debe ser >= 0; recibí {max_retries!r}.")
        if retry_base_delay < 0:
            raise ValueError(
                f"retry_base_delay debe ser >= 0; recibí {retry_base_delay!r}."
            )

        self._llm = llm_client
        self._system = system_prompt
        self._max_iterations = max_iterations
        self._max_history_messages = max_history_messages
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        # Memoria de la conversación (M2). Historial completo y persistente
        # entre llamadas a `run`: acá se escribe TODO (turnos de usuario,
        # del assistant y resultados de tools). Lo que se envía al LLM en
        # cada chat es la vista recortada que devuelve `_ventana()`.
        self._history: list[dict[str, Any]] = []
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

        Contrato (tests/conformance/test_m1.py y test_m2.py):
          - Llama a `self._llm.chat(..., tools=list(self._schemas.values()))`.
          - Si la respuesta contiene tool_calls, ejecuta cada uno y vuelca
            los resultados en la siguiente llamada al chat.
          - Si la respuesta solo contiene texto (sin `tool_calls`), lo
            devuelve en `AgentResult.answer`. El cierre de `run` sigue
            siendo el de M1 (texto sin tools); `final_result` es exclusivo
            de `structured_call`.
          - Limita el bucle a `self._max_iterations` y termina limpio.
          - Registra cada invocación de herramienta como un `AgentStep`.

        Estado (M2): la conversación persiste en `self._history`, así que
        llamadas sucesivas sobre la misma instancia la continúan. Cada
        `chat` recibe `_ventana()`, nunca más de `max_history_messages`
        mensajes.

        Tokens (M2): `AgentResult.input_tokens/output_tokens` acumulan lo
        reportado por los `LLMResponse` de ESTE run. Si ninguno reportó
        tokens quedan en `None`; si alguno reportó, se suma tratando los
        `None` por-respuesta como 0 (regla del docstring de `AgentResult`).
        """
        self._history.append({"role": "user", "content": user_message})
        steps: list[AgentStep] = []
        tokens_entrada = 0
        tokens_salida = 0
        # Bandera global: distingue "nadie reportó" (→ None) de "alguien
        # reportó y los demás no" (→ los faltantes suman 0).
        alguien_reporto = False

        # El `for` (en vez de `while True`) es nuestra garantía de no tener
        # bucles infinitos: como mucho hacemos `max_iterations` llamadas al LLM.
        for _ in range(self._max_iterations):
            response = self._con_reintentos(
                lambda: self._llm.chat(
                    messages=self._ventana(),
                    # Sin tools registradas pasamos None; el contrato exige
                    # que, si hay tools, su nombre aparezca en la lista.
                    tools=list(self._schemas.values()) or None,
                    system=self._system,
                )
            )
            if response.input_tokens is not None or response.output_tokens is not None:
                alguien_reporto = True
            tokens_entrada += response.input_tokens or 0
            tokens_salida += response.output_tokens or 0

            # Condición de parada: texto sin tool_calls => respuesta final.
            # Se persiste como turno del assistant para que los próximos
            # `run` la vean como parte de la conversación.
            if not response.tool_calls:
                answer = response.content or ""
                if not answer.strip():
                    # El modelo cerró con contenido vacío. M2 exige que `run`
                    # nunca devuelva un `answer` vacío, así que reportamos el
                    # hecho en vez de propagar el vacío. Cuando SÍ hay texto
                    # se devuelve exactamente ese texto (contrato de M1).
                    answer = (
                        "El modelo terminó el turno sin devolver contenido. "
                        "Reformulá la consulta o volvé a intentarlo."
                    )
                self._history.append({"role": "assistant", "content": answer})
                return AgentResult(
                    answer=answer,
                    steps=steps,
                    input_tokens=tokens_entrada if alguien_reporto else None,
                    output_tokens=tokens_salida if alguien_reporto else None,
                )

            # El LLM pidió herramientas. Registramos su turno (con los
            # tool_calls) y luego ejecutamos cada una.
            self._history.append(self._assistant_turn(response))
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
                self._history.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": output if error is None else error,
                    }
                )

        # Se agotó `max_iterations` sin una respuesta de texto final. Aun así
        # devolvemos un `AgentResult` válido. `answer` no queda vacío (M2 lo
        # exige): explica el corte y qué se alcanzó a hacer, mientras `error`
        # sigue permitiendo detectarlo programáticamente.
        usadas = list(dict.fromkeys(s.tool_name for s in steps if s.tool_name))
        detalle = ", ".join(usadas) if usadas else "ninguna"
        respuesta_parcial = (
            f"No llegué a una respuesta final: alcancé el límite de "
            f"{self._max_iterations} iteraciones. Herramientas utilizadas: "
            f"{detalle}."
        )
        self._history.append({"role": "assistant", "content": respuesta_parcial})
        return AgentResult(
            answer=respuesta_parcial,
            steps=steps,
            error=f"Se alcanzó el máximo de iteraciones ({self._max_iterations}).",
            input_tokens=tokens_entrada if alguien_reporto else None,
            output_tokens=tokens_salida if alguien_reporto else None,
        )

    def _ventana(
        self, historia: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """Vista del historial acotada a `max_history_messages` (Sliding Window).

        Opera sobre `self._history` por defecto; `structured_call` le pasa
        su lista de trabajo (conversación + mensajes locales de reparación)
        porque el tope rige para TODA llamada a `chat`, no solo las de `run`.

        Política (y su porqué, en orden de prioridad):

        1. **Recencia (invariante del enunciado):** el último mensaje del
           usuario aparece siempre. Sin él, el LLM ni siquiera sabría qué
           se le está preguntando en este turno.
        2. **Ancla:** se conserva el primer mensaje del usuario (el "goal"
           de la conversación); es el recorte recomendado en clase para no
           olvidar el objetivo aunque el medio se descarte.
        3. **Cola reciente:** el resto del presupuesto se llena con los
           mensajes más nuevos, que son los que sostienen el turno actual.
        4. **Coherencia estructural:** un `role:"tool"` sin el turno
           assistant que emitió su `tool_call` es un huérfano: si el corte
           deja huérfanos al inicio de la cola, se descartan. Quedar por
           debajo del tope es válido; superarlo o mandar pares rotos, no.

        El system prompt y los esquemas de tools NO consumen presupuesto:
        viajan por los parámetros `system=` y `tools=` de `chat(...)`,
        fuera de la lista `messages`.
        """
        if historia is None:
            historia = self._history
        tope = self._max_history_messages
        if len(historia) <= tope:
            return list(historia)

        # Índice del último mensaje del usuario (existe siempre: `run` y
        # `structured_call` lo agregan antes de llamar al LLM).
        i_ultimo_user = max(
            i for i, m in enumerate(historia) if m.get("role") == "user"
        )

        # Caso normal: ancla + cola de los últimos (tope - 1) mensajes.
        # Con tope 1 no hay lugar para el ancla: va solo la cola.
        usa_ancla = tope >= 2
        n_cola = tope - 1 if usa_ancla else tope
        inicio_cola = len(historia) - n_cola

        if inicio_cola <= i_ultimo_user:
            cola = historia[inicio_cola:]
            # Coherencia: sin resultados de tool huérfanos al inicio.
            while cola and cola[0].get("role") == "tool":
                cola = cola[1:]
            return ([historia[0]] if usa_ancla else []) + cola

        # Presupuesto tan chico que la cola reciente ya no incluye al
        # último user (p. ej. un run con muchas tools): la recencia manda.
        # El último user desplaza al ancla y encabeza la ventana; la cola
        # se acorta en uno para hacerle lugar. Los huérfanos se limpian
        # ANTES de prepender el user, para que no queden ocultos tras él.
        cola = historia[len(historia) - (tope - 1):] if tope >= 2 else []
        while cola and cola[0].get("role") == "tool":
            cola = cola[1:]
        return [historia[i_ultimo_user]] + cola

    def _con_reintentos(self, operacion: Callable[[], _T]) -> _T:
        """Ejecuta `operacion` reintentando los fallos transitorios.

        Política (enunciado: "resiliencia"):
          - transitorio (ver `_es_error_transitorio`) => hasta
            `max_retries` reintentos con backoff exponencial;
          - no transitorio => se propaga limpio, sin reintentar (repetir
            un bug no lo arregla);
          - transitorio agotado => se propaga la última excepción.

        Envuelve tanto las llamadas al cliente LLM como la ejecución de
        herramientas; quién atrapa lo que se propaga depende del llamador
        (el LLM no tiene plan B; una tool cae al camino de `AgentStep.error`).
        """
        intento = 0
        while True:
            try:
                return operacion()
            except Exception as exc:  # noqa: BLE001 — clasificamos y decidimos.
                if intento >= self._max_retries or not _es_error_transitorio(exc):
                    raise
                if self._retry_base_delay > 0:
                    time.sleep(self._retry_base_delay * (2**intento))
                intento += 1

    def _dispatch(self, call: ToolCall) -> tuple[str | None, str | None]:
        """Ejecuta un único `tool_call`. Devuelve `(output, error)` y nunca lanza.

        - Tool desconocida (alucinada por el LLM) => `(None, mensaje)`.
        - `arguments` con JSON inválido => `(None, mensaje)`.
        - La tool lanza una excepción (p. ej. división por cero) => `(None, mensaje)`.
        - Éxito => `(resultado_str, None)`.

        Los fallos transitorios de la tool (red, timeouts) se reintentan
        vía `_con_reintentos`; si aun así fallan, o el error no era
        transitorio, el mensaje termina en `AgentStep.error` y se
        realimenta al LLM como observación — el error vuelve al loop, no
        lo rompe.
        """
        tool = self._tools.get(call.name)
        if tool is None:
            return None, f"Herramienta desconocida: {call.name!r}."

        try:
            kwargs = json.loads(call.arguments) if call.arguments else {}
        except json.JSONDecodeError as exc:
            return None, f"Argumentos JSON inválidos para {call.name!r}: {exc}."

        try:
            return self._con_reintentos(lambda: tool(**kwargs)), None
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

        Mecanismo: se le ofrece al LLM una única herramienta sintética,
        `final_result`, cuyo JSON Schema de argumentos ES el `schema`
        Pydantic pedido. "Responder" pasa a ser "invocar esa tool con
        argumentos válidos": el schema es la firma de la tool y la
        condición de aceptación a la vez. No se registra con
        `register_tool` porque no ejecuta nada — es solo el cierre.

        Reparación: hasta `1 + max_repair_attempts` llamadas. Cada modo de
        fallo recibe una respuesta distinta para que el modelo pueda
        corregirse:
          - argumentos inválidos (JSON roto / ValidationError) → mensaje
            `role:"tool"` con el detalle del error;
          - texto libre → mensaje `role:"user"` de reparación;
          - tool alucinada → mensaje `role:"tool"` indicando que solo
            existe `final_result`.
        Agotados los intentos levanta `SalidaEstructuradaError` (nunca
        devuelve `None` ni instancias parciales).

        Memoria: el prompt y el resultado validado se persisten en la
        conversación (los `run` posteriores los ven); los intentos de
        reparación quedan locales a esta llamada. Si todo falla, el
        historial no se toca. La ventana (`_ventana`) aplica igual que en
        `run`: ninguna llamada supera `max_history_messages` mensajes.
        """
        tool_de_cierre = final_result_tool_schema(schema)
        # Lista de trabajo local: la conversación + el prompt + los
        # intercambios de reparación. Recién se persiste al tener éxito.
        trabajo = list(self._history) + [{"role": "user", "content": prompt}]
        ultima_causa: Exception | None = None
        detalle_final = "el modelo no produjo una salida válida"

        for _ in range(1 + max_repair_attempts):
            response = self._con_reintentos(
                lambda: self._llm.chat(
                    messages=self._ventana(trabajo),
                    tools=[tool_de_cierre],
                    system=self._system,
                )
            )

            # Caso 1: texto libre, sin tool_calls => pedir el formato.
            if not response.tool_calls:
                detalle_final = "el modelo respondió texto libre en lugar de invocar final_result"
                trabajo.append(
                    {"role": "assistant", "content": response.content or ""}
                )
                trabajo.append(
                    {
                        "role": "user",
                        "content": (
                            "Tu respuesta anterior fue texto libre y no sirve. "
                            f"Invocá la herramienta {FINAL_RESULT_TOOL_NAME} con "
                            "argumentos que respeten exactamente su schema; no "
                            "respondas con texto."
                        ),
                    }
                )
                continue

            # Hubo tool_calls: los registramos como turno del assistant y
            # respondemos cada uno (dejar un tool_call sin respuesta rompe
            # la coherencia <tool_call, tool_response> del historial).
            trabajo.append(self._assistant_turn(response))
            cierre = next(
                (tc for tc in response.tool_calls if tc.name == FINAL_RESULT_TOOL_NAME),
                None,
            )

            for call in response.tool_calls:
                if cierre is not None and call.id == cierre.id:
                    continue  # el cierre se evalúa después, con su propio mensaje
                detalle_final = f"el modelo invocó una herramienta inexistente: {call.name!r}"
                trabajo.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": (
                            f"Herramienta desconocida: {call.name!r}. La única "
                            f"disponible es {FINAL_RESULT_TOOL_NAME}; invocala "
                            "con argumentos válidos para terminar."
                        ),
                    }
                )
            if cierre is None:
                continue

            # Caso 2: llegó final_result => validar argumentos contra schema.
            try:
                datos = json.loads(cierre.arguments) if cierre.arguments else {}
                instancia = schema.model_validate(datos)
            except (json.JSONDecodeError, ValidationError) as exc:
                ultima_causa = exc
                detalle_final = f"los argumentos de {FINAL_RESULT_TOOL_NAME} no validan"
                trabajo.append(
                    {
                        "role": "tool",
                        "tool_call_id": cierre.id,
                        "content": (
                            f"Argumentos inválidos para {FINAL_RESULT_TOOL_NAME}: "
                            f"{exc}. Volvé a invocar la herramienta corrigiendo "
                            "exactamente esos campos."
                        ),
                    }
                )
                continue

            # Éxito: persistimos el intercambio limpio (prompt + resultado)
            # en la conversación; los intentos fallidos quedan afuera.
            self._history.append({"role": "user", "content": prompt})
            self._history.append(
                {"role": "assistant", "content": instancia.model_dump_json()}
            )
            return instancia

        raise SalidaEstructuradaError(
            f"structured_call agotó {1 + max_repair_attempts} intentos: "
            f"{detalle_final}."
        ) from ultima_causa
