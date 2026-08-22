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
    """Agrega un grupo de corridas en un `Resumen`."""
    n = len(trazas)
    exitosas = [t for t in trazas if t.get("meta_lograda")]
    return Resumen(
        n=n,
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
