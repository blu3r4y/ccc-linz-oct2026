# Level 6 merge tools

These are copies of the working tools from the session scratchpad.

- `merge6.py DIR...`: per-item best-of merge, every program checked with `valid6`, into `$BEST6`. That defaults to `best6/` next to the script; e.g. `BEST6=<scratchpad>/best6`. Run it with `PYTHONPATH=.` from the repo root.
- `peritem6.py PROGDIR OUTFILE NAME`: per-item `<i>.txt` programs → a full candidate file, filling gaps from best6.

`data/out_level-6_*.txt` in the repo holds the best set as of the last checkpoint commit.
