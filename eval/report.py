"""Genera el resumen de una corrida: `summary.json` + informe en markdown."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from eval.analysis import modo_principal, resumen_modos
from eval.config import ORDEN_ESCENARIOS
from eval.metrics import agrupar_por, eficiencia, resumir


def _tabla(cabeceras: list[str], filas: list[list[str]]) -> str:
    sep = "|" + "|".join("---" for _ in cabeceras) + "|"
    cab = "| " + " | ".join(cabeceras) + " |"
    cuerpo = ["| " + " | ".join(f) + " |" for f in filas]
    return "\n".join([cab, sep, *cuerpo])


def _orden_escenario(nombre: str) -> int:
    try:
        return ORDEN_ESCENARIOS.index(nombre)
    except ValueError:
        return len(ORDEN_ESCENARIOS)


def construir_resumen(trazas: list[dict[str, Any]]) -> dict[str, Any]:
    """Estructura agregada de la corrida, lista para serializar."""
    notas = [t["juez"] for t in trazas if isinstance(t.get("juez"), dict) and "error_juez" not in t["juez"]]
    rubrica: dict[str, float] = {}
    if notas:
        for dim in ("coherencia_plan", "recuperacion_errores", "exploracion_eficiente"):
            valores = [n[dim] for n in notas if isinstance(n.get(dim), int)]
            if valores:
                rubrica[dim] = round(statistics.fmean(valores), 2)
    return {
        "n_corridas": len(trazas),
        "modelo": trazas[0]["modelo"] if trazas else "",
        "global": resumir(trazas).como_dict(),
        "por_condicion": {k: v.como_dict() for k, v in agrupar_por(trazas, "condicion").items()},
        "por_dificultad": {k: v.como_dict() for k, v in agrupar_por(trazas, "dificultad").items()},
        "por_escenario": {k: v.como_dict() for k, v in agrupar_por(trazas, "escenario").items()},
        "modos_de_fallo": resumen_modos(trazas),
        "rubrica_media": rubrica,
    }


def render_markdown(resumen: dict[str, Any], trazas: list[dict[str, Any]]) -> str:
    """Informe legible de la corrida."""
    g = resumen["global"]
    partes = [
        "# Resultados de la evaluación",
        "",
        f"Modelo: `{resumen['modelo']}` · corridas: {resumen['n_corridas']}",
        "",
        "## Global",
        "",
        _tabla(
            ["métrica", "valor"],
            [
                ["tasa de éxito", f"{g['tasa_exito']:.0%} ({g['exitos']}/{g['n']})"],
                ["eficiencia media (éxitos)", f"{g['eficiencia_media']:.2f}"],
                ["fracción de llamadas repetidas", f"{g['repeticion_media']:.0%}"],
                ["pasos medios", str(g["pasos_medios"])],
                ["llamadas al LLM medias", str(g["llamadas_llm_medias"])],
                ["tokens entrada / salida", f"{g['tokens_entrada_medios']} / {g['tokens_salida_medios']}"],
                ["latencia mediana", f"{g['latencia_mediana_s']} s"],
                ["latencia media", f"{g['latencia_media_s']} s"],
            ],
        ),
        "",
    ]

    if len(resumen["por_condicion"]) > 1:
        partes += [
            "## Por condición",
            "",
            _tabla(
                ["condición", "éxito", "eficiencia", "repetidas", "pasos", "tokens in"],
                [
                    [
                        c,
                        f"{d['tasa_exito']:.0%} ({d['exitos']}/{d['n']})",
                        f"{d['eficiencia_media']:.2f}",
                        f"{d['repeticion_media']:.0%}",
                        str(d["pasos_medios"]),
                        str(d["tokens_entrada_medios"]),
                    ]
                    for c, d in resumen["por_condicion"].items()
                ],
            ),
            "",
        ]

    partes += [
        "## Por dificultad",
        "",
        _tabla(
            ["dificultad", "éxito", "repetidas", "pasos medios"],
            [
                [d, f"{v['tasa_exito']:.0%} ({v['exitos']}/{v['n']})",
                 f"{v['repeticion_media']:.0%}", str(v["pasos_medios"])]
                for d, v in sorted(
                    resumen["por_dificultad"].items(),
                    key=lambda kv: ["easy", "medium", "hard", "extreme"].index(kv[0])
                    if kv[0] in ["easy", "medium", "hard", "extreme"] else 9,
                )
            ],
        ),
        "",
        "## Por escenario",
        "",
        _tabla(
            ["escenario", "óptimo", "éxito", "pasos medios", "repetidas", "modo de fallo principal"],
            [
                [
                    e,
                    str(next((t["optimo"] for t in trazas if t["escenario"] == e), "?")),
                    f"{v['tasa_exito']:.0%} ({v['exitos']}/{v['n']})",
                    str(v["pasos_medios"]),
                    f"{v['repeticion_media']:.0%}",
                    ", ".join(
                        sorted(
                            {
                                modo_principal(t) or "—"
                                for t in trazas
                                if t["escenario"] == e and not t["meta_lograda"]
                            }
                        )
                    ) or "—",
                ]
                for e, v in sorted(
                    resumen["por_escenario"].items(), key=lambda kv: _orden_escenario(kv[0])
                )
            ],
        ),
        "",
        "## Modos de fallo (categoría principal por corrida fallida)",
        "",
        _tabla(
            ["modo", "corridas"],
            [[m, str(c)] for m, c in resumen["modos_de_fallo"].items()] or [["—", "0"]],
        ),
        "",
    ]

    if resumen["rubrica_media"]:
        partes += [
            "## Rúbrica cualitativa (LLM-as-judge, 1–5)",
            "",
            _tabla(
                ["dimensión", "media"],
                [[k, f"{v:.2f}"] for k, v in resumen["rubrica_media"].items()],
            ),
            "",
        ]
    return "\n".join(partes)


def escribir(destino: Path, trazas: list[dict[str, Any]]) -> dict[str, Any]:
    """Deja `summary.json` y `informe.md` en `destino`. Devuelve el resumen."""
    resumen = construir_resumen(trazas)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "summary.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (destino / "informe.md").write_text(
        render_markdown(resumen, trazas), encoding="utf-8"
    )
    return resumen
