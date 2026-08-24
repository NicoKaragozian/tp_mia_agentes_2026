"""Planificación explícita previa al bucle reactivo (M3, intento 8).

Motivación medida, no intuición. Con Nova Lite el 100% de los fracasos son
bucles, y las corridas fallidas gastan 50-100 pasos ejecutando apenas 7-8
acciones distintas. El experimento E5 mostró que **impedirle** repetir no
ayuda: el agente no falla porque repita, repite porque se quedó sin ideas.
Ningún parámetro del bucle reactivo le da ideas.

Un planificador ataca eso otro: antes de tocar el mundo, el agente escribe
una secuencia de sub-objetivos. Ese plan viaja en el `system` —fuera del
presupuesto de la ventana deslizante— así que sigue visible cuando el
historial ya se recortó, que es exactamente el momento en que empiezan los
bucles.

El enunciado señala este camino para `office-sequence`, cuya meta es compuesta
y ordenada: dice que "premia a un agente que descompone y planifica el orden
de sub-objetivos en lugar de reaccionar paso a paso" y menciona el
experimento *planner explícito vs ReAct puro*.

El plan se pide con `structured_call` (M2): el schema garantiza que vuelve una
lista de pasos utilizable, con reparación automática si el modelo se desvía.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field


class Plan(BaseModel):
    """Plan inicial del agente. El schema es el contrato de salida."""

    objetivo: Annotated[
        str,
        Field(description="El objetivo final, en una frase."),
    ]
    pasos: Annotated[
        list[str],
        Field(
            min_length=2,
            max_length=10,
            description=(
                "Sub-objetivos en orden, uno por elemento. Cada uno debe ser "
                "una meta verificable ('conseguir la llave del cofre'), no una "
                "llamada concreta a una herramienta."
            ),
        ),
    ]


SYSTEM_PLANIFICADOR = (
    "Sos un agente que va a resolver una sala de escape por texto. Antes de "
    "actuar, planificás. Todavía NO conocés el contenido de la sala: tu plan "
    "debe ser una estrategia general de exploración y resolución, en el orden "
    "en que conviene abordarla."
)

PROMPT_PLANIFICAR = """\
Vas a resolver esta consigna en una sala de escape:

{consigna}

Herramientas disponibles: {herramientas}.

Escribí un plan de sub-objetivos en orden. Pensá en qué hace falta conseguir \
antes de qué: normalmente hay que observar la sala, examinar los contenedores \
para revelar lo que esconden, tomar los objetos útiles y recién entonces \
usarlos sobre las cerraduras. Si la consigna pide conseguir algo ADEMÁS de \
abrir la puerta, ese sub-objetivo va antes de abrirla."""


def bloque_de_plan(plan: Plan) -> str:
    """Formatea el plan para adjuntarlo al system prompt del bucle."""
    pasos = "\n".join(f"  {i}. {p}" for i, p in enumerate(plan.pasos, 1))
    return (
        f"\n\nTU PLAN (escrito por vos antes de empezar; seguilo en orden y "
        f"llevá la cuenta mental de en cuál estás):\nObjetivo: {plan.objetivo}\n"
        f"{pasos}\n"
        "Si un paso ya está cumplido, pasá al siguiente en lugar de repetir "
        "acciones. Si un paso resulta imposible, saltá al siguiente que sí "
        "puedas avanzar."
    )
