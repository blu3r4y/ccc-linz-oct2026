"""Per-item best-of merge for level 6 outputs.

Usage (repo root as cwd):  uv run python <scratchpad>/merge6.py DIR [DIR ...]

Every DIR may hold out_level-6_<n>-<name>.txt files (any subset). The current
best set lives in <scratchpad>/best6/ and is always a candidate too, so the
merge only ever improves. Each candidate program is validated with valid6;
invalid ones are skipped and reported. Writes best6/ and prints per-file totals.
"""

import sys
from pathlib import Path

from ccc.__main__ import load
from ccc.contest import valid6

BEST = Path(__file__).parent / "best6"
BEST.mkdir(exist_ok=True)


def programs(path: Path) -> list[list[list[str]]]:
    text = path.read_text().strip()
    return [[t.split() for t in p.splitlines() if t.strip()] for p in text.split("\n\n")]


dirs = [BEST] + [Path(d) for d in sys.argv[1:]]
total_before = total_after = 0
for inp in sorted(Path("data").glob("in_level-6_[1-9]*.txt")):
    name = inp.name.replace("in_", "out_", 1)
    items = load(inp.read_text().splitlines())["items"]
    best: list[list[list[str]] | None] = [None] * len(items)
    source = [""] * len(items)
    before = None
    for d in dirs:
        f = d / name
        if not f.exists():
            continue
        progs = programs(f)
        if len(progs) != len(items):
            print(f"  skip {f}: {len(progs)} programs for {len(items)} items")
            continue
        bad = 0
        for i, (item, p) in enumerate(zip(items, progs)):
            if best[i] is not None and len(p) >= len(best[i]):
                continue
            if not valid6(item, p):
                bad += 1
                continue
            best[i], source[i] = p, d.name
        if d == BEST:
            before = sum(map(len, progs))
        if bad:
            print(f"  {f}: {bad} invalid programs ignored")
    if any(b is None for b in best):
        print(f"{name}: incomplete, not written")
        continue
    after = sum(map(len, best))
    tmp = BEST / (name + ".tmp")  # atomic: an interrupted merge never truncates best6
    tmp.write_text("\n\n".join("\n".join(" ".join(t) for t in p) for p in best))
    tmp.replace(BEST / name)
    wins = {s: source.count(s) for s in set(source)}
    print(f"{name}: {before if before is not None else '-'} -> {after} lines  {wins}")
    total_before += before or 0
    total_after += after
print(f"total: {total_before or '-'} -> {total_after}")
