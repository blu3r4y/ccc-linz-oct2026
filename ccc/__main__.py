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
            rows = int(header[1])
            items.append(parse(lines[i + 1 : i + 1 + rows]))
            i += 1 + rows
        elif len(header) == 1:  # L4: "r", tick count, ticks of 6 commands
            r, n_ticks = int(header[0]), int(lines[i + 1])
            ticks = [line.split() for line in lines[i + 2 : i + 2 + n_ticks]]
            items.append((r, ticks))
            i += 2 + n_ticks
        else:
            raise ValueError(f"unknown item header: {lines[i]!r}")
    return dict(items=items)


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
