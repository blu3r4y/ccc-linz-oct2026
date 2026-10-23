from pathlib import Path

import pytest

from .__main__ import load
from .contest import DIRS, RULES, fire3, hexagon, parse, ray, render, ring, run4, solve

DATA = Path(__file__).parent.parent / "data"

BOARD_LEVELS = (2, 3)  # levels whose input items are boards
BOARD_INPUTS = sorted(
    p.name for lvl in BOARD_LEVELS for p in DATA.glob(f"in_level-{lvl}_*.txt")
)
OUTPUTS = sorted(  # every output that exists, uploaded and confirmed (or the example)
    (lvl, p.name.replace("out_", "in_", 1))
    for lvl in RULES
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
