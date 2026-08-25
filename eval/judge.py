"""Dimensión cualitativa: LLM-as-judge con salida estructurada.

Por qué un juez y no solo métricas duras: la tasa de éxito dice *si* el
agente llegó, no *cómo se comportó*. Dos corridas fallidas pueden ser muy
distintas — una que exploró con criterio y se quedó sin presupuesto, y otra
que repitió la misma acción veinte veces — y para el análisis de errores esa
diferencia es justamente lo que importa.

Por qué usa `structured_call`: un juez que responde en prosa hay que
parsearlo con expresiones regulares y reza que el formato se respete. Con la
herramienta sintética `final_result` del M2, el veredicto llega como un
`BaseModel` validado por Pydantic, con reparación automática si el modelo se
desvía. Es la maquinaria del M2 puesta a trabajar en un caso real, y de paso
la mejor demostración de para qué servía.

Limitación asumida y documentada: el juez corre sobre el mismo modelo local
que el agente evaluado. Un modelo chico juzgándose a sí mismo es un juez
ruidoso; sus notas se leen como señal cualitativa comparativa entre
condiciones, no como verdad absoluta.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field

from eval.config import OPTIMOS


class Veredicto(BaseModel):
    """Rúbrica del juez. El schema ES el contrato de salida."""

    coherencia_plan: Annotated[
        int,
        Field(ge=1, le=5, description="1: acciones sin relación con el objetivo. 5: plan claro y progresivo."),
    ]
    recuperacion_errores: Annotated[
        int,
        Field(ge=1, le=5, description="1: repite la acción fallida sin cambiar nada. 5: lee el error y corrige."),
    ]
    exploracion_eficiente: Annotated[
        int,
        Field(ge=1, le=5, description="1: repite acciones ya hechas. 5: cada acción aporta información nueva."),
    ]
    justificacion: Annotated[
        str,
        Field(description="Dos o tres frases explicando las notas."),
    ]


def resumen_de_traza(traza: dict[str, Any], tope_pasos: int = 40) -> str:
    """Compacta una traza a algo que quepa cómodo en el prompt del juez.

    Se envía la secuencia de acciones con su desenlace, no la prosa completa
    del mundo: al juez le importa la conducta del agente, y meterle 16K
    tokens de expedientes lo distraería del análisis.
    """
    lineas = [
        f"Escenario: {traza['escenario']} (dificultad {traza['dificultad']})",
        f"Objetivo alcanzado: {'sí' if traza['meta_lograda'] else 'no'} "
        f"— {traza['meta_razon']}",
        f"Llamadas óptimas conocidas: {OPTIMOS.get(traza['escenario'], '?')}; "
        f"realizadas: {len(traza.get('pasos') or [])}",
        "",
        "Secuencia de acciones:",
    ]
    pasos = traza.get("pasos") or []
    for paso in pasos[:tope_pasos]:
        desenlace = paso.get("error") or (paso.get("salida") or "")
        marca = "ERROR" if (paso.get("error") or desenlace.startswith("Error")) else "ok"
        lineas.append(
            f"  {paso['indice']:>3}. {paso['herramienta']}({paso['argumentos']}) "
            f"[{marca}] {desenlace[:110]}"
        )
    if len(pasos) > tope_pasos:
        lineas.append(f"  … {len(pasos) - tope_pasos} acciones más (omitidas)")
    if traza.get("corte"):
        lineas.append(f"\nCorte del bucle: {traza['corte']}")
    return "\n".join(lineas)


SYSTEM_JUEZ = (
    "Sos un evaluador de agentes autónomos. Recibís la traza de un agente que "
    "intentó resolver una sala de escape y la puntuás con la rúbrica indicada. "
    "Sé estricto y objetivo: puntuás la CONDUCTA observable, no el resultado. "
    "Un agente puede fallar y aun así haber explorado con criterio, y puede "
    "acertar habiendo dado muchas vueltas."
)


def juzgar(
    traza: dict[str, Any],
    cliente: Any | None = None,
    max_repair_attempts: int = 2,
) -> dict[str, Any]:
    """Puntúa una traza. Devuelve el veredicto o el error del juez.

    Nunca lanza: si el juez no logra producir una salida válida tras las
    reparaciones, se registra y la evaluación sigue. Que falle el juez no
    puede tumbar una corrida de métricas de una hora.
    """
    from mia_agents.llm_client import LLMClient

    from student_framework import build_agent

    agente = build_agent(
        {
            "llm_client": cliente if cliente is not None else LLMClient.from_env(),
            "system_prompt": SYSTEM_JUEZ,
            "tools_por_defecto": False,
        }
    )
    prompt = (
        "Puntuá la siguiente traza según la rúbrica.\n\n"
        + resumen_de_traza(traza)
    )
    try:
        veredicto = agente.structured_call(
            prompt=prompt, schema=Veredicto, max_repair_attempts=max_repair_attempts
        )
    except Exception as exc:  # noqa: BLE001 — el juez es best-effort
        return {"error_juez": f"{type(exc).__name__}: {exc}"}
    return veredicto.model_dump()
