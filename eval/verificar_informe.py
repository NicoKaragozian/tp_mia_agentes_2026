#!/usr/bin/env python3
"""Verifica que cada cifra del informe coincida con las trazas.

    python eval/verificar_informe.py

El informe cita más de setenta números repartidos entre tablas de resultados,
experimentos, rúbricas del juez y figuras. Cada vez que se agrega una campaña o
se recalcula una métrica, cualquiera de ellos puede quedar viejo sin que nada
lo avise, y una cifra desactualizada en un documento que se defiende oralmente
es peor que una que falta.

Este script recalcula todo desde `eval/results/*/trazas.json` y falla si algo no
coincide con `docs/informe-m3.md`. Requiere las trazas crudas, así que corre
solo en la máquina donde se hizo la evaluación; las figuras, en cambio, se
regeneran desde los resúmenes versionados (ver `eval/figuras.py`).

Los intervalos de confianza se calculan con el método de Wilson, el mismo que
usa el informe: con celdas de diez corridas la aproximación normal produce
límites fuera del rango válido.
"""
import json, math, statistics, collections
from pathlib import Path
from eval.metrics import eficiencia, agrupar_por
from eval.analysis import modo_principal

R, INF = Path("eval/results"), Path("docs/informe-m3.md").read_text(encoding="utf-8")
mal, n = [], 0
def tz(d): return [t for t in json.loads((R/d/"trazas.json").read_text("utf-8")) if not t.get("fallo_infra")]
def v(etq, calc, esperado):
    global n; n += 1
    if str(calc) != str(esperado): mal.append(f"{etq}: calculado={calc} informe={esperado}")
def wilson(ok, total, z=1.96):
    p = ok/total; d = 1 + z*z/total
    c = (p + z*z/(2*total))/d
    h = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/d
    return max(0, round(100*(c-h))), min(100, round(100*(c+h)))
def presente(etq, txt):
    global n; n += 1
    if txt not in INF: mal.append(f"{etq}: no aparece en el informe -> {txt!r}")

DIF = {"study-with-key":"easy","color-locks":"medium","apartment-keys":"medium","library-search":"hard",
       "office-sequence":"hard","extreme-archive":"extreme","vault-combination":"extreme","backtracking-vault":"extreme"}
base = [t for d in ("nova-final","e5-bloqueo","e6-planner") for t in tz(d) if t["condicion"]=="baseline"] + tz("nova-extreme")
por = collections.defaultdict(list)
for t in base: por[t["escenario"]].append(t)

# 3.3 tasa por escenario + IC
for e in DIF:
    g = por[e]; ok = sum(1 for t in g if t["meta_lograda"])
    presente(f"3.3 {e}", f"{ok} de {len(g)} ({round(100*ok/len(g))} %)")
    lo, hi = wilson(ok, len(g))
    presente(f"3.3 IC {e}", f"{lo} a {hi}")
ok = sum(1 for t in base if t["meta_lograda"])
presente("3.3 total", f"**{ok} de {len(base)} ({round(100*ok/len(base))} %)**")
lo, hi = wilson(ok, len(base))
presente("3.3 IC total", f"**{lo} a {hi}**")

# dificultad
pd = collections.defaultdict(lambda:[0,0])
for t in base:
    pd[DIF[t["escenario"]]][0]+=int(bool(t["meta_lograda"])); pd[DIF[t["escenario"]]][1]+=1
presente("dificultad", "easy %d %%, medium %d %%, hard %d %%,"%tuple(round(100*pd[d][0]/pd[d][1]) for d in ("easy","medium","hard")))
presente("dificultad extreme", f"extreme {round(100*pd['extreme'][0]/pd['extreme'][1])} %")
cinco = [t for t in base if DIF[t["escenario"]]!="extreme"]; ok5 = sum(1 for t in cinco if t["meta_lograda"])
presente("5 obligatorios", f"{ok5} de {len(cinco)}"); presente("5 obligatorios pct", f"{100*ok5/len(cinco):.1f}".replace(".",",")+" %")
lo5, hi5 = wilson(ok5, len(cinco))
presente("5 obligatorios IC", f"intervalo de {lo5} a {hi5}")

# 3.4 like-for-like
for etq, dirs, ex_txt in (("llama",("e1-memoria","e2-prompt"),"8 de 32 (25 %)"), ("nova",("e1-nova","e2-nova"),"70 de 100 (70 %)")):
    tr = [t for d in dirs for t in tz(d) if t["condicion"]=="baseline"]
    ok = sum(1 for t in tr if t["meta_lograda"]); fall=[t for t in tr if not t["meta_lograda"]]
    v(f"3.4 {etq} exito", f"{ok} de {len(tr)} ({round(100*ok/len(tr))} %)", ex_txt)
    c = collections.Counter(modo_principal(t) for t in fall)
    presente(f"3.4 {etq} bucle", f"{round(100*c['bucle']/len(fall))} %")

# 3.5 eficiencia agrupada
acc = collections.defaultdict(lambda:[0.0,0])
for t in base:
    if t["meta_lograda"]:
        acc[t["escenario"]][0]+=eficiencia(t); acc[t["escenario"]][1]+=1
for e in DIF:
    if acc[e][1]:
        presente(f"3.5 ef {e}", f"{acc[e][0]/acc[e][1]:.2f}".replace(".",","))
glob5 = [eficiencia(t) for t in cinco if t["meta_lograda"]]
presente("3.5 global", f"**{statistics.fmean(glob5):.2f}".replace(".",",")+"**")

# 3.6 juez
b = [t for t in tz("nova-final") if isinstance(t.get("juez"),dict) and "error_juez" not in t["juez"]]
D = ("coherencia_plan","recuperacion_errores","exploracion_eficiente")
for etq, sel in (("todas",b),("exito",[t for t in b if t["meta_lograda"]]),("fallo",[t for t in b if not t["meta_lograda"]])):
    for d in D: presente(f"3.6 {etq} {d}", f"{statistics.fmean(t['juez'][d] for t in sel):.2f}".replace(".",","))

# experimentos
for d, cond, ex, rep, pas in (("e1-nova","baseline","35/50","48","50,5"),("e1-nova","memoria_ajustada","29/50","58","60,5"),
                              ("e1-nova","memoria_minima","17/50","77","78,4"),("e2-nova","baseline","35/50","50","51,6"),
                              ("e2-nova","prompt_generico","35/50","48","50,4")):
    s = agrupar_por(tz(d),"condicion")[cond]
    v(f"{d} {cond} exito", f"{s.exitos}/{s.n}", ex)
    v(f"{d} {cond} repetidas", str(round(100*s.repeticion_media)), rep)
    v(f"{d} {cond} pasos", f"{s.pasos_medios:.1f}".replace(".",","), pas)
s = agrupar_por(tz("e3-limpio"),"condicion")
v("E3 baseline", f"{s['baseline'].exitos}/{s['baseline'].n}", "18/25")
v("E3 tokens", f"{s['con_memoria_acciones'].tokens_entrada_medios:,.0f}".replace(",","."), "136.515")
s = agrupar_por(tz("e5-bloqueo"),"condicion")
v("E5 baseline", str(round(100*s["baseline"].tasa_exito)), "80"); v("E5 bloqueo", str(round(100*s["con_bloqueo"].tasa_exito)), "70")
s = agrupar_por(tz("e6-planner"),"condicion")
v("E6 planner", f"{s['con_planner'].exitos}/{s['con_planner'].n}", "39/50")

# figura vs tabla
import re
svg = (Path("docs/figuras/eficiencia-por-escenario.svg")).read_text("utf-8")
for e in DIF:
    if acc[e][1]:
        val = f"{acc[e][0]/acc[e][1]:.2f}".replace(".",",")
        if f">{val}<" not in svg: mal.append(f"figura eficiencia: falta {e}={val}")
        n += 1

print(f"{n} comprobaciones · {len(mal)} discrepancias")
for m in mal:
    print("  !!", m)
raise SystemExit(1 if mal else 0)
