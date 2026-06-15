"""Tests del mundo simulado de M3.

Ejercitan las herramientas FIJAS de `mia_world` directamente, sin pasar
por un LLM real. Sirven para asegurar que el mundo es funcional y
consistente, independientemente del estado del agente del estudiante.

Una iteración futura añadirá un test que ejecute un agente real
(`build_agent`) contra un escenario; por ahora los tests del agente
viven en `test_m1.py` / `test_m2.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mia_world import (
    Item,
    Room,
    Scenario,
    World,
    check_goal,
    list_scenarios,
    load_scenario,
    make_world_tools,
)
from mia_world.cli import _resolve_scenario


SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "scenarios"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_study_scenario() -> Scenario:
    """Construye el escenario 'estudio con llave' inline.

    Los tests usan esto en vez de cargar el JSON para no acoplarse a la
    ruta del fichero. Un test aparte verifica que `load_scenario` produce
    un estado equivalente.
    """
    items = {
        "alfombra": Item(
            id="alfombra",
            name="alfombra",
            description="Una vieja alfombra. Algo abulta debajo.",
            container=True,
            contains=["llave_oro"],
        ),
        "llave_oro": Item(
            id="llave_oro",
            name="llave dorada",
            description="Una llave dorada, pesada.",
            takeable=True,
            hidden_by="alfombra",
        ),
        "escritorio": Item(
            id="escritorio",
            name="escritorio",
            description="Cajones vacíos.",
            container=True,
            contains=[],
        ),
        "puerta_principal": Item(
            id="puerta_principal",
            name="puerta principal",
            description="Puerta robusta de roble.",
            locked={"requires_item": "llave_oro"},
            open_state="closed",
        ),
    }
    rooms = {
        "estudio": Room(
            id="estudio",
            name="Estudio",
            description="Un estudio pequeño forrado de libros.",
            items=["alfombra", "escritorio", "puerta_principal"],
        ),
    }
    world = World(rooms=rooms, items=items, current_room="estudio")
    return Scenario(
        id="study-with-key",
        description="Un estudio cerrado.",
        user_message="Encuentra la forma de salir.",
        initial_world=world,
        goal={"type": "item_open", "item": "puerta_principal"},
    )


def _tools(world: World) -> dict[str, callable]:
    return {schema.name: fn for fn, schema in make_world_tools(world)}


# ---------------------------------------------------------------------------
# Visibilidad y look
# ---------------------------------------------------------------------------


def test_look_lists_visible_items_only() -> None:
    """`look` muestra los items directamente en la sala, no los ocultos."""
    world = _build_study_scenario().initial_world
    out = _tools(world)["look"]()
    assert "alfombra" in out
    assert "escritorio" in out
    assert "puerta principal" in out
    assert "llave" not in out, "la llave está oculta bajo la alfombra y no debería aparecer"


def test_look_marks_locked_doors_as_closed() -> None:
    world = _build_study_scenario().initial_world
    out = _tools(world)["look"]()
    assert "cerrada" in out


def test_examining_carpet_reveals_hidden_key() -> None:
    """Tras examinar la alfombra, la llave queda visible en la sala."""
    world = _build_study_scenario().initial_world
    tools = _tools(world)
    msg = tools["examine"](target="alfombra")
    assert "llave" in msg, f"el examine debe listar el contenido: {msg!r}"

    out = tools["look"]()
    assert "llave" in out, "la llave revelada debe aparecer en look posteriores"


# ---------------------------------------------------------------------------
# take
# ---------------------------------------------------------------------------


def test_take_hidden_item_requires_reveal_first() -> None:
    """No se puede tomar un item antes de descubrirlo."""
    world = _build_study_scenario().initial_world
    tools = _tools(world)
    msg = tools["take"](item="llave_oro")
    assert "Error" in msg
    assert "llave_oro" not in world.inventory


def test_take_after_reveal_moves_item_to_inventory() -> None:
    world = _build_study_scenario().initial_world
    tools = _tools(world)
    tools["examine"](target="alfombra")
    msg = tools["take"](item="llave_oro")
    assert "Tomas" in msg
    assert world.inventory == ["llave_oro"]
    # La llave ya no está en el contenedor padre.
    assert "llave_oro" not in world.items["alfombra"].contains


def test_take_non_takeable_fails() -> None:
    """La alfombra es contenedor pero no `takeable`. No debe poder cogerse."""
    world = _build_study_scenario().initial_world
    msg = _tools(world)["take"](item="alfombra")
    assert "Error" in msg
    assert "alfombra" not in world.inventory


# ---------------------------------------------------------------------------
# use
# ---------------------------------------------------------------------------


def test_use_without_item_in_inventory_fails() -> None:
    world = _build_study_scenario().initial_world
    msg = _tools(world)["use"](item="llave_oro", target="puerta_principal")
    assert "Error" in msg
    assert world.items["puerta_principal"].open_state == "closed"


def test_use_correct_key_opens_door() -> None:
    world = _build_study_scenario().initial_world
    tools = _tools(world)
    tools["examine"](target="alfombra")
    tools["take"](item="llave_oro")
    msg = tools["use"](item="llave_oro", target="puerta_principal")
    assert "abre" in msg.lower()
    assert world.items["puerta_principal"].open_state == "open"


def test_use_wrong_target_does_not_open() -> None:
    """Usar la llave sobre el escritorio (no cerrado) no rompe nada."""
    world = _build_study_scenario().initial_world
    tools = _tools(world)
    tools["examine"](target="alfombra")
    tools["take"](item="llave_oro")
    msg = tools["use"](item="llave_oro", target="escritorio")
    assert "Error" not in msg or "no pasa" in msg.lower()
    assert world.items["puerta_principal"].open_state == "closed"


# ---------------------------------------------------------------------------
# Solución óptima end-to-end + goal
# ---------------------------------------------------------------------------


def test_optimal_solution_satisfies_goal() -> None:
    scenario = _build_study_scenario()
    world = scenario.initial_world
    tools = _tools(world)

    assert check_goal(world, scenario.goal) == (False, "puerta principal está cerrada")

    tools["examine"](target="alfombra")
    tools["take"](item="llave_oro")
    tools["use"](item="llave_oro", target="puerta_principal")

    won, reason = check_goal(world, scenario.goal)
    assert won is True
    assert "abierta" in reason


# ---------------------------------------------------------------------------
# Cargador de escenarios desde JSON
# ---------------------------------------------------------------------------


SCENARIO_PATH = (
    Path(__file__).resolve().parents[2] / "scenarios" / "01-study-with-key.json"
)


@pytest.mark.skipif(
    not SCENARIO_PATH.exists(),
    reason=f"Escenario no encontrado en {SCENARIO_PATH}",
)
def test_load_scenario_from_disk() -> None:
    """`load_scenario` produce un mundo en el que la solución óptima funciona."""
    scenario = load_scenario(SCENARIO_PATH)
    assert scenario.id == "study-with-key"
    assert scenario.goal == {"type": "item_open", "item": "puerta_principal"}

    world = scenario.initial_world
    tools = _tools(world)
    tools["examine"](target="alfombra")
    tools["take"](item="llave_oro")
    tools["use"](item="llave_oro", target="puerta_principal")
    won, _ = check_goal(world, scenario.goal)
    assert won is True


# ---------------------------------------------------------------------------
# Robustez frente a entradas inválidas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tool_name,kwargs",
    [
        ("examine", {"target": "fantasma"}),
        ("take", {"item": "fantasma"}),
        ("use", {"item": "fantasma", "target": "puerta_principal"}),
        ("use", {"item": "llave_oro", "target": "fantasma"}),
    ],
)
def test_invalid_ids_return_error_strings(tool_name: str, kwargs: dict) -> None:
    """Ids inexistentes nunca deben lanzar excepciones; devuelven texto de error."""
    world = _build_study_scenario().initial_world
    msg = _tools(world)[tool_name](**kwargs)
    assert isinstance(msg, str)
    assert "Error" in msg


# ---------------------------------------------------------------------------
# Contenedores cerrados con llave (semántica de medium/hard)
# ---------------------------------------------------------------------------


def test_examining_locked_container_hides_contents() -> None:
    """Un contenedor cerrado con llave NO debe filtrar sus contenidos al examinarlo."""
    items = {
        "cofre": Item(
            id="cofre",
            name="cofre",
            description="Un cofre.",
            container=True,
            contains=["tesoro"],
            locked={"requires_item": "llave"},
            open_state="closed",
        ),
        "tesoro": Item(
            id="tesoro",
            name="tesoro",
            description="...",
            takeable=True,
            hidden_by="cofre",
        ),
    }
    rooms = {"sala": Room(id="sala", name="Sala", description="...", items=["cofre"])}
    world = World(rooms=rooms, items=items, current_room="sala")

    msg = _tools(world)["examine"](target="cofre")
    assert "tesoro" not in msg, (
        "examinar un contenedor cerrado con llave no debe listar su contenido"
    )
    assert "cerrad" in msg.lower()
    assert "cofre" not in world.revealed, (
        "el contenedor no debe quedar 'revealed' hasta que se abra"
    )


def test_unlocking_container_then_examining_reveals_contents() -> None:
    """Una vez abierto con `use`, el examen del contenedor debe revelar el contenido."""
    items = {
        "cofre": Item(
            id="cofre",
            name="cofre",
            description="Un cofre.",
            container=True,
            contains=["tesoro"],
            locked={"requires_item": "llave"},
            open_state="closed",
        ),
        "tesoro": Item(
            id="tesoro",
            name="tesoro",
            description="Un tesoro.",
            takeable=True,
            hidden_by="cofre",
        ),
        "llave": Item(id="llave", name="llave", description="...", takeable=True),
    }
    rooms = {
        "sala": Room(id="sala", name="Sala", description="...", items=["cofre", "llave"])
    }
    world = World(rooms=rooms, items=items, current_room="sala")
    tools = _tools(world)

    tools["take"](item="llave")
    tools["use"](item="llave", target="cofre")
    msg = tools["examine"](target="cofre")
    assert "tesoro" in msg
    assert "cofre" in world.revealed


# ---------------------------------------------------------------------------
# Suite de escenarios: solución óptima por dificultad
# ---------------------------------------------------------------------------


# (scenario_file, action_sequence). Cada acción es (tool_name, kwargs).
_SCENARIO_SOLUTIONS = {
    "01-study-with-key.json": [
        ("examine", {"target": "alfombra"}),
        ("take", {"item": "llave_oro"}),
        ("use", {"item": "llave_oro", "target": "puerta_principal"}),
    ],
    "02-medium-color-locks.json": [
        ("take", {"item": "llave_plata"}),
        ("use", {"item": "llave_plata", "target": "cofre_plata"}),
        ("examine", {"target": "cofre_plata"}),
        ("take", {"item": "llave_roja"}),
        ("use", {"item": "llave_roja", "target": "cofre_rojo"}),
        ("examine", {"target": "cofre_rojo"}),
        ("take", {"item": "llave_verde"}),
        ("use", {"item": "llave_verde", "target": "cofre_verde"}),
        ("examine", {"target": "cofre_verde"}),
        ("take", {"item": "llave_oro"}),
        ("use", {"item": "llave_oro", "target": "puerta_principal"}),
    ],
    "03-hard-library-search.json": [
        ("examine", {"target": "estanteria_alta"}),
        ("examine", {"target": "libro_sermones"}),
        ("take", {"item": "llave_caja"}),
        ("use", {"item": "llave_caja", "target": "caja_fuerte"}),
        ("examine", {"target": "caja_fuerte"}),
        ("take", {"item": "llave_grabada"}),
        ("use", {"item": "llave_grabada", "target": "puerta_principal"}),
    ],
    "04-extreme-archive.json": [
        ("examine", {"target": "estanteria_archivo"}),
        ("examine", {"target": "expediente_7240"}),
        ("take", {"item": "llave_archivo"}),
        ("use", {"item": "llave_archivo", "target": "puerta_principal"}),
    ],
    "05-medium-apartment-keys.json": [
        ("go", {"direction": "norte"}),
        ("go", {"direction": "este"}),
        ("examine", {"target": "cajon"}),
        ("take", {"item": "llave_oro"}),
        ("go", {"direction": "oeste"}),
        ("go", {"direction": "sur"}),
        ("use", {"item": "llave_oro", "target": "puerta_principal"}),
    ],
    "06-hard-office-sequence.json": [
        ("go", {"direction": "este"}),
        ("go", {"direction": "este"}),
        ("examine", {"target": "cajon_llaves"}),
        ("take", {"item": "llave_caja"}),
        ("go", {"direction": "oeste"}),
        ("go", {"direction": "norte"}),
        ("use", {"item": "llave_caja", "target": "caja_fuerte"}),
        ("examine", {"target": "caja_fuerte"}),
        ("take", {"item": "documento_confidencial"}),
        ("take", {"item": "llave_maestra"}),
        ("go", {"direction": "sur"}),
        ("go", {"direction": "oeste"}),
        ("use", {"item": "llave_maestra", "target": "puerta_principal"}),
    ],
    "07-extreme-vault-combination.json": [
        ("go", {"direction": "norte"}),
        ("go", {"direction": "este"}),
        ("examine", {"target": "banco_herramientas"}),
        ("take", {"item": "nucleo_rojo"}),
        ("take", {"item": "llave_deposito"}),
        ("go", {"direction": "oeste"}),
        ("use", {"item": "llave_deposito", "target": "puerta_deposito"}),
        ("go", {"direction": "norte"}),
        ("examine", {"target": "cajon_deposito"}),
        ("take", {"item": "nucleo_verde"}),
        ("take", {"item": "llave_vitrina"}),
        ("go", {"direction": "sur"}),
        ("go", {"direction": "oeste"}),
        ("use", {"item": "llave_vitrina", "target": "vitrina"}),
        ("examine", {"target": "vitrina"}),
        ("take", {"item": "nucleo_azul"}),
        ("go", {"direction": "este"}),
        ("go", {"direction": "sur"}),
        ("use", {"item": "nucleo_rojo", "target": "puerta_principal"}),
        ("use", {"item": "nucleo_azul", "target": "puerta_principal"}),
        ("use", {"item": "nucleo_verde", "target": "puerta_principal"}),
    ],
    "08-extreme-backtracking-vault.json": [
        ("go", {"direction": "norte"}),
        ("examine", {"target": "escritorio"}),
        ("take", {"item": "llave_intermedia"}),
        ("use", {"item": "llave_intermedia", "target": "puerta_blindada"}),
        ("go", {"direction": "norte"}),
        ("examine", {"target": "armario"}),
        ("take", {"item": "llave_boveda"}),
        ("use", {"item": "llave_boveda", "target": "reja"}),
        ("go", {"direction": "norte"}),
        ("examine", {"target": "caja_seguridad"}),
        ("take", {"item": "llave_oxidada"}),
        ("go", {"direction": "sur"}),
        ("go", {"direction": "sur"}),
        ("go", {"direction": "sur"}),
        ("use", {"item": "llave_oxidada", "target": "cofre_antiguo"}),
        ("examine", {"target": "cofre_antiguo"}),
        ("take", {"item": "llave_maestra"}),
        ("use", {"item": "llave_maestra", "target": "puerta_principal"}),
    ],
}


@pytest.mark.parametrize("scenario_file,actions", list(_SCENARIO_SOLUTIONS.items()))
def test_scenario_optimal_solution_wins(scenario_file: str, actions: list) -> None:
    """Cada escenario JSON tiene una solución óptima conocida que satisface la meta."""
    scenario = load_scenario(SCENARIOS_DIR / scenario_file)
    world = scenario.initial_world
    tools = _tools(world)
    for tool_name, kwargs in actions:
        result = tools[tool_name](**kwargs)
        assert not result.startswith("Error"), (
            f"{tool_name}({kwargs}) en {scenario_file} devolvió error: {result}"
        )
    won, reason = check_goal(world, scenario.goal)
    assert won, f"{scenario_file} debería resolverse con la secuencia óptima: {reason}"


def test_scenarios_cover_all_difficulties() -> None:
    """La carpeta `scenarios/` ofrece al menos un escenario por nivel de dificultad."""
    scenarios = list_scenarios(SCENARIOS_DIR)
    by_diff = {sc.difficulty for sc in scenarios}
    expected = {"easy", "medium", "hard", "extreme"}
    assert expected.issubset(by_diff), (
        f"faltan dificultades: {expected} - {by_diff} = {expected - by_diff}"
    )


# ---------------------------------------------------------------------------
# Resolver de la CLI
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec,expected_id",
    [
        ("easy", "study-with-key"),
        ("medium", "color-locks"),
        ("hard", "library-search"),
        ("extreme", "extreme-archive"),
        ("study-with-key", "study-with-key"),
        ("color-locks", "color-locks"),
        ("library-search", "library-search"),
        ("extreme-archive", "extreme-archive"),
        ("apartment-keys", "apartment-keys"),
        ("office-sequence", "office-sequence"),
    ],
)
def test_cli_resolver_finds_scenarios(spec: str, expected_id: str) -> None:
    sc = _resolve_scenario(spec, SCENARIOS_DIR)
    assert sc.id == expected_id


def test_cli_resolver_difficulty_picks_first_by_filename() -> None:
    """Con varios escenarios por dificultad, el resolver devuelve el de menor índice."""
    # Hay dos `medium` (02-color-locks, 05-apartment-keys) y dos `hard`
    # (03-library-search, 06-office-sequence). El resolver elige el primero
    # por orden de nombre de fichero.
    assert _resolve_scenario("medium", SCENARIOS_DIR).id == "color-locks"
    assert _resolve_scenario("hard", SCENARIOS_DIR).id == "library-search"


def test_cli_resolver_unknown_spec_raises() -> None:
    with pytest.raises(SystemExit):
        _resolve_scenario("no-existe", SCENARIOS_DIR)


# ---------------------------------------------------------------------------
# Navegación multi-sala (verbo `go`) — semántica de medium/hard
# ---------------------------------------------------------------------------


def _build_two_room_world() -> World:
    items = {
        "llave": Item(id="llave", name="llave", description="...", takeable=True),
        "puerta": Item(
            id="puerta",
            name="puerta",
            description="...",
            locked={"requires_item": "llave"},
            open_state="closed",
        ),
    }
    rooms = {
        "sala_a": Room(
            id="sala_a",
            name="Sala A",
            description="...",
            items=["puerta"],
            exits={"norte": "sala_b"},
        ),
        "sala_b": Room(
            id="sala_b",
            name="Sala B",
            description="...",
            items=["llave"],
            exits={"sur": "sala_a"},
        ),
    }
    return World(rooms=rooms, items=items, current_room="sala_a")


def test_make_world_tools_includes_go_only_with_exits() -> None:
    single_room = _build_study_scenario().initial_world
    assert "go" not in {sch.name for _, sch in make_world_tools(single_room)}

    multi_room = _build_two_room_world()
    assert "go" in {sch.name for _, sch in make_world_tools(multi_room)}


def test_go_changes_current_room_and_logs_event() -> None:
    world = _build_two_room_world()
    assert world.event_log == ["enter:sala_a"]
    msg = _tools(world)["go"](direction="norte")
    assert "Sala B" in msg
    assert world.current_room == "sala_b"
    assert world.event_log == ["enter:sala_a", "enter:sala_b"]


def test_go_invalid_direction_returns_error_and_does_not_move() -> None:
    world = _build_two_room_world()
    msg = _tools(world)["go"](direction="oeste")
    assert "Error" in msg
    assert world.current_room == "sala_a"


def test_look_lists_available_exits() -> None:
    world = _build_two_room_world()
    out = _tools(world)["look"]()
    assert "Salidas" in out
    assert "norte" in out


def test_item_not_visible_from_other_room() -> None:
    """La llave de sala_b no es visible ni tomable desde sala_a."""
    world = _build_two_room_world()
    tools = _tools(world)
    assert "Error" in tools["take"](item="llave")
    tools["go"](direction="norte")
    assert "Tomas" in tools["take"](item="llave")
    assert "llave" in world.inventory


# ---------------------------------------------------------------------------
# Goals compuestos y de secuencia
# ---------------------------------------------------------------------------


def test_goal_agent_in_room_and_item_in_inventory() -> None:
    world = _build_two_room_world()
    assert check_goal(world, {"type": "agent_in_room", "room": "sala_b"})[0] is False
    _tools(world)["go"](direction="norte")
    assert check_goal(world, {"type": "agent_in_room", "room": "sala_b"})[0] is True

    assert (
        check_goal(world, {"type": "item_in_inventory", "item": "llave"})[0] is False
    )
    _tools(world)["take"](item="llave")
    assert check_goal(world, {"type": "item_in_inventory", "item": "llave"})[0] is True


def test_goal_all_of_requires_every_subgoal() -> None:
    world = _build_two_room_world()
    goal = {
        "type": "all_of",
        "goals": [
            {"type": "item_in_inventory", "item": "llave"},
            {"type": "item_open", "item": "puerta"},
        ],
    }
    tools = _tools(world)
    assert check_goal(world, goal)[0] is False
    tools["go"](direction="norte")
    tools["take"](item="llave")
    assert check_goal(world, goal)[0] is False, "falta abrir la puerta"
    tools["go"](direction="sur")
    tools["use"](item="llave", target="puerta")
    assert check_goal(world, goal)[0] is True


def test_goal_any_of_passes_with_one_subgoal() -> None:
    world = _build_two_room_world()
    goal = {
        "type": "any_of",
        "goals": [
            {"type": "item_open", "item": "puerta"},
            {"type": "agent_in_room", "room": "sala_b"},
        ],
    }
    assert check_goal(world, goal)[0] is False
    _tools(world)["go"](direction="norte")
    assert check_goal(world, goal)[0] is True


def test_multi_item_lock_opens_only_when_all_pieces_inserted() -> None:
    items = {
        "a": Item(id="a", name="pieza A", description="...", takeable=True),
        "b": Item(id="b", name="pieza B", description="...", takeable=True),
        "x": Item(id="x", name="pieza X", description="...", takeable=True),
        "panel": Item(
            id="panel",
            name="panel",
            description="...",
            locked={"requires_items": ["a", "b"]},
            open_state="closed",
        ),
    }
    rooms = {
        "s": Room(id="s", name="S", description="...", items=["a", "b", "x", "panel"])
    }
    world = World(rooms=rooms, items=items, current_room="s")
    tools = _tools(world)
    for piece in ("a", "b", "x"):
        tools["take"](item=piece)

    assert "no encaja" in tools["use"](item="x", target="panel").lower()
    assert world.items["panel"].open_state == "closed"

    msg_a = tools["use"](item="a", target="panel")
    assert "falta" in msg_a.lower()
    assert world.items["panel"].open_state == "closed"

    msg_b = tools["use"](item="b", target="panel")
    assert "abre" in msg_b.lower()
    assert world.items["panel"].open_state == "open"


def test_locked_exit_blocks_until_gate_opened() -> None:
    items = {
        "llave": Item(id="llave", name="llave", description="...", takeable=True),
        "porton": Item(
            id="porton",
            name="portón",
            description="...",
            locked={"requires_item": "llave"},
            open_state="closed",
        ),
    }
    rooms = {
        "s1": Room(
            id="s1",
            name="S1",
            description="...",
            items=["llave", "porton"],
            exits={"norte": "s2"},
            locked_exits={"norte": "porton"},
        ),
        "s2": Room(id="s2", name="S2", description="...", exits={"sur": "s1"}),
    }
    world = World(rooms=rooms, items=items, current_room="s1")
    tools = _tools(world)

    blocked = tools["go"](direction="norte")
    assert "Error" in blocked and "bloqueado" in blocked.lower()
    assert world.current_room == "s1"

    tools["take"](item="llave")
    tools["use"](item="llave", target="porton")
    assert "Llegas" in tools["go"](direction="norte")
    assert world.current_room == "s2"


def test_goal_sequence_enforces_order() -> None:
    """`sequence` falla si las condiciones se cumplen en el orden equivocado."""
    goal = {
        "type": "sequence",
        "goals": [
            {"type": "item_in_inventory", "item": "llave"},
            {"type": "item_open", "item": "puerta"},
        ],
    }

    # Orden correcto: tomar la llave ANTES de abrir la puerta.
    world = _build_two_room_world()
    tools = _tools(world)
    tools["go"](direction="norte")
    tools["take"](item="llave")
    tools["go"](direction="sur")
    tools["use"](item="llave", target="puerta")
    assert check_goal(world, goal)[0] is True

    # Mismo estado final, pero el `event_log` revela el orden: aquí no hay
    # forma física de abrir antes de tomar, así que validamos el chequeo de
    # orden con un log manipulado.
    world2 = _build_two_room_world()
    world2.inventory.append("llave")
    world2.items["puerta"].open_state = "open"
    world2.event_log = ["enter:sala_a", "open:puerta", "take:llave"]
    won, reason = check_goal(world2, goal)
    assert won is False
    assert "orden" in reason
