"""E7: reflexión al detectar un ciclo improductivo.

El bucle es el único modo de fallo que sobrevive con Nova Lite. E5 ya intentó
atacarlo bloqueando repeticiones y empeoró el resultado, y la razón quedó
medida: bloquear disparaba demasiado temprano, sobre corridas que se iban a
recuperar solas. Acá el disparador es la repetición *sostenida* y la
respuesta no es prohibir sino pedirle al modelo que reconsidere.

Todo corre con `MockLLMClient`, sin API.
"""

from __future__ import annotations

import json

import pytest

from mia_agents.testing import MockLLMClient, make_recording_tool
from mia_agents.types import LLMResponse, ToolCall
from student_framework import build_agent
from student_framework.ciclos import (
    UMBRAL_CICLO,
    VENTANA_CICLO,
    hay_ciclo,
    resumen_del_ciclo,
)


def _llamada(nombre: str, call_id: str, texto: str) -> LLMResponse:
    """El LLM pide la misma tool; `texto` distingue (o no) los argumentos."""
    return LLMResponse(
        content=None,
        tool_calls=[
            ToolCall(id=call_id, name=nombre, arguments=json.dumps({"text": texto}))
        ],
    )


def _agente_en_bucle(*, reflexionar: bool, pasos: int = 60, variedad: int = 2):
    """Agente cuyo LLM pide siempre las mismas `variedad` acciones."""
    tool, schema = make_recording_tool()
    respuestas = [
        _llamada(schema.name, f"c{i}", f"a{i % variedad}") for i in range(pasos)
    ]
    respuestas.append(LLMResponse(content="me rindo"))
    mock = MockLLMClient(respuestas)
    agente = build_agent(
        {"llm_client": mock, "max_iterations": pasos + 1, "reflexionar": reflexionar}
    )
    agente.register_tool(tool, schema)
    return agente, mock


def _avisos(agente) -> list[str]:
    """Turnos de reflexión que quedaron en el historial."""
    return [
        m["content"]
        for m in agente._history
        if m.get("role") == "user" and "[PAUSA DEL SISTEMA]" in (m.get("content") or "")
    ]


# --- detección pura ----------------------------------------------------------


def test_hay_ciclo_necesita_la_ventana_completa():
    """Con menos acciones que la ventana no se acusa a nadie de dar vueltas."""
    assert hay_ciclo([("look", "{}")] * (VENTANA_CICLO - 1)) is False


def test_hay_ciclo_detecta_repeticion_sostenida():
    assert hay_ciclo([("look", "{}"), ("examine", "{}")] * VENTANA_CICLO) is True


def test_hay_ciclo_ignora_secuencia_variada():
    variadas = [("t", str(i)) for i in range(VENTANA_CICLO * 2)]
    assert hay_ciclo(variadas) is False


def test_hay_ciclo_mira_solo_la_ventana_reciente():
    """Un ciclo viejo del que el agente ya salió no debe seguir disparando."""
    viejo = [("look", "{}")] * VENTANA_CICLO
    nuevo = [("t", str(i)) for i in range(VENTANA_CICLO)]
    assert hay_ciclo(viejo + nuevo) is False


def test_hay_ciclo_rechaza_ventana_invalida():
    with pytest.raises(ValueError):
        hay_ciclo([("a", "b")] * 30, ventana=0)


def test_resumen_nombra_las_acciones_repetidas():
    resumen = resumen_del_ciclo([("look", "{}"), ("examine", "{}")] * VENTANA_CICLO)
    assert "look" in resumen and "examine" in resumen


def test_resumen_vacio_si_no_hay_repeticiones():
    assert resumen_del_ciclo([("t", str(i)) for i in range(VENTANA_CICLO)]) == ""


def test_umbral_es_coherente_con_la_ventana():
    """Los valores calibrados tienen que seguir siendo un umbral de fracción."""
    assert 0 < UMBRAL_CICLO < 1
    assert VENTANA_CICLO > 1


# --- integración con el bucle del agente -------------------------------------


def test_apagado_por_defecto_no_inyecta_nada():
    """M1 y M2 no pueden cambiar de comportamiento."""
    agente, _ = _agente_en_bucle(reflexionar=False)
    agente.run("resolvé esto")
    assert _avisos(agente) == []


def test_encendido_inyecta_la_reflexion_al_detectar_el_ciclo():
    agente, _ = _agente_en_bucle(reflexionar=True)
    agente.run("resolvé esto")
    avisos = _avisos(agente)
    assert avisos, "el agente cicló y no se inyectó ninguna reflexión"


def test_la_reflexion_nombra_lo_que_se_esta_repitiendo():
    """Un aviso genérico le deja al modelo el trabajo que ya demostró no
    saber hacer: descubrir cuáles son las acciones estériles."""
    agente, _ = _agente_en_bucle(reflexionar=True)
    agente.run("resolvé esto")
    assert "record" in _avisos(agente)[0]


def test_no_se_repite_en_cada_paso():
    """Mientras dura el ciclo la condición es verdadera en todos los pasos;
    avisar veinte veces seguidas convierte el aviso en ruido."""
    agente, _ = _agente_en_bucle(reflexionar=True, pasos=60)
    agente.run("resolvé esto")
    assert len(_avisos(agente)) <= 60 // VENTANA_CICLO + 1


def test_no_dispara_si_el_agente_explora_con_variedad():
    agente, _ = _agente_en_bucle(reflexionar=True, pasos=60, variedad=60)
    agente.run("resolvé esto")
    assert _avisos(agente) == []


def test_la_reflexion_no_rompe_el_contrato_de_run():
    """Sigue devolviendo un AgentResult válido, con sus pasos."""
    agente, _ = _agente_en_bucle(reflexionar=True)
    resultado = agente.run("resolvé esto")
    assert resultado.answer
    assert len(resultado.steps) == 60


def test_resumen_rechaza_ventana_invalida():
    """`acciones[-0:]` es la lista entera, no la vacía: sin validar, una
    ventana de cero haría que el resumen describiera toda la historia."""
    with pytest.raises(ValueError):
        resumen_del_ciclo([("a", "{}")] * 30, ventana=0)
