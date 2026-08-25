"""Taxonomía de modos de fallo, clasificada automáticamente desde la traza.

Por qué automático: el enunciado pide categorizar dónde y por qué falla el
agente, no dar un número suelto. Con 8 escenarios × condiciones ×
repeticiones son cientos de corridas; clasificarlas a ojo no escala y, peor,
no es reproducible. Cada categoría de acá se decide con una regla explícita
sobre datos observables de la traza.

Una corrida puede exhibir varios modos a la vez (repetir Y agotar el
presupuesto, por ejemplo). `modo_principal` elige uno para los desgloses,
siguiendo el orden de prioridad de `_PRIORIDAD`: primero lo que explica
mejor por qué no llegó a la meta.
"""

from __future__ import annotations

import collections
import json
import re
from typing import Any

#: Un único `chat` puede pedir varias tools; el bucle las ejecuta todas.
#: Contamos una llamada como repetida si (herramienta, argumentos) ya salió.
UMBRAL_BUCLE = 0.30  # fracción de llamadas repetidas para hablar de bucle

#: Ventana de contexto de cada proveedor, en tokens. El techo NO es una
#: propiedad de la tarea sino del modelo con el que se la corre, así que
#: clasificar "desborde de contexto" contra un único número fijo mide mal en
#: cuanto se compara más de un proveedor: 16.384 es el `num_ctx` que
#: `LLMClient` le pasa a Ollama, pero Nova Lite admite 300.000 y un prompt de
#: 16.000 tokens no lo acerca ni remotamente a su límite.
TECHOS_CONTEXTO: dict[str, int] = {
    "ollama": 16_384,          # mia_agents/llm_client.py: num_ctx por defecto
    "amazon.nova-lite": 300_000,
    "amazon.nova-micro": 128_000,
    "amazon.nova-pro": 300_000,
}

#: Si no reconocemos el modelo, asumimos el techo más chico. Prefiere marcar
#: de más antes que dejar pasar un desborde real sin diagnosticar.
TECHO_POR_DEFECTO = 16_384

UMBRAL_CONTEXTO = 0.85


def techo_contexto(modelo: str) -> int:
    """Ventana de contexto del modelo que produjo una traza.

    `modelo` viene de la traza con la forma `proveedor:id`, por ejemplo
    `ollama:llama3.1:8b` o `bedrock:amazon.nova-lite-v1:0`. Se busca por
    subcadena para no depender de la versión exacta del identificador.
    """
    m = (modelo or "").lower()
    for clave, techo in TECHOS_CONTEXTO.items():
        if clave in m:
            return techo
    return TECHO_POR_DEFECTO


#: Orden de prioridad: el primero que aplique es el modo principal.
_PRIORIDAD = [
    "tool_call_en_texto",
    "orden_incorrecto",
    "desborde_contexto",
    "bucle",
    "accion_invalida",
    "argumentos_invalidos",
    "tool_alucinada",
    "limite_iteraciones",
    "parada_prematura",
]

_RE_TOOL_EN_TEXTO = re.compile(r'\{[^{}]*"(?:name|arguments|tool)"\s*:', re.S)


def _firma(paso: dict[str, Any]) -> str:
    return f"{paso.get('herramienta')}|{paso.get('argumentos')}"


def fraccion_repetidas(pasos: list[dict[str, Any]]) -> float:
    """Proporción de llamadas que repiten una (herramienta, argumentos) previa."""
    if not pasos:
        return 0.0
    cuenta = collections.Counter(_firma(p) for p in pasos)
    repetidas = sum(c - 1 for c in cuenta.values() if c > 1)
    return repetidas / len(pasos)


def clasificar(traza: dict[str, Any]) -> list[str]:
    """Devuelve todos los modos de fallo observables en una traza.

    Una corrida exitosa devuelve lista vacía aunque haya cometido errores
    por el camino: si llegó a la meta, esos errores fueron recuperados y no
    son modos de *fallo*.
    """
    # El fallo de infraestructura se chequea ANTES que la meta: una corrida
    # puede haber abierto la puerta y reventar después (el mundo ya quedó en
    # estado ganador, pero la corrida se truncó). Clasificarla como éxito
    # limpio escondería que el proveedor falló.
    if traza.get("fallo_infra"):
        return ["fallo_infraestructura"]
    if traza.get("meta_lograda"):
        return []

    modos: list[str] = []
    pasos = traza.get("pasos") or []

    if _RE_TOOL_EN_TEXTO.search(traza.get("respuesta") or ""):
        # El modelo escribió la llamada como texto en vez de emitirla por la
        # API de tool-calling; el bucle lo leyó como respuesta final y cortó.
        modos.append("tool_call_en_texto")

    if "orden" in (traza.get("meta_razon") or "").lower():
        modos.append("orden_incorrecto")

    picos = [
        ll.get("input_tokens") or 0 for ll in (traza.get("llamadas_llm") or [])
    ]
    techo = techo_contexto(traza.get("modelo", ""))
    if picos and max(picos) >= techo * UMBRAL_CONTEXTO:
        modos.append("desborde_contexto")

    if fraccion_repetidas(pasos) >= UMBRAL_BUCLE:
        modos.append("bucle")

    # La herramienta corrió pero el mundo rechazó la acción (id inexistente,
    # objeto no revelado, salida bloqueada...).
    if any(
        not p.get("error") and (p.get("salida") or "").startswith("Error")
        for p in pasos
    ):
        modos.append("accion_invalida")

    errores = [p.get("error") or "" for p in pasos if p.get("error")]
    if any(e.startswith("Argumentos inválidos") or "JSON inválidos" in e for e in errores):
        modos.append("argumentos_invalidos")
    if any(e.startswith("Herramienta desconocida") for e in errores):
        modos.append("tool_alucinada")

    if traza.get("corte"):
        modos.append("limite_iteraciones")
    elif "tool_call_en_texto" not in modos:
        # Cerró por su cuenta con texto, sin haber cumplido la meta.
        modos.append("parada_prematura")

    return modos


def modo_principal(traza: dict[str, Any]) -> str | None:
    """El modo más explicativo de la traza, o `None` si tuvo éxito."""
    modos = clasificar(traza)
    if not modos:
        return None
    for candidato in _PRIORIDAD:
        if candidato in modos:
            return candidato
    return modos[0]


def resumen_modos(trazas: list[dict[str, Any]]) -> dict[str, int]:
    """Cuenta de modos principales sobre un conjunto de corridas."""
    cuenta: collections.Counter[str] = collections.Counter()
    for t in trazas:
        modo = modo_principal(t)
        if modo:
            cuenta[modo] += 1
    return dict(cuenta.most_common())


def cargar(directorio: str) -> list[dict[str, Any]]:
    """Lee `trazas.json` de un directorio de resultados."""
    from pathlib import Path

    return json.loads((Path(directorio) / "trazas.json").read_text(encoding="utf-8"))
