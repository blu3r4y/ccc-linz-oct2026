from collections.abc import Iterator

Cell = tuple[int, int]  # (row, col) in the ASCII board, '-' gaps are left out
Board = dict[Cell, str]

# emitter digit -> (row, col) step
DIRS = {
    "1": (0, 2),
    "2": (1, 1),
    "3": (1, -1),
    "4": (0, -2),
    "5": (-1, -1),
    "6": (-1, 1),
}


def solve(data: dict[str, list[Board]]) -> str:
    return "\n\n".join(render(fire(b)) for b in data["boards"])


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
    dy, dx = DIRS[digit]
    y, x = start[0] + dy, start[1] + dx
    while b.get((y, x)) in ("O", "M"):
        yield y, x
        y, x = y + dy, x + dx


def fire(b: Board) -> Board:
    for start, c in list(b.items()):
        if c in DIRS:
            for cell in ray(b, start, c):
                b[cell] = "M"
    return b


def board(r: int) -> str:
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
