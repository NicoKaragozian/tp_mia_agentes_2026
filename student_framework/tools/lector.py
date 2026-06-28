"""Herramienta 2 (M1): lector de archivos de texto (E/S restringida).

Función pura `fn(...) -> str` + su `ToolSchema`. Lee archivos de texto
UTF-8 con **acceso acotado** a un directorio base (sandbox): rechaza
cualquier ruta que intente salir de él. Esto anticipa los guardrails de
M3 y evita leer archivos arbitrarios del sistema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from mia_agents.types import ToolSchema

#: Directorio base permitido. Las rutas se interpretan relativas a `data/`
#: en la raíz del repo y deben resolver dentro de él.
_BASE_DIR = Path(__file__).resolve().parents[2] / "data"

#: Tope defensivo para no volcar archivos enormes al contexto del LLM.
_MAX_BYTES = 100_000


def _resolver_dentro_de_base(ruta: str) -> Path | None:
    """Resuelve `ruta` contra el directorio base y verifica que no se escape.

    Devuelve la ruta resuelta si queda dentro de `_BASE_DIR`, o `None` si
    intenta salir (p. ej. con `../`) o es una ruta absoluta fuera de la base.
    Resolver ambos lados neutraliza `..` y symlinks antes de comparar.
    """
    base = _BASE_DIR.resolve()
    candidata = (base / ruta).resolve()
    try:
        candidata.relative_to(base)
    except ValueError:
        return None
    return candidata


def leer_archivo(
    ruta: Annotated[
        str,
        Field(
            description=(
                "Ruta del archivo de texto a leer, relativa al directorio "
                "de datos permitido."
            )
        ),
    ],
) -> str:
    """Lee y devuelve el contenido de un archivo de texto (UTF-8).

    El acceso está acotado a un directorio base permitido: se rechazan las
    rutas que intenten salir de él (por ejemplo con `../`). Solo lee
    archivos regulares de texto. Ante cualquier problema (acceso denegado,
    archivo inexistente, contenido no UTF-8 o error de E/S) devuelve un
    mensaje descriptivo en lugar de lanzar una excepción.
    """
    objetivo = _resolver_dentro_de_base(ruta)
    if objetivo is None:
        return (
            f"Error: acceso denegado, la ruta {ruta!r} queda fuera del "
            f"directorio permitido."
        )
    if not objetivo.exists():
        return f"Error: el archivo {ruta!r} no existe."
    if not objetivo.is_file():
        return f"Error: {ruta!r} no es un archivo regular."

    try:
        # Chequear el tamaño con stat() ANTES de leer: así un archivo enorme
        # no se carga entero a memoria solo para rechazarlo después.
        if objetivo.stat().st_size > _MAX_BYTES:
            return (
                f"Error: el archivo {ruta!r} supera el límite de "
                f"{_MAX_BYTES} bytes."
            )
        datos = objetivo.read_bytes()
    except OSError as exc:
        return f"Error de E/S al leer {ruta!r}: {exc}."

    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return f"Error: {ruta!r} no es un archivo de texto UTF-8 válido."


leer_archivo_schema = ToolSchema.from_callable(leer_archivo)

#: Línea load-bearing del auto-descubrimiento (ver tools/__init__.py).
TOOLS = [(leer_archivo, leer_archivo_schema)]
