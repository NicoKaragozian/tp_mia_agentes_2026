"""Calibración del juez contra etiquetas humanas.

La materia insiste en que un juez basado en un modelo no se acepta por
default: hay que medir su acuerdo con anotadores humanos usando un
estadístico corregido por azar antes de confiar en sus veredictos. Este
módulo arma el conjunto a etiquetar y calcula el acuerdo cuando las
etiquetas están puestas.

Dos decisiones que hacen honesta la comparación:

* el anotador ve **exactamente** el mismo texto que vio el juez, el que
  produce `judge.resumen_de_traza`, ni más ni menos;
* el anotador **no** ve la nota del juez. Las notas viven aparte, en el
  archivo de claves, y solo se leen al calcular el acuerdo.

Uso:

    python eval/calibracion.py armar      # genera el material a etiquetar
    python eval/calibracion.py acuerdo    # una vez completadas las planillas
"""

from __future__ import annotations

import csv
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from eval.judge import resumen_de_traza

DIR = Path("docs/calibracion")
DIMENSIONES = ("coherencia_plan", "recuperacion_errores", "exploracion_eficiente")

#: Semilla fija: el conjunto etiquetado tiene que ser el mismo si alguien
#: regenera el material a mitad de camino.
SEMILLA = 20260828


def _trazas_juzgadas(raiz: Path = Path("eval/results")) -> list[dict[str, Any]]:
    """Todas las trazas que tienen un veredicto válido del juez."""
    salida = []
    for campania in sorted(raiz.iterdir()):
        archivo = campania / "trazas.json"
        if not archivo.exists():
            continue
        for i, traza in enumerate(json.loads(archivo.read_text(encoding="utf-8"))):
            juez = traza.get("juez")
            if isinstance(juez, dict) and "error_juez" not in juez:
                traza["_origen"] = f"{campania.name}#{i}"
                salida.append(traza)
    return salida


def muestrear(trazas: list[dict[str, Any]], n: int = 40) -> list[dict[str, Any]]:
    """Muestra estratificada por desenlace y escenario.

    Sin estratificar, una muestra al azar sobre una población con 56 % de
    éxitos deja los fracasos sub-representados, y los fracasos son
    justamente donde la rúbrica tiene que discriminar.
    """
    rng = random.Random(SEMILLA)
    estratos: dict[tuple, list] = defaultdict(list)
    for t in trazas:
        estratos[(t["escenario"], bool(t["meta_lograda"]))].append(t)

    for grupo in estratos.values():
        rng.shuffle(grupo)

    elegidas: list[dict[str, Any]] = []
    claves = sorted(estratos)
    while len(elegidas) < n and any(estratos[k] for k in claves):
        for k in claves:
            if estratos[k] and len(elegidas) < n:
                elegidas.append(estratos[k].pop())
    rng.shuffle(elegidas)
    return elegidas


def armar(n: int = 40) -> None:
    """Escribe el cuadernillo a etiquetar, la plantilla y las claves."""
    elegidas = muestrear(_trazas_juzgadas(), n)
    DIR.mkdir(parents=True, exist_ok=True)

    partes = [_ENCABEZADO]
    claves = {}
    for i, t in enumerate(elegidas, 1):
        ident = f"T{i:02d}"
        claves[ident] = {"origen": t["_origen"], "juez": {d: t["juez"][d] for d in DIMENSIONES}}
        partes.append(f"\n\n---\n\n## {ident}\n\n```\n{resumen_de_traza(t)}\n```\n")
    (DIR / "trazas-a-etiquetar.md").write_text("".join(partes), encoding="utf-8")

    with (DIR / "etiquetas-plantilla.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "anotador", *DIMENSIONES])
        for ident in claves:
            w.writerow([ident, "", "", "", ""])

    (DIR / "claves.json").write_text(
        json.dumps(claves, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{len(elegidas)} trazas en {DIR}/trazas-a-etiquetar.md")
    print(f"planilla en {DIR}/etiquetas-plantilla.csv (una copia por anotador)")


def kappa_ponderado(a: list[int], b: list[int], k: int = 5) -> float:
    """Kappa de Cohen con pesos cuadráticos.

    Ponderado y no simple porque la rúbrica es ordinal: confundir un 4 con un
    5 no es el mismo error que confundir un 1 con un 5, y el kappa simple los
    trata igual.
    """
    if len(a) != len(b) or not a:
        raise ValueError("hacen falta dos listas del mismo largo y no vacías")

    obs = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x - 1][y - 1] += 1

    n = len(a)
    fa = [sum(fila) for fila in obs]
    fb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    peso = [[((i - j) / (k - 1)) ** 2 for j in range(k)] for i in range(k)]

    num = sum(peso[i][j] * obs[i][j] for i in range(k) for j in range(k))
    den = sum(peso[i][j] * fa[i] * fb[j] / n for i in range(k) for j in range(k))
    return 1.0 - num / den if den else 0.0


def spearman(a: list[float], b: list[float]) -> float:
    """Correlación de rangos, con promedio en los empates."""
    def rangos(v):
        orden = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(orden):
            j = i
            while j + 1 < len(orden) and v[orden[j + 1]] == v[orden[i]]:
                j += 1
            medio = (i + j) / 2 + 1
            for p in range(i, j + 1):
                r[orden[p]] = medio
            i = j + 1
        return r

    ra, rb = rangos(a), rangos(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else 0.0


def acuerdo() -> None:
    """Compara las planillas completadas contra el juez."""
    claves = json.loads((DIR / "claves.json").read_text(encoding="utf-8"))
    filas = []
    for archivo in sorted(DIR.glob("etiquetas-*.csv")):
        if archivo.name == "etiquetas-plantilla.csv":
            continue
        with archivo.open(encoding="utf-8") as fh:
            filas += [f for f in csv.DictReader(fh) if (f.get("id") or "").strip()]
    if not filas:
        print(f"No hay planillas completadas en {DIR}/ (esperaba etiquetas-<nombre>.csv)")
        return

    humanos = defaultdict(lambda: defaultdict(list))
    for f in filas:
        for d in DIMENSIONES:
            v = (f.get(d) or "").strip()
            if v:
                humanos[f["id"].strip()][d].append(int(v))

    print(f"{len(filas)} filas de {len({f['anotador'] for f in filas})} anotador(es)\n")
    print(f"{'dimensión':24s} {'n':>4s} {'kappa':>7s} {'spearman':>9s}  lectura")
    for d in DIMENSIONES:
        h, j = [], []
        for ident, notas in humanos.items():
            if ident in claves and notas[d]:
                h.append(round(statistics.mean(notas[d])))
                j.append(claves[ident]["juez"][d])
        if not h:
            continue
        k = kappa_ponderado(h, j)
        print(f"{d:24s} {len(h):4d} {k:7.3f} {spearman(h, j):9.3f}  {_lectura(k)}")


def _lectura(k: float) -> str:
    """Escala de Landis y Koch, la convencional para reportar kappa."""
    for tope, etiqueta in ((0.0, "sin acuerdo"), (0.20, "leve"), (0.40, "aceptable"),
                           (0.60, "moderado"), (0.80, "sustancial")):
        if k <= tope:
            return etiqueta
    return "casi perfecto"


_ENCABEZADO = """# Calibración del juez — cuadernillo de etiquetado

Cada bloque es **el texto exacto que recibió el juez** para puntuar esa
traza: ni más ni menos información. Puntuá vos con la misma rúbrica, sin
mirar `claves.json` (ahí están las notas del juez, y verlas antes arruina la
medición).

Cada anotador trabaja **por separado** y sin comentar sus notas con los
demás hasta que estén las tres planillas.

## Rúbrica (idéntica a la del juez)

Puntuás la **conducta observable, no el resultado**. Un agente puede fallar
y aun así haber explorado con criterio, y puede acertar habiendo dado
muchas vueltas.

| Dimensión | 1 | 5 |
| :---- | :---- | :---- |
| `coherencia_plan` | acciones sin relación con el objetivo | plan claro y progresivo |
| `recuperacion_errores` | repite la acción fallida sin cambiar nada | lee el error y corrige |
| `exploracion_eficiente` | repite acciones ya hechas | cada acción aporta información nueva |

Los valores intermedios (2, 3, 4) son válidos y esperables.

## Cómo cargar las notas

Copiá `etiquetas-plantilla.csv` a `etiquetas-<tunombre>.csv` y completá las
tres columnas de cada fila, poniendo tu nombre en `anotador`. Cuando estén
las tres planillas:

```
python eval/calibracion.py acuerdo
```
"""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "acuerdo":
        acuerdo()
    else:
        armar()
