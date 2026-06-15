"""Tests de generación de ToolSchema desde callables."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import Field

from mia_agents.types import ToolSchema


def calculator(
    left_operand: Annotated[float, Field(description="Primer operando numérico.")],
    right_operand: Annotated[float, Field(description="Segundo operando numérico.")],
    operator: Annotated[str, Field(description="Operador: +, -, *, %.")],
) -> str:
    """Calcula el resultado de dos operandos y un operador aritmético."""
    return str(left_operand)


def greet(name: str, polite: bool = True) -> str:
    """Saluda a alguien."""
    return f"Hola {name}"


def test_from_callable_uses_function_name_and_docstring() -> None:
    schema = ToolSchema.from_callable(calculator)

    assert schema.name == "calculator"
    assert "operador" in schema.description.lower()
    assert schema.parameters["type"] == "object"
    assert "left_operand" in schema.parameters["properties"]
    assert "right_operand" in schema.parameters["properties"]
    assert "operator" in schema.parameters["properties"]
    assert set(schema.parameters["required"]) == {
        "left_operand",
        "right_operand",
        "operator",
    }


def test_from_callable_field_description() -> None:
    schema = ToolSchema.from_callable(calculator)
    assert "operando" in schema.parameters["properties"]["left_operand"]["description"]


def test_from_callable_optional_parameter_not_required() -> None:
    schema = ToolSchema.from_callable(greet)
    assert "name" in schema.parameters["required"]
    assert "polite" not in schema.parameters.get("required", [])


def test_from_callable_uses_full_docstring() -> None:
    def multi(x: str) -> str:
        """Resumen corto.

        Detalle adicional para el modelo.
        """
        return x

    schema = ToolSchema.from_callable(multi)
    assert "Resumen corto." in schema.description
    assert "Detalle adicional" in schema.description


def test_from_callable_overrides() -> None:
    schema = ToolSchema.from_callable(
        calculator, name="calc", description="Calculadora custom."
    )
    assert schema.name == "calc"
    assert schema.description == "Calculadora custom."


def test_to_llm_spec_unchanged() -> None:
    schema = ToolSchema.from_callable(greet)
    spec = schema.to_llm_spec()
    assert spec["name"] == "greet"
    assert spec["parameters"] == schema.parameters


def test_from_callable_zero_parameters() -> None:
    def look() -> str:
        """Describe la sala actual."""
        return "ok"

    schema = ToolSchema.from_callable(look)
    assert schema.parameters["type"] == "object"
    assert schema.parameters.get("properties", {}) == {}


def test_var_kwargs_rejected() -> None:
    def bad(**kwargs: str) -> str:
        return ""

    with pytest.raises(TypeError, match="\\*\\*kwargs"):
        ToolSchema.from_callable(bad)
