"""Write the outputs for one level: `uv run python -m ccc.run [level] [filter]`.

Level defaults to the latest one; `filter` keeps only inputs whose name contains it
(e.g. `small`), plus the example, which is always checked. Files run in name order, i.e. example first and largest last, and
each output is written as soon as it is done. The example is checked, not written,
and a mismatch stops the run. Wrap in `timeout` when trying a new solver.
"""

import sys
import time
from pathlib import Path

from .__main__ import load
from .contest import RULES, solve

DATA = Path(__file__).parent.parent / "data"

level = int(sys.argv[1]) if len(sys.argv) > 1 else max(RULES)
only = sys.argv[2] if len(sys.argv) > 2 else ""
for f in sorted(DATA.glob(f"in_level-{level}_*.txt")):
    if only not in f.name and "example" not in f.name:
        continue
    out = f.with_name(f.name.replace("in_", "out_", 1))
    start = time.perf_counter()
    result = solve(load(f.read_text().splitlines()), level)
    took = f"{time.perf_counter() - start:.2f}s"
    if "example" in f.name:
        ok = out.exists() and result == out.read_text().strip()
        print(f"{f.name}: example {'OK' if ok else 'MISMATCH'} ({took})", flush=True)
        if not ok:
            sys.exit(1)
    else:
        out.write_text(result)
        print(f"{f.name}: wrote {out.name} ({took})", flush=True)
