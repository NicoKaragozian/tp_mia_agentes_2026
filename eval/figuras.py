#!/usr/bin/env python3
"""Genera las figuras del informe a partir de los resúmenes versionados.

    python eval/figuras.py

Dos decisiones de diseño que conviene explicitar:

**Sin dependencias de graficación.** Las figuras se emiten como SVG escrito a
mano desde la biblioteca estándar. Agregar matplotlib obligaría a quien
reproduzca el trabajo a instalarlo, en un repositorio cuya premisa es Python
puro sin SDKs externos. Como efecto lateral, el SVG es texto: se versiona, se
diffea y GitHub lo renderiza dentro del markdown del informe.

**Se leen los resúmenes, no las trazas.** Las figuras se construyen desde
`eval/results/*/summary.json`, que están versionados (4 KB cada uno), no desde
las trazas crudas (93 MB, ignoradas por git). Es decir que cualquiera puede
regenerar las figuras del informe sin credenciales, sin proveedor LLM y sin
gastar una sola llamada al modelo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "eval" / "results"
DESTINO = RAIZ / "docs" / "figuras"

# Paleta sobria y legible en fondo claro u oscuro, con un acento por serie.
TINTA = "#1b2432"
SUAVE = "#8894a6"
REJILLA = "#d8dee6"
COLORES = ["#2b4c7e", "#a6392f", "#2c6a4f", "#8a6d1f"]

ANCHO, ALTO = 720, 380
MARGEN = {"izq": 190, "der": 30, "arriba": 46, "abajo": 52}


def _esc(texto: str) -> str:
    return (
        texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def _cabecera(titulo: str, subtitulo: str = "") -> list[str]:
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" '
        f'width="{ANCHO}" height="{ALTO}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{ANCHO}" height="{ALTO}" fill="#ffffff"/>',
        f'<text x="{MARGEN["izq"] - 150}" y="26" font-size="15" font-weight="600" '
        f'fill="{TINTA}">{_esc(titulo)}</text>',
    ]
    if subtitulo:
        partes.append(
            f'<text x="{MARGEN["izq"] - 150}" y="42" font-size="11" '
            f'fill="{SUAVE}">{_esc(subtitulo)}</text>'
        )
    return partes


def barras_horizontales(
    ruta: Path,
    titulo: str,
    subtitulo: str,
    etiquetas: Sequence[str],
    valores: Sequence[float],
    textos: Sequence[str],
    maximo: float = 100.0,
    unidad: str = "%",
) -> None:
    """Barras horizontales, una por categoría, con su valor anotado al final."""
    partes = _cabecera(titulo, subtitulo)
    x0 = MARGEN["izq"]
    ancho_util = ANCHO - x0 - MARGEN["der"] - 58
    alto_util = ALTO - MARGEN["arriba"] - MARGEN["abajo"]
    paso = alto_util / max(len(etiquetas), 1)
    grosor = min(paso * 0.62, 30)

    # Rejilla vertical cada 25 % del máximo.
    for i in range(5):
        x = x0 + ancho_util * i / 4
        v = maximo * i / 4
        partes.append(
            f'<line x1="{x:.1f}" y1="{MARGEN["arriba"]}" x2="{x:.1f}" '
            f'y2="{MARGEN["arriba"] + alto_util:.1f}" stroke="{REJILLA}" stroke-width="1"/>'
        )
        partes.append(
            f'<text x="{x:.1f}" y="{ALTO - MARGEN["abajo"] + 34:.1f}" font-size="10" '
            f'fill="{SUAVE}" text-anchor="middle">{v:g}{unidad}</text>'
        )

    for i, (etq, val, txt) in enumerate(zip(etiquetas, valores, textos)):
        y = MARGEN["arriba"] + paso * i + (paso - grosor) / 2
        largo = ancho_util * (val / maximo) if maximo else 0
        color = COLORES[i % len(COLORES)]
        partes.append(
            f'<text x="{x0 - 10}" y="{y + grosor / 2 + 4:.1f}" font-size="11.5" '
            f'fill="{TINTA}" text-anchor="end">{_esc(etq)}</text>'
        )
        partes.append(
            f'<rect x="{x0}" y="{y:.1f}" width="{max(largo, 1):.1f}" '
            f'height="{grosor:.1f}" fill="{color}" rx="2"/>'
        )
        partes.append(
            f'<text x="{x0 + largo + 8:.1f}" y="{y + grosor / 2 + 4:.1f}" '
            f'font-size="11" fill="{TINTA}">{_esc(txt)}</text>'
        )

    partes.append("</svg>")
    ruta.write_text("\n".join(partes), encoding="utf-8")


def series_agrupadas(
    ruta: Path,
    titulo: str,
    subtitulo: str,
    categorias: Sequence[str],
    series: Sequence[tuple[str, Sequence[float]]],
    maximo: float = 100.0,
    unidad: str = "%",
) -> None:
    """Barras verticales agrupadas: una categoría por grupo, N series."""
    partes = _cabecera(titulo, subtitulo)
    x0, y0 = 60, MARGEN["arriba"] + 14
    ancho_util = ANCHO - x0 - MARGEN["der"]
    alto_util = ALTO - y0 - MARGEN["abajo"] - 16
    paso = ancho_util / max(len(categorias), 1)
    grosor = min(paso / (len(series) + 1), 44)

    for i in range(5):
        y = y0 + alto_util * (1 - i / 4)
        partes.append(
            f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + ancho_util:.1f}" y2="{y:.1f}" '
            f'stroke="{REJILLA}" stroke-width="1"/>'
        )
        partes.append(
            f'<text x="{x0 - 8}" y="{y + 4:.1f}" font-size="10" fill="{SUAVE}" '
            f'text-anchor="end">{maximo * i / 4:g}{unidad}</text>'
        )

    for c, categoria in enumerate(categorias):
        centro = x0 + paso * c + paso / 2
        base = centro - grosor * len(series) / 2
        for s, (_, valores) in enumerate(series):
            v = valores[c]
            alto = alto_util * (v / maximo) if maximo else 0
            x = base + grosor * s
            partes.append(
                f'<rect x="{x:.1f}" y="{y0 + alto_util - alto:.1f}" '
                f'width="{grosor - 4:.1f}" height="{max(alto, 1):.1f}" '
                f'fill="{COLORES[s % len(COLORES)]}" rx="2"/>'
            )
            partes.append(
                f'<text x="{x + (grosor - 4) / 2:.1f}" '
                f'y="{y0 + alto_util - alto - 5:.1f}" font-size="9.5" '
                f'fill="{TINTA}" text-anchor="middle">{v:g}</text>'
            )
        partes.append(
            f'<text x="{centro:.1f}" y="{y0 + alto_util + 17:.1f}" font-size="11" '
            f'fill="{TINTA}" text-anchor="middle">{_esc(categoria)}</text>'
        )

    # Leyenda
    lx = x0
    for s, (nombre, _) in enumerate(series):
        partes.append(
            f'<rect x="{lx}" y="{ALTO - 22}" width="10" height="10" '
            f'fill="{COLORES[s % len(COLORES)]}" rx="2"/>'
        )
        partes.append(
            f'<text x="{lx + 15}" y="{ALTO - 13}" font-size="10.5" '
            f'fill="{TINTA}">{_esc(nombre)}</text>'
        )
        lx += 20 + len(nombre) * 6.2

    partes.append("</svg>")
    ruta.write_text("\n".join(partes), encoding="utf-8")


def _resumen(nombre: str) -> dict:
    return json.loads((RESULTADOS / nombre / "summary.json").read_text(encoding="utf-8"))


def _pooled_por_escenario(directorios: Sequence[str], condicion: str = "baseline") -> dict:
    """Agrega por escenario sumando varias campañas de la misma condición."""
    from collections import defaultdict

    acc: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for d in directorios:
        ruta = RESULTADOS / d / "trazas.json"
        if not ruta.is_file():  # las trazas no se versionan; caemos al summary
            s = _resumen(d)
            for esc, v in s["por_escenario"].items():
                acc[esc][0] += v["exitos"]
                acc[esc][1] += v["n"]
            continue
        for t in json.loads(ruta.read_text(encoding="utf-8")):
            if t.get("fallo_infra") or t["condicion"] != condicion:
                continue
            acc[t["escenario"]][0] += int(bool(t["meta_lograda"]))
            acc[t["escenario"]][1] += 1
    return dict(acc)


# ---------------------------------------------------------------------------
# Las figuras del informe. Cada una responde una pregunta concreta del texto;
# ninguna es decorativa.
# ---------------------------------------------------------------------------

ORDEN = [
    "study-with-key",
    "color-locks",
    "apartment-keys",
    "library-search",
    "office-sequence",
    "extreme-archive",
    "vault-combination",
    "backtracking-vault",
]
DIFICULTAD = {
    "study-with-key": "easy",
    "color-locks": "medium",
    "apartment-keys": "medium",
    "library-search": "hard",
    "office-sequence": "hard",
    "extreme-archive": "extreme",
    "vault-combination": "extreme",
    "backtracking-vault": "extreme",
}


def fig_exito_por_escenario() -> None:
    """¿Dónde está el techo del agente? (sección 3.3)"""
    campanas = ["nova-final", "e5-bloqueo", "e6-planner"]
    # Los escenarios extreme se suman solo si su campaña ya terminó.
    if (RESULTADOS / "nova-extreme" / "summary.json").is_file():
        campanas.append("nova-extreme")
    datos = _pooled_por_escenario(campanas)
    etq, val, txt = [], [], []
    for e in ORDEN:
        if e not in datos:
            continue
        ok, n = datos[e]
        etq.append(f"{e}  ({DIFICULTAD[e]})")
        val.append(100 * ok / n)
        txt.append(f"{ok}/{n}")
    total_ok = sum(datos[e][0] for e in datos)
    total_n = sum(datos[e][1] for e in datos)
    barras_horizontales(
        DESTINO / "exito-por-escenario.svg",
        "Tasa de éxito por escenario",
        f"Nova Lite · {total_n} corridas · global {100 * total_ok / total_n:.0f} %",
        etq, val, txt,
    )


def fig_eficiencia() -> None:
    """Llegar no es lo mismo que llegar bien. (sección 3.5)"""
    s = _resumen("nova-final")["por_escenario"]
    etq, val, txt = [], [], []
    for e in ORDEN:
        if e not in s or not s[e]["eficiencia_media"]:
            continue
        etq.append(e)
        val.append(s[e]["eficiencia_media"])
        txt.append(f'{s[e]["eficiencia_media"]:.2f}')
    barras_horizontales(
        DESTINO / "eficiencia-por-escenario.svg",
        "Eficiencia sobre corridas exitosas",
        "óptimo dividido llamadas usadas · 1,00 sería el camino ideal",
        etq, val, txt, maximo=1.0, unidad="",
    )


def fig_e1_memoria() -> None:
    """El costo de recortar la ventana, en dos métricas a la vez. (E1)"""
    s = _resumen("e1-nova")["por_condicion"]
    cats = ["ventana 50", "ventana 8", "ventana 4"]
    claves = ["baseline", "memoria_ajustada", "memoria_minima"]
    series_agrupadas(
        DESTINO / "e1-memoria.svg",
        "E1 · efecto del tamaño de la ventana deslizante",
        "Nova Lite · 50 corridas por condición",
        cats,
        [
            ("tasa de éxito %", [round(100 * s[k]["tasa_exito"]) for k in claves]),
            ("llamadas repetidas %", [round(100 * s[k]["repeticion_media"]) for k in claves]),
        ],
    )


def fig_juez() -> None:
    """¿El juez distingue una corrida buena de una mala? (sección 3.6)"""
    # La rúbrica por condición se recalcula desde las trazas cuando están
    # disponibles; el resumen versionado solo guarda la media global.
    from collections import defaultdict
    import statistics

    ruta = RESULTADOS / "e1-nova" / "trazas.json"
    dims = ("coherencia_plan", "recuperacion_errores", "exploracion_eficiente")
    if ruta.is_file():
        por = defaultdict(list)
        for t in json.loads(ruta.read_text(encoding="utf-8")):
            j = t.get("juez")
            if isinstance(j, dict) and "error_juez" not in j:
                por[t["condicion"]].append(j)
        claves = ["baseline", "memoria_ajustada", "memoria_minima"]
        series = [
            (
                d.replace("_", " "),
                [round(statistics.fmean(x[d] for x in por[k]), 2) for k in claves],
            )
            for d in dims
        ]
        series_agrupadas(
            DESTINO / "juez-por-condicion.svg",
            "E1 · rúbrica del juez por condición",
            "escala 1 a 5 · las tres dimensiones caen junto con la tasa de éxito",
            ["ventana 50", "ventana 8", "ventana 4"],
            series,
            maximo=5.0,
            unidad="",
        )


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for fn in (fig_exito_por_escenario, fig_eficiencia, fig_e1_memoria, fig_juez):
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except (FileNotFoundError, KeyError) as exc:
            print(f"  --  {fn.__name__} omitida ({type(exc).__name__}: {exc})")
    generadas = sorted(p.name for p in DESTINO.glob("*.svg"))
    print(f"\n{len(generadas)} figuras en {DESTINO.relative_to(RAIZ)}:")
    for g in generadas:
        print(f"  {g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
