from collections import Counter
from collections.abc import Callable, Iterator

Cell = tuple[int, int]  # (row, col) in the ASCII board, '-' gaps are left out
Board = dict[Cell, str]
Rule = Callable[[Board], Board]

# emitter digit -> (row, col) step, clockwise starting east
DIRS = {
    "1": (0, 2),  # →
    "2": (1, 1),  # ↘
    "3": (1, -1),  # ↙
    "4": (0, -2),  # ←
    "5": (-1, -1),  # ↖
    "6": (-1, 1),  # ↗
}


def solve(data: dict[str, list[Board]], rule: Rule | None = None) -> str:
    rule = rule or fire3  # the current level
    return "\n\n".join(render(rule(b)) for b in data["boards"])


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


# --- beams and per-level rules ---


def beam_hits(b: Board) -> Counter[Cell]:
    """how many beams cross each cell, all emitters fire at once"""
    return Counter(
        cell for start, c in b.items() if c in DIRS for cell in ray(b, start, c)
    )


def fire2(b: Board) -> Board:
    """level 2: every beam creates matter"""
    for cell in beam_hits(b):
        b[cell] = "M"
    return b


def fire3(b: Board) -> Board:
    """level 3: 2 beams create matter, 3+ destroy it, 0-1 leave the cell as is"""
    for cell, n in beam_hits(b).items():
        if n == 2:
            b[cell] = "M"
        elif n >= 3:
            b[cell] = "O"
    return b
