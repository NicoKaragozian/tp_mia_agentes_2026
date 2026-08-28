"""Detección de ciclos improductivos sobre la secuencia de acciones.

El agente puede quedar atrapado repitiendo un puñado de acciones hasta
agotar el presupuesto de iteraciones. Detectarlo es más sutil de lo que
parece, y la sutileza está medida: sobre 180 corridas de evaluación, el 78 %
repite alguna acción y la primera repetición cae en el paso 3 tanto en las
corridas que terminan bien como en las que terminan mal. Peor: el 65 % de
las corridas que empiezan a repetir igual llegan a la meta.

Es decir, "repitió una acción" no distingue nada, y una intervención que se
dispare con esa señal castiga sobre todo a corridas sanas. Lo que sí separa
es la repetición **sostenida**: la diversidad de acciones dentro de una
ventana móvil.
"""

from __future__ import annotations

from collections import Counter

#: Ventana móvil y umbral de diversidad, elegidos por barrido sobre las 180
#: corridas baseline de la evaluación. Con estos valores la detección aparece
#: en el 100 % de las corridas que fracasan y solo en el 14 % de las que
#: triunfan, en el paso 19 (mediana), dejando unos 80 pasos de margen para
#: hacer algo al respecto. Ventanas más cortas o umbrales más altos suben la
#: falsa alarma sin ganar sensibilidad.
VENTANA_CICLO = 20
UMBRAL_CICLO = 0.5

Accion = tuple[str, str]


def hay_ciclo(
    acciones: list[Accion],
    ventana: int = VENTANA_CICLO,
    umbral: float = UMBRAL_CICLO,
) -> bool:
    """¿Las últimas `ventana` acciones son un ciclo improductivo?

    Una secuencia más corta que la ventana nunca lo es: hacen falta datos
    suficientes antes de acusar a nadie de estar dando vueltas.
    """
    if ventana <= 0:
        raise ValueError("la ventana tiene que ser positiva")
    if len(acciones) < ventana:
        return False
    tramo = acciones[-ventana:]
    return len(set(tramo)) / ventana < umbral


def resumen_del_ciclo(acciones: list[Accion], ventana: int = VENTANA_CICLO) -> str:
    """Lista las acciones repetidas de la ventana, de más a menos frecuente.

    Se usa para decirle al modelo qué está repitiendo exactamente. Un aviso
    genérico ("estás en un bucle") le deja el trabajo de descubrir cuál; uno
    concreto le ahorra ese paso.
    """
    # Sin esta validación, `ventana=0` haría `acciones[-0:]`, que en Python es
    # la lista ENTERA y no la lista vacía. El resumen pasaría a describir toda
    # la historia en lugar de la ventana reciente, en silencio.
    if ventana <= 0:
        raise ValueError("la ventana tiene que ser positiva")
    conteo = Counter(acciones[-ventana:])
    repetidas = [(a, n) for a, n in conteo.most_common() if n > 1]
    if not repetidas:
        return ""
    return "; ".join(
        f"{herramienta}({args}) {n} veces" for (herramienta, args), n in repetidas
    )
