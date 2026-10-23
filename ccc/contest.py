from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from typing import Any

Cell = tuple[int, int]  # (row, col) in the ASCII board, '-' gaps are left out
Board = dict[Cell, str]
Rule = Callable[[Any], Board]  # one parsed input item (see load) -> final board

# emitter digit -> (row, col) step, clockwise starting east
DIRS = {
    "1": (0, 2),  # →
    "2": (1, 1),  # ↘
    "3": (1, -1),  # ↙
    "4": (0, -2),  # ←
    "5": (-1, -1),  # ↖
    "6": (-1, 1),  # ↗
}


def solve(data: dict[str, list[Any]], level: int | None = None) -> str:
    rule = RULES[level or max(RULES)]  # default: the latest level
    return "\n\n".join(render(rule(item)) for item in data["items"])


# --- board representation: the only code that touches raw coordinates ---


def parse(lines: list[str]) -> Board:
    return {
        (y, x): c for y, row in enumerate(lines) for x, c in enumerate(row) if c != "-"
    }


def render(b: Board) -> str:
    rows = max(y for y, _ in b) + 1
    cols = max(x for _, x in b) + 1
    return "\n".join(
        "".join(b.get((y, x), "-") for x in range(cols)) for y in range(rows)
    )


def ray(b: Board, start: Cell, digit: str) -> Iterator[Cell]:
    """cells a beam from `start` crosses, through 'O' and 'M' up to the border"""
    dy, dx = DIRS[digit]
    y, x = start[0] + dy, start[1] + dx
    while b.get((y, x)) in ("O", "M"):
        yield y, x
        y, x = y + dy, x + dx


def hexagon(r: int) -> str:
    """level 1: empty board of radius r"""
    rows: list[str] = []
    for i in range(2 * r + 1):
        d = abs(i - r)
        n = 2 * r + 1 - d
        if d == r:
            cells = ["*"] * n
        else:
            cells = ["*"] + ["O"] * (n - 2) + ["*"]
        pad = "-" * d
        rows.append(pad + "-".join(cells) + pad)
    return "\n".join(rows)


def ring(r: int) -> list[Cell]:
    """border cells clockwise from the west corner; corner d-1 is at index (d-1)*r"""
    y, x = r, 0
    cells: list[Cell] = []
    for side in "612345":  # walk the sides ↗ → ↘ ↙ ← ↖
        dy, dx = DIRS[side]
        for _ in range(r):
            cells.append((y, x))
            y, x = y + dy, x + dx
    return cells


# --- beams and per-level rules ---

Emitter = tuple[Cell, str]  # position, direction digit


def hits(b: Board, emitters: Iterable[Emitter]) -> Counter[Cell]:
    """how many beams cross each cell, all emitters fire at once"""
    return Counter(cell for start, d in emitters for cell in ray(b, start, d))


def beam_hits(b: Board) -> Counter[Cell]:
    """hits() of the emitters drawn on the board"""
    return hits(b, ((cell, c) for cell, c in b.items() if c in DIRS))


def create_or_destroy(b: Board, counts: Counter[Cell]) -> Board:
    """2 beams create matter, 3+ destroy it, 0-1 leave the cell as is"""
    for cell, n in counts.items():
        if n == 2:
            b[cell] = "M"
        elif n >= 3:
            b[cell] = "O"
    return b


def fire2(b: Board) -> Board:
    """level 2: every beam creates matter"""
    for cell in beam_hits(b):
        b[cell] = "M"
    return b


def fire3(b: Board) -> Board:
    """level 3: all emitters on the board fire once"""
    return create_or_destroy(b, beam_hits(b))


Program = tuple[int, list[list[str]]]  # radius, ticks of 6 commands (one per emitter)


def run_ticks(b: Board, r: int, ticks: list[list[str]]) -> Board:
    """emitters start off on the corners of radius r and move along the border.

    Per tick, every emitter applies its command at once (F/B: one cell clockwise /
    counter-clockwise, T: toggle on/off, -: nothing), then the active ones fire
    with the create/destroy rule. Emitters stay off the board dict: several can
    share one border cell.
    """
    border = ring(r)
    pos = [k * r for k in range(6)]  # index into border, emitter k = digit k+1
    on = [False] * 6
    for tick in ticks:
        for k, cmd in enumerate(tick):
            if cmd == "F":
                pos[k] = (pos[k] + 1) % len(border)
            elif cmd == "B":
                pos[k] = (pos[k] - 1) % len(border)
            elif cmd == "T":
                on[k] = not on[k]
        active = [(border[pos[k]], str(k + 1)) for k in range(6) if on[k]]
        create_or_destroy(b, hits(b, active))
    return b


def run4(program: Program) -> Board:
    """level 4: run the program on an empty board"""
    r, ticks = program
    return run_ticks(parse(hexagon(r).splitlines()), r, ticks)


# level -> rule; register each new level here (tests and ccc.run pick it up).
# Keep old rules as they are so old levels stay solvable and tested.
RULES: dict[int, Rule] = {2: fire2, 3: fire3, 4: run4}
