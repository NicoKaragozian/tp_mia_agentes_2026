"""Tests unitarios de las herramientas (calculadora y lector).

Las tools son funciones puras `fn(...) -> str`: se testean directamente,
sin agente ni LLM.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

from student_framework.tools.calculadora import (
    calculadora,
    calculadora_schema,
)
from student_framework.tools.lector import (
    _BASE_DIR,
    _MAX_BYTES,
    leer_archivo,
    leer_archivo_schema,
)


# --------------------------------------------------------------------------- #
# Calculadora
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "a, b, op, esperado",
    [
        (2, 3, "+", "5"),
        (10, 4, "-", "6"),
        (6, 7, "*", "42"),
        (10, 3, "%", "1"),
        (8, 2, "/", "4"),
        (7, 2, "/", "3.5"),
        (-5, 3, "+", "-2"),
    ],
)
def test_calculadora_operaciones(a: float, b: float, op: str, esperado: str) -> None:
    resultado = calculadora(a, b, op)
    assert resultado == esperado
    assert isinstance(resultado, str)


def test_calculadora_division_por_cero() -> None:
    assert "división por cero" in calculadora(1, 0, "/").lower()


def test_calculadora_modulo_por_cero() -> None:
    assert "división por cero" in calculadora(1, 0, "%").lower()


def test_calculadora_operador_invalido() -> None:
    out = calculadora(1, 2, "^")
    assert "no soportado" in out.lower()
    assert isinstance(out, str)


def test_calculadora_operador_con_espacios() -> None:
    assert calculadora(2, 2, " + ") == "4"


def test_calculadora_operando_no_numerico_nombra_parametro_y_valor() -> None:
    out = calculadora("cuarenta y dos", 2, "+")
    assert "operando_a" in out
    assert "cuarenta y dos" in out
    assert "número" in out.lower()


def test_calculadora_segundo_operando_no_numerico() -> None:
    out = calculadora(1, None, "+")
    assert "operando_b" in out
    assert "None" in out


def test_calculadora_rechaza_booleanos() -> None:
    out = calculadora(True, 2, "+")
    assert "operando_a" in out
    assert "booleano" in out.lower()


def test_calculadora_coerciona_strings_numericos() -> None:
    # El LLM a veces manda los números como texto: no vale la pena rebotarlo.
    assert calculadora("7", "2", "/") == "3.5"
    assert calculadora(" 10 ", 4, "-") == "6"


def test_calculadora_operador_invalido_lista_los_permitidos() -> None:
    out = calculadora(1, 2, "^")
    for op in ("+", "-", "*", "%", "/"):
        assert op in out


def test_calculadora_division_por_cero_es_accionable() -> None:
    out = calculadora(1, 0, "/")
    assert "operando_b" in out
    assert "distinto de 0" in out


def test_calculadora_schema() -> None:
    props = calculadora_schema.parameters["properties"]
    assert set(props) == {"operando_a", "operando_b", "operador"}
    assert set(calculadora_schema.parameters["required"]) == {
        "operando_a",
        "operando_b",
        "operador",
    }


# --------------------------------------------------------------------------- #
# Lector de archivos
# --------------------------------------------------------------------------- #


@pytest.fixture
def archivo_en_sandbox() -> Iterator[tuple[str, str]]:
    """Crea un archivo de texto dentro de `data/` y devuelve (nombre, contenido)."""
    _BASE_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"_test_{uuid.uuid4().hex}.txt"
    contenido = "hola mundo\nsegunda línea\n"
    ruta = _BASE_DIR / nombre
    ruta.write_text(contenido, encoding="utf-8")
    try:
        yield nombre, contenido
    finally:
        ruta.unlink(missing_ok=True)


def test_lector_lee_archivo_existente(archivo_en_sandbox: tuple[str, str]) -> None:
    nombre, contenido = archivo_en_sandbox
    assert leer_archivo(nombre) == contenido


def test_lector_archivo_inexistente() -> None:
    out = leer_archivo("no_existe_12345.txt")
    assert "no existe" in out.lower()


def test_lector_rechaza_path_traversal() -> None:
    out = leer_archivo("../CLAUDE.md")
    assert "acceso denegado" in out.lower()


def test_lector_rechaza_ruta_absoluta_externa() -> None:
    out = leer_archivo("/etc/passwd")
    assert "acceso denegado" in out.lower()


def test_lector_directorio_no_es_archivo() -> None:
    _BASE_DIR.mkdir(parents=True, exist_ok=True)
    sub = _BASE_DIR / f"_dir_{uuid.uuid4().hex}"
    sub.mkdir()
    try:
        out = leer_archivo(sub.name)
        assert "no es un archivo regular" in out.lower()
    finally:
        sub.rmdir()


def test_lector_archivo_no_utf8() -> None:
    _BASE_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"_bin_{uuid.uuid4().hex}.bin"
    ruta = _BASE_DIR / nombre
    ruta.write_bytes(b"\xff\xfe\x00\x01binario")
    try:
        out = leer_archivo(nombre)
        assert "utf-8" in out.lower()
    finally:
        ruta.unlink(missing_ok=True)


def test_lector_archivo_supera_limite() -> None:
    _BASE_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"_big_{uuid.uuid4().hex}.txt"
    ruta = _BASE_DIR / nombre
    ruta.write_bytes(b"a" * (_MAX_BYTES + 1))
    try:
        out = leer_archivo(nombre)
        assert "límite" in out.lower()
    finally:
        ruta.unlink(missing_ok=True)


def test_lector_ruta_vacia_explica_como_deberia_verse() -> None:
    out = leer_archivo("   ")
    assert "vacía" in out.lower()
    assert "relativa" in out.lower()


def test_lector_ruta_absoluta_nombra_la_regla() -> None:
    out = leer_archivo("/etc/passwd")
    assert "absoluta" in out.lower()
    assert "relativa" in out.lower()


def test_lector_ruta_con_puntos_nombra_la_regla() -> None:
    out = leer_archivo("../CLAUDE.md")
    assert "'..'" in out


def test_lector_inexistente_lista_los_disponibles(
    archivo_en_sandbox: tuple[str, str],
) -> None:
    nombre, _ = archivo_en_sandbox
    out = leer_archivo("no_existe_12345.txt")
    assert "no existe" in out.lower()
    assert nombre in out, "el error debería listar los archivos disponibles"


def test_lector_directorio_lista_su_contenido() -> None:
    _BASE_DIR.mkdir(parents=True, exist_ok=True)
    sub = _BASE_DIR / f"_dir_{uuid.uuid4().hex}"
    sub.mkdir()
    adentro = sub / "adentro.txt"
    adentro.write_text("x", encoding="utf-8")
    try:
        out = leer_archivo(sub.name)
        assert "directorio" in out.lower()
        assert "adentro.txt" in out
    finally:
        adentro.unlink()
        sub.rmdir()


def test_lector_schema() -> None:
    assert "ruta" in leer_archivo_schema.parameters["properties"]
    assert "ruta" in leer_archivo_schema.parameters["required"]


# --------------------------------------------------------------------------- #
# Descubrimiento: ambas tools quedan registradas
# --------------------------------------------------------------------------- #


def test_tools_en_registry() -> None:
    from student_framework.tools import REGISTRY

    nombres = {schema.name for _, schema in REGISTRY}
    assert {"calculadora", "leer_archivo"} <= nombres
