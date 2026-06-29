"""Herramienta 1 (M1): calculadora aritmética binaria (cómputo puro).

Función pura `fn(...) -> str` + su `ToolSchema` derivado con
`ToolSchema.from_callable`. No conoce el bucle del agente: se testea sola.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from mia_agents.types import ToolSchema

#: Operadores soportados (los del enunciado + división para cubrir el caso
#: de "división por cero"). Sin `eval`: solo la operación binaria indicada.
_OPERADORES = frozenset({"+", "-", "*", "%", "/"})


def calculadora(
    operando_a: Annotated[float, Field(description="Primer operando numérico.")],
    operando_b: Annotated[float, Field(description="Segundo operando numérico.")],
    operador: Annotated[
        str, Field(description="Operador aritmético: uno de + - * % /.")
    ],
) -> str:
    """Realiza una operación aritmética binaria entre dos números.

    Soporta los operadores + (suma), - (resta), * (multiplicación),
    % (módulo/resto) y / (división). Devuelve el resultado como texto.
    No evalúa expresiones arbitrarias: solo aplica la operación indicada a
    los dos operandos. Ante un operador inválido o una división por cero
    devuelve un mensaje de error (no lanza excepción).
    """
    op = operador.strip()
    if op not in _OPERADORES:
        return (
            f"Error: operador no soportado {operador!r}. "
            f"Usá uno de: + - * % /."
        )
    if op in {"/", "%"} and operando_b == 0:
        return "Error: división por cero."

    if op == "+":
        resultado = operando_a + operando_b
    elif op == "-":
        resultado = operando_a - operando_b
    elif op == "*":
        resultado = operando_a * operando_b
    elif op == "%":
        resultado = operando_a % operando_b
    else:  # "/"
        resultado = operando_a / operando_b

    # Mostrar enteros sin la cola ".0" (4.0 -> "4"); el resto, como float.
    if isinstance(resultado, float) and resultado.is_integer():
        return str(int(resultado))
    return str(resultado)


calculadora_schema = ToolSchema.from_callable(calculadora)

#: Línea load-bearing del auto-descubrimiento (ver tools/__init__.py).
TOOLS = [(calculadora, calculadora_schema)]
