import os
import time
from collections import Counter, deque
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from heapq import nsmallest
from itertools import product
from typing import Any

Cell = tuple[int, int]  # (row, col) in the ASCII board, '-' gaps are left out
Board = dict[Cell, str]
# one parsed input item (see load) -> final board, a plain answer (e.g. a count),
# or a program (ticks of 6 commands)
Rule = Callable[[Any], Board | int | list[list[str]]]

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
    level = level or max(RULES)  # default: the latest level
    rule = RULES[level]
    if level in PARALLEL:  # independent, slow items: spread over processes
        with ProcessPoolExecutor(min(16, os.cpu_count() or 1)) as pool:
            results = list(pool.map(rule, data["items"]))
    else:
        results = [rule(item) for item in data["items"]]
    if all(isinstance(res, dict) for res in results):  # boards: blank line between
        return "\n\n".join(render(b) for b in results)
    if all(isinstance(res, list) for res in results):  # programs: blank line between
        return "\n\n".join("\n".join(" ".join(t) for t in p) for p in results)
    return "\n".join(map(str, results))


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


def neighbours(cell: Cell) -> list[Cell]:
    """the 6 adjacent cells (may lie off the board)"""
    return [(cell[0] + dy, cell[1] + dx) for dy, dx in DIRS.values()]


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


def iter_ticks(b: Board, r: int, ticks: list[list[str]]) -> Iterator[Board]:
    """emitters start off on the corners of radius r and move along the border.

    Per tick, every emitter applies its command at once (F/B: one cell clockwise /
    counter-clockwise, T: toggle on/off, -: nothing), then the active ones fire
    with the create/destroy rule. Emitters stay off the board dict: several can
    share one border cell. Yields `b` (changed in place) after every tick, so the
    caller may inspect or edit it between ticks.
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
        yield b


def run_ticks(b: Board, r: int, ticks: list[list[str]]) -> Board:
    """run all ticks, return the final board"""
    for b in iter_ticks(b, r, ticks):
        pass
    return b


def run4(program: Program) -> Board:
    """level 4: run the program on an empty board"""
    r, ticks = program
    return run_ticks(parse(hexagon(r).splitlines()), r, ticks)


Task = tuple[int, Board, list[list[str]]]  # radius, pattern board, ticks


def run5(task: Task) -> int:
    """level 5: count how often the pattern gets built and submitted.

    After each tick, the pattern is complete when all its 'M' cells are 'M' and no
    other 'M' touches them. Then it is submitted: its cells go back to 'O'.
    """
    r, pattern, ticks = task
    want = {cell for cell, c in pattern.items() if c == "M"}
    halo = {n for cell in want for n in neighbours(cell)} - want
    count = 0
    for b in iter_ticks(parse(hexagon(r).splitlines()), r, ticks):
        if all(b[c] == "M" for c in want) and all(b.get(c) != "M" for c in halo):
            for c in want:
                b[c] = "O"
            count += 1
    return count


# --- level 6: write a short program that submits a pattern `count` times ---

Order = tuple[int, Board, int]  # radius, pattern board, required count
CMDS = "-TFB"  # '-' first: ties keep the program calm
PAIRS = [(0, 1), (0, 2), (1, 2), (1, 0), (2, 0), (2, 1)]  # driver emitters, 3 axes


@lru_cache
def chords(r: int) -> tuple[dict[Cell, int], dict[tuple[int, int], int]]:
    """interior cell -> bit, and (emitter k, offset o) -> bitmask of its beam.

    Emitter k (0-based, digit k+1) starts on corner k*r of the ring. Its useful
    positions are the 2r-1 border cells around that corner, ring index k*r + o
    with o in -(r-1)..r-1: together their beams cover every interior cell once
    (one chord per row of its axis). At o = ±r it would sit on the next corner
    and shine along the border, so we never go there.
    """
    empty = parse(hexagon(r).splitlines())
    border = ring(r)
    bit = {c: 1 << i for i, c in enumerate(c for c, v in empty.items() if v == "O")}
    masks = {
        (k, o): sum(
            bit[c] for c in ray(empty, border[(k * r + o) % (6 * r)], str(k + 1))
        )
        for k in range(6)
        for o in range(-(r - 1), r)
    }
    return bit, masks


def count_hits(beams: Iterable[int]) -> tuple[int, int]:
    """bitwise adder over beam masks: (cells hit exactly 2x, cells hit 3+x).

    `one`/`two` hold the low bits of a per-cell counter that saturates into `many`.
    """
    one = two = many = 0
    for m in beams:
        many |= two & m
        carry = one & m
        one ^= m
        two = (two ^ carry) & ~many
    return two & ~many, many


def zone6(order: Order) -> tuple[int, int]:
    """bitmasks of the pattern's 'M' cells and of its halo (interior cells next to
    them): the only cells that decide a submission"""
    r, pattern, _ = order
    bit, _ = chords(r)
    want = sum(bit[c] for c, v in pattern.items() if v == "M")
    halo = sum(  # a set first: cells next to several 'M' cells count once
        bit[n]
        for n in {n for c, v in pattern.items() if v == "M" for n in neighbours(c)}
        if pattern.get(n) == "O"
    )
    return want, halo


def move(cmd: str, o: int, on: bool, r: int) -> tuple[int, bool] | None:
    """an emitter's (offset, on) after `cmd`, or None if it leaves its 2r-1 cells"""
    if cmd == "F":
        o += 1
    elif cmd == "B":
        o -= 1
    elif cmd == "T":
        on = not on
    return (o, on) if abs(o) < r else None


def drive(
    r: int, a: int, b: int, start: tuple[int, int, bool, bool], todo: int, halo: int
) -> tuple[list[tuple[str, str]], int]:
    """BFS for the driver pair a, b: the shortest command path to a state where
    both are on and their beams cross on a `todo` cell. Returns (path, crossing).
    No state on the way may cross on a halo cell (that would build an 'M' there).
    """
    _, ch = chords(r)
    prev: dict[tuple[int, int, bool, bool], Any] = {start: None}
    queue = deque([start])
    while queue:
        s = queue.popleft()
        oa, ob, ona, onb = s
        if ona and onb and ch[a, oa] & ch[b, ob] & todo:
            target, path = ch[a, oa] & ch[b, ob], []
            while prev[s] is not None:
                s, cmds = prev[s]
                path.append(cmds)
            return path[::-1], target
        for x, y in product(CMDS, CMDS):
            na, nb = move(x, oa, ona, r), move(y, ob, onb, r)
            if na is None or nb is None:
                continue
            t = (na[0], nb[0], na[1], nb[1])
            if t in prev or (t[2] and t[3] and ch[a, t[0]] & ch[b, t[1]] & halo):
                continue
            prev[t] = (s, (x, y))
            queue.append(t)
    raise ValueError("no reachable pattern cell")


def build(order: Order, a: int, b: int) -> list[list[str]]:
    """greedy program: emitters a, b drive (BFS, one pattern cell at a time), the
    other 4 helpers pick the best of their <= 4^4 command combinations each tick.

    A combination is rejected if a halo cell gets exactly 2 hits (stray 'M' next
    to the pattern) or a built pattern cell gets 3+ (destroyed). Score:
    1000 * newly built pattern cells, plus each helper's potential: the most
    unbuilt pattern cells on a chord it could reach, minus 0.5 per step to get
    there, plus 0.1 for being on. Driver-only (helpers off) is always allowed, so
    every pattern cell eventually gets built.
    """
    r, _, count = order
    _, ch = chords(r)
    want, halo = zone6(order)
    helpers = [k for k in range(6) if k not in (a, b)]
    span = range(-(r - 1), r)
    o, on = [0] * 6, [False] * 6
    matter, done, ticks = 0, 0, []
    path: list[tuple[str, str]] = []
    target = 0
    while done < count:
        todo = want & ~matter
        if not target & todo:  # driver target built (or none yet): plan anew
            path, target = drive(r, a, b, (o[a], o[b], on[a], on[b]), todo, halo)
        x, y = path.pop(0) if path else ("-", "-")
        o[a], on[a] = move(x, o[a], on[a], r)  # type: ignore[misc]
        o[b], on[b] = move(y, o[b], on[b], r)  # type: ignore[misc]
        driver = [ch[k, o[k]] for k in (a, b) if on[k]]

        options = []
        for k in helpers:
            todo_on = {o2: (ch[k, o2] & todo).bit_count() for o2 in span}
            opts = []
            for cmd in CMDS:
                if (m := move(cmd, o[k], on[k], r)) is None:
                    continue
                nk, nonk = m
                pot = max(n - 0.5 * abs(nk - o2) for o2, n in todo_on.items())
                opts.append((cmd, m, ch[k, nk] if nonk else 0, pot + 0.1 * nonk))
            options.append(opts)

        built = want & matter
        best, best_score = None, -1.0
        for combo in product(*options):
            two, many = count_hits(driver + [beam for _, _, beam, _ in combo])
            if two & halo or many & built:
                continue
            after = (matter | two) & ~many
            score = 1000 * (after & todo).bit_count() + sum(p for *_, p in combo)
            if score > best_score:
                best, best_score, best_after = combo, score, after
        assert best is not None  # helpers off is always allowed

        cmds = ["-"] * 6
        cmds[a], cmds[b] = x, y
        for k, (cmd, (nk, nonk), _, _) in zip(helpers, best):
            cmds[k], o[k], on[k] = cmd, nk, nonk
        ticks.append(cmds)
        matter = best_after
        if want & ~matter == 0:  # complete (halo is never 'M'): submit
            matter &= ~want
            done += 1
            target = 0  # more targets now: re-plan
    return ticks


def baseline6(order: Order) -> list[list[str]]:
    """the shortest greedy `build` over all driver pairs: always valid, the fallback"""
    return min((build(order, a, b) for a, b in PAIRS), key=len)


# --- level 6: repeat cycles ---
#
# A submission turns the pattern back into 'O' and needs a halo without 'M', so
# after every submission the cells that matter are all 'O' again: every repetition
# is the same problem. So build the pattern with a cycle of m fire ticks and repeat
# it. A config says where each emitter fires from: an offset on its arc (see
# `chords`), or None (off). For a cycle with a uniform `gap` between fires, the
# program has setup + 1 + (count * m - 1) * gap lines, so m (and gap 1) matter most.

Config = tuple[int | None, ...]  # per emitter: offset (on), or None (off)
Frames = dict[int, list[tuple[int, Config, bool]]]
BUDGET = 3.0  # seconds per item and search step (enumerations, cover searches)


def submissions6(order: Order, ticks: list[list[str]]) -> list[int]:
    """`run5` on bitmasks: the ticks (1-based) at which the pattern is submitted.
    Only for programs that keep every emitter on its arc (else: no submissions)."""
    r = order[0]
    _, ch = chords(r)
    want, halo = zone6(order)
    o, on = [0] * 6, [False] * 6
    matter, subs = 0, []
    for t, tick in enumerate(ticks, 1):
        for k, cmd in enumerate(tick):
            if (m := move(cmd, o[k], on[k], r)) is None:
                return []
            o[k], on[k] = m
        two, many = count_hits(ch[k, o[k]] for k in range(6) if on[k])
        matter = (matter | two) & ~many
        if matter & want == want and not matter & halo:
            matter &= ~want
            subs.append(t)
    return subs


@lru_cache(maxsize=4)
def frames6(r: int, want: int, halo: int) -> Frames:
    """every clean partial frame: a config whose exactly-2-hit cells are pattern
    cells only (some, not necessarily all). Keyed by the pattern cells it builds:
    mask -> [(setup ticks, config, nondestructive)], cheapest first. Setup = the
    farthest walk from home + 1 toggle. Nondestructive: no 3+ hits on the pattern,
    so it never undoes cells built by an earlier frame of the cycle.

    Brute force over the lines that touch the pattern or its halo (others act like
    off), with a bitwise adder per emitter; stops after BUDGET seconds.
    """
    _, ch = chords(r)
    zone = want | halo
    span = range(-(r - 1), r)
    opts = [
        [(None, 0)] + [(o, ch[k, o]) for o in span if ch[k, o] & zone] for k in range(6)
    ]
    found: Frames = {}
    cfg: list[int | None] = [None] * 6
    deadline = time.perf_counter() + BUDGET

    def rec(k: int, one: int, two: int, many: int, setup: int) -> None:
        if k == 6:
            if two & want and not two & halo:
                found.setdefault(two, []).append((setup, tuple(cfg), not many & want))
            return
        if k == 3 and time.perf_counter() > deadline:
            raise TimeoutError
        for o, m in opts[k]:
            cfg[k] = o
            if o is None:
                rec(k + 1, one, two, many, setup)
            else:
                many2 = many | (two & m)
                rec(
                    k + 1,
                    one ^ m,
                    (two ^ (one & m)) & ~many2,
                    many2,
                    max(setup, abs(o) + 1),
                )
        cfg[k] = None

    try:
        rec(0, 0, 0, 0, 0)
    except TimeoutError:
        pass
    for configs in found.values():
        configs.sort(key=lambda c: c[0])
    return found


def cycle_gap(cycle: list[Config], stay: bool = True) -> int:
    """the smallest uniform number of ticks between fires that lets every emitter
    get from one use to its next (cyclically). Between uses on consecutive fires an
    emitter stays on and moves (|delta| ticks; with `stay` off it takes the slow,
    dark way below); otherwise it toggles off, moves, toggles on: |delta| + 2 ticks."""
    m, gap = len(cycle), 1
    for k in range(6):
        uses = [i for i in range(m) if cycle[i][k] is not None]
        for a, b in zip(uses, uses[1:] + uses[:1]):
            apart = (b - a) % m or m
            d = abs(cycle[b][k] - cycle[a][k])  # type: ignore[operator]
            if apart == 1 and (stay or d == 0):
                gap = max(gap, d)
            else:
                gap = max(gap, -(-(d + 2) // apart))
    return gap


def cycle_setup(cycle: list[Config], gap: int) -> int:
    """idle-free lead-in: ticks before the first fire, so every emitter can walk
    from home (offset 0) to its first position and toggle on in time"""
    return max(
        [0]
        + [
            abs(o) - i * gap
            for k in range(6)
            for i, o in enumerate(c[k] for c in cycle)
            if o is not None and all(c[k] is None for c in cycle[:i])
        ]
    )


def cycle_lines(cycle: list[Config], count: int) -> int:
    """predicted program length: setup + 1 + (count * m - 1) * gap"""
    gap = cycle_gap(cycle)
    return cycle_setup(cycle, gap) + 1 + (count * len(cycle) - 1) * gap


def cycle_program(
    cycle: list[Config], fires: int, stay: bool = True
) -> list[list[str]]:
    """the ticks that fire the cycle's configs `fires` times in a row, one every
    `cycle_gap` ticks. Off emitters walk as early as possible and toggle on at the
    fire; on emitters that are needed at the next fire stay on and move just before
    it (they also fire on the ticks in between: `submissions6` checks the result)."""
    m, gap = len(cycle), cycle_gap(cycle, stay)
    setup = cycle_setup(cycle, gap)
    ticks = [["-"] * 6 for _ in range(setup + 1 + (fires - 1) * gap)]
    for k in range(6):
        pos, last = 0, None  # last use: (fire number, tick index)
        for j in range(fires):
            if (o := cycle[j % m][k]) is None:
                continue
            t = setup + j * gap  # tick index of fire j
            step, d = "F" if o > pos else "B", abs(o - pos)
            if last and last[0] == j - 1 and (stay or d == 0):
                for i in range(d):  # stay on, move right before the fire
                    ticks[t - i][k] = step
            else:
                start = 0
                if last:  # off right after the last use
                    ticks[last[1] + 1][k] = "T"
                    start = last[1] + 2
                for i in range(d):
                    ticks[start + i][k] = step
                ticks[t][k] = "T"
            pos, last = o, (j, t)
        if last and last[0] < fires - 1:  # stays dark after its last use
            ticks[last[1] + 1][k] = "T"
    return ticks


def try_cycles(
    order: Order, cycles: Iterable[list[Config]], tries: int = 30
) -> list[list[str]] | None:
    """the shortest program among the most promising cycles (by `cycle_lines`),
    checked by simulation and cut right after the count-th submission"""
    count = order[2]
    best = None
    for cycle in nsmallest(tries, cycles, key=lambda c: cycle_lines(c, count)):
        for stay in (True, False):
            for rot in range(len(cycle)):
                c = cycle[rot:] + cycle[:rot]
                prog = cycle_program(c, (count + 1) * len(c), stay)
                subs = submissions6(order, prog)
                if len(subs) >= count and (best is None or subs[count - 1] < len(best)):
                    best = prog[: subs[count - 1]]
    return best


def frame6(order: Order) -> list[list[str]] | None:
    """one-tick cycle: a single config whose 2-hit cells are exactly the pattern.
    Walk there, toggle on, and every later tick re-fires it: count - 1 '-' lines
    after the setup. Cost: setup + count lines."""
    r, _, count = order
    want, halo = zone6(order)
    frames = frames6(r, want, halo)
    return try_cycles(order, [[c] for _, c, _ in frames.get(want, [])[:30]])


def pick(configs: list[tuple[int, Config, bool]], n: int, nd: bool) -> list[Config]:
    """the n cheapest configs, nondestructive ones only if `nd`"""
    return [c for _, c, ok in configs if ok or not nd][:n]


def pair6(order: Order) -> list[list[str]] | None:
    """two-tick cycle A, B: A builds part of the pattern, B the rest without
    destroying A's cells (A fires first after a reset, so it may hit pattern cells
    3 times). Mostly a gap of 1: emitters on in both move at most 1 cell, the
    others toggle. Cost: about setup + 2 * count lines."""
    r, _, _ = order
    want, halo = zone6(order)
    frames = frames6(r, want, halo)
    deadline = time.perf_counter() + BUDGET

    def cycles() -> Iterator[list[Config]]:
        for y, ys in frames.items():
            if time.perf_counter() > deadline:
                return
            if y == want or not any(nd for *_, nd in ys):
                continue
            for x in supersets(frames, want & ~y, y):
                if x != want:
                    for a, b in product(pick(frames[x], 6, False), pick(ys, 6, True)):
                        yield [a, b]

    return try_cycles(order, cycles())


def supersets(frames: Frames, need: int, free: int) -> Iterator[int]:
    """the frame masks that are `need` plus some bits of `free`"""
    if 1 << free.bit_count() < len(frames):  # few candidates: look them up
        s = free
        while True:
            if need | s in frames:
                yield need | s
            if s == 0:
                return
            s = (s - 1) & free
    else:
        yield from (x for x in frames if x & need == need and not x & ~(need | free))


def triple6(order: Order, top: int = 60) -> list[list[str]] | None:
    """three-tick cycle A, B, C for patterns no pair covers: B and C are
    nondestructive frames among the `top` biggest, A covers the rest. Cost: about
    setup + 3 * count lines."""
    r, _, _ = order
    want, halo = zone6(order)
    frames = frames6(r, want, halo)
    deadline = time.perf_counter() + BUDGET
    nds = sorted(
        (y for y, ys in frames.items() if y != want and any(nd for *_, nd in ys)),
        key=lambda y: -y.bit_count(),
    )[:top]

    def cycles() -> Iterator[list[Config]]:
        for i, y in enumerate(nds):
            for z in nds[i + 1 :]:
                need = want & ~(y | z)
                if not need or time.perf_counter() > deadline:
                    continue
                for x in supersets(frames, need, y | z):
                    if x | y != want and x | z != want:
                        for a, b, c in product(
                            pick(frames[x], 3, False),
                            pick(frames[y], 3, True),
                            pick(frames[z], 3, True),
                        ):
                            yield [a, b, c]
                            yield [a, c, b]

    return try_cycles(order, cycles())


def parkings(r: int, want: int, halo: int) -> list[tuple[int, Config]]:
    """every way to park emitters (an offset each, or None) so that every pattern
    cell lies on at least 2 parked lines, as (setup, config), cheapest first"""
    _, ch = chords(r)
    span = range(-(r - 1), r)
    opts = [[None] + [o for o in span if ch[k, o] & (want | halo)] for k in range(6)]
    found: list[tuple[int, Config]] = []
    cfg: list[int | None] = [None] * 6
    deadline = time.perf_counter() + BUDGET

    def rec(k: int, once: int, twice: int, setup: int) -> None:
        left = 6 - k  # each emitter adds at most 1 line through a cell
        if left == 0 and want & ~twice or left == 1 and want & ~once:
            return
        if k == 6:
            found.append((setup, tuple(cfg)))
            return
        if k == 3 and time.perf_counter() > deadline:
            raise TimeoutError
        for o in opts[k]:
            cfg[k] = o
            if o is None:
                rec(k + 1, once, twice, setup)
            else:
                m = ch[k, o]
                rec(k + 1, once | m, twice | once & m, max(setup, abs(o) + 1))
        cfg[k] = None

    try:
        rec(0, 0, 0, 0)
    except TimeoutError:
        pass
    return sorted(found, key=lambda f: f[0])


def toggle_cycle(
    r: int, want: int, halo: int, parked: Config, depth: int, deadline: float
) -> list[Config] | None:
    """BFS over the pattern + halo state: the shortest sequence of on-subsets of
    the parked emitters that builds exactly the pattern (and nothing in its
    halo) from scratch, as a list of configs; None if longer than `depth` (or
    out of time)"""
    _, ch = chords(r)
    zone = want | halo
    used = [k for k in range(6) if parked[k] is not None]
    effects = {}
    for subset in range(1, 1 << len(used)):
        on = [k for i, k in enumerate(used) if subset >> i & 1]
        two, many = count_hits(ch[k, parked[k]] for k in on)
        effects.setdefault((two & zone, many & zone), on)
    prev: dict[int, Any] = {0: None}
    frontier = [0]
    for _ in range(depth):
        nxt = []
        if time.perf_counter() > deadline:
            return None
        for s in frontier:
            for (two, many), on in effects.items():
                t = (s | two) & ~many
                if t in prev:
                    continue
                prev[t] = (s, on)
                if t == want:
                    path = []
                    while prev[t] is not None:
                        t, on = prev[t]
                        path.append(
                            tuple(parked[k] if k in on else None for k in range(6))
                        )
                    return path[::-1]
                nxt.append(t)
        frontier = nxt
    return None


def toggle6(order: Order, depth: int = 6) -> list[list[str]] | None:
    """parked toggle cycle: emitters walk to fixed lines once, then each tick only
    switches which of them are on (one T per emitter per tick, so a gap of 1).
    BFS finds the fewest ticks m per parking; parkings go cheapest first, until
    the budget runs out. Cost: setup + m * count lines."""
    r, _, count = order
    want, halo = zone6(order)
    deadline = time.perf_counter() + BUDGET
    found = []
    best = depth
    for _, parked in parkings(r, want, halo):
        if time.perf_counter() > deadline:
            break
        cycle = toggle_cycle(r, want, halo, parked, best, deadline)
        if cycle is not None:
            found.append(cycle)
            best = len(cycle)
    return try_cycles(order, found[-30:])


STRATEGIES = [frame6, pair6, triple6, toggle6]


def program6(order: Order) -> list[list[str]]:
    """level 6: the shortest valid program of a portfolio of strategies (the
    greedy baseline always among them)"""
    candidates = [baseline6(order)]
    for strategy in STRATEGIES:
        if len(candidates[0]) <= order[2] + 1:  # no cycle can beat it
            break
        if (prog := strategy(order)) is not None:
            candidates.append(prog)
    return min((p for p in candidates if valid6(order, p)), key=len)


def valid6(order: Order, program: list[list[str]]) -> bool:
    """does the program submit the pattern exactly `count` times?"""
    r, pattern, count = order
    return run5((r, pattern, program)) == count


# level -> rule; register each new level here (tests and ccc.run pick it up).
# Keep old rules as they are so old levels stay solvable and tested.
RULES: dict[int, Rule] = {2: fire2, 3: fire3, 4: run4, 5: run5, 6: program6}
# levels with many valid answers: level -> validator(item, answer) used instead of
# diffing against the expected output
CHECKS: dict[int, Callable[[Any, Any], bool]] = {6: valid6}
PARALLEL = {6}  # slow levels whose items solve() spreads over processes
