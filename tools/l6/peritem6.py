"""Turn a folder of per-item programs (<index>.txt) into a full candidate file.

Usage (repo root as cwd): uv run python <scratchpad>/peritem6.py PROGDIR OUTFILE NAME
NAME is the input stem, e.g. 2-medium. Items without a file (or an empty one)
take the current best6 program, so the result is complete; merge6 validates it.
"""

import sys
from pathlib import Path

best = Path(__file__).parent / "best6"
progdir, outfile, name = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
base = (best / f"out_level-6_{name}.txt").read_text().strip().split("\n\n")
out = []
for i, prog in enumerate(base):
    f = progdir / f"{i}.txt"
    text = f.read_text().strip() if f.exists() else ""
    out.append(text if text else prog)
outfile.parent.mkdir(parents=True, exist_ok=True)
outfile.write_text("\n\n".join(out))
print(f"{name}: {sum(1 for i in range(len(base)) if (progdir / f'{i}.txt').exists())} per-item files")
