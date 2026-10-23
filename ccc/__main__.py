from pathlib import Path
from pprint import pprint
from typing import Any

from loguru import logger as log

from .contest import parse, solve
from .utils import infer_current_level, infer_quests_for_level


def load(lines: list[str]) -> dict[str, list[Any]]:
    """N items, separated by blank lines; the header line's shape picks the format"""
    n = int(lines[0])
    items: list[Any] = []
    i = 1
    for _ in range(n):
        while not lines[i].strip():
            i += 1
        header = lines[i].split()
        if len(header) == 3:  # L2+: "r rows cols" + board rows
            r, rows = int(header[0]), int(header[1])
            board = parse(lines[i + 1 : i + 1 + rows])
            i += 1 + rows
            if i < len(lines) and len(lines[i].split()) == 1:  # L5: + ticks
                ticks, i = read_ticks(lines, i)
                items.append((r, board, ticks))
            else:
                items.append(board)
        elif len(header) == 4:  # L6: "r rows cols count" + pattern rows
            r, rows, _, count = map(int, header)
            items.append((r, parse(lines[i + 1 : i + 1 + rows]), count))
            i += 1 + rows
        elif len(header) == 1:  # L4: "r" + ticks
            ticks, i = read_ticks(lines, i + 1)
            items.append((int(header[0]), ticks))
        else:
            raise ValueError(f"unknown item header: {lines[i]!r}")
    return dict(items=items)


def read_ticks(lines: list[str], i: int) -> tuple[list[list[str]], int]:
    """a tick count at line i, then that many ticks of 6 commands; returns next i"""
    n = int(lines[i])
    return [line.split() for line in lines[i + 1 : i + 1 + n]], i + 1 + n


if __name__ == "__main__":
    base_path = Path("data")
    level = infer_current_level(base_path)
    quests = infer_quests_for_level(base_path, level)
    # quests = ["example"]

    for quest in quests:
        input_file = base_path / f"level{level}_{quest}.in"
        output_file = input_file.with_suffix(".out")

        if not input_file.exists():
            log.warning(f"file not found, skip: {input_file}")
            continue

        with open(input_file, "r") as fi:
            data = load(fi.read().splitlines())
            pprint(data)

            print("=== Input {}".format(quest))
            print("======================")

            result = solve(data)
            pprint(result)

            with open(output_file, "w+") as fo:
                fo.write(result)
