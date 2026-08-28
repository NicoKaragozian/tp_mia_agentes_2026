"""Detección de ciclos improductivos en una traza.

El bucle es el único modo de fallo que sobrevive con Nova Lite: los 50
fracasos de la campaña baseline se clasifican así sin excepción. Este módulo
responde *cuándo* una corrida entra en el ciclo, que es distinto de *si*
repite alguna acción.

La distinción importa porque la intuición ingenua está mal. Sobre las 180
corridas baseline:

* el 78 % repite al menos una acción, y la primera repetición cae en el paso
  3 (mediana) tanto en las que fracasan como en las que triunfan, de modo que
  "repitió una acción" no separa nada;
* el 65 % de las corridas que empiezan a repetir **igual llegan a la meta**.

Por eso bloquear repeticiones (E5) empeoró el resultado: disparaba en el paso
3 de corridas sanas. Lo que sí separa es la repetición *sostenida*, medida
como la diversidad de acciones en una ventana móvil.
"""

from __future__ import annotations

from typing import Any

# Los umbrales viven con el agente, que es quien los usa en producción; acá
# solo se los aplica a las trazas ya grabadas. Duplicarlos sería garantizar
# que en algún momento discrepen.
from student_framework.ciclos import UMBRAL_CICLO, VENTANA_CICLO

__all__ = ["UMBRAL_CICLO", "VENTANA_CICLO", "detectar_ciclo", "primera_repeticion"]


def _clave(paso: dict[str, Any]) -> tuple[str, str]:
    """Identidad de una acción: herramienta más argumentos exactos."""
    return (paso.get("herramienta", ""), paso.get("argumentos", ""))


def primera_repeticion(pasos: list[dict[str, Any]]) -> int | None:
    """Índice del primer paso cuya acción ya se había ejecutado antes.

    Sirve para el diagnóstico, no como disparador: ocurre igual de temprano en
    las corridas que terminan bien.
    """
    visto: set[tuple[str, str]] = set()
    for paso in pasos:
        clave = _clave(paso)
        if clave in visto:
            return paso.get("indice")
        visto.add(clave)
    return None


def detectar_ciclo(
    pasos: list[dict[str, Any]],
    ventana: int = VENTANA_CICLO,
    umbral: float = UMBRAL_CICLO,
) -> int | None:
    """Índice del paso donde la corrida entra en un ciclo improductivo.

    Devuelve el primer paso en el que las últimas `ventana` acciones tienen
    una fracción de acciones distintas menor a `umbral`, o `None` si nunca
    ocurre. Una corrida con menos de `ventana` pasos nunca dispara.
    """
    if ventana <= 0:
        raise ValueError("la ventana tiene que ser positiva")

    for fin in range(ventana, len(pasos) + 1):
        tramo = pasos[fin - ventana : fin]
        if len({_clave(p) for p in tramo}) / ventana < umbral:
            return tramo[-1].get("indice")
    return None
