"""Ejecuta un caso de evaluación: un escenario bajo una condición.

Reutiliza el mundo FIJO de la cátedra (`load_scenario`, `make_world_tools`,
`check_goal`) directamente, sin pasar por `mia_world.cli`: necesitamos
inyectar configuración en el agente y quedarnos con la traza, cosas que la
CLI no expone. El patrón de registro es el mismo que usa `build_agent` con
el `REGISTRY` de nuestras tools: iterar `(fn, schema)` y llamar a
`register_tool`.
"""

from __future__ import annotations

import time
import traceback
from dataclasses import asdict, dataclass, field
from typing import Any

from mia_agents.llm_client import LLMClient
from mia_world.goals import check_goal
from mia_world.scenarios import load_scenario
from mia_world.state import Scenario
from mia_world.tools import make_world_tools

from eval.config import Condicion, DIR_ESCENARIOS, OPTIMOS, presupuesto_iteraciones
from eval.recording import ClienteGrabador

from student_framework import build_agent


@dataclass
class Paso:
    """Una invocación de herramienta, aplanada para el reporte."""

    indice: int
    herramienta: str | None
    argumentos: str | None
    salida: str | None
    error: str | None


@dataclass
class Traza:
    """Todo lo observable de una corrida. Serializable a JSON."""

    escenario: str
    dificultad: str
    condicion: str
    repeticion: int
    modelo: str
    meta_lograda: bool
    meta_razon: str
    optimo: int
    pasos: list[Paso] = field(default_factory=list)
    llamadas_llm: list[dict[str, Any]] = field(default_factory=list)
    #: Lo que vio el modelo en su última llamada, ya recortado por la ventana.
    ultimo_contexto: list[dict[str, Any]] = field(default_factory=list)
    n_llamadas_llm: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    latencia_s: float = 0.0
    corte: str | None = None
    respuesta: str = ""
    fallo_infra: str | None = None

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def _escenario(spec: str) -> Scenario:
    """Resuelve un id de escenario a su `Scenario` cargado desde JSON."""
    from mia_world.scenarios import list_scenarios

    for sc in list_scenarios(DIR_ESCENARIOS):
        if sc.id == spec:
            return sc
    path = DIR_ESCENARIOS / spec
    if path.is_file():
        return load_scenario(path)
    raise SystemExit(f"Escenario desconocido: {spec!r}")


def ejecutar_caso(
    escenario_id: str,
    condicion: Condicion,
    repeticion: int = 0,
    modelo: str = "",
    cliente: Any | None = None,
) -> Traza:
    """Corre un escenario bajo una condición y devuelve su traza.

    Nunca lanza por culpa del agente: un fallo de infraestructura (el
    proveedor caído, por ejemplo) queda registrado en `fallo_infra` para
    que una corrida larga no se pierda entera por un caso.
    """
    escenario = _escenario(escenario_id)
    mundo = escenario.initial_world

    grabador = ClienteGrabador(cliente if cliente is not None else LLMClient.from_env())
    config: dict[str, Any] = {
        "llm_client": grabador,
        "max_iterations": presupuesto_iteraciones(escenario_id),
        # Sin las tools de M1/M2: en la sala de escape son distractores que
        # no resuelven nada y ocupan contexto en cada llamada.
        "tools_por_defecto": False,
        **condicion.overrides,
    }
    agente = build_agent(config)
    for fn, schema in make_world_tools(mundo):
        agente.register_tool(fn, schema)

    traza = Traza(
        escenario=escenario.id,
        dificultad=escenario.difficulty,
        condicion=condicion.nombre,
        repeticion=repeticion,
        modelo=modelo,
        meta_lograda=False,
        meta_razon="(no ejecutado)",
        optimo=OPTIMOS.get(escenario.id, 0),
    )

    inicio = time.perf_counter()
    try:
        resultado = agente.run(escenario.user_message)
        traza.respuesta = resultado.answer
        traza.corte = resultado.error
        traza.input_tokens = resultado.input_tokens
        traza.output_tokens = resultado.output_tokens
        traza.pasos = [
            Paso(
                indice=i,
                herramienta=p.tool_name,
                argumentos=p.tool_input,
                salida=p.tool_output,
                error=p.error,
            )
            for i, p in enumerate(resultado.steps)
        ]
    except Exception:
        # El agente propaga errores no recuperables (política de M2). Que
        # un caso reviente no debe tumbar la corrida entera.
        traza.fallo_infra = traceback.format_exc(limit=3)

    traza.latencia_s = time.perf_counter() - inicio
    traza.llamadas_llm = grabador.como_dicts()
    traza.ultimo_contexto = grabador.ultimo_contexto
    traza.n_llamadas_llm = len(grabador.llamadas)

    # La meta se evalúa SIEMPRE sobre el estado del mundo, no sobre lo que
    # el agente diga haber hecho: es lo que la hace una métrica fiable.
    lograda, razon = check_goal(mundo, escenario.goal)
    traza.meta_lograda = bool(lograda)
    traza.meta_razon = razon
    return traza
