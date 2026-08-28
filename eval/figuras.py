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
            # Sin ancho mínimo: un 0 debe verse como 0, no como una barra
            # de un pixel que sugiere un valor positivo.
            f'<rect x="{x0}" y="{y:.1f}" width="{largo:.1f}" '
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
                f'width="{grosor - 4:.1f}" height="{alto:.1f}" '
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


def _pooled_por_escenario(
    directorios: Sequence[str], condicion: str = "baseline"
) -> dict[str, list[int]]:
    """Suma éxitos y corridas por escenario, SOLO de la condición indicada.

    Lee `por_condicion_escenario` del resumen, no `por_escenario`: este último
    agrega todas las condiciones del experimento, así que usarlo mezclaría el
    baseline con la rama experimental de e5 o e6 e inflaría tanto el
    denominador como la tasa.

    No hay lectura de trazas en ningún camino. Todo sale de los resúmenes
    versionados, que es lo que hace que las figuras se regeneren desde un clon
    limpio.
    """
    from collections import defaultdict

    acc: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for d in directorios:
        cruce = _resumen(d).get("por_condicion_escenario", {})
        if condicion not in cruce:
            raise KeyError(
                f"la campaña {d!r} no tiene la condición {condicion!r}; "
                f"disponibles: {sorted(cruce) or '(ninguna)'}"
            )
        for esc, v in cruce[condicion].items():
            acc[esc][0] += v["exitos"]
            acc[esc][1] += v["n"]
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
    """Llegar no es lo mismo que llegar bien. (sección 3.5)

    Agrupa las mismas campañas que la figura de tasa de éxito. Usar una sola
    campaña daría números distintos de los de la tabla del informe, que está
    calculada sobre el total: la figura y la tabla tienen que salir del mismo
    conjunto de corridas o el lector encuentra dos valores para lo mismo.

    La media agrupada se calcula ponderando la media de cada campaña por su
    número de éxitos, que es sobre lo que está tomada.
    """
    from collections import defaultdict

    campanas = ["nova-final", "e5-bloqueo", "e6-planner"]
    if (RESULTADOS / "nova-extreme" / "summary.json").is_file():
        campanas.append("nova-extreme")

    acc: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])  # suma, éxitos
    for d in campanas:
        cruce = _resumen(d).get("por_condicion_escenario", {})
        for esc, v in cruce.get("baseline", {}).items():
            if v["exitos"]:
                acc[esc][0] += v["eficiencia_media"] * v["exitos"]
                acc[esc][1] += v["exitos"]

    etq, val, txt = [], [], []
    for e in ORDEN:
        if e not in acc or not acc[e][1]:
            continue
        media = acc[e][0] / acc[e][1]
        etq.append(e)
        val.append(round(media, 2))
        txt.append(f"{media:.2f}".replace(".", ","))
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
    rubrica = _resumen("e1-nova").get("rubrica_por_condicion", {})
    claves = ["baseline", "memoria_ajustada", "memoria_minima"]
    faltantes = [k for k in claves if k not in rubrica]
    if faltantes:
        raise KeyError(
            f"faltan veredictos del juez para {faltantes}; corré la evaluación "
            f"con --juez para poder generar esta figura"
        )
    dims = ("coherencia_plan", "recuperacion_errores", "exploracion_eficiente")
    series_agrupadas(
        DESTINO / "juez-por-condicion.svg",
        "E1 · rúbrica del juez por condición",
        "escala 1 a 5 · las tres dimensiones caen junto con la tasa de éxito",
        ["ventana 50", "ventana 8", "ventana 4"],
        [(d.replace("_", " "), [rubrica[k][d] for k in claves]) for d in dims],
        maximo=5.0,
        unidad="",
    )


#: Campañas cuyo brazo baseline entra en la estimación agrupada del control.
#: Son homogéneas entre sí (chi cuadrado 3,13 sobre 5 grados de libertad), que
#: es la condición que habilita a tratarlas como una sola muestra.
_BRAZOS_BASELINE = (
    "nova-final", "e5-bloqueo", "e6-planner",
    "e7-reflexion", "e9-distractores", "e8-temperatura",
)

#: Los cinco escenarios obligatorios; los extreme no entran en los experimentos.
_CINCO = (
    "study-with-key", "color-locks", "apartment-keys",
    "library-search", "office-sequence",
)


def _pooled_condicion(campanias, condicion) -> tuple[int, int]:
    """Éxitos y total de una condición agrupando varias campañas.

    Suma sobre `por_condicion_escenario`, restringido a los cinco escenarios
    obligatorios, para que agregar una campaña que corrió otros escenarios no
    cambie el número en silencio.
    """
    exitos = total = 0
    for campania in campanias:
        por = _resumen(campania).get("por_condicion_escenario", {})
        for escenario, datos in por.get(condicion, {}).items():
            if escenario in _CINCO:
                exitos += datos["exitos"]
                total += datos["n"]
    return exitos, total


def fig_e7_reflexion() -> None:
    """El único efecto positivo establecido del trabajo. (E7)"""
    be, bn = _pooled_condicion(_BRAZOS_BASELINE, "baseline")
    te, tn = _pooled_condicion(("e7-reflexion", "e7-ampliacion"), "con_reflexion")
    if not bn or not tn:
        raise KeyError("faltan resúmenes de E7 o de los brazos baseline")
    barras_horizontales(
        DESTINO / "e7-reflexion.svg",
        "E7 · reflexión al detectar un ciclo improductivo",
        f"Nova Lite · {bn} corridas de control contra {tn} con reflexión · p = 0,0105",
        [f"baseline ({be}/{bn})", f"con reflexión ({te}/{tn})"],
        [100 * be / bn, 100 * te / tn],
        [f"{100 * be / bn:.1f} %".replace(".", ","),
         f"{100 * te / tn:.1f} %".replace(".", ",")],
    )


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    figuras = (fig_exito_por_escenario, fig_eficiencia, fig_e1_memoria,
               fig_juez, fig_e7_reflexion)
    fallidas: list[str] = []
    for fn in figuras:
        antes = {p.name for p in DESTINO.glob("*.svg")}
        try:
            fn()
        except (FileNotFoundError, KeyError) as exc:
            fallidas.append(f"{fn.__name__}: {type(exc).__name__}: {exc}")
            print(f"  FALLÓ  {fn.__name__}")
            continue
        # Verificar que efectivamente se escribió algo: una función que no
        # lanza pero tampoco produce SVG dejaría el informe con una imagen
        # rota sin que nada lo avise.
        if {p.name for p in DESTINO.glob("*.svg")} == antes and not antes:
            fallidas.append(f"{fn.__name__}: no produjo ningún SVG")
            print(f"  FALLÓ  {fn.__name__} (sin salida)")
            continue
        print(f"  ok     {fn.__name__}")

    generadas = sorted(p.name for p in DESTINO.glob("*.svg"))
    print(f"\n{len(generadas)} figuras en {DESTINO.relative_to(RAIZ)}:")
    for g in generadas:
        print(f"  {g}")
    if fallidas:
        print("\nFiguras no generadas:")
        for f in fallidas:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
