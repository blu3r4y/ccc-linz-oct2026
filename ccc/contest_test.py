from pathlib import Path

from .__main__ import load
from .contest import solve

DATA = Path(__file__).parent.parent / "data"


def test_level1_example():
    lines = (DATA / "in_level-1_0-example.txt").read_text().splitlines()
    expected = (DATA / "out_level-1_0-example.txt").read_text()
    assert solve(load(lines)) == expected.strip()
