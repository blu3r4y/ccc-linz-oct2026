from pathlib import Path

import pytest

from .__main__ import load
from .contest import DIRS, board, parse, ray, render, solve

DATA = Path(__file__).parent.parent / "data"
LEVEL2 = sorted(p.name for p in DATA.glob("in_level-2_*.txt"))


def read(name: str) -> str:
    return (DATA / name).read_text()


def blocks(name: str) -> list[list[str]]:
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
    """board(2) with (cell, char) overrides"""
    return parse(board(2).splitlines()) | dict(cells)


def test_level1_example():
    radii = [int(x) for x in read("in_level-1_0-example.txt").split()[1:]]
    expected = read("out_level-1_0-example.txt").strip()
    assert "\n\n".join(board(r) for r in radii) == expected


def test_level2_example():
    data = load(read("in_level-2_0-example.txt").splitlines())
    assert solve(data) == read("out_level-2_0-example.txt").strip()


@pytest.mark.parametrize("name", LEVEL2)
def test_parse_render_roundtrip(name: str):
    for rows in blocks(name):
        assert render(parse(rows)) == "\n".join(rows)


@pytest.mark.parametrize("name", LEVEL2)
def test_load_level2(name: str):
    boards = load(read(name).splitlines())["boards"]
    assert len(boards) == int(read(name).split()[0]) == len(blocks(name))
    for b in boards:
        assert sum(c in DIRS for c in b.values()) == 1


# board(2):  --*-*-*--
#            -*-O-O-*-
#            *-O-O-O-*
#            -*-O-O-*-
#            --*-*-*--
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
