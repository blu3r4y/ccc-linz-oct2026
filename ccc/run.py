"""Write the outputs for one level: `uv run python -m ccc.run [level]` (default: latest).

Checks the example first and skips writing if it doesn't match.
"""

import sys
from pathlib import Path

from .__main__ import load
from .contest import RULES, solve

DATA = Path(__file__).parent.parent / "data"

level = int(sys.argv[1]) if len(sys.argv) > 1 else max(RULES)
for f in sorted(DATA.glob(f"in_level-{level}_*.txt")):
    out = f.with_name(f.name.replace("in_", "out_", 1))
    result = solve(load(f.read_text().splitlines()), level)
    if "example" in f.name:
        ok = out.exists() and result == out.read_text().strip()
        print(f"{f.name}: example {'OK' if ok else 'MISMATCH'}")
        if not ok:
            sys.exit(1)
    else:
        out.write_text(result)
        print(f"{f.name}: wrote {out.name}")
