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


def presupuesto_iteraciones(escenario_id: str = "") -> int:
    """Tope de iteraciones del bucle. **El mismo para todos los escenarios.**

    Por qué no un número chico: cada iteración del bucle es UNA llamada al
    LLM, y si el modelo pide una herramienta por turno, un escenario de 21
    llamadas óptimas necesita al menos 22 iteraciones. Con el default del
    framework (10) los escenarios largos fallarían por límite antes de que el
    modelo tuviera oportunidad de razonar mal, y el análisis de errores
    estaría midiendo nuestro techo en lugar de al agente.

    Por qué uniforme y no proporcional a cada escenario: el criterio de
    aprobación exige "el mismo agente en los tres niveles, sin trucos por
    escenario". Un presupuesto derivado del óptimo de cada caso usa
    información que el agente no tiene por qué conocer — sería ajustar la
    configuración a la respuesta. El valor se fija una sola vez desde el peor
    caso del dataset (`2 × máximo óptimo + 8`), y ese mismo número rige para
    los ocho escenarios.

    El valor NO se eligió a ojo: sale del experimento E4, que comparó 25, 50
    y 100 iteraciones sobre los dos escenarios más difíciles y encontró una
    mejora monótona (38% -> 56% -> 81%). Con 50, los éxitos de office-sequence
    se acumulaban exactamente en el techo, señal de que el tope estaba
    cortando corridas que iban camino a resolver.

    El parámetro se mantiene por compatibilidad con las llamadas existentes,
    pero no se usa: el presupuesto no depende del escenario.
    """
    return 100


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
    descripcion="Prompt especializado, ventana de 50 mensajes.",
    overrides={
        "system_prompt": PROMPT_SALA_DE_ESCAPE,
        "max_history_messages": 50,
        "memoria_de_acciones": False,
    },
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

#: E3 — memoria de acciones. Mide si el registro compacto de lo ya ejecutado,
#: inyectado en el system prompt (fuera del presupuesto de la ventana),
#: reduce el bucle. Es la memoria episódica que el informe del M3 había
#: dejado anotada como trabajo futuro.
E3_ACCIONES = [
    BASELINE,
    Condicion(
        nombre="con_memoria_acciones",
        descripcion="Baseline más el registro de acciones ya ejecutadas.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": True,
        },
    ),
]

#: E4 — presupuesto de pasos. El enunciado sugiere "reducir max steps" como
#: experimento; medimos también el inverso, porque 10 de 14 éxitos de
#: office-sequence terminaron exactamente en el techo de 50: si el tope está
#: cortando corridas que iban a resolver, subirlo debería mover la tasa.
E4_PRESUPUESTO = [
    BASELINE,
    Condicion(
        nombre="presupuesto_100",
        descripcion="Baseline con el doble de iteraciones (100).",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "max_iterations": 100,
        },
    ),
    Condicion(
        nombre="presupuesto_25",
        descripcion="Baseline con la mitad de iteraciones (25).",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "max_iterations": 25,
        },
    ),
]

#: E5 — bloqueo de repeticiones estériles. El 100% de los fracasos con Nova
#: Lite son bucles; avisarle al modelo no sirvió (E3), así que acá se le
#: impide ejecutar la repetición.
E5_BLOQUEO = [
    BASELINE,
    Condicion(
        nombre="con_bloqueo",
        descripcion="Baseline que se niega a ejecutar repeticiones estériles.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "bloquear_repeticiones": True,
        },
    ),
]

#: E6 — planificación explícita. Único intento arquitectónico: en vez de
#: ajustar un parámetro del bucle reactivo, el agente escribe un plan de
#: E7 — reflexión ante un ciclo. El bucle es el único modo de fallo que
#: sobrevive con Nova Lite. E5 lo atacó prohibiendo repeticiones y empeoró; el
#: diagnóstico posterior mostró por qué (disparaba en el paso 3, sobre
#: corridas que se recuperaban solas). Acá el disparador está calibrado sobre
#: las trazas y la respuesta es pedir replanteo en lugar de prohibir.
E7_REFLEXION = [
    BASELINE,
    Condicion(
        nombre="con_reflexion",
        descripcion="Baseline más un turno de reflexión al detectar un ciclo.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "reflexionar": True,
        },
    ),
]

#: E8 — temperatura. Las 834 corridas anteriores usaron el default de 0,2 sin
#: excepción. El bucle es una patología de repetición y la temperatura es la
#: perilla más directa sobre repetición que existe, así que dejarla fija era
#: una variable no controlada.
E8_TEMPERATURA = [
    BASELINE,
    Condicion(
        nombre="temperatura_05",
        descripcion="Baseline con temperatura 0,5.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "temperatura": 0.5,
        },
    ),
    Condicion(
        nombre="temperatura_09",
        descripcion="Baseline con temperatura 0,9.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "temperatura": 0.9,
        },
    ),
]

#: E9 — herramientas distractoras. El runner corre sin las tools de M1/M2
#: porque "son distractores que ocupan contexto"; eso venía siendo una
#: afirmación del código que nadie había medido.
E9_DISTRACTORES = [
    BASELINE,
    Condicion(
        nombre="con_distractores",
        descripcion="Baseline más las tools de M1/M2, que no resuelven nada acá.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "memoria_de_acciones": False,
            "tools_por_defecto": True,
        },
    ),
]


#: sub-objetivos antes de empezar y lo mantiene en el system prompt.
E6_PLANNER = [
    BASELINE,
    Condicion(
        nombre="con_planner",
        descripcion="Baseline que planifica sub-objetivos antes de actuar.",
        overrides={
            "system_prompt": PROMPT_SALA_DE_ESCAPE,
            "max_history_messages": 50,
            "planificar": True,
        },
    ),
]

EXPERIMENTOS: dict[str, list[Condicion]] = {
    "e1-memoria": E1_MEMORIA,
    "e2-prompt": E2_PROMPT,
    "e3-acciones": E3_ACCIONES,
    "e4-presupuesto": E4_PRESUPUESTO,
    "e5-bloqueo": E5_BLOQUEO,
    "e6-planner": E6_PLANNER,
    "e7-reflexion": E7_REFLEXION,
    "e8-temperatura": E8_TEMPERATURA,
    "e9-distractores": E9_DISTRACTORES,
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
    "e3-acciones": (
        "El bucle es el modo de fallo dominante y su causa medida es que el "
        "agente pierde de vista lo que ya intentó: una corrida larga genera "
        "más mensajes de los que entran en la ventana. Agrandar la ventana no "
        "sirve (con 160 mensajes la repetición subió a 74%: más contexto "
        "diluye la atención). La hipótesis es que un registro DEDUPLICADO de "
        "acciones ya ejecutadas, inyectado en el system prompt y por lo tanto "
        "fuera del presupuesto de la ventana, baja la fracción de llamadas "
        "repetidas y sube la tasa de éxito. Refutaría la hipótesis que la "
        "repetición no baje — indicaría que el agente sí ve sus intentos "
        "previos y aun así insiste, o sea que el problema es de razonamiento "
        "y no de memoria."
    ),
    "e4-presupuesto": (
        "Los éxitos de office-sequence se acumulan exactamente en el techo de "
        "50 pasos (10 de 14), lo que sugiere que el tope está cortando "
        "corridas que iban camino a resolver. Si es así, duplicarlo a 100 debe "
        "subir la tasa de éxito y bajarla a 25 debe hundirla. Refutaría la "
        "hipótesis que 100 no mejore: significaría que las corridas que agotan "
        "el presupuesto ya están cicladas y más pasos solo son más repetición "
        "(los fracasos hacen 50 pasos con apenas 7-8 acciones distintas, así "
        "que esta refutación es plausible)."
    ),
    "e5-bloqueo": (
        "El 100% de los fracasos medidos con Nova Lite son bucles, y las "
        "corridas fallidas gastan 50-100 pasos ejecutando apenas 7-8 acciones "
        "distintas. Avisarle al modelo que estaba repitiendo no tuvo ningún "
        "efecto (E3). La hipótesis es que IMPEDIRLE ejecutar una repetición ya "
        "demostrada estéril lo fuerza a explorar otra rama y sube la tasa de "
        "éxito. Refutaría la hipótesis que la tasa no suba: significaría que "
        "el agente, bloqueado en una acción, simplemente cicla entre otras "
        "acciones igual de estériles, y que el problema no es la repetición "
        "sino que no se le ocurre qué más hacer."
    ),
    "e6-planner": (
        "Siete intervenciones sobre el bucle reactivo no movieron la tasa de "
        "éxito. E5 mostró por qué: el agente no falla porque repita, repite "
        "porque se quedó sin ideas, y bloquearle caminos no le crea uno nuevo. "
        "La hipótesis es que un plan de sub-objetivos escrito ANTES de actuar "
        "—y sostenido en el system prompt, fuera del presupuesto de la "
        "ventana, así sigue visible cuando el historial ya se recortó— le da "
        "al agente adónde ir cuando se queda sin ideas, y sube la tasa de "
        "éxito por encima del 80% del baseline. El enunciado sugiere este "
        "camino para office-sequence, cuya meta es compuesta y ordenada. "
        "Refutaría la hipótesis que la tasa no suba: significaría que el "
        "problema no es la falta de un plan sino la incapacidad del modelo "
        "para ejecutarlo, y que ninguna estructura que le demos alcanza."
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
    "e7-reflexion": (
        "Un turno de reflexión disparado por repetición SOSTENIDA sube la tasa "
        "de éxito respecto del baseline, a diferencia de E5. El disparador "
        "calibrado aparece en el 100 % de las corridas que fracasan y solo en "
        "el 14 % de las que triunfan, con unos 80 pasos de margen por delante, "
        "así que la intervención llega a tiempo y casi no molesta a quien iba "
        "bien. Riesgo asumido: el 14 % de falsa alarma puede descarrilar "
        "corridas sanas, igual que en E5 pero mucho menos seguido."
    ),
    "e8-temperatura": (
        "Subir la temperatura reduce el bucle, porque el ciclo es un atractor "
        "determinista y basta ruido para salir. Esperamos una curva en U: 0,5 "
        "mejor que 0,2 por romper ciclos, y 0,9 peor que 0,5 porque el ruido "
        "empieza a arruinar la disciplina de tool calling."
    ),
    "e9-distractores": (
        "Agregar las tres tools de M1/M2 baja la tasa de éxito y sube el "
        "consumo de tokens. Es la afirmación que el código viene haciendo sin "
        "haberla medido; si el efecto resulta nulo, el comentario hay que "
        "corregirlo."
    ),
}
