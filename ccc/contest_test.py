from pathlib import Path

import pytest

from . import contest
from .__main__ import load
from .contest import (
    CHECKS,
    DIRS,
    RULES,
    baseline6,
    cycle_gap,
    cycle_program,
    fire3,
    frame6,
    hexagon,
    parse,
    program6,
    ray,
    render,
    ring,
    run4,
    run5,
    solve,
    submissions6,
    valid6,
)

DATA = Path(__file__).parent.parent / "data"

BOARD_LEVELS = (2, 3)  # levels whose input items are boards
BOARD_INPUTS = sorted(
    p.name for lvl in BOARD_LEVELS for p in DATA.glob(f"in_level-{lvl}_*.txt")
)
OUTPUTS = sorted(  # every output that exists, uploaded and confirmed (or the example)
    (lvl, p.name.replace("out_", "in_", 1))
    for lvl in RULES
    if lvl not in CHECKS  # those have many valid answers: see test_valid_outputs
    for p in DATA.glob(f"out_level-{lvl}_*.txt")
)


def read(name: str) -> str:
    return (DATA / name).read_text()


def blocks(name: str) -> list[list[str]]:
    """the raw rows of each board in an input file"""
    lines = read(name).splitlines()
    out, i = [], 1
    for _ in range(int(lines[0])):
        while not lines[i].strip():
            i += 1
        rows = int(lines[i].split()[1])
        out.append(lines[i + 1 : i + 1 + rows])
        i += 1 + rows
    return out


def small(*cells) -> dict:
    """hexagon(2) with (cell, char) overrides"""
    return parse(hexagon(2).splitlines()) | dict(cells)


def test_level1_example():
    radii = [int(x) for x in read("in_level-1_0-example.txt").split()[1:]]
    expected = read("out_level-1_0-example.txt").strip()
    assert "\n\n".join(hexagon(r) for r in radii) == expected


@pytest.mark.parametrize("level, name", OUTPUTS)
def test_outputs(level: int, name: str):
    data = load(read(name).splitlines())
    expected = read(name.replace("in_", "out_", 1)).strip()
    assert solve(data, level) == expected


@pytest.mark.parametrize("name", BOARD_INPUTS)
def test_load_boards(name: str):
    boards = load(read(name).splitlines())["items"]
    assert len(boards) == int(read(name).split()[0]) == len(blocks(name))
    for rows, b in zip(blocks(name), boards):
        assert render(b) == "\n".join(rows)
        emitters = [c for c in b.values() if c in DIRS]
        assert emitters and len(set(emitters)) == len(emitters)


# hexagon(2):  --*-*-*--
#              -*-O-O-*-
#              *-O-O-O-*
#              -*-O-O-*-
#              --*-*-*--
@pytest.mark.parametrize(
    "start, digit, expected",
    [
        ((2, 0), "1", [(2, 2), (2, 4), (2, 6)]),
        ((0, 2), "2", [(1, 3), (2, 4), (3, 5)]),
        ((0, 6), "3", [(1, 5), (2, 4), (3, 3)]),
        ((2, 8), "4", [(2, 6), (2, 4), (2, 2)]),
        ((4, 6), "5", [(3, 5), (2, 4), (1, 3)]),
        ((4, 2), "6", [(3, 3), (2, 4), (1, 5)]),
    ],
)
def test_ray_directions(start, digit, expected):
    assert list(ray(small((start, digit)), start, digit)) == expected


@pytest.mark.parametrize("start, digit", [((0, 2), "6"), ((2, 0), "4"), ((4, 6), "2")])
def test_ray_outward_is_empty(start, digit):
    assert list(ray(small((start, digit)), start, digit)) == []


@pytest.mark.parametrize(
    "block, expected",
    [
        (((2, 4), "*"), [(2, 2)]),
        (((2, 6), "4"), [(2, 2), (2, 4)]),
        (((2, 2), "M"), [(2, 2), (2, 4), (2, 6)]),  # passes through 'M'
    ],
)
def test_ray_stops_at_star_and_emitter(block, expected):
    assert list(ray(small(((2, 0), "1"), block), (2, 0), "1")) == expected


def test_fire3_rules():
    # beams on hexagon(2): 1 -> (2,2) (2,4) (2,6), 2 -> (1,3) (2,4) (3,5),
    # 4 -> (3,5) (3,3), 6 -> (3,3) (2,4) (1,5)
    emitters = [((2, 0), "1"), ((0, 2), "2"), ((3, 7), "4"), ((4, 2), "6")]
    b = fire3(small(*emitters, ((2, 4), "M"), ((2, 6), "M")))
    assert b[(2, 4)] == "O"  # 3 hits destroy
    assert b[(3, 5)] == b[(3, 3)] == "M"  # 2 hits create
    assert b[(2, 2)] == b[(1, 3)] == "O"  # 1 hit, unchanged
    assert b[(2, 6)] == "M"  # 1 hit, existing matter stays


@pytest.mark.parametrize("r", [2, 3, 7])
def test_ring(r: int):
    cells = ring(r)
    board = parse(hexagon(r).splitlines())
    assert len(cells) == len(set(cells)) == 6 * r
    assert all(board[c] == "*" for c in cells)
    corners = [(r, 0), (0, r), (0, 3 * r), (r, 4 * r), (2 * r, 3 * r), (2 * r, r)]
    assert [cells[k * r] for k in range(6)] == corners  # emitter starts, 1..6


def program(*ticks: str) -> list[list[str]]:
    return [t.split() for t in ticks]


def test_run4_toggle_and_shared_cell():
    # ring(2): 0 (2,0) 1 (1,1) 2 (0,2) ... 10 (4,2) 11 (3,1)
    b = run4(
        (
            2,
            program(
                "T T - - - -",  # 1 → and 2 ↘ meet at (2,4): M
                "- - T - - -",  # + 3 ↙: 3 hits at (2,4) destroy it again
                # 1 and 2 both move to (1,1) before firing, 3 off, 6 ↗ on:
                # 1 → (1,3) (1,5), 2 ↘ (2,2) (3,3), 6 ↗ (3,3) (2,4) (1,5)
                "F B T - - T",
            ),
        )
    )
    assert render(b) == render(small(((3, 3), "M"), ((1, 5), "M")))


def test_run4_wraps_around():
    b = run4(
        (
            2,
            program(
                "B T - - - -",  # 1 back to index 11 (3,1), 2 ↘ on
                "T - - - - -",  # 1 → (3,3) (3,5) meets 2 ↘ at (3,5)
                "F - - - - -",  # 1 forward to index 0 (2,0), meets 2 at (2,4)
            ),
        )
    )
    assert render(b) == render(small(((3, 5), "M"), ((2, 4), "M")))


def test_load_level4():
    items = load(read("in_level-4_0-example.txt").splitlines())["items"]
    assert [(r, len(ticks)) for r, ticks in items] == [(2, 3), (3, 6), (3, 6)]
    assert all(len(t) == 6 for _, ticks in items for t in ticks)


def test_load_level5():
    items = load(read("in_level-5_0-example.txt").splitlines())["items"]
    shapes = [(r, len(ticks)) for r, _, ticks in items]
    assert shapes == [(3, 7), (3, 6)]
    assert [list(p.values()).count("M") for _, p, _ in items] == [5, 3]


ROW = ["T", "-", "-", "T", "-", "-"]  # emitters 1 + 4: (2,2) (2,4) (2,6) get 2 hits
IDLE = ["-"] * 6


@pytest.mark.parametrize(
    "want, ticks, expected",
    [
        ({(2, 4)}, [ROW], 0),  # its neighbours are 'M' too: not submitted
        ({(2, 2), (2, 4), (2, 6)}, [ROW], 1),
        ({(2, 2), (2, 4), (2, 6)}, [ROW, IDLE, IDLE], 3),  # rebuilt every tick
        ({(2, 2), (2, 4), (2, 6)}, [], 0),
    ],
)
def test_run5(want, ticks, expected):
    pattern = small(*((c, "M") for c in want))
    assert run5((2, pattern, ticks)) == expected


def test_load_level6():
    items = load(read("in_level-6_0-example.txt").splitlines())["items"]
    assert [(r, count) for r, _, count in items] == [(3, 3), (3, 1), (4, 4)]
    assert [list(p.values()).count("M") for _, p, _ in items] == [5, 16, 8]


def programs(text: str) -> list[list[list[str]]]:
    return [[t.split() for t in p.splitlines()] for p in text.strip().split("\n\n")]


VALID_OUTPUTS = sorted(p.name for p in DATA.glob("out_level-6_*.txt"))


@pytest.mark.parametrize("name", VALID_OUTPUTS)
def test_valid_outputs(name: str):
    items = load(read(name.replace("out_", "in_", 1)).splitlines())["items"]
    progs = programs(read(name))
    assert len(progs) == len(items)
    assert all(valid6(item, p) for item, p in zip(items, progs))


def test_program6_example(monkeypatch):
    monkeypatch.setattr(contest, "BUDGET", 0.05)
    items = load(read("in_level-6_0-example.txt").splitlines())["items"]
    progs = [program6(item) for item in items]
    assert all(valid6(item, p) for item, p in zip(items, progs))
    assert sum(map(len, progs)) < 446  # the reference's naive solution


def test_frame6_repeats_one_tick():
    # emitters 1 → and 4 ← share the middle row: on at home, it is built every
    # tick, so k = 5 takes setup (1 toggle tick) + 4 idle ticks
    order = (2, small(*(((2, x), "M") for x in (2, 4, 6))), 5)
    assert cycle_program([(0, None, None, 0, None, None)], 5) == [ROW] + [IDLE] * 4
    prog = frame6(order)
    assert prog is not None and len(prog) == 1 + 4 and valid6(order, prog)


def test_cycle_gap():
    stay = (1, None, None, None, None, None)
    assert cycle_gap([(0,) + stay[1:], stay]) == 1  # on in both, moves 1 cell
    assert cycle_gap([(-1,) + stay[1:], stay]) == 2  # moves 2 cells
    off = (None,) * 6
    assert cycle_gap([(-1,) + stay[1:], off, stay]) == 2  # off, move 2, on: 4 ticks


def test_submissions6_matches_run5():
    items = load(read("in_level-6_0-example.txt").splitlines())["items"]
    for order in items:
        prog = baseline6(order)
        r, pattern, count = order
        subs = submissions6(order, prog)
        assert len(subs) == run5((r, pattern, prog)) == count


@pytest.mark.parametrize("name", ["in_level-6_0-example.txt", "in_level-6_1-small.txt"])
def test_program6_never_worse(name: str, monkeypatch):
    monkeypatch.setattr(contest, "BUDGET", 0.05)  # keep the searches short
    for order in load(read(name).splitlines())["items"]:
        prog = program6(order)
        assert valid6(order, prog) and len(prog) <= len(baseline6(order))


def test_program6_center():
    order = (2, small(((2, 4), "M")), 3)
    assert program6(order) == [list("TT----"), ["-"] * 6, ["-"] * 6]
    assert valid6(order, program6(order))
