"""Tests de la infraestructura de evaluación (M3).

La taxonomía de errores y las métricas son las que sostienen todas las
afirmaciones del informe: si clasifican mal, el análisis entero queda
viciado. Se testean con trazas sintéticas, sin LLM ni mundo real, para que
corran en cualquier máquina y en milisegundos.
"""

from __future__ import annotations

import pytest

from eval.bucle import detectar_ciclo, primera_repeticion
from eval.calibracion import kappa_ponderado, muestrear, spearman
from eval.metrics import pass_at_k, pass_pow_k
from eval.analysis import (
    clasificar,
    fraccion_repetidas,
    modo_principal,
    resumen_modos,
    techo_contexto,
)
from eval.config import OPTIMOS, presupuesto_iteraciones
from eval.metrics import eficiencia, resumir


def _paso(indice: int, herramienta: str, argumentos: str, salida="ok", error=None):
    return {
        "indice": indice,
        "herramienta": herramienta,
        "argumentos": argumentos,
        "salida": salida,
        "error": error,
    }


def _traza(**kwargs):
    """Traza mínima válida; los kwargs pisan lo que haga falta."""
    base = {
        "escenario": "study-with-key",
        "dificultad": "easy",
        "condicion": "baseline",
        "repeticion": 0,
        "modelo": "test",
        "meta_lograda": False,
        "meta_razon": "puerta principal está cerrada",
        "optimo": 3,
        "pasos": [],
        "llamadas_llm": [],
        "n_llamadas_llm": 0,
        "input_tokens": 100,
        "output_tokens": 10,
        "latencia_s": 1.0,
        "corte": None,
        "respuesta": "no pude",
        "fallo_infra": None,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Presupuesto de iteraciones
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("escenario", list(OPTIMOS))
def test_presupuesto_supera_al_optimo(escenario: str):
    """Nunca se corta un escenario por nuestro techo antes de que el modelo
    tenga oportunidad de resolverlo: el presupuesto debe superar al óptimo."""
    assert presupuesto_iteraciones(escenario) > OPTIMOS[escenario]


# ---------------------------------------------------------------------------
# Detección de repeticiones
# ---------------------------------------------------------------------------


def test_fraccion_repetidas_cuenta_llamadas_identicas():
    pasos = [
        _paso(0, "examine", '{"target": "alfombra"}'),
        _paso(1, "examine", '{"target": "alfombra"}'),
        _paso(2, "examine", '{"target": "alfombra"}'),
        _paso(3, "take", '{"item": "llave"}'),
    ]
    assert fraccion_repetidas(pasos) == 0.5  # 2 repeticiones sobre 4 llamadas


def test_fraccion_repetidas_distingue_argumentos():
    """Misma herramienta con distinto objetivo NO es repetir."""
    pasos = [
        _paso(0, "examine", '{"target": "alfombra"}'),
        _paso(1, "examine", '{"target": "escritorio"}'),
    ]
    assert fraccion_repetidas(pasos) == 0.0


def test_fraccion_repetidas_sin_pasos():
    assert fraccion_repetidas([]) == 0.0


# ---------------------------------------------------------------------------
# Taxonomía de modos de fallo
# ---------------------------------------------------------------------------


def test_corrida_exitosa_no_tiene_modos_de_fallo():
    """Aunque se haya equivocado por el camino: si llegó, los errores fueron
    recuperados y no son modos de fallo."""
    traza = _traza(
        meta_lograda=True,
        pasos=[_paso(0, "examine", "{}", error="Argumentos inválidos para 'examine'.")],
    )
    assert clasificar(traza) == []
    assert modo_principal(traza) is None


def test_detecta_bucle():
    pasos = [_paso(i, "look", "{}") for i in range(10)]
    traza = _traza(pasos=pasos, corte="Se alcanzó el máximo de iteraciones (10).")
    modos = clasificar(traza)
    assert "bucle" in modos
    assert modo_principal(traza) == "bucle"


def test_detecta_tool_call_en_texto():
    """El modelo escribió la llamada como texto y el bucle la leyó como final."""
    traza = _traza(respuesta='{"name": "look"}')
    assert "tool_call_en_texto" in clasificar(traza)
    assert modo_principal(traza) == "tool_call_en_texto"


def test_detecta_accion_invalida_del_mundo():
    """La herramienta corrió, pero el mundo rechazó la acción."""
    traza = _traza(
        pasos=[_paso(0, "go", '{"direction": "sur"}', salida="Error: no hay salida 'sur'")],
    )
    assert "accion_invalida" in clasificar(traza)


def test_detecta_argumentos_invalidos_y_tool_alucinada():
    traza = _traza(
        pasos=[
            _paso(0, "examine", "{}", error="Argumentos inválidos para 'examine'."),
            _paso(1, "volar", "{}", error="Herramienta desconocida: 'volar'."),
        ]
    )
    modos = clasificar(traza)
    assert "argumentos_invalidos" in modos
    assert "tool_alucinada" in modos


def test_detecta_parada_prematura():
    """Cerró con texto normal, sin corte y sin cumplir la meta."""
    traza = _traza(respuesta="Creo que la puerta ya está abierta.")
    assert modo_principal(traza) == "parada_prematura"


def test_detecta_limite_de_iteraciones_sin_bucle():
    pasos = [_paso(i, "examine", f'{{"target": "obj{i}"}}') for i in range(10)]
    traza = _traza(pasos=pasos, corte="Se alcanzó el máximo de iteraciones (10).")
    assert modo_principal(traza) == "limite_iteraciones"


def test_detecta_desborde_de_contexto():
    traza = _traza(llamadas_llm=[{"input_tokens": 15_000}])
    assert "desborde_contexto" in clasificar(traza)


def test_detecta_orden_incorrecto():
    traza = _traza(meta_razon="condiciones cumplidas en orden incorrecto")
    assert "orden_incorrecto" in clasificar(traza)


def test_fallo_de_infraestructura_se_aisla():
    """Un caso que revienta por infra no se cuenta como fallo del agente."""
    traza = _traza(fallo_infra="ConnectionError: proveedor caído")
    assert clasificar(traza) == ["fallo_infraestructura"]


def test_resumen_modos_cuenta_principales():
    trazas = [
        _traza(pasos=[_paso(i, "look", "{}") for i in range(10)], corte="límite"),
        _traza(respuesta='{"name": "look"}'),
        _traza(meta_lograda=True),
    ]
    resumen = resumen_modos(trazas)
    assert resumen["bucle"] == 1
    assert resumen["tool_call_en_texto"] == 1
    assert sum(resumen.values()) == 2, "la corrida exitosa no debe contarse"


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------


def test_eficiencia_es_none_si_no_llego_a_la_meta():
    """Pocos pasos en una corrida fallida significa que se rindió, no que
    fue eficiente."""
    assert eficiencia(_traza(pasos=[_paso(0, "look", "{}")])) is None


def test_eficiencia_optimo_sobre_usados():
    traza = _traza(meta_lograda=True, optimo=3, pasos=[_paso(i, "x", str(i)) for i in range(6)])
    assert eficiencia(traza) == 0.5


def test_eficiencia_acotada_a_uno():
    """Resolver por debajo del óptimo publicado no da eficiencia > 1."""
    traza = _traza(meta_lograda=True, optimo=10, pasos=[_paso(0, "x", "0")])
    assert eficiencia(traza) == 1.0


def test_resumir_agrega_tasa_y_conteos():
    trazas = [_traza(meta_lograda=True, pasos=[_paso(0, "x", "0")]), _traza()]
    r = resumir(trazas)
    assert r.n == 2 and r.exitos == 1 and r.tasa_exito == 0.5


def test_resumir_sin_trazas_no_divide_por_cero():
    r = resumir([])
    assert r.n == 0 and r.tasa_exito == 0.0


def test_fallo_de_infra_gana_sobre_meta_lograda():
    """Una corrida que abrió la puerta y después reventó no es un éxito limpio.

    El mundo queda en estado ganador (check_goal da True) pero la corrida se
    truncó: contarla como éxito sin más escondería que el proveedor falló.
    """
    traza = _traza(meta_lograda=True, fallo_infra="ConnectionError: proveedor caído")
    assert clasificar(traza) == ["fallo_infraestructura"]


def test_resumir_excluye_las_corridas_contaminadas():
    """Sus pasos y tokens quedaron truncados: promediarlas ensucia todo."""
    trazas = [
        _traza(meta_lograda=True, pasos=[_paso(0, "x", "0")]),
        _traza(meta_lograda=False),
        _traza(meta_lograda=True, fallo_infra="boom", pasos=[_paso(i, "x", str(i)) for i in range(99)]),
    ]
    r = resumir(trazas)
    assert r.n == 2, "la corrida contaminada no entra en el denominador"
    assert r.descartadas == 1
    assert r.exitos == 1 and r.tasa_exito == 0.5
    assert r.pasos_medios == 0.5, "los 99 pasos truncados no deben promediarse"


# ---------------------------------------------------------------------------
# Generación de figuras (M3)
# ---------------------------------------------------------------------------


def test_resumen_incluye_el_cruce_condicion_escenario():
    """Sin el cruce, una figura que grafique el baseline de un experimento
    mezclaría su rama experimental: `por_escenario` agrega ambas."""
    from eval.report import construir_resumen

    trazas = [
        _traza(condicion="baseline", escenario="a", meta_lograda=True),
        _traza(condicion="baseline", escenario="a", meta_lograda=False),
        _traza(condicion="con_bloqueo", escenario="a", meta_lograda=False),
    ]
    r = construir_resumen(trazas)

    assert r["por_escenario"]["a"]["n"] == 3, "el agregado suma todo"
    cruce = r["por_condicion_escenario"]
    assert cruce["baseline"]["a"]["n"] == 2
    assert cruce["baseline"]["a"]["exitos"] == 1
    assert cruce["con_bloqueo"]["a"]["n"] == 1


def test_pooled_por_escenario_filtra_por_condicion(tmp_path, monkeypatch):
    """El bug que motivó el cruce: sumar `por_escenario` inflaría el
    denominador con las corridas de la rama experimental."""
    import json

    from eval import figuras

    campana = tmp_path / "camp"
    campana.mkdir()
    (campana / "summary.json").write_text(
        json.dumps(
            {
                "por_escenario": {"a": {"exitos": 5, "n": 20}},
                "por_condicion_escenario": {
                    "baseline": {"a": {"exitos": 4, "n": 10}},
                    "con_bloqueo": {"a": {"exitos": 1, "n": 10}},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(figuras, "RESULTADOS", tmp_path)

    assert figuras._pooled_por_escenario(["camp"]) == {"a": [4, 10]}
    assert figuras._pooled_por_escenario(["camp"], "con_bloqueo") == {"a": [1, 10]}


def test_pooled_falla_claro_si_la_condicion_no_existe(tmp_path, monkeypatch):
    import json

    from eval import figuras

    campana = tmp_path / "camp"
    campana.mkdir()
    (campana / "summary.json").write_text(
        json.dumps({"por_condicion_escenario": {"baseline": {"a": {"exitos": 1, "n": 2}}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(figuras, "RESULTADOS", tmp_path)

    with pytest.raises(KeyError, match="con_planner"):
        figuras._pooled_por_escenario(["camp"], "con_planner")


def test_barra_de_valor_cero_no_dibuja_barra(tmp_path):
    """Un ancho mínimo de un pixel haría ver un 0 % como si fuera positivo."""
    from eval.figuras import barras_horizontales

    destino = tmp_path / "f.svg"
    barras_horizontales(
        destino, "t", "s", ["nada", "todo"], [0.0, 100.0], ["0/10", "10/10"]
    )
    svg = destino.read_text(encoding="utf-8")

    assert 'width="0.0"' in svg, "el 0 debe dibujarse con ancho 0"
    assert "0/10" in svg and "10/10" in svg, "las anotaciones se muestran igual"


def test_las_figuras_no_leen_trazas_crudas():
    """La reproducibilidad prometida en el informe depende de esto: las
    trazas pesan 93 MB y no se versionan, así que un clon limpio no las
    tiene."""
    from pathlib import Path

    codigo = Path("eval/figuras.py").read_text(encoding="utf-8")
    assert "trazas.json" not in codigo, (
        "figuras.py debe construirse solo desde los resúmenes versionados"
    )


# --- techo de contexto por proveedor ----------------------------------------


def test_techo_contexto_distingue_proveedores():
    """El techo depende del modelo, no es una constante del problema."""
    assert techo_contexto("ollama:llama3.1:8b") == 16_384
    assert techo_contexto("bedrock:amazon.nova-lite-v1:0") == 300_000


def test_techo_contexto_cae_al_mas_chico_si_no_reconoce():
    """Ante un modelo desconocido conviene marcar de más que de menos."""
    assert techo_contexto("proveedor:modelo-inventado") == 16_384
    assert techo_contexto("") == 16_384


def test_desborde_no_se_marca_con_el_techo_de_otro_proveedor():
    """Un prompt de 16k desborda a Ollama pero no a Nova Lite.

    Es el error que este cambio corrige: medir las corridas de Bedrock contra
    el `num_ctx` que el framework le pasa a Ollama marcaba desbordes que no
    existían.
    """
    llamadas = [{"input_tokens": 16_000, "output_tokens": 10}]
    base = {"meta_lograda": False, "pasos": [], "llamadas_llm": llamadas,
            "corte": "limite_iteraciones", "fallo_infra": False}

    assert "desborde_contexto" in clasificar({**base, "modelo": "ollama:llama3.1:8b"})
    assert "desborde_contexto" not in clasificar(
        {**base, "modelo": "bedrock:amazon.nova-lite-v1:0"}
    )


# --- deteccion de ciclos improductivos ---------------------------------------


def _pasos(acciones):
    """Arma una lista de pasos a partir de nombres de herramienta."""
    return [
        {"indice": i, "herramienta": a, "argumentos": "{}", "salida": "", "error": None}
        for i, a in enumerate(acciones)
    ]


def test_primera_repeticion_encuentra_el_indice():
    pasos = _pasos(["look", "examine", "take", "look"])
    assert primera_repeticion(pasos) == 3


def test_primera_repeticion_none_si_todo_es_distinto():
    assert primera_repeticion(_pasos(["look", "examine", "take"])) is None


def test_detectar_ciclo_ignora_una_repeticion_aislada():
    """Una repetición suelta no es un ciclo: el 65 % de las corridas que
    repiten alguna vez igual llegan a la meta."""
    pasos = _pasos(["look", "a", "b", "look"] + [f"t{i}" for i in range(20)])
    assert detectar_ciclo(pasos) is None


def test_detectar_ciclo_dispara_con_repeticion_sostenida():
    """Veinte pasos alternando entre dos acciones son media docena de
    acciones distintas sobre veinte: muy por debajo del umbral."""
    pasos = _pasos([f"t{i}" for i in range(10)] + ["a", "b"] * 10)
    indice = detectar_ciclo(pasos)
    assert indice is not None and indice >= 10


def test_detectar_ciclo_no_dispara_si_la_corrida_es_corta():
    assert detectar_ciclo(_pasos(["a"] * 5)) is None


def test_detectar_ciclo_rechaza_ventana_invalida():
    with pytest.raises(ValueError):
        detectar_ciclo(_pasos(["a"] * 30), ventana=0)


# --- pass@k y pass^k ---------------------------------------------------------


def test_pass_at_k_crece_con_los_intentos():
    """Reintentar solo puede ayudar."""
    valores = [pass_at_k(30, 20, k) for k in (1, 2, 3, 5)]
    assert valores == sorted(valores)
    assert valores[0] == pytest.approx(20 / 30)


def test_pass_pow_k_decrece_con_los_intentos():
    """Exigir k aciertos seguidos solo puede costar más."""
    valores = [pass_pow_k(30, 20, k) for k in (1, 2, 3, 5)]
    assert valores == sorted(valores, reverse=True)
    assert valores[0] == pytest.approx(20 / 30)


def test_pass_at_k_degenera_cuando_no_quedan_fracasos():
    """Con n=10 y un solo éxito, pass@10 es 1,0 por construcción."""
    assert pass_at_k(10, 1, 10) == 1.0
    assert pass_at_k(10, 1, 5) == pytest.approx(0.5)


def test_pass_pow_k_es_cero_si_faltan_exitos():
    assert pass_pow_k(10, 2, 3) == 0.0


def test_pass_k_rechaza_argumentos_imposibles():
    with pytest.raises(ValueError):
        pass_at_k(10, 11, 1)
    with pytest.raises(ValueError):
        pass_pow_k(10, 5, 0)


# --- calibracion del juez ----------------------------------------------------


def test_kappa_acuerdo_perfecto():
    a = [1, 2, 3, 4, 5, 3, 2]
    assert kappa_ponderado(a, a) == pytest.approx(1.0)


def test_kappa_penaliza_menos_los_errores_chicos():
    """Es ponderado justamente para esto: confundir 4 con 5 no es lo mismo
    que confundir 1 con 5."""
    base = [1, 2, 3, 4, 5, 1, 5, 2]
    cerca = [1, 2, 3, 5, 5, 1, 5, 2]
    lejos = [1, 2, 3, 4, 1, 1, 1, 2]
    assert kappa_ponderado(base, cerca) > kappa_ponderado(base, lejos)


def test_kappa_rechaza_listas_incompatibles():
    with pytest.raises(ValueError):
        kappa_ponderado([1, 2], [1])
    with pytest.raises(ValueError):
        kappa_ponderado([], [])


def test_spearman_monotono_da_uno():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_promedia_empates():
    """Sin promediar los empates el coeficiente queda mal definido."""
    assert spearman([1, 1, 2, 2], [1, 1, 2, 2]) == pytest.approx(1.0)


def test_muestreo_es_reproducible():
    """La semilla es fija: regenerar el material no puede cambiar el conjunto."""
    trazas = [
        {"escenario": f"e{i % 4}", "meta_lograda": i % 3 == 0, "_origen": str(i),
         "juez": {}}
        for i in range(60)
    ]
    assert [t["_origen"] for t in muestrear(trazas, 12)] == [
        t["_origen"] for t in muestrear(trazas, 12)
    ]
