"""Configuración de la evaluación: escenarios, presupuestos y condiciones.

Todo lo que en el informe hay que justificar como "decisión de diseño"
vive acá, en un solo lugar y con su porqué escrito al lado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from student_framework.prompts import PROMPT_GENERICO, PROMPT_SALA_DE_ESCAPE

RAIZ = Path(__file__).resolve().parent.parent
DIR_ESCENARIOS = RAIZ / "scenarios"
DIR_RESULTADOS = Path(__file__).resolve().parent / "results"

#: Llamadas a herramientas de la solución óptima de cada escenario, según
#: la tabla del enunciado (ENUNCIADO_M3.md). Es la referencia contra la
#: que medimos eficiencia: un agente que resuelve en 8 pasos algo que se
#: resuelve en 3 llegó a la meta, pero dando vueltas.
OPTIMOS: dict[str, int] = {
    "study-with-key": 3,
    "color-locks": 11,
    "apartment-keys": 7,
    "library-search": 7,
    "office-sequence": 13,
    "extreme-archive": 4,
    "vault-combination": 21,
    "backtracking-vault": 18,
}

#: Orden de dificultad creciente, para los desgloses del informe.
ORDEN_ESCENARIOS: list[str] = list(OPTIMOS)


def presupuesto_iteraciones(escenario_id: str) -> int:
    """Tope de iteraciones del bucle para un escenario.

    Por qué no un número fijo: cada iteración del bucle es UNA llamada al
    LLM, y si el modelo pide una herramienta por turno, un escenario de 21
    llamadas óptimas necesita al menos 22 iteraciones. Con el default del
    framework (10) los escenarios largos fallarían por límite antes de que
    el modelo tuviera oportunidad de razonar mal, y el análisis de errores
    estaría midiendo nuestro techo en lugar de al agente.

    La fórmula `2 * óptimo + 8` da margen para explorar y equivocarse
    (aproximadamente el doble del camino ideal) sin volverse infinita, y
    escala con la dificultad en vez de regalarle presupuesto de escenario
    difícil a uno fácil.
    """
    return 2 * OPTIMOS.get(escenario_id, 10) + 8


@dataclass(frozen=True)
class Condicion:
    """Una configuración del agente bajo la que se corre el dataset.

    `nombre` identifica la condición en los resultados; `overrides` son
    claves que se pasan tal cual a `build_agent(config)`.
    """

    nombre: str
    descripcion: str
    overrides: dict = field(default_factory=dict)


#: Condición de referencia: el agente tal como lo especializamos para el
#: mundo. Todos los experimentos se comparan contra esta.
BASELINE = Condicion(
    nombre="baseline",
    descripcion="Prompt especializado, ventana amplia (50 mensajes).",
    overrides={"system_prompt": PROMPT_SALA_DE_ESCAPE, "max_history_messages": 50},
)

#: E1 — presupuesto de memoria. Mide el trabajo de M2: qué pasa cuando la
#: ventana deslizante recorta agresivamente el historial.
E1_MEMORIA = [
    BASELINE,
    Condicion(
        nombre="memoria_ajustada",
        descripcion="Prompt especializado, ventana de 8 mensajes.",
        overrides={"system_prompt": PROMPT_SALA_DE_ESCAPE, "max_history_messages": 8},
    ),
    Condicion(
        nombre="memoria_minima",
        descripcion="Prompt especializado, ventana de 4 mensajes.",
        overrides={"system_prompt": PROMPT_SALA_DE_ESCAPE, "max_history_messages": 4},
    ),
]

#: E2 — system prompt. Control = el default del scaffold, sin noción del
#: mundo; tratamiento = la especialización del M3.
E2_PROMPT = [
    Condicion(
        nombre="prompt_generico",
        descripcion="Prompt por defecto del framework ('Eres un asistente útil').",
        overrides={"system_prompt": PROMPT_GENERICO, "max_history_messages": 50},
    ),
    BASELINE,
]

EXPERIMENTOS: dict[str, list[Condicion]] = {
    "e1-memoria": E1_MEMORIA,
    "e2-prompt": E2_PROMPT,
}


#: Hipótesis de cada experimento, escritas ANTES de correrlos (quedan en el
#: historial de git en un commit anterior al de los resultados). Un
#: experimento cuya hipótesis se refuta enseña más que uno amañado.
HIPOTESIS: dict[str, str] = {
    "e1-memoria": (
        "El modo de fallo dominante del baseline es el bucle: el agente "
        "reinvoca acciones que ya ejecutó (51% de las llamadas en el piloto, "
        "hasta 88% en vault-combination). Si repetir se debe a que el agente "
        "no VE en su contexto que ya hizo esa acción, entonces recortar la "
        "ventana debería empeorarlo de forma monótona: esperamos que al bajar "
        "max_history_messages de 50 a 8 y a 4 suba la fracción de llamadas "
        "repetidas y baje la tasa de éxito. Refutaría la hipótesis que la "
        "repetición no cambie (el bucle vendría de la política del modelo, no "
        "de la memoria) o que una ventana más chica ayude (menos contexto, "
        "menos distracción)."
    ),
    "e2-prompt": (
        "El prompt genérico del framework produce conducta de asistente "
        "conversacional, no de agente: en las pruebas manuales el modelo hizo "
        "un look y le preguntó al usuario qué hacer, terminando el bucle con "
        "la puerta cerrada. Esperamos que el prompt especializado suba la "
        "tasa de éxito y reduzca las paradas prematuras. Refutaría la "
        "hipótesis que la diferencia sea nula, lo que indicaría que el cuello "
        "de botella es la capacidad del modelo y no la instrucción."
    ),
}
