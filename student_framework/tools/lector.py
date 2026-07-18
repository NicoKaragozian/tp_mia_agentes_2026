"""Herramienta 2: lector de archivos de texto (E/S restringida).

Función pura `fn(...) -> str` + su `ToolSchema`. Lee archivos de texto
UTF-8 con **acceso acotado** a un directorio base (sandbox): rechaza
cualquier ruta que intente salir de él. Esto anticipa los guardrails de
M3 y evita leer archivos arbitrarios del sistema.

M2 — errores recuperables: cada regla violada tiene su propio mensaje
(ruta vacía, absoluta, con `..`, fuera del sandbox), explicando qué se
esperaba en su lugar. Y los dos casos donde el LLM puede elegir mejor
reciben contexto para hacerlo: archivo inexistente => se listan los
archivos disponibles; ruta que es un directorio => se lista su contenido.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Annotated

from pydantic import Field

from mia_agents.types import ToolSchema

#: Directorio base permitido. Las rutas se interpretan relativas a `data/`
#: en la raíz del repo y deben resolver dentro de él.
_BASE_DIR = Path(__file__).resolve().parents[2] / "data"

#: Tope defensivo para no volcar archivos enormes al contexto del LLM.
_MAX_BYTES = 100_000

#: Máximo de entradas mostradas al listar un directorio en un mensaje.
_MAX_LISTADO = 20


def _resolver_dentro_de_base(ruta: str) -> Path | None:
    """Resuelve `ruta` contra el directorio base y verifica que no se escape.

    Devuelve la ruta resuelta si queda dentro de `_BASE_DIR`, o `None` si
    intenta salir (p. ej. vía symlinks) o es una ruta absoluta externa.
    Resolver ambos lados neutraliza `..` y symlinks antes de comparar.
    """
    base = _BASE_DIR.resolve()
    candidata = (base / ruta).resolve()
    try:
        candidata.relative_to(base)
    except ValueError:
        return None
    return candidata


def _listar(directorio: Path) -> str:
    """Nombres dentro de `directorio` (subdirectorios con '/'), acotados."""
    try:
        entradas = sorted(
            e.name + ("/" if e.is_dir() else "") for e in directorio.iterdir()
        )
    except OSError as exc:
        return f"(no se pudo listar: {exc})"
    if not entradas:
        return "(vacío)"
    visibles = entradas[:_MAX_LISTADO]
    if len(entradas) > _MAX_LISTADO:
        visibles.append(f"... y {len(entradas) - _MAX_LISTADO} más")
    return ", ".join(visibles)


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

    El acceso está acotado a un directorio base permitido: se rechazan
    rutas vacías, absolutas, con `..` o que escapen del sandbox. Solo lee
    archivos regulares de texto. Ante cualquier problema devuelve un
    mensaje descriptivo (con los archivos disponibles cuando corresponde)
    en lugar de lanzar una excepción.
    """
    if not isinstance(ruta, str) or not ruta.strip():
        return (
            "Error: la ruta está vacía. Pasá una ruta relativa al directorio "
            "de datos permitido, por ejemplo 'notas.txt' o 'sub/archivo.txt'."
        )
    ruta = ruta.strip()

    # Reglas del sandbox, cada una con su mensaje (el orden importa: se
    # informa la regla más específica que se pueda determinar).
    if Path(ruta).is_absolute():
        return (
            f"Error: acceso denegado: la ruta {ruta!r} es absoluta. Este "
            f"lector solo acepta rutas relativas al directorio de datos "
            f"permitido, por ejemplo 'notas.txt'."
        )
    if ".." in PurePosixPath(ruta).parts:
        return (
            f"Error: acceso denegado: la ruta {ruta!r} contiene '..', que "
            f"permitiría escapar del directorio de datos. Usá una ruta "
            f"relativa sin '..', por ejemplo 'notas.txt'."
        )
    objetivo = _resolver_dentro_de_base(ruta)
    if objetivo is None:
        return (
            f"Error: acceso denegado: la ruta {ruta!r} resuelve fuera del "
            f"directorio de datos permitido. Usá una ruta relativa que quede "
            f"dentro de él, por ejemplo 'notas.txt'."
        )

    if not objetivo.exists():
        directorio = objetivo.parent
        if directorio.is_dir():
            return (
                f"Error: el archivo {ruta!r} no existe. Archivos disponibles "
                f"en ese directorio: {_listar(directorio)}. Elegí uno de esos "
                f"nombres y reintentá."
            )
        return (
            f"Error: el archivo {ruta!r} no existe (tampoco existe su "
            f"directorio). Archivos disponibles en la raíz del directorio "
            f"de datos: {_listar(_BASE_DIR) if _BASE_DIR.is_dir() else '(vacío)'}."
        )
    if not objetivo.is_file():
        return (
            f"Error: {ruta!r} no es un archivo regular: es un directorio. "
            f"Contiene: {_listar(objetivo)}. Indicá la ruta de uno de sus "
            f"archivos, p. ej. '{PurePosixPath(ruta) / 'archivo.txt'}'."
        )

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
