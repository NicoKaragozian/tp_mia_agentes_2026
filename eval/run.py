#!/usr/bin/env python3
"""Entrypoint reproducible de la evaluación del M3.

    python eval/run.py                      # baseline sobre los 8 escenarios
    python eval/run.py --smoke              # 1 escenario fácil, 1 repetición
    python eval/run.py --experimento e1-memoria
    python eval/run.py --experimento e2-prompt --escenarios study-with-key color-locks

Sin pasos manuales: elige el proveedor desde el entorno (`OLLAMA_HOST` o
`BEDROCK_MODEL_ID`, igual que `LLMClient.from_env`), corre los casos,
guarda las trazas en `eval/results/` y deja un resumen por pantalla.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# `python eval/run.py` deja `eval/` en sys.path[0]; hace falta la raíz del
# repo para importar `student_framework`, `mia_agents` y `mia_world`.
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

# El proveedor puede venir de un `.env` en vez de variables exportadas (es lo
# que documenta el scaffold). Hay que levantarlo ANTES de verificar nada, o
# `os.environ` se ve vacío y la evaluación aborta con un falso negativo.
from mia_agents._env import load_env_files  # noqa: E402

load_env_files()

from eval.config import (  # noqa: E402
    BASELINE,
    DIR_RESULTADOS,
    EXPERIMENTOS,
    ORDEN_ESCENARIOS,
)
from eval.judge import juzgar  # noqa: E402
from eval.report import escribir  # noqa: E402
from eval.runner import ejecutar_caso  # noqa: E402


def _modelo_configurado() -> str:
    """Identifica el modelo activo para dejarlo asentado en los resultados."""
    if os.environ.get("OLLAMA_HOST"):
        return f"ollama:{os.environ.get('OLLAMA_MODEL', 'llama3.1')}"
    if os.environ.get("BEDROCK_MODEL_ID"):
        return f"bedrock:{os.environ['BEDROCK_MODEL_ID']}"
    return "(sin configurar)"


def _verificar_proveedor() -> None:
    if os.environ.get("OLLAMA_HOST") or os.environ.get("BEDROCK_MODEL_ID"):
        return
    raise SystemExit(
        "No hay proveedor LLM configurado. Definí uno antes de evaluar:\n"
        '  export OLLAMA_HOST="http://localhost:11434"  '
        'OLLAMA_MODEL="llama3.1:8b"\n'
        '  # o bien: export BEDROCK_MODEL_ID="amazon.nova-lite-v1:0" '
        'AWS_REGION="us-east-1"'
    )


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eval/run.py", description=__doc__)
    p.add_argument(
        "--experimento",
        choices=sorted(EXPERIMENTOS),
        help="Corre las condiciones de un experimento. Sin esto, solo baseline.",
    )
    p.add_argument(
        "--escenarios",
        nargs="+",
        default=None,
        help=f"Ids a evaluar (por defecto los {len(ORDEN_ESCENARIOS)}).",
    )
    p.add_argument(
        "--condicion",
        default=None,
        help=(
            "Corre solo esta condición del experimento. Sirve para ampliar un "
            "brazo sin volver a pagar los demás."
        ),
    )
    p.add_argument(
        "--repeticiones",
        type=int,
        default=3,
        help="Corridas por caso; el LLM es estocástico (defecto: 3).",
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Corrida mínima de humo: escenario fácil, 1 repetición.",
    )
    p.add_argument(
        "--juez",
        action="store_true",
        help="Puntúa cada traza con el LLM-as-judge (una llamada extra por caso).",
    )
    p.add_argument(
        "--salida",
        default=None,
        help="Directorio de resultados (defecto: eval/results/<timestamp>).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    _verificar_proveedor()

    escenarios = args.escenarios or ORDEN_ESCENARIOS
    condiciones = EXPERIMENTOS[args.experimento] if args.experimento else [BASELINE]
    if args.condicion:
        condiciones = [c for c in condiciones if c.nombre == args.condicion]
        if not condiciones:
            raise SystemExit(
                f"No existe la condición {args.condicion!r} en "
                f"{args.experimento or 'baseline'}."
            )
    repeticiones = args.repeticiones
    if args.smoke:
        escenarios, condiciones, repeticiones = ["study-with-key"], [BASELINE], 1

    modelo = _modelo_configurado()
    etiqueta = args.experimento or "baseline"
    marca = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    destino = Path(args.salida) if args.salida else DIR_RESULTADOS / f"{etiqueta}-{marca}"
    destino.mkdir(parents=True, exist_ok=True)

    total = len(escenarios) * len(condiciones) * repeticiones
    print(f"# {etiqueta}: {total} corridas | modelo: {modelo}")
    print(f"# resultados -> {destino}\n")

    trazas = []
    hecho = 0
    fallos_seguidos = 0
    for condicion in condiciones:
        for escenario in escenarios:
            for rep in range(repeticiones):
                hecho += 1
                print(
                    f"[{hecho}/{total}] {condicion.nombre} · {escenario} · rep {rep}",
                    end=" ",
                    flush=True,
                )
                traza = ejecutar_caso(escenario, condicion, rep, modelo)
                trazas.append(traza)
                # Un fallo de infraestructura aislado se tolera; varios
                # seguidos casi siempre significan que el problema es global
                # (credenciales vencidas, proveedor caído) y seguir solo gasta
                # tiempo produciendo trazas inservibles.
                fallos_seguidos = fallos_seguidos + 1 if traza.fallo_infra else 0
                if fallos_seguidos >= 3:
                    print(
                        f"\nAbortado: {fallos_seguidos} fallos de infraestructura "
                        f"seguidos. Suele ser la sesión del proveedor vencida "
                        f"(`aws sso login`). Último error:\n"
                        f"{(traza.fallo_infra or '').strip().splitlines()[-1]}"
                    )
                    # Antes de salir se agrega lo que YA se midió. Abortar sin
                    # guardar deja el directorio con los JSON por caso pero sin
                    # `trazas.json` ni `summary.json`, y una campaña de horas
                    # queda inutilizable hasta que alguien la reconstruya a
                    # mano. Las corridas ya están pagas: perderlas es el peor
                    # desenlace posible de una interrupción.
                    parcial = [t.como_dict() for t in trazas]
                    (destino / "trazas.json").write_text(
                        json.dumps(parcial, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    escribir(destino, parcial)
                    print(
                        f"Se guardaron las {len(parcial)} corridas ya hechas en "
                        f"{destino} (parcial)."
                    )
                    raise SystemExit(2)
                marca_meta = "OK " if traza.meta_lograda else "fail"
                extra = " (infra)" if traza.fallo_infra else ""
                print(
                    f"-> {marca_meta} {len(traza.pasos):>2} tools "
                    f"{traza.latencia_s:>5.0f}s{extra}"
                )
                (destino / f"{condicion.nombre}__{escenario}__{rep}.json").write_text(
                    json.dumps(traza.como_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

    crudo = [t.como_dict() for t in trazas]

    if args.juez:
        print("\n# rúbrica cualitativa (LLM-as-judge)")
        for i, dic in enumerate(crudo, 1):
            print(f"[{i}/{len(crudo)}] juzgando {dic['condicion']} · {dic['escenario']}",
                  end=" ", flush=True)
            dic["juez"] = juzgar(dic)
            print("->", "error" if "error_juez" in dic["juez"] else "ok")

    (destino / "trazas.json").write_text(
        json.dumps(crudo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    resumen = escribir(destino, crudo)

    g = resumen["global"]
    print(f"\nMeta lograda: {g['exitos']}/{g['n']} ({g['tasa_exito']:.0%})"
          f" | repetidas: {g['repeticion_media']:.0%}")
    if resumen["modos_de_fallo"]:
        print("Modos de fallo:", ", ".join(
            f"{m}={c}" for m, c in resumen["modos_de_fallo"].items()))
    print(f"Resultados en {destino}  (summary.json + informe.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
