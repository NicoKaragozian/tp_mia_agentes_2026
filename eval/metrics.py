"""Métricas cuantitativas sobre un conjunto de trazas.

Dos decisiones que el informe tiene que justificar:

1. **La métrica principal es la tasa de éxito según `check_goal`**, que
   inspecciona el *estado del mundo*, no el texto del agente. Un agente
   puede afirmar con total convicción "¡abrí la puerta!" sin haberla
   abierto (de hecho pasa). Medir sobre el mundo hace la métrica inmune a
   la elocuencia del modelo.

2. **La métrica secundaria es la eficiencia contra el óptimo conocido**,
   que el enunciado publica por escenario. Llegar a la meta en 23 pasos
   cuando se puede en 11 es un éxito, pero uno caro: sin esta segunda
   métrica, "resolvió" y "resolvió dando vueltas" se ven igual.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from math import comb
from typing import Any, Iterable

from eval.analysis import fraccion_repetidas


def _media(valores: Iterable[float]) -> float:
    datos = [v for v in valores if v is not None]
    return statistics.fmean(datos) if datos else 0.0


def _mediana(valores: Iterable[float]) -> float:
    """Mediana: resistente a corridas atípicas.

    Hace falta: una corrida quedó registrada en 6207 s (la máquina estuvo
    inactiva mientras la evaluación corría desatendida) contra una mediana
    de 12 s. Esa única observación multiplicaba por 30 la media de su
    condición. La latencia se reporta por mediana; la media queda a la
    vista para que la diferencia entre ambas delate estos casos.
    """
    datos = [v for v in valores if v is not None]
    return statistics.median(datos) if datos else 0.0


@dataclass
class Resumen:
    """Métricas agregadas de un grupo de corridas."""

    n: int
    descartadas: int
    exitos: int
    tasa_exito: float
    eficiencia_media: float          # solo sobre las exitosas
    pasos_medios: float
    repeticion_media: float
    llamadas_llm_medias: float
    tokens_entrada_medios: float
    tokens_salida_medios: float
    latencia_media_s: float
    latencia_mediana_s: float

    def como_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "descartadas": self.descartadas,
            "exitos": self.exitos,
            "tasa_exito": round(self.tasa_exito, 3),
            "eficiencia_media": round(self.eficiencia_media, 3),
            "pasos_medios": round(self.pasos_medios, 1),
            "repeticion_media": round(self.repeticion_media, 3),
            "llamadas_llm_medias": round(self.llamadas_llm_medias, 1),
            "tokens_entrada_medios": round(self.tokens_entrada_medios),
            "tokens_salida_medios": round(self.tokens_salida_medios),
            "latencia_media_s": round(self.latencia_media_s, 1),
            "latencia_mediana_s": round(self.latencia_mediana_s, 1),
        }


def eficiencia(traza: dict[str, Any]) -> float | None:
    """`óptimo / pasos usados`, acotada a 1.0. `None` si no llegó a la meta.

    Solo tiene sentido en corridas exitosas: en las fallidas, "pocos pasos"
    puede significar que se rindió enseguida, que es lo contrario de ser
    eficiente.
    """
    if not traza.get("meta_lograda"):
        return None
    pasos = len(traza.get("pasos") or [])
    optimo = traza.get("optimo") or 0
    if pasos == 0 or optimo == 0:
        return None
    return min(1.0, optimo / pasos)


def resumir(trazas: list[dict[str, Any]]) -> Resumen:
    """Agrega un grupo de corridas en un `Resumen`.

    Las corridas con `fallo_infra` se **excluyen** de todos los agregados y
    se cuentan aparte en `descartadas`. Una corrida que reventó por
    infraestructura es una observación contaminada: sus pasos, tokens y
    latencia quedaron truncados en un punto arbitrario, así que promediarla
    junto al resto ensucia cada métrica. Que el contador sea visible obliga
    a mirar cuántas se perdieron en lugar de que desaparezcan en silencio.
    """
    descartadas = [t for t in trazas if t.get("fallo_infra")]
    trazas = [t for t in trazas if not t.get("fallo_infra")]
    n = len(trazas)
    exitosas = [t for t in trazas if t.get("meta_lograda")]
    return Resumen(
        n=n,
        descartadas=len(descartadas),
        exitos=len(exitosas),
        tasa_exito=(len(exitosas) / n) if n else 0.0,
        eficiencia_media=_media(e for e in (eficiencia(t) for t in exitosas) if e),
        pasos_medios=_media(len(t.get("pasos") or []) for t in trazas),
        repeticion_media=_media(
            fraccion_repetidas(t.get("pasos") or []) for t in trazas
        ),
        llamadas_llm_medias=_media(t.get("n_llamadas_llm") or 0 for t in trazas),
        tokens_entrada_medios=_media(t.get("input_tokens") or 0 for t in trazas),
        tokens_salida_medios=_media(t.get("output_tokens") or 0 for t in trazas),
        latencia_media_s=_media(t.get("latencia_s") or 0.0 for t in trazas),
        latencia_mediana_s=_mediana(t.get("latencia_s") or 0.0 for t in trazas),
    )


def agrupar_por(
    trazas: list[dict[str, Any]], clave: str
) -> dict[str, Resumen]:
    """Resume las trazas agrupándolas por un campo (`escenario`, `condicion`...)."""
    grupos: dict[str, list[dict[str, Any]]] = {}
    for t in trazas:
        grupos.setdefault(str(t.get(clave)), []).append(t)
    return {k: resumir(v) for k, v in sorted(grupos.items())}


# --- confiabilidad: pass@k y pass^k ------------------------------------------


def pass_at_k(n: int, exitos: int, k: int) -> float:
    """Probabilidad de que al menos uno de `k` intentos llegue a la meta.

    Estimador insesgado `1 - C(n-e, k) / C(n, k)`, el mismo que usa la
    literatura de generación de código. Responde "¿sirve si lo reintento?".

    Ojo con el caso degenerado: si `n - exitos < k` no quedan suficientes
    fracasos para formar una muestra de k que falle entera, y el estimador
    devuelve 1,0 por construcción. Con n = 10 el valor de `pass@10` no dice
    nada sobre el sistema, solo que en esas diez corridas hubo algún éxito.
    """
    if not 0 <= exitos <= n or k < 1:
        raise ValueError("n, exitos y k inconsistentes")
    if n - exitos < k:
        return 1.0
    return 1.0 - comb(n - exitos, k) / comb(n, k)


def pass_pow_k(n: int, exitos: int, k: int) -> float:
    """Probabilidad de que `k` intentos acierten **todos**.

    Estimador `C(e, k) / C(n, k)`. Responde "¿puedo confiar en él?", que es
    una pregunta bastante más dura que la de `pass_at_k` y la que importa si
    el agente va a correr sin nadie mirando.
    """
    if not 0 <= exitos <= n or k < 1:
        raise ValueError("n, exitos y k inconsistentes")
    if exitos < k:
        return 0.0
    return comb(exitos, k) / comb(n, k)
