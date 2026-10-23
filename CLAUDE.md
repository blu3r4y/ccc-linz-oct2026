# CCC Linz Oct 2026

Python solutions for the Classic Cloudflight Coding Contest (codingcontest.org). Time-boxed contest: speed over polish.

## Contest format

- Levels 1..N unlock one after another. Each level has a spec PDF, an example input with its expected output, and the real inputs, which get uploaded for scoring.
- The user drops everything into `data/`. **This contest's naming** (unlike the `levelN_M.in` of past contests): `data/level-N.pdf`, `data/in_level-N_M-<name>.txt` (`0-example`, `1-small`, `2-large`, ...), and `data/out_level-N_0-example.txt`. Write outputs next to the inputs as `out_level-N_M-<name>.txt`. Read the PDF for the spec.
- Later levels usually extend earlier ones, so evolve the code in place rather than starting over.
- The contest also asks for the source code as a zip: `git archive --format zip -o code.zip HEAD`.

## Code layout

- `ccc/__main__.py`: `load(lines) -> dict` parses an input file into `{"items": [...]}`: a count line, then N items with blank lines between them. The shape of each item's header line picks the format: `r rows cols` plus the rows gives a `Board` (L2, L3); a lone `r` gives a `Program` `(r, ticks)` (L4). A new input format means a new branch there. The user wants the main loop **left as is**. That loop still expects `levelN_M.in` (and so does `ccc/utils.py`), so `python -m ccc` finds nothing for this contest's files. Use `ccc.run` instead.
- `ccc/contest.py`: `solve(data, level=None) -> str` is the solution. It applies the level's rule (one input item -> final `Board`) to each item, renders each result, and joins them with `"\n\n"` and no trailing newline. `level=None` means the latest level.
  - **New level = new rule function (`fireN`, `runN`, ...) + one entry in `RULES = {level: rule}`** at the bottom of the file. Keep old rules as they are, so old levels stay solvable and tested. Reuse the building blocks (`ray`, `beam_hits`, ...), and split one out when a new level needs part of an old rule.
  - `Board = dict[(row, col), char]`, keyed by ASCII position with the `-` gaps left out ("doubled-width" coordinates; chosen over axial, numpy, or the raw grid).
  - `parse` / `render` convert to and from the ASCII rows. `ray(board, start, digit)` yields the cells a beam crosses (through `O`/`M`) until the border. `hits(board, emitters)` counts the beams over each cell (`beam_hits` does it for the emitters drawn on the board), `create_or_destroy` applies the 2 / 3+ rule, and `ring(r)` lists the border cells clockwise from the west corner. `run_ticks(board, r, ticks)` runs a moving-emitter program on any board (`run4` calls it on an empty hexagon). `hexagon(r)` draws an empty board (L1).
  - `DIRS`: emitter digit -> step, `1=(0,2)` →, `2=(1,1)` ↘, `3=(1,-1)` ↙, `4=(0,-2)` ←, `5=(-1,-1)` ↖, `6=(-1,1)` ↗. Clockwise, so turning is index arithmetic mod 6.
  - Only `parse`, `render`, `DIRS`, `ray`, `hexagon` and `ring` touch raw coordinates. Everything else treats cells as opaque keys (`cell in board`, a `Counter`), so a switch to axial coordinates only changes those.
- `ccc/run.py`: `uv run python -m ccc.run [N]` (default: the latest level in `RULES`). It checks the example against `out_level-N_0-example.txt` (and exits if it doesn't match), then writes `out_level-N_*.txt` for the real inputs.
- `ccc/utils.py`: infers the level and quests from `levelN_M.in` filenames (doesn't match this contest's naming).
- Tests: `ccc/contest_test.py`. Once a level is in `RULES`, `test_outputs` checks every `out_level-N_*.txt` that exists (the example and the confirmed uploads) against `solve(load(in), N)`, so old levels can't silently regress. `test_load_boards` round-trips every input board (add a level to `BOARD_LEVELS` if its items are boards). Add a small hand-traced rule test per level on `hexagon(2)` (the `small()` helper).
- `ccc/scratchpad.ipynb`: notebook for exploring.

## Levels so far

- L1: draw a hexagon board of radius r.
- L2: one emitter, its beam turns `O` into `M` until the border.
- L3: multiple emitters. A cell hit by 2 beams becomes `M`, 3+ hits destroy it, 0-1 hits leave it unchanged. The output may keep the emitter digits.
- L4: input is programs, not boards (`r`, tick count, ticks of 6 commands `F`/`B`/`T`/`-`). The six emitters start off on the corners (emitter d at `ring(r)[(d-1)*r]`) and move along the border; each tick, all commands apply at once, then the active emitters fire with the L3 rule. Emitters are kept off the board dict, because they can share a cell. Output is rendered without emitters.

## Commands

```sh
uv sync                      # Python 3.14, deps: numpy scipy networkx funcy loguru matplotlib
uv run --with pytest pytest ccc -q   # tests (pytest is not a project dep)
uv run ruff format && uv run ruff check --select I --fix
```

Write the outputs for level N (it checks the example first):

```sh
uv run python -m ccc.run [N]
```

Write or edit Python files with the Write/Edit tools, not Python heredocs in Bash: on this Windows machine, `\n` escapes in a heredoc came out as literal newlines with CRLF.

## Git workflow

- One commit per level ("Solve level N"), plus a tag `levelN`. Commit the level's `data/` files too (PDF, inputs, outputs). Tick the level off in the README's `## Challenges` list: `- :heavy_check_mark: **[Level N](data/level-N.pdf)** - [Solution](/../levelN/ccc/contest.py)`.
- The user uploads the outputs and confirms they're correct. Only then commit the level, staging only that level's `data/` files, never the next level's.
- The user commits themselves. Don't commit unless asked.
- Remote: `git@github.com:blu3r4y/ccc-linz-oct2026.git`. Pushing needs the user's ssh-agent, so ask them to run `! git push --follow-tags`.
- Reference from the last contest: `../ccc-linz-nov2025`.
