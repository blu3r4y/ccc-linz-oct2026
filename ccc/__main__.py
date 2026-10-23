from pathlib import Path
from pprint import pprint

from loguru import logger as log

from .contest import Board, parse, solve
from .utils import infer_current_level, infer_quests_for_level


def load(lines: list[str]) -> dict[str, list[Board]]:
    n = int(lines[0])
    boards: list[Board] = []
    i = 1
    for _ in range(n):
        while not lines[i].strip():
            i += 1
        _r, rows, _cols = map(int, lines[i].split())
        boards.append(parse(lines[i + 1 : i + 1 + rows]))
        i += 1 + rows
    return dict(boards=boards)


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
