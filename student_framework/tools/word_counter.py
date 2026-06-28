from __future__ import annotations

from typing import Annotated

from pydantic import Field

from mia_agents.types import ToolSchema


def word_counter(
    text: Annotated[str, Field(description = "El texto cuyas palabras se van a contar.")],
) -> str:
    """Cuenta la cantidad de palabras en un texto.

    Separa el texto por espacios en blanco y devuelve la cantidad de palabras como texto.
    """
    words = text.split() # split() sin argumentos separa por cualquier espacio en blanco
    return str(len(words)) # len() cuenta los elementos, lo devolvemos como str

word_counter_schema = ToolSchema.from_callable(word_counter)

TOOLS = [(word_counter, word_counter_schema)] # línea load-bearing: sin esto el auto-descubrimiento no la encuentra