"""Herramienta 1: calculadora aritmética binaria (cómputo puro).

Función pura `fn(...) -> str` + su `ToolSchema` derivado con
`ToolSchema.from_callable`. No conoce el bucle del agente: se testea sola.

M2 — errores recuperables: la firma declara `float`, pero el LLM arma los
argumentos como JSON y puede mandar cualquier cosa ("cuarenta", null, un
bool). En vez de crashear, cada error devuelve un mensaje accionable que
nombra QUÉ parámetro falló, QUÉ valor llegó y POR QUÉ no sirve, para que
el modelo pueda corregirse en el siguiente intento.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from mia_agents.types import ToolSchema

#: Operadores soportados (los del enunciado + división para cubrir el caso
#: de "división por cero"). Sin `eval`: solo la operación binaria indicada.
_OPERADORES = frozenset({"+", "-", "*", "%", "/"})

#: Cómo se muestran los operadores permitidos en los mensajes de error.
_OPERADORES_LEGIBLES = "+ - * % /"


def _como_numero(nombre: str, valor: Any) -> tuple[float | None, str | None]:
    """Coerciona `valor` a float; si no puede, explica el fallo.

    Devuelve `(numero, None)` en éxito o `(None, mensaje)` en error. Se
    aceptan int/float y strings numéricos ("3.5"): son errores de formato
    triviales del LLM que no vale la pena rebotar. Un bool se rechaza
    explícitamente (en Python `True` ES un int, pero como operando casi
    seguro es un argumento mal armado).
    """
    if isinstance(valor, bool):
        return None, (
            f"Error: el parámetro {nombre!r} recibió {valor!r}, que es un "
            f"booleano y no un número. Pasá un valor numérico, p. ej. "
            f"{nombre}=2."
        )
    if isinstance(valor, (int, float)):
        return float(valor), None
    if isinstance(valor, str):
        try:
            return float(valor.strip()), None
        except ValueError:
            pass
    return None, (
        f"Error: el parámetro {nombre!r} recibió {valor!r}, que no es un "
        f"número ni un texto numérico. Pasá un valor numérico, p. ej. "
        f"{nombre}=3.5."
    )


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
    los dos operandos. Ante un argumento inválido (operando no numérico,
    operador no soportado, división por cero) devuelve un mensaje de
    error accionable en lugar de lanzar una excepción.
    """
    a, error = _como_numero("operando_a", operando_a)
    if error is not None:
        return error
    b, error = _como_numero("operando_b", operando_b)
    if error is not None:
        return error

    if not isinstance(operador, str):
        return (
            f"Error: el parámetro 'operador' recibió {operador!r}, que no es "
            f"un string. Pasá uno de: {_OPERADORES_LEGIBLES}."
        )
    op = operador.strip()
    if op not in _OPERADORES:
        return (
            f"Error: operador no soportado {operador!r}. "
            f"Usá uno de: {_OPERADORES_LEGIBLES}."
        )
    if op in {"/", "%"} and b == 0:
        return (
            f"Error: división por cero: 'operando_b' vale 0 y la operación "
            f"{op!r} no está definida con divisor 0. Reintentá con un "
            f"'operando_b' distinto de 0."
        )

    if op == "+":
        resultado = a + b
    elif op == "-":
        resultado = a - b
    elif op == "*":
        resultado = a * b
    elif op == "%":
        resultado = a % b
    else:  # "/"
        resultado = a / b

    # Mostrar enteros sin la cola ".0" (4.0 -> "4"); el resto, como float.
    if isinstance(resultado, float) and resultado.is_integer():
        return str(int(resultado))
    return str(resultado)


calculadora_schema = ToolSchema.from_callable(calculadora)

#: Línea load-bearing del auto-descubrimiento (ver tools/__init__.py).
TOOLS = [(calculadora, calculadora_schema)]
