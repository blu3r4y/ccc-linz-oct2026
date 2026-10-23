# CCC Linz Oct 2026

Python solutions for the Classic Cloudflight Coding Contest (codingcontest.org). Time-boxed contest: speed over polish.

## Contest format

- Levels 1..N unlock one after another. Each level has a spec PDF, an example input with its expected output, and the real inputs, which get uploaded for scoring.
- The user drops everything into `data/`. **This contest's naming** (unlike the `levelN_M.in` of past contests): `data/level-N.pdf`, `data/in_level-N_M-<name>.txt` (`0-example`, `1-small`, `2-large`, ...), and `data/out_level-N_0-example.txt`. Write outputs next to the inputs as `out_level-N_M-<name>.txt`. Read the PDF for the spec.
- Later levels usually extend earlier ones, so evolve the code in place rather than starting over.
- The contest also asks for the source code as a zip: `git archive --format zip -o code.zip HEAD`.

## Code layout

- `ccc/__main__.py`: `load(lines) -> dict` parses an input file into `{"boards": [Board, ...]}`: a count line, then per board an `r rows cols` header and its rows, with blank lines between boards. The user wants its main loop **left as is**. That loop still expects `levelN_M.in` (and so does `ccc/utils.py`), so `python -m ccc` finds nothing for this contest's files. Generate the outputs with the one-off command below instead.
- `ccc/contest.py`: `solve(data) -> str` is the solution. Boards are joined with `"\n\n"`, with no trailing newline.
  - `Board = dict[(row, col), char]`, keyed by ASCII position with the `-` gaps left out ("doubled-width" coordinates; chosen over axial, numpy, or the raw grid).
  - `parse` / `render` convert to and from the ASCII rows. `ray(board, start, digit)` yields the cells a beam crosses until the border.
  - `DIRS`: emitter digit -> step, `1=(0,2)` →, `2=(1,1)` ↘, `3=(1,-1)` ↙, `4=(0,-2)` ←, `5=(-1,-1)` ↖, `6=(-1,1)` ↗. Clockwise, so turning is index arithmetic mod 6.
  - Only `parse`, `render`, `DIRS` and `ray` touch raw coordinates. Everything else treats cells as opaque keys (`cell in board`, a `Counter`), so a switch to axial coordinates only changes those four.
- `ccc/utils.py`: infers the level and quests from `levelN_M.in` filenames (doesn't match this contest's naming).
- Tests: `ccc/contest_test.py` checks `solve(load(example input))` against `out_level-N_0-example.txt`. Add one test per level.
- `ccc/scratchpad.ipynb`: notebook for exploring.

## Levels so far

- L1: draw a hexagon board of radius r.
- L2: one emitter, its beam turns `O` into `M` until the border.
- L3 (in progress): multiple emitters. A cell hit by 2 beams becomes `M`, 3+ hits destroy it, 0-1 hits leave it unchanged. The output may keep the emitter digits.

## Commands

```sh
uv sync                      # Python 3.14, deps: numpy scipy networkx funcy loguru matplotlib
uv run --with pytest pytest ccc -q   # tests (pytest is not a project dep)
uv run ruff format && uv run ruff check --select I --fix
```

Write the outputs for level N (skips the example so its expected output stays intact):

```sh
uv run python -c "
from pathlib import Path
from ccc.__main__ import load
from ccc.contest import solve
for f in Path('data').glob('in_level-N_*.txt'):
    if 'example' not in f.name:
        f.with_name(f.name.replace('in_', 'out_', 1)).write_text(solve(load(f.read_text().splitlines())))
"
```

Write or edit Python files with the Write/Edit tools, not Python heredocs in Bash: on this Windows machine, `\n` escapes in a heredoc came out as literal newlines with CRLF.

## Git workflow

- One commit per level ("Solve level N"), plus a tag `levelN`. Commit the level's `data/` files too (PDF, inputs, outputs). Tick the level off in the README's `## Challenges` list: `- :heavy_check_mark: **[Level N](data/level-N.pdf)** - [Solution](/../levelN/ccc/contest.py)`.
- The user uploads the outputs and confirms they're correct. Only then commit the level, staging only that level's `data/` files, never the next level's.
- The user commits themselves. Don't commit unless asked.
- Remote: `git@github.com:blu3r4y/ccc-linz-oct2026.git`. Pushing needs the user's ssh-agent, so ask them to run `! git push --follow-tags`.
- Reference from the last contest: `../ccc-linz-nov2025`.
