# Level 6 merge and remote tools

These are copies of the working tools from the session scratchpad. See `SESSION.md`.

- `merge6.py DIR...`: per-item best-of merge, every program checked with `valid6`, into `$BEST6`. That defaults to `best6/` next to the script; e.g. `BEST6=<scratchpad>/best6`. Run it with `PYTHONPATH=.` from the repo root.
- `peritem6.py PROGDIR OUTFILE NAME`: per-item `<i>.txt` programs → a full candidate file, filling gaps from best6.
- `harvest6.sh`: pull every `~/scratch/l6_*/out/out_level-6_[2-4]*.txt` from `ccc1` and `ccc2`, merge, and push best6 back to `~/scratch/best6/` on both boxes.
- `remote.sh`: `push` / `run` / `pull6` / `scratch` / `ps` against `ccc1`/`ccc2` (env `HOST`, `DIR`). It never ships `.venv` or `*.pem`.

`data/out_level-6_*.txt` in the repo holds the best set as of the last checkpoint commit.
