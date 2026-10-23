"""Write the outputs for one level: `uv run python -m ccc.run [level] [filter]`.

Level defaults to the latest one; `filter` keeps only inputs whose name contains it
(e.g. `small`), plus the example, which is always checked. Files run in name order,
i.e. example first and largest last, and each output is written as soon as it is
done. The example is checked, not written, and a failed check stops the run. Levels
in `CHECKS` (many valid answers) are validated per item instead of diffed against
the example output. Wrap in `timeout` when trying a new solver.
"""

import sys
import time
from pathlib import Path

from .__main__ import load
from .contest import CHECKS, RULES, solve

DATA = Path(__file__).parent.parent / "data"


def check(level: int, items: list, result: str) -> tuple[bool, str]:
    """validate each program of a CHECKS level; returns (ok, summary)"""
    programs = [[t.split() for t in p.splitlines()] for p in result.split("\n\n")]
    if len(programs) != len(items):
        return False, f"{len(programs)} programs for {len(items)} items"
    bad = [
        i for i, (it, p) in enumerate(zip(items, programs)) if not CHECKS[level](it, p)
    ]
    lines = sum(map(len, programs))
    return not bad, f"{'valid' if not bad else f'INVALID items {bad}'}, {lines} lines"


def main() -> None:
    level = int(sys.argv[1]) if len(sys.argv) > 1 else max(RULES)
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    for f in sorted(DATA.glob(f"in_level-{level}_*.txt")):
        if only not in f.name and "example" not in f.name:
            continue
        out = f.with_name(f.name.replace("in_", "out_", 1))
        start = time.perf_counter()
        data = load(f.read_text().splitlines())
        result = solve(data, level)
        took = f"{time.perf_counter() - start:.2f}s"
        if level in CHECKS:
            ok, summary = check(level, data["items"], result)
            if "example" in f.name and out.exists():
                ref = sum(1 for line in out.read_text().splitlines() if line.strip())
                summary += f" (reference: {ref} lines)"
            elif ok and "example" not in f.name:
                out.write_text(result)
                summary += f", wrote {out.name}"
            print(f"{f.name}: {summary} ({took})", flush=True)
            if not ok:
                sys.exit(1)
        elif "example" in f.name:
            ok = out.exists() and result == out.read_text().strip()
            print(
                f"{f.name}: example {'OK' if ok else 'MISMATCH'} ({took})", flush=True
            )
            if not ok:
                sys.exit(1)
        else:
            out.write_text(result)
            print(f"{f.name}: wrote {out.name} ({took})", flush=True)


if __name__ == "__main__":  # guard: solve() spawns worker processes on Windows
    main()
